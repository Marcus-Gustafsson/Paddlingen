# Development Overview

Last updated: 2026-03-20

## Purpose

This document is the main development overview for the project.

Use it to understand:

- which environment the project expects,
- which document to read next,
- how to run the app locally,
- where important project settings currently live,
- which parts of the workflow are still unfinished.

## Development Environment

The project is developed on:

- Windows 11
- WSL
- a Linux shell such as `bash`

Assume:

- Python 3.13 is used for this project.
- commands are run from the project root,
- Docker Desktop is installed on Windows,
- WSL integration is enabled for the distro you use.

## Which Development Document To Read

Use the document that matches the task:

1. `docs/dev/dev_overview.md`
   Read this first for the general workflow.
2. `docs/dev/dev_docker.md`
   Read this when working with Docker and containers.
3. `docs/dev/dev_ngrok.md`
   Read this when exposing the local site through ngrok for testers or real
   phones.
4. `docs/dev/dev_database.md`
   Read this when working with Supabase, migrations, or schema setup.
5. `docs/dev/dev_testing.md`
   Read this when running tests, linting, formatting, or using development seed
   commands.

## Current Local Run Flow

The public homepage can now be protected by one shared password gate.

If `PUBLIC_SITE_PASSWORD_HASH` is set in `.env`:

- `/` first shows the public lock screen,
- the visitor must enter the shared password,
- then the homepage unlocks for that browser session.

Generate the hash with:

```bash
uv run flask --app wsgi generate-public-site-password-hash
```

### Start the app locally

```bash
uv run flask --app wsgi --debug run
```

Why:

- Starts the Flask development server.

Then open:

```text
http://127.0.0.1:5000
```

## Important Event Settings

The app now reads its main public event settings from the active row in the
`events` table.

Examples:

- event title and subtitle,
- event date and time,
- start and end locations,
- canoe count,
- canoe price,
- max canoes per booking,
- weather forecast window,
- weather coordinates,
- FAQ text,
- rules text,
- contact email and phone.

Why this matters:

- Normal yearly event changes now belong in the database instead of the source
  code.
- The app still keeps matching fallback values in `config.py` so the homepage
  can continue to work if the database row is missing.

Important note:

- If the active event row is missing, the app logs a warning and uses the
  fallback values from `config.py`.
- Run `uv run flask --app wsgi seed-active-event` after applying migrations so
  the database gets its first active event row.
- Some low-change operational values are intentionally hidden from the admin
  event form to keep the UI simpler:
  - max canoes per booking,
  - weather forecast window,
  - weather latitude,
  - weather longitude.
- Those values are still stored in the `events` table and copied forward when a
  new event is created.
- If one of them must change, edit the active event row directly in Supabase
  and keep the matching fallback in `config.py` updated too.

## Current Frontend Structure

The public frontend is now split into smaller files.

### CSS

- `static/css/base.css`
- `static/css/home.css`
- `static/css/modals.css`
- `static/css/booking.css`
- `static/css/gallery.css`
- `static/css/admin.css`

### JavaScript

- `static/js/booking_progress.js`
- `static/js/weather.js`
- `static/js/modals.js`
- `static/js/gallery.js`
- `static/js/booking.js`
- `static/js/main.js`

### Images

- `static/images/nitten.png` is the current homepage background image.
- `static/images/previous_years/` contains the original previous-years images.
- `static/images/previous_years/ribbon/` contains generated ribbon-sized image
  variants.
- `static/images/previous_years/gallery/` contains generated gallery-sized
  image variants.
- `data/previous_year_images.json` stores stable public image IDs for the
  previous-years gallery. These IDs are shown in the gallery through a small
  `?` popup instead of being visible all the time.
- The generated ribbon and gallery variants are no longer linked directly from
  `/static/` on the public page. Flask now serves them through protected image
  routes after the shared public password has been unlocked.

## Current Admin Setup

The project currently expects admin credentials from environment variables.

Example:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
PUBLIC_SITE_PASSWORD_HASH=replace-me-with-generated-hash
```

Important note:

- Update this workflow later if the admin setup path changes.

Current admin dashboard behavior:

- `/login` opens the admin login page.
- `/admin` opens a dashboard with two main actions:
  - booking management,
  - event management.
- Booking management currently supports:
  - adding one manual booking,
  - choosing the manual payment method,
  - editing participant names,
  - deleting bookings.
- Event management currently supports:
  - selecting an existing event,
  - editing the selected event,
  - creating a new event by copying an existing one,
  - activating the selected event.
- Both `/unlock` and `/login` are rate limited already, but the current
  limiter storage is still the simple in-memory development setup.

## Current Known Workflow Gaps

These areas are still planned work:

- Stripe is not yet integrated,
- monitoring and alerts are not yet configured.
