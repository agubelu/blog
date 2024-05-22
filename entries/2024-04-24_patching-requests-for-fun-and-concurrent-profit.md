Patching requests for fun and (concurrent) profit
---
Because life is too short to spam calls to `SSL_CTX_load_verify_locations()`.

## What's the issue?

Let's consider the following script. It runs a bunch of concurrent requests against a URL using the [requests](https://requests.readthedocs.io/en/latest/) library, both with certificate verification enabled and disabled, and outputs the time it takes to do it in both cases.

```py
from time import time
from threading import Thread
import requests
import urllib3

# Mute warnings when cert verification is disabled
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

What's the time difference between the two? It turns out it is highly dependent on your local configuration. On my local machine, with a relatively modern config (Python 3.12 + OpenSSL 3.0.2), the times are `~1.2s` for `verify=True` and `~0.5s` for `verify=False`.

It's a >100% difference, but we initially blamed it on cert verification not being trivial and taking some time. However, we observed even larger differences (>500%) in some of our  environments, and decided to find out what was going on.

## What's going on?

Our main use case for requests is running lots of requests concurrently, and we spent some time bisecting this oddity to see if there was room for a performance optimization.

The issue is a bit more clear after profiling the concurrent executions. When verifying certs, these are the top 3 function calls by total time spent in them among all threads:

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

In the first case, a full 0.68 seconds are spent in the `load_verify_locations()` function of the `ssl` module, which configures a `SSLContext` object to use a set of root CA certificates for validation. This is done via a C FFI call to OpenSSL's `SSL_CTX_load_verify_locations()` which [is known](https://github.com/python/cpython/issues/95031) to be [quite slow](https://github.com/openssl/openssl/issues/16871). This happens once per request (hence the `30` on the left).

Taken at face value, 0.68 seconds isn't that big of a deal, but please note that this is **longer than the network wait for the requests themselves**. In scenarios with a higher concurrency, we have also observed some global blocking going on, either because each FFI call locks up the GIL or because of some thread safety mechanisms in OpenSSL itself. In either case, the performance hit gets worse and worse as you scale the number of concurrent requests up. We also think that this is more or less pronounced depending on internal changes between OpenSSL's versions, hence the variability between environments.

When cert validation isn't needed, these calls are skipped which speeds up concurrent performance dramatically.

## A possible fix

It isn't possible to skip loading root CA certificates entirely, but it isn't necessary to do it on every request. At the time of writing this, a call to `load_verify_locations()` happens when:

- A new `urllib3.connectionpool.HTTPSConnectionPool` is created, or

- On each connection, by urllib3's `ssl_wrap_socket()`, when the connection's `ca_certs` or `ca_cert_dir` attributes are set (see [the relevant code](https://github.com/urllib3/urllib3/blob/9929d3c4e03b71ba485148a8390cd9411981f40f/src/urllib3/util/ssl_.py#L438)).

Recently, Requests added an internal `_get_connection()` function that caches connection pools, and so, for most cases, the first case doesn't need to be addressed anymore, since most HTTPS requests will share the same cached `HTTPSConnectionPool` instead of creating one per request.

The second one is addressed in [the submitted PR](https://github.com/psf/requests/pull/6667). It creates a default `SSLContext` with the default CA certificates already loaded, and patches the function that hooks up each connection with a secure context to reuse the default one:

```py
DEFAULT_SSL_CONTEXT = create_urllib3_context()
DEFAULT_SSL_CONTEXT.load_verify_locations(extract_zipped_paths(DEFAULT_CA_BUNDLE_PATH))

def _urllib3_request_context(
    ...
    cert_reqs = "CERT_REQUIRED"
    if verify is False:
        cert_reqs = "CERT_NONE"
+   elif verify is True:
+       pool_kwargs["ssl_context"] = DEFAULT_SSL_CONTEXT
+   elif isinstance(verify, str):
+       if not os.path.isdir(verify):
+           pool_kwargs["ca_certs"] = verify
+       else:
+           pool_kwargs["ca_cert_dir"] = verify
    pool_kwargs["cert_reqs"] = cert_reqs
```

When `verify=True`, we provide the connection pool with a `SSLContext` with the CA certificates already loaded. As shown, by not setting `ca_certs` or `ca_cert_dir` in that case, we avoid a spurious call to `load_verify_locations()` by urllib3 and cert verification still works as intended. A couple of additional changes are also made in the PR to carefully avoid setting those two connection parameters when not needed.

A small caveat happens when `verify` isn't a boolean, but rather a string indicating a path to an alternative CA bundle or cert store. In those cases, we do set `ca_certs` or `ca_cert_dir` accordingly to ensure that the alternative CA bundle requested by the user is loaded instead. There is further room for optimization here, because this use case will still incur in a call to `load_verify_locations()` per request. Perhaps the previous approach could be generalized by caching different `SSLContext` objects depending on the CA bundle that the request wishes to use.

---

Update: The corresponding [pull request](https://github.com/psf/requests/pull/6667) has since been accepted by the maintainers and merged, and the changes have been published in version [2.32.0](https://github.com/psf/requests/blob/main/HISTORY.md#2320-2024-05-20) of Requests.