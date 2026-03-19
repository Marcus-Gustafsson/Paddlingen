# Database Development

Last updated: 2026-03-19

## Purpose

This document explains the current database workflow.

It covers:

- Supabase setup,
- connection-string notes,
- migrations,
- schema reset steps,
- event seeding,
- admin seeding.

## Current Database Direction

The project currently uses:

- SQLAlchemy for database access,
- Alembic for schema migrations,
- Supabase as the first hosted Postgres environment to test against.

Why:

- The current app already works as a normal Postgres-backed Flask app.
- That means the simplest Supabase path is to treat Supabase as hosted
  Postgres first.

## Supabase Values To Collect

From the Supabase dashboard, collect:

- database connection string,
- database password.

Optional later values:

- project URL,
- anon key,
- service role key.

## Connection Notes

Important rules for this project:

- Use `DATABASE_URL` for the Flask backend.
- If Supabase shows `postgresql://`, change it to `postgresql+psycopg://`.
- If the direct host fails with IPv6 `Network is unreachable`, use the
  Supavisor session pooler connection instead.

Example shape:

```env
DATABASE_URL=postgresql+psycopg://...
```

Important note:

- The service role key is server-side only.
- Never expose it in the browser.

## Migration Commands

### Create a migration

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

Why:

- Generates a new Alembic migration after model changes.

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

## Reset the Supabase test schema

Use this only when the Supabase test database contains an older schema and you
intentionally want to replace it.

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

- Older tables and the old `alembic_version` entry can block the current schema
  from rebuilding cleanly.

Then run:

```bash
uv run alembic upgrade head
uv run flask --app wsgi seed-active-event
uv run flask --app wsgi seed-admin
```

Why this order:

- `alembic upgrade head` creates the tables and columns.
- `seed-active-event` inserts or refreshes the first active event row and
  backfills older booking rows that still have no `event_id`.
- `seed-admin` creates the login account for the admin area.

## Current Schema Reminder

The current main tables are:

- `events`
- `event_weather_cache`
- `booking_orders`
- `booked_canoes`
- `admin_users`

Important note:

- The public homepage now prefers the active row in `events`.
- If the event row or one of its fields is missing, the app logs a warning and
  falls back to the matching value in `config.py`.

Important `events` fields now include:

- title and subtitle
- event date and start time
- start and end locations
- available canoes
- price per canoe
- max canoes per booking
- weather forecast window
- weather latitude and longitude
- FAQ, rules, and contact values

## New Event Commands

### Seed or refresh the active event

```bash
uv run flask --app wsgi seed-active-event
```

Why:

- Creates the first active event row from the values currently stored in
  `config.py`.
- Safe to run more than once.
- Also backfills older `booking_orders` rows whose `event_id` is still empty.

### Fresh local reset

```bash
uv run flask --app wsgi init-db
```

Why:

- Drops and recreates the local schema.
- Seeds the active event row automatically.
- Does not create the admin user, so follow it with:

```bash
uv run flask --app wsgi seed-admin
```
