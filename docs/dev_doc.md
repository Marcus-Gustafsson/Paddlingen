# Paddlingen Development Document

Last updated: 2026-03-18

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

### Test the current landing-page redesign locally

```bash
uv run flask --app wsgi --debug run
```

Then open:

```text
http://127.0.0.1:5000
```

What to check:

- The homepage shows one main landing hero instead of the older sidebar-led
  layout.
- The weather panel is in the top-left area.
- The information and contact buttons are in the top-right area.
- The booking progress bar shows the helper text `Tryck för att se deltagare`.
- Clicking the progress bar opens the participant list modal.
- Clicking `Visa bilder från tidigare år` opens the gallery modal.

## Current Docker Commands

These commands are for the first app-container step only.

Beginner-friendly note:

- A Docker image is the built application package.
- A Docker container is one running instance created from that image.
- `docker run ...` starts one container directly.
- `docker compose ...` starts services defined in `compose.yaml`.
- Compose is useful even for one service because it gives the project a stable
  name in Docker Desktop and makes it easier to add more services later.

### Build the Flask app image

```bash
docker build -t paddlingen-web .
```

Why:

- Builds the current Flask application container from the root `Dockerfile`.

Important note:

- After recent cleanup, the container should no longer download Python
  dependencies at startup.
- If you change the `Dockerfile`, rebuild the image before running it again.

### Run the Flask app container directly

```bash
docker run --rm --name paddlingen-web -p 8080:8080 --env-file .env paddlingen-web
```

Why:

- Starts the Flask app container directly with a clear project-specific name.
- `--rm` removes the container automatically when it stops.
- This command keeps the container attached to your terminal, so logs appear in
  the terminal while it is running.

What to expect:

- It is normal that you still see Flask and request logs in the terminal.
- Docker Desktop shows the same logs because both views are reading the same
  container output stream.
- Press `Ctrl+C` to stop the container.

### Run the Flask app container in the background

```bash
docker run -d --rm --name paddlingen-web -p 8080:8080 --env-file .env paddlingen-web
```

Why:

- Runs the same container in detached mode so your terminal is free again.

Useful follow-up commands:

```bash
docker logs -f paddlingen-web
docker stop paddlingen-web
```

### Run the app through Docker Compose

```bash
docker compose up --build
```

Why:

- Uses the root `compose.yaml` file.
- Gives the project a stable Compose project name, `paddlingen`.
- Shows a clearer grouped view in Docker Desktop than a random auto-generated
  container name.

What to expect:

- In attached mode, logs still appear in the terminal. That is normal.
- Docker Desktop will show the service under the `paddlingen` project.

### Run Docker Compose in the background

```bash
docker compose up --build -d
```

Useful follow-up commands:

```bash
docker compose logs -f web
docker compose ps
docker compose down
```

Important note:

- The current `compose.yaml` only contains the Flask app service.
- Compose stacks are often used for multiple services, but they are still
  useful for one service when you want stable naming and easier project-level
  management.
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

- Drops and recreates tables through the helper script, then seeds the admin
  user.

Important note:

- This is useful for fast local resets.
- Do not use this as the normal schema-management path for Supabase or other
  shared databases. Use Alembic there, then run the admin seeding command
  separately.

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

### Reset the Supabase test schema before rerunning the initial migration

Use this only when the Supabase test database already contains an older version
of the project schema and you intentionally want to replace it.

Run these statements in the Supabase SQL editor:

```sql
drop table if exists booked_canoes cascade;
drop table if exists booking_orders cascade;
drop table if exists admin_users cascade;
drop table if exists pending_booking cascade;
drop table if exists rent_form cascade;
drop table if exists users cascade;
drop table if exists alembic_version cascade;
```

Why:

- The initial migration file was replaced with the new normalized booking
  schema.
- If the old tables or the old `alembic_version` row remain in Supabase,
  `alembic upgrade head` will not rebuild the database the way the code now
  expects.

What to do after the cleanup:

```bash
uv run alembic upgrade head
uv run flask --app wsgi seed-admin
```

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

### 2026-03-18

- Replaced the old `RentForm` and `PendingBooking` schema with
  `booking_orders` and `booked_canoes`.
- Replaced the old initial Alembic migration with a new initial normalized
  booking schema.
- Changed `.env` loading so explicit environment variables win over `.env`
  values, which keeps tests and scripts from accidentally talking to Supabase.
- Updated the Docker workflow so the container starts Flask directly instead of
  running `uv` at container startup.
- Added a root `compose.yaml` with a stable project name and container name for
  easier Docker Desktop usage.
- Reworked the public homepage into a single landing hero with:
  - weather in the top-left area,
  - information and contact actions in the top-right area,
  - a clickable progress bar that opens the participant list,
  - and a previous-years image ribbon below the booking button.
- Removed the old sidebar, archive-section, and overview-panel CSS blocks that
  no longer belong to the redesigned homepage.
- Changed the previous-years ribbon to a continuous marquee that loops through
  the full previous-years image list instead of a smaller preview subset.
