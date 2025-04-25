The Art of the Upsert
---

Upserts are some of the most convenient database operations, and yet many people haven't heard of them. In this post we'll briefly explore what they are, and how to squeeze every last bit of performance out of them in Postgres.

## What's an upsert?

I'm sure you have dealt with this situation before: you have a piece of data with a unique identifier, which may or may not exist in the database. If it doesn't exist, we want to insert it as a new entry. If it does exist, we want to update the existing record with the latest information.

Upserts are short for update-or-insert, and they cover this exact use case. They provide a convenient way to either insert a row or update an existing one. This is done atomically, in a single statement, thus guaranteeing either outcome.

Using upserts has some obvious benefits: first, they simplify your logic *a lot*, because you can use the same code path for both cases instead of having to treat them separately. But their atomicity also means you don't have to deal with an entire class of concurrency-related problems, especially if the database in question has a high volume of possibly-overlapping writes.

## Upserts in Postgres

Let's see how upserts work with a specific example. Imagine a personal content manager for a blog, where a user writes and updates their posts. Each post has an internal ID, a unique slug[^1], some textual content, and the timestamps when it was created and last updated.

The corresponding table definition in Postgres would look like this:

```sql
CREATE SEQUENCE blog_post_id_seq;

CREATE TABLE blog_post (
    id INT PRIMARY KEY DEFAULT nextval('blog_post_id_seq'),
    slug TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

You can probably already imagine a front-end form that handles both the creation and update cases. If the received post has a slug that is not yet present in the table, we will insert a new row. If it already exists, we want to update the `content` and `updated_at` fields accordingly. An upsert, in other words.

In Postgres, we can upsert a blog post with the following query:

```sql
INSERT INTO blog_post (slug, content)
SELECT
    :slug,
    :content
ON CONFLICT (slug) DO UPDATE SET
    content = EXCLUDED.content,
    updated_at = now();
```

There are a few details to unpack here:

- The values preceded by colons, like `:slug`, are query placeholders for the actual values to be inserted.
- The `ON CONFLICT` clause must be provided with a target, indicating exactly *what* should be conflicting for it to trigger. This can either be a column name or an expression covered by a `UNIQUE` index.
    - Another option is `ON CONFLICT DO NOTHING` if you don't wish to update an existing value. In this case, the conflict target can be omitted, and it will be triggered by any `UNIQUE` violation.
- The keyword `EXCLUDED` alludes to the row that we tried to insert, so `EXCLUDED.content` is the same as `:content`.

This is sufficient for a basic upsert, but this query has some shortcomings that we can address.

### Optimizing sequence usage

When we tried to insert new values, we explicitly listed only the columns `slug` and `content`. In order to complete the insertion attempt, Postgres automatically calculates the default values for all other columns. In the case of `id`, since we intended it to be an auto-incremental value, the default is `nextval('blog_post_id_seq')`.

This means that, for every upsert, the sequence we're using for our primary key is advanced, regardless of whether or not an insertion actually occurs. If there is a conflict and an update is performed instead, the value we obtained from the sequence is discarded. You can test this by inserting a new value, updating it a bunch of times, and then inserting a different one. You will see that the ID assigned to the new one has a gap equal to the number of updates performed.

This is not ideal, and can end up quickly exhausting an `INT` (32 bit) sequence if there's a high volume of upserts. The solution is to explictly provide a value for the `id`, only advancing the sequence when needed:

```sql
INSERT INTO blog_post (id, slug, content)
SELECT
    coalesce(
        (SELECT id FROM blog_post WHERE slug = :slug),
        nextval('blog_post_id_seq')
    ),
    :slug,
    :content
ON CONFLICT (slug) DO UPDATE SET
    content = EXCLUDED.content,
    updated_at = now();
```

Here, `coalesce()` is a function that receives any number of arguments, and returns the first one that is not null. Its arguments are lazily evaluated. This prevents spurious use of the sequence by reusing the existing ID whenever possible[^2], only advancing the sequence for actual insertions.

[^1]: A slug is a text-based unique identifier that is commonly used as part of a URL. For example, this post's slug is `the-art-of-the-upsert`.

[^2]: You may notice that now, when an entry already exists, both `slug` and `id` will trigger a conflict. In this query, you can use either `ON CONFLICT (id)` or `ON CONFLICT (slug)` as they are now equivalent.

### Write optimizations

We can still improve the previous upsert. When it updates an existing post, it will always trigger a write, regardless of whether or not the content has already changed.

This is problematic for a couple of reasons: first, writing data takes time and requires acquiring write locks, so avoiding a write when it's not necessary is an important optimization, especially for busy tables. Additionally, the `updated_at` column gets overwritten with the current timestamp, even if the content didn't change.

We can avoid the need for a write by adding a `WHERE` clause:

```sql
INSERT INTO blog_post (id, slug, content)
SELECT
    coalesce(
        (SELECT id FROM blog_post WHERE slug = :slug),
        nextval('blog_post_id_seq')
    ),
    :slug,
    :content
ON CONFLICT (slug) DO UPDATE SET
    content = EXCLUDED.content,
    updated_at = now()
WHERE
    blog_post.content IS DISTINCT FROM EXCLUDED.content;
```

Using `IS DISTINCT FROM` instead of `<>` in this clause is highly recommended. The difference is that, when `NULL` values are involved, `IS DISTINCT FROM` behaves as you'd expect, while `something <> NULL` is always `NULL`. Using `IS DISTINCT FROM` makes `NULL` comparable to other values and equal to itself. Even though in this particular case the relevant column is `NOT NULL`, it's still a good habit to have.

If answering the question "has anything changed?" requires comparing more columns, the most compact way to do it is:

```sql
INSERT INTO mytable (...)
SELECT
    ...
WHERE
    (my_table.a, my_table.b, my_table.c)
    IS DISTINCT FROM
    (EXCLUDED.a, EXCLUDED.b, EXCLUDED.c)
```

There is one last optimization, which you will probably only need if you have a high throughput of write operations to your table. Although the previous change has removed the need for a write when it's not needed, Postgres still acquires write locks for those rows. In busy environments, and especially for highly referenced rows, this can lead to lock contention issues.

The only way to avoid acquiring a write lock in such cases is by not having any data to write in the first place, discarding it via another `WHERE` clause:

```sql
INSERT INTO blog_post (id, slug, content)
SELECT
    coalesce(
        (SELECT id FROM blog_post WHERE slug = :slug),
        nextval('blog_post_id_seq')
    ),
    :slug,
    :content
WHERE NOT EXISTS (
    SELECT 1 FROM blog_post
    WHERE slug = :slug
      AND content IS NOT DISTINCT FROM :content
)
ON CONFLICT (slug) DO UPDATE SET
    content = EXCLUDED.content,
    updated_at = now()
WHERE
    blog_post.content IS DISTINCT FROM EXCLUDED.content;
```

At this point, you will probably notice that the `WHERE NOT EXISTS` and `ON CONFLICT ... WHERE` clauses seem redundant. However, they can't be simplifier further. This is because using only `WHERE NOT EXISTS` runs into concurrency issues if two or more simultaneous transactions try to insert an element with the same unique identifier.

In this scenario, all concurrent transactions will evaluate `NOT EXISTS` as true and will try to insert the values. Only one of them will succeed, and all the remaining ones will error out due to the `UNIQUE` violation. This is exactly what `ON CONFLICT` is supposed to handle, and why it is still required in the query.