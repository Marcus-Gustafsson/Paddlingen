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

## Current Development Environment

- Main development machine: Windows 11
- Main development shell: WSL
- Expected shell: `bash`
- Expected working directory: project root

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

- The roadmap plans to move local development toward Docker plus PostgreSQL as
  the main workflow.
- When that happens, this section must be updated.

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
- PostgreSQL is not yet the default local path,
- Stripe is not yet integrated,
- `ngrok` workflow is not yet documented,
- monitoring and alerting are not yet configured.

## Change Log

Use this section to record notable development workflow changes over time.

### 2026-03-17

- Created `docs/dev_doc.md` as the central place for development commands and
  workflow notes.
