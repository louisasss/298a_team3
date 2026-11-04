# ADR 001: Demo application scope

**Status:** Proposed — awaiting team sign-off (team meeting, Nov 4, 2026)
**Date:** Nov 3, 2026
**Author:** Akshit Tyagi
**Issue:** T3-66 — Define the app scope and implement core endpoints with tests
**Deciders:** Akshit Tyagi, Sang Ah Lee, Pragya Priyadarshini, Louisa Stumpf

## Context

The conventional CI/CD pipeline — and later the agent pipelines built on it —
needs a demo service to build, deploy, canary, and deliberately break. The
service has to be small enough to build and verify quickly, but real enough
that its releases can fail in the ways the project studies: error spikes,
latency regressions, and single-endpoint failures.

This record fixes the application's scope before implementation begins, so
the Step 1 issues (endpoints, database, metrics, failure injection,
containerization) all build against one agreed contract. It fixes scope and
behavior, not the implementation stack — the stack follows the pinned team
toolchain from the repo-setup issue.

## Decision Drivers

- **The demo must explain itself in minutes.** The service is demoed live
  (Team Meeting 2, Nov 12) to an audience that has never seen it; the
  domain has to be graspable in one sentence, with no business rules to
  learn first.
- **/readyz must have a real dependency to fail against.** T3-66 requires
  /readyz to fail when a required dependency is unreachable; a service
  with no required dependency makes that criterion untestable.
- **The failure scenarios must be demoable on the service.** Error spike,
  latency regression, single failing endpoint, and borderline behavior
  (T3-86) each need a natural home in the service's endpoints.
- **Schedule is a real counterweight.** The Step 1 chain gates the rest
  of the pipeline work; a smaller, stateless service would be faster to
  build. This driver pushed toward the stateless option; it was weighed
  and is recorded under Alternatives, not ignored.
- **Stable and canary share one database.** Any data design must keep
  schema changes backward-compatible while both versions are live.

## Decision

### The service

**ParcelPost**, a mock parcel-delivery company. The demo service is its
shipment-tracking API: the service customers and internal systems call to
create a shipment and follow it to delivery.

### Endpoints

| Method | Path | Purpose | Success | Error paths |
|---|---|---|---|---|
| GET | /shipments | List shipments, optional `?status=` filter | 200, list of shipments | 400 — unknown filter value |
| GET | /shipments/{id} | Fetch one shipment | 200, the shipment | 404 — unknown id |
| POST | /shipments | Create a shipment (`origin`, `destination`) | 201, shipment with generated `tracking_code`, status `created` | 400 — missing or empty field |
| PATCH | /shipments/{id}/status | Advance the shipment's status | 200, updated shipment | 400 — unknown status value; 404 — unknown id; 409 — illegal status transition |
| GET | /healthz | Liveness | 200 while the process is up; checks nothing external | — |
| GET | /readyz | Readiness | 200 when the database is reachable | 503 — database unreachable |

Declared here, implemented under their own issues:

| Method | Path | Purpose | Issue |
|---|---|---|---|
| GET | /metrics | Prometheus metrics (request counts, latency, build info) | T3-68 |
| GET | /version | Running version (commit SHA) | T3-69 |

### Status lifecycle

`created → picked_up → in_transit → out_for_delivery → delivered`

Transitions follow the order above. Skipping a state or moving backwards
from `delivered` is an illegal transition (409). A status value outside the
lifecycle is a bad request (400).

### Data

Database-backed. One table, `shipments`:

`id, tracking_code, origin, destination, status, created_at, updated_at`

Seed data ships with the schema: a handful of shipments spread across the
statuses, so list, filter, and detail endpoints show real data on first run.

Stable and canary versions share one database, so all schema changes must
be backward-compatible (additive) while both versions are live.

### Health and readiness

- `/healthz` is liveness only: it must never depend on the database or any
  external system, or Kubernetes would restart healthy pods during a
  dependency outage.
- `/readyz` is readiness: 200 only when the service can serve traffic,
  which means the database answers. When it does not, readyz returns 503
  and the pod leaves the Service endpoints without being restarted.

### Failure scenarios the service must support

Via environment-variable failure-injection switches (T3-69; off by default):
an error-rate switch, an added-latency switch, and a single-endpoint
failure switch that can target one route (e.g. POST /shipments) alone.

These support the five verification scenarios (T3-86): healthy release
(promote), error spike (abort), latency regression (abort), single failing
endpoint (abort), borderline behavior (pause / Inconclusive).

Every endpoint ships with at least one success-path test and one
error-path test, including a test that /readyz returns 503 when the
database is unreachable; one command runs the full suite (per T3-66).

## Consequences

**What this enables**

- Every acceptance criterion of T3-66 is genuinely satisfiable — in
  particular, `/readyz` has a real required dependency to fail against.
- The richest demo of the candidates considered: creation failures, status
  errors, and dependency failures are all realistic production incidents.
- The single-endpoint switch has a meaningful target (POST /shipments):
  writes fail while reads stay healthy.

**What it costs**

- T3-67 (schema, migrations, seed data) and T3-79 (database in-cluster
  with persistent storage and secrets) remain in scope as real work.
- T3-79 additionally depends on the Kustomize base/overlay setup issue.
- The database is one more component to run in Compose locally and in the
  cluster later.

## Alternatives considered

**Stateless quote/rate service** — same endpoint shape and failure switches,
every operation computed in memory, no database. It would have skipped
T3-67 and T3-79 by those issues' own wording, saving roughly 5–10 hours and
one cross-team dependency. Not chosen: with no database, `/readyz` has no
required dependency to fail against, so that T3-66 criterion would need
rewording and would be weaker; and the demo loses any dependency-failure
story. The schedule saving did not outweigh the weaker acceptance criteria
and demo.


