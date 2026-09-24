# Moving a live database into the shared instance

Runbook for migrating a running project from its own PostgreSQL container into the shared instance, without losing data and without a one-way door.

This is the procedure I used on a live project. The verification steps are the point — a restore that "completed successfully" is not evidence that the data arrived.

## Before you start

- Know the row counts you expect. If you cannot say what "correct" looks like afterwards, you cannot verify the migration.
- Do this during a quiet window. Writes during the dump are lost.
- **Keep the old volume.** Do not delete anything until the new path has proven itself under real traffic.

## 1. Create the tenant

```sql
CREATE ROLE myapp WITH LOGIN PASSWORD '<from your secret store>';
CREATE DATABASE myapp OWNER myapp;
REVOKE ALL ON DATABASE myapp FROM PUBLIC;
GRANT CONNECT ON DATABASE myapp TO myapp;

\connect myapp
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO myapp;
```

## 2. Record the source state

```bash
# Row counts per table, saved for comparison
docker compose exec old-db psql -U myapp -d myapp -Atc "
  SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname;
" > /tmp/before.txt

# Sequence values - the part people forget
docker compose exec old-db psql -U myapp -d myapp -Atc "
  SELECT schemaname||'.'||sequencename, last_value
  FROM pg_sequences ORDER BY 1;
" > /tmp/before-seq.txt
```

`n_live_tup` is an estimate. For small tables, or when it matters, use real `COUNT(*)` queries.

## 3. Stop writes

```bash
docker compose stop myapp myapp-worker
```

The worker matters as much as the web process. A background job writing during the dump is exactly the data you will lose.

## 4. Dump and restore

```bash
docker compose exec old-db pg_dump -U myapp -d myapp -Fc -f /tmp/myapp.dump
docker compose cp old-db:/tmp/myapp.dump ./myapp.dump

docker compose cp ./myapp.dump postgres:/tmp/myapp.dump
docker compose exec postgres pg_restore -U postgres -d myapp --no-owner --role=myapp /tmp/myapp.dump
```

`-Fc` (custom format) allows selective restore and parallelism; a plain SQL dump does not. `--no-owner --role=myapp` makes everything land owned by the tenant role rather than the source's owner.

Read the `pg_restore` output. Errors here scroll past easily and a partial restore looks a lot like a successful one.

## 5. Verify before switching

```bash
docker compose exec postgres psql -U myapp -d myapp -Atc "
  SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname;
" > /tmp/after.txt

diff /tmp/before.txt /tmp/after.txt && echo "row counts match"
```

Then sequences:

```bash
docker compose exec postgres psql -U myapp -d myapp -Atc "
  SELECT schemaname||'.'||sequencename, last_value FROM pg_sequences ORDER BY 1;
" > /tmp/after-seq.txt

diff /tmp/before-seq.txt /tmp/after-seq.txt && echo "sequences match"
```

**Sequences are the trap.** If they restore behind the data, the application starts issuing primary keys that already exist, and you get duplicate-key errors on the first insert — minutes after you have declared the migration a success.

Fix them explicitly if they drifted:

```sql
SELECT setval('mytable_id_seq', (SELECT COALESCE(MAX(id), 1) FROM mytable));
```

## 6. Switch over

Point the app at the new database and start it:

```bash
# DATABASE_URL=postgres://myapp:<password>@postgres:5432/myapp
docker compose up -d myapp myapp-worker
docker compose logs -f myapp
```

Then exercise it for real: a read, a write, a background job. A migration verified only by `SELECT 1` is not verified.

## 7. Wait, then clean up

Leave the old container stopped and its volume intact for at least a few days of normal traffic. Rolling back is a one-line change while that volume exists, and impossible once it is gone.

Only then:

```bash
docker compose rm -f old-db
docker volume rm <project>_old-db-data
```

## If it goes wrong

Point `DATABASE_URL` back at the old container and start it. That is the entire rollback, and it is only available because step 7 has not been done yet. This is why the old volume stays.
