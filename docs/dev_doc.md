# Paddlingen Development Document

Last updated: 2026-03-17

## Purpose

This document is the practical development reference for the project.

Use it to record:

- how the project is run locally,
- what commands are used,
- what setup steps are required,
- what has been implemented,
- why a technical choice was made,
- what should be updated when the workflow changes.

This document should be updated whenever the development workflow changes or a
new important command/process is introduced.

## Documentation Rule

If something changes in how the project is developed, tested, or run, update
this file.

Examples:

- a new setup step,
- a new dependency,
- a new required environment variable,
- a new test command,
- a new Docker command,
- a changed deployment-related workflow,
- a changed payment or database workflow.

## Supabase Direction

The current roadmap direction is:

- keep the Flask app containerized with Docker,
- test the database against a hosted Supabase project,
- keep SQLAlchemy and Alembic as the main backend data layer.

Why:

- Official Supabase guidance recommends Postgres connection strings for
  Postgres clients and persistent backend services.
- The current app already works through SQLAlchemy, so the first Supabase test
  should use `DATABASE_URL` instead of rewriting backend code.

## Current Development Environment

- Main development machine: Windows 11
- Main development shell: WSL
- Expected shell: `bash`
- Expected working directory: project root
- Docker commands assume Docker Desktop is installed on Windows and WSL
  integration is enabled for this distro.

## Important Event Settings

The main event values that are likely to change between years should be edited
in `config.py`.

Examples:

- event year,
- event date,
- event time,
- canoe count,
- canoe price,
- location name,
- location map URL.

Why:

- These values were moved into one easy-to-find place so yearly updates and
  pre-event testing are simpler.

Example use case:

- If you want to test the weather API before the real event, temporarily change
  the event date values in `config.py`, reload the app, and verify the weather
  widget behavior.

Important note:

- If you change these values, also check whether any user-facing copy or
  previous-year section labels should be updated.

## Common Commands

### Install dependencies

```bash
make install
```

Why:

- Installs project dependencies using `uv`.

Alternative:

```bash
uv sync
```

### Run the test suite

```bash
make test
```

Why:

- Runs the automated test suite with pytest.

Alternative:

```bash
uv run -m pytest -q
```

### Run linting

```bash
make lint
```

Why:

- Checks the codebase with Ruff.

### Check formatting

```bash
make format-check
```

Why:

- Verifies whether the code matches the expected Black formatting.

### Apply formatting

```bash
make format
```

Why:

- Formats the codebase with Black.

### Run type checking

```bash
make type-check
```

Why:

- Runs mypy to catch type-related issues.

## Current Local Run Flow

The project still reflects an older local workflow and will be updated further
as the roadmap progresses.

### Start the app locally

```bash
uv run flask --app wsgi --debug run
```

Why:

- Starts the Flask development server.

Current note:

- The roadmap plans to move local development toward Docker for the Flask app
  and Supabase for the first real hosted database tests.
- When that happens, this section must be updated.

## Current Docker Commands

These commands are for the first app-container step only.

### Build the Flask app image

```bash
docker build -t paddlingen-web .
```

Why:

- Builds the current Flask application container from the root `Dockerfile`.

### Run the Flask app container

```bash
docker run --rm -p 8080:8080 --env-file .env paddlingen-web
```

Why:

- Starts the Flask app container and exposes it on `http://127.0.0.1:8080`.

Important note:

- This is only the first Docker step.
- The database is planned to be tested through Supabase rather than a local
  PostgreSQL container.
- Until the Supabase integration step is completed, the app container will
  still use its current database configuration path.

## Current Supabase Setup Notes

For the current roadmap direction, gather these values from the Supabase
dashboard:

- database connection string,
- database password.

Optional later values:

- project URL,
- anon key,
- service role key.

Connection note:

- For the Flask backend, the first choice should be a normal Postgres
  connection string through `DATABASE_URL`.
- If direct connection support is awkward in the current environment, the
  Supavisor session pooler is the fallback choice.
- The API keys are not required for the current SQLAlchemy-based setup.
- If Supabase shows a URL starting with `postgresql://`, change it to
  `postgresql+psycopg://` for this project so SQLAlchemy uses the installed
  `psycopg` v3 driver.
- If the error mentions an IPv6 address and says `Network is unreachable`, the
  direct database host is not reachable from the current machine. In that case,
  switch to the Supavisor session pooler connection string instead of the
  direct host.

Important note:

- The service role key is server-side only and must never be exposed in the
  browser.

## Current Database Commands

### Initialize the database

```bash
uv run python init_db.py
```

Why:

- Initializes the database and seeds the admin user through the helper script.

### Create a migration

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

Why:

- Generates an Alembic migration after model changes.

### Apply migrations

```bash
uv run alembic upgrade head
```

Why:

- Applies all pending migrations.

### Roll back the latest migration

```bash
uv run alembic downgrade -1
```

Why:

- Reverts the latest migration step.

## Current Admin Setup

The project currently expects admin credentials from environment variables.

Example variables:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```

Important note:

- Update this section if the admin setup flow changes later.

## Current Known Workflow Gaps

These are known areas that will likely change later:

- local Docker setup is not yet the main workflow,
- Supabase integration is not yet completed,
- Stripe is not yet integrated,
- `ngrok` workflow is not yet documented,
- monitoring and alerting are not yet configured.

## Change Log

Use this section to record notable development workflow changes over time.

### 2026-03-17

- Created `docs/dev_doc.md` as the central place for development commands and
  workflow notes.
- Moved important current-event settings into `config.py` so yearly changes and
  testing are easier.
- Added the first Flask app `Dockerfile` and `.dockerignore`.
- Changed the roadmap direction from a local PostgreSQL container to Supabase
  as the first hosted database to test.
