Patching requests for fun and (concurrent) profit
---
Because life is too short to spam calls to `SSL_CTX_load_verify_locations()`.

## Reproducing the problem

Let's consider the following script. It runs a bunch of concurrent requests against a URL using the [requests](https://requests.readthedocs.io/en/latest/) library, both with certificate verification enabled and disabled, and outputs the time it takes to do it in both cases.

```py
from time import time
from threading import Thread
import requests
import urllib3

urllib3.disable_warnings()

def do_request(verify):
    requests.get('https://example.com', verify=verify)

def measure(verify):
    threads = [Thread(target=do_request, args=(verify,)) for _ in range(30)]

    start = time()
    for t in threads: t.start()
    for t in threads: t.join()
    end = time()

    print(end - start)

measure(verify=True)
measure(verify=False)
```

What's the time difference between the two? It turns out it is highly dependent on your local configuration. In my local machine, with a relatively modern config (Python 3.12 + OpenSSL 3.0.2), the times are `~1.2s` for `verify=True` and `~0.5s` for `verify=False`.

It's a >100% difference, but we initially blamed it on cert verification taking some time. However, we observed even larger differences (>500%) in some environments, and decided to find out what was going on.

## Problem description

Our main use case for requests is running lots of requests concurrently, and we spent some time bisecting this oddity to see if there was room for a performance optimization.

The issue is a bit more clear if you profile the concurrent executions. When verifying certs, these are the top 3 function calls by time spent in them:

```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
30/1    0.681    0.023    0.002    0.002 {method 'load_verify_locations' of '_ssl._SSLContext' objects}
30/1    0.181    0.006    0.002    0.002 {method 'connect' of '_socket.socket' objects}
60/2    0.180    0.003    1.323    0.662 {method 'read' of '_ssl._SSLSocket' objects}
```

Conversely, this is how the top 3 looks like without cert verification:

```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
30/1    0.233    0.008    0.001    0.001 {method 'do_handshake' of '_ssl._SSLSocket' objects}
30/1    0.106    0.004    0.002    0.002 {method 'connect' of '_socket.socket' objects}
60/2    0.063    0.001    0.505    0.253 {method 'read' of '_ssl._SSLSocket' objects}
```

In the first case, a full 0.68 seconds are spent in the `load_verify_locations()` function of the `ssl` module, which configures a `SSLContext` object to use a set of CA certificates for validation. Inside it, there is a C FFI call to OpenSSL's `SSL_CTX_load_verify_locations()` which [is known](https://github.com/python/cpython/issues/95031) to be [quite slow](https://github.com/openssl/openssl/issues/16871). This happens once per request (hence the `30` on the left).

We believe that, in some cases, there is even some blocking going on, either because each FFI call locks up the GIL or because of some thread safety mechanisms in OpenSSL itself. We also think that this is more or less pronounced depending on internal changes between OpenSSL's versions, hence the variability between environments.

When cert validation isn't needed, these calls are skipped (though not always, see below) which speeds up concurrent performance dramatically.

## Submitted solution

It isn't possible to skip loading root CA certificates entirely, but it isn't necessary to do it on every request. More specifically, a brand new `SSLContext` is created every time a `PoolManager` is created. In requests, this is every time a `Session` is created (since `requests.get()` and friends create a one-time use `Session`, this happens on every request). Before connecting, the `SSLContext` is provided the relevant CA bundle or directory and it loads it via `load_verify_locations()`.

We can stop the `PoolManager` constructor from creating a brand new and empty `SSLContext` every time if we give it an existing context. The main change made in this PR is the creation of a module-level `SSLContext` object in `adapters.py`, in which we load the default CA certificate bundle, and then pass it on to all `PoolManager`s created by the HTTP adapter:

```py
DEFAULT_SSL_CONTEXT = create_urllib3_context()
DEFAULT_SSL_CONTEXT.load_verify_locations(DEFAULT_CA_BUNDLE_PATH)

(...)

self.poolmanager = PoolManager(
     num_pools=connections,
     maxsize=maxsize,
     block=block,
+    ssl_context=ssl_context,
     **pool_kwargs,
)
```

This allows us to call `load_verify_locations()` only once on module load and still supply all connections with a SSL context they can use to verify server certificates.

To fully make this work, we also had to patch `HTTPAdapter.cert_verify()` to not set the connection's `ca_certs` or `ca_cert_dir` attributes, since this triggers a call to the connection's context's `load_verify_locations()` by urllib3 (see [the relevant code](https://github.com/urllib3/urllib3/blob/9929d3c4e03b71ba485148a8390cd9411981f40f/src/urllib3/util/ssl_.py#L438)):




Since the connection uses a SSL context with the certs already loaded, cert validation still works fine. I set up a server with an expired certificate at https://badcert.agube.lu, so you can test against that URL instead of Amazon's robots.txt to check that `verify=True` and `verify=False` still behave as expected and are now equally fast.

### Caveat

This works fine if using the system's default CA bundle of root certificates, since it's what's loaded in the default SSL context that's reused. However, this isn't always the case: the user can request to use a different bundle by setting the `REQUESTS_CA_BUNDLE` or `CURL_CA_BUNDLE` env variables, or by passing an explicit bundle path to the `verify` parameter.

Since `Session.merge_environment_settings` takes care of setting the `verify` argument to a path if a relevant environment variable is in use, we work around this by checking if an alternative bundle should be used in `cert_verify()`. In that case, `ca_certs` or `ca_cert_dir` are set again to trigger loading the requested bundle:

```py

```

If this happens, the performance optimization is lost as `load_verify_locations()` is called on every request again, but the desired behavior is maintained.