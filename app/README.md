## ParcelPost app

Demo shipment-tracking service for the canary pipeline project.
Scope and API are defined in ADR 001 ('docs/adr/001-application.md').

## Run the tests

From this folder, in the devcontainer:

    pip install -r requirements.txt
    python -m pytest -q

Tests run against an in-memory SQLite database; the app itself targets Postgres (see below).

## Set up the database

The app reads its database location from the 'DATABASE_URL' environment variable; the default points at a local Postgres with user, password, and database all named 'parcelpost'.

From the repository root, one command takes an empty database to migrated and seeded:

    make db-setup

It runs the Alembic migrations ('alembic upgrade head') and then the seed script ('app/src/seed.py'), which inserts ten demo shipments - two in each status. The seed is safe to re-run: if the table already has rows, it inserts nothing.

To start over from an empty database:

    cd app
    alembic downgrade base
    cd ..
    make db-setup


## Schema changes must stay backward-compatible

Stable and canary run side by side against ONE database during a rollout, and rollback can swap the pods back to the old version at any moment - but it cannot roll back the schema. The old code must therefore keep working against the new schema, and the new code against the old one, for the whole rollout window.


In practice:

- Expand first: add new columns as nullable (or with a default),
  and only start requiring them in a later release.
- Never rename or drop a column in the same release that stops
  using it. A rename is: add the new column, copy the data, drop
  the old column in a following release.
- Every migration ships with code that works with both the schema
  before it and the schema after it.


## Failure injection

Three environment variables turn the running service bad on purpose, for
canary analysis and the failure scenario suite. All three are off by
default, are read once at startup (change them and restart), and never
affect /healthz, /readyz, /metrics, or /version.

- `FAILURE_ERROR_RATE` — probability (0 to 1) that a business request
  fails with a 500 before doing any work. Unset or 0 means no failures.
- `FAILURE_LATENCY_MS` — milliseconds of delay added to each business
  request before the failure roll. Unset or 0 means no added latency.
- `FAILURE_TARGET` — restricts injection to one operation, written as
  method + route template, e.g. `POST /shipments`. Unset means all
  business operations.