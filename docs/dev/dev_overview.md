# Development Overview

Last updated: 2026-03-24

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
3. `docs/dev/dev_coolify.md`
   Read this when preparing the Hetzner + Coolify deployment path.
4. `docs/dev/dev_ngrok.md`
   Read this when exposing the local site through ngrok for testers or real
   phones.
5. `docs/dev/dev_stripe.md`
   Read this when creating a Stripe account, collecting API keys, installing
   the Stripe CLI, or preparing local webhook testing.
6. `docs/dev/dev_database.md`
   Read this when working with Supabase, migrations, or schema setup.
7. `docs/dev/dev_webdev_tips.md`
   Read this when you inspect an element in the browser and need to find the
   correct file to change.
8. `docs/dev/dev_testing.md`
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

If the shared public-site password was rotated and later forgotten, recover by
generating and saving a new one with:

```bash
uv run flask --app wsgi reset-public-site-password
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
- The dashboard also now includes smaller utility actions for:
  - rotating the shared public-site password,
  - an event-day checklist for marking which booked canoes have been picked up.
- Booking management currently supports:
  - adding one manual canoe booking,
  - choosing the manual payment method,
  - editing the pickup person and optional rider names,
  - deleting bookings.
- The underlying `booked_canoes` data model now also supports optional second-
  and third-rider name fields on each canoe row, but the public and admin UI
  still need their later follow-up work before those extra riders are visible
  and editable in every related screen.
- The public booking modal now collects:
  - one required pickup person,
  - one optional second rider shown through a small add/remove button,
  - one optional third rider shown through a small add/remove button.
- The public participant overview now groups matching names and shows the canoe
  count on the right instead of listing every canoe row separately.
- The grouped overview and grouped checklist helper data now also prepare one
  canoe-detail row per canoe under each grouped pickup person.
- The public participant overview and the admin checklist now both render
  expandable grouped rows so the saved rider names can be inspected canoe by
  canoe without losing the compact grouped default view.
- The public booking flow now also rejects a new booking if one exact
  participant name would end up above five total canoes for the active event.
- The public payment return surface now includes:
  - `/payment-success` for the current placeholder success return,
  - `/payment-cancel` for the current placeholder cancel return.
- This keeps the public flow aligned with the planned Stripe-hosted Checkout
  shape before the real Stripe SDK and webhooks are added.
- Event management currently supports:
  - selecting an existing event,
  - editing the selected event,
  - creating a new event from the selected event, or from the code-defined
    event template values when the database is still empty,
  - activating the selected event.
- Shared public-site password management currently supports:
  - saving a new shared password through the admin dashboard,
  - warning admins to write down the new password because it cannot be shown
    again later,
  - storing only the hash in the `public_site_access_settings` table,
  - falling back to `PUBLIC_SITE_PASSWORD_HASH` only when the database has no
    admin-managed value yet,
  - creating the table automatically on the first successful save if an older
    local database does not have it yet,
  - resetting the password from the CLI if it was forgotten and the admin page
    is no longer reachable.
- Admin account management currently supports:
  - adding extra named admin users from a prompted CLI command,
  - changing the password for the currently logged-in admin from the admin
    dashboard.
- Event-day checklist support currently allows:
  - opening a grouped checklist from the admin dashboard,
  - saving which booked canoes have been picked up,
  - reopening the checklist later with the saved state still visible.
- Both `/unlock` and `/login` are rate limited already, but the current
  limiter storage is still the simple in-memory development setup.

## Current Known Workflow Gaps

These areas are still planned work:

- Stripe is not yet fully integrated. The project now has:
  - the chosen Stripe-hosted Checkout direction,
  - the planned webhook-first payment flow,
  - the Stripe SDK dependency,
  - explicit Stripe environment variables,
  - server-side Stripe-ready checkout preparation from the active event row,
  - a Stripe setup guide for manual dashboard and CLI work.
- The project still needs Stripe session creation, webhook verification, and
  real payment-state handling.
- monitoring and alerts are not yet configured.

## Planned Stripe Flow

The current roadmap now defines the first safe real payment flow like this:

1. Validate the booking request on the server.
2. Check availability using both confirmed bookings and active unpaid
   reservation holds.
3. Create the booking attempt first in the project's own database tables.
4. Create temporary reserved canoe rows with an expiration time.
5. Create a Stripe Checkout Session from server-side data.
6. Store the Stripe Checkout Session ID on the local booking order.
7. Redirect the visitor to Stripe Checkout.
8. Treat `/payment-success` as an informational return page only.
9. Treat `/payment-cancel` as an informational page plus unpaid-reservation
   cleanup.
10. Treat the verified Stripe webhook as the final payment confirmation source.

Important beginner note:

- "Local booking order" means a row in this project's own database tables such
  as `booking_orders`, not browser session data and not temporary memory.
- The browser return from Stripe is helpful for user experience, but the
  webhook is the real source of truth for whether payment succeeded.
