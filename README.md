# multi-app-edge

**Many applications, one domain, one small server.** A reference implementation of the hosting pattern I ran for 13 live services during my internship: a single nginx reverse proxy in front of independent containerised apps, each mounted under its own path prefix, all sharing one PostgreSQL instance.

Written from scratch as a public, runnable reference. No employer code.

```
                     ┌──────────────────────────┐
  browser ─────────▶ │  nginx edge  :80         │
                     │  one domain, path prefix │
                     └───┬──────────────────┬───┘
                         │ /alpha/          │ /beta/
                         ▼                  ▼
                  ┌─────────────┐    ┌─────────────┐
                  │ Django+     │    │ static SPA  │
                  │ gunicorn    │    │ (nginx)     │
                  └──┬───────┬──┘    └─────────────┘
                     │       │
            ┌────────▼──┐ ┌──▼──────┐
            │ celery    │ │  redis  │
            │ worker    │ └─────────┘
            └────────┬──┘
                     ▼
        ┌────────────────────────────┐
        │  shared PostgreSQL 16      │
        │  db + login role per app   │
        └────────────────────────────┘
```

## Why this exists

A VM with 4 GB of RAM will not hold a dozen projects if each one brings its own database container. Measured on the real system:

| | per-project stack | shared instance |
|---|---|---|
| PostgreSQL memory | 100–150 MB **each** | ~200 MB **total** |
| Memory per project | ~2 GB | 0.5–1 GB |
| Projects the server holds | *n* | roughly **2n** |

The shared instance freed about a gigabyte of RAM. Explicit CPU and memory limits did the rest. Neither change required touching application code.

## Run it

```bash
cp .env.example .env
docker compose up --build
```

Then:

- http://localhost:8080/alpha/ — Django, reports the prefix and scheme it sees
- http://localhost:8080/alpha/readyz — readiness, checks the database
- http://localhost:8080/beta/ — static SPA, confirms its assets loaded
- http://localhost:8080/healthz — the edge itself

## What this demonstrates

**Path-prefix routing done twice, correctly, in two different ways.** Django is *told* it lives at `/alpha` (`FORCE_SCRIPT_NAME`) and the prefix is passed through untouched, so every URL it generates carries the prefix. The static app is built at `/` and the prefix is *stripped* by an explicit `rewrite`. Getting these backwards produces the two classic failures: redirects that dump the user on the domain root, and `.css`/`.js` requests answered with `index.html`, which the browser reports as a MIME-type error.

**A proxy that survives its backends.** Upstreams are given as variables with Docker's DNS named as `resolver`, so nginx resolves them per request. With literal upstreams, one unavailable container stops nginx from starting — taking down every other app on the box.

**Multi-tenant PostgreSQL.** One instance, one database and one login role per service, `public` schema locked down so tenants cannot create objects in each other's namespace. See [docs/postgres-migration.md](docs/postgres-migration.md) for moving a live database into it without losing data.

**Operational defaults, not afterthoughts.** Every service has CPU and memory limits, a restart policy and log rotation. This is [why](docs/incidents.md).

**Liveness separated from readiness.** `/healthz` deliberately does not touch the database — a health check that fails when PostgreSQL blips will restart-loop a perfectly healthy app. `/readyz` does check it, because an app that cannot reach its database should not receive traffic.

**CI that tests the system, not the images.** The [pipeline](.github/workflows/ci.yml) validates the compose file and nginx config, builds, starts the whole stack, and then asserts that each app answers *through the proxy under its own prefix* and that assets come back with the right content types. Building images proves nothing about whether the routing works.

## Repository layout

```
docker-compose.yml          services, networks, resource limits, log rotation
nginx/conf.d/default.conf   the edge: prefixes, rewrites, security headers
postgres/init/              per-service database and role creation
apps/alpha/                 Django under a prefix + celery worker
apps/beta/                  static SPA under a prefix
docs/postgres-migration.md  moving a live database into the shared instance
docs/incidents.md           four failures and what each one changed
.github/workflows/ci.yml    build, start, verify routing end to end
```

## What this is not

Not production-ready as-is. TLS terminates elsewhere, secrets come from `.env` rather than a secret store, and there is no metrics or alerting stack. Those are the next three things I would add, in that order.

---

Built by [Zhanibek Sultanbek](https://github.com/ZSultanbek) · Almaty
