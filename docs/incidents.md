# Incidents

Four failures from running this pattern for real, and what each one permanently changed. Every one of them was found in logs, not by guessing.

---

## 1. An unbounded ML service exhausted a worker node

**Symptom.** A Swarm worker node became unresponsive. Services scheduled on it stopped answering.

**Cause.** I deployed a machine-learning inference service with resource limits set from a guess rather than from measurement. Under real input it consumed everything the node had.

**Fix.** Measured actual consumption under load, revised the limits to match, restarted the service.

**What changed permanently.** CPU limits, memory limits, a restart policy and log rotation became a mandatory part of every deployment, not something added when a service misbehaves. Both are visible in `docker-compose.yml`.

**The honest version.** The limits existed before the incident — they were just wrong, because I set them without measuring first. A limit you guessed is not a limit, it is a hope.

---

## 2. Stylesheets and scripts failing as "MIME-type errors"

**Symptom.** An app under a path prefix rendered unstyled. The browser console reported a MIME-type refusal for `.css` and `.js`.

**Cause.** Nothing to do with MIME types. The prefix was being handled incorrectly at the proxy, so asset requests fell through to the SPA fallback and were answered with `index.html`. The browser correctly refused to execute HTML as JavaScript and reported the content type it got.

**Diagnosis.** The receiving container's own access log showed the asset requests arriving as `/` — that is where the truth was, not in the browser error.

**Fix.** An explicit `rewrite` for the prefix, plus an asset location that returns 404 rather than falling through. Both are in `nginx/conf.d/default.conf` and `apps/beta/nginx.conf`.

**Lesson.** The error the browser reports and the error that occurred are often different errors. Trust the server log over the client message.

---

## 3. A service still running configuration I had already changed

**Symptom.** A config change had no effect. The file on disk was unambiguously correct.

**Cause.** The running process still held the old configuration. The file and the process are not the same thing, and I had been verifying the file.

**Fix.** Recreate the container, not just edit the file.

**What changed permanently.** After any configuration change I verify against the running process — its environment, its effective config, its behaviour through the proxy — and never against the file I just edited.

---

## 4. A worker that could not resolve the database host

**Symptom.** A Celery worker failed every task with a DNS resolution error for the database host. The web application, using the same connection string, was fine.

**Cause.** The worker had not been attached to the network the database was on. Same string, different network namespace, different answer.

**Fix.** Attach the worker to the shared data network. Visible in `docker-compose.yml`, where `alpha-worker` joins `data`.

**Related.** A long-running worker also accumulates stale database connections — the socket dies quietly and the error surfaces hours later as an `InterfaceError`. `apps/alpha/config/middleware.py` closes old connections at the boundary, and `conn_health_checks` is enabled in the database settings.

---

## The pattern across all four

Three of these produced a symptom that pointed somewhere other than the cause: a MIME-type error that was a routing bug, a config that was correct on disk and stale in memory, a DNS failure that was a network-attachment mistake. In each case the container's own logs held the real answer.

The fourth was mine outright, and it is the one that changed the most about how I deploy anything.
