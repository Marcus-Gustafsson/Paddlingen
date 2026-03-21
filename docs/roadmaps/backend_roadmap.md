# Backend Roadmap

Last updated: 2026-03-20

## Goal

Keep the booking backend correct, simple, and ready for real event use.

This roadmap covers:

- database structure,
- Supabase usage,
- booking safety,
- Stripe integration,
- backend testability.

## Completed Foundation Work

These backend milestones are already done:

- Docker plus Supabase local development has been standardized.
- The current SQLAlchemy app can connect to Supabase Postgres.
- Alembic migrations run against Supabase.
- The current booking and admin CRUD flows have been tested against Supabase.

## Phase 1: Keep The Current Backend Stable

### Step 1. Keep Docker and Supabase setup working (Completed 2026-03-18)

Completed work:

- Added the Docker app container setup.
- Selected the Supavisor session pooler connection.
- Documented the current Supabase workflow.

### Step 2. Keep the current schema working while Stripe is still fake (Completed 2026-03-18)

Completed work:

- Replaced the older booking tables with:
  - `booking_orders`
  - `booked_canoes`
  - `admin_users`
- Confirmed the current placeholder payment flow still writes bookings
  correctly.

## Phase 2: Move Event Settings Into The Database

Goal:

- Stop depending on hardcoded event values in `config.py` for normal yearly
  changes.

Why this phase matters:

- Non-technical admins should be able to update event settings later.
- The app needs a better place to store active event information.
- The weather cache should stay separate from the main event row so the data
  model remains easier to understand and update.
- This also gives the weather widget a cleaner way to handle past events.

### Step 1. Design the `events` table and active-event rule (Completed 2026-03-19)

What to do:

- Define a new `events` table.
- Define a separate `event_weather_cache` table.
- Decide how the app knows which event is the live event.
- Start with one row per event date or event instance.

Suggested columns:

- `id`
- `title`
- `subtitle`
- `event_date`
- `start_time`
- `starting_location_name`
- `starting_location_url`
- `end_location_name`
- `end_location_url`
- `available_canoes`
- `price_per_canoe_sek`
- `max_canoes_per_booking`
- `weather_forecast_days_before_event`
- `weather_latitude`
- `weather_longitude`
- `faq_booking_text`
- `faq_changes_and_questions_text`
- `rules_on_the_water_text`
- `rules_after_paddling_text`
- `contact_email`
- `contact_phone`
- `is_active`

Suggested weather-cache columns:

- `id`
- `event_id`
- `source`
- `forecast_for_date`
- `summary`
- `temperature_c`
- `rain_mm`
- `icon`
- `fetched_at`
- `expires_at`

Why:

- This is the cleanest way to move event configuration out of source code.
- It also gives the booking system a real event record to point at later.
- It gives the app a clear place to store both the starting location and the
  pickup or finish location, which are not always the same place.
- It keeps changing weather data separate from the slower-moving event
  configuration.

How to test:

- Review the table design and confirm each column has a clear purpose.
- Confirm there is one clear rule for choosing the active event.

### Step 2. Add the `events` model and migration (Completed 2026-03-19)

What to do:

- Add the SQLAlchemy model.
- Add an Alembic migration.
- Seed one first active event row.

Why:

- The table must exist before the app can read event settings from the
  database.

How to test:

- Run the migration.
- Confirm the table appears in Supabase.
- Confirm one active event row can be inserted.

### Step 3. Read the public event settings from the database (Completed 2026-03-19)

What to do:

- Replace the current config-driven homepage event values with the active event
  row.

Why:

- The public page should render from the database once the event table exists.

How to test:

- Change one event field in the database.
- Reload the homepage and confirm the new value appears.

### Step 4. Link bookings to the active event (Completed 2026-03-19)

What to do:

- Add an event relationship so bookings belong to a specific event row.

Why:

- This avoids assuming there is only one event forever.
- It will matter later when old bookings and future years must coexist.

How to test:

- Create a booking and confirm it points to the active event row.

Implementation note:

- The app now prefers the active `events` row for homepage settings.
- If the row or any field is missing, the app logs a warning and falls back to
  the matching value in `config.py`.
- A `seed-active-event` CLI command now creates or refreshes the first active
  event row and backfills older bookings whose `event_id` is still empty.

### Step 5. Store the latest weather snapshot for the active event

What to do:

- Save the latest valid weather data and the update timestamp in the separate
  `event_weather_cache` table.

Why:

- Each page load should not depend on a fresh external API call.
- Cached weather also helps when the event date has already passed.

How to test:

- Fetch weather once.
- Confirm the data is stored and can be reused without another API call.

### Step 6. Decide what the weather widget shows after the event has passed

What to do:

- Decide whether to show:
  - the cached event-day weather,
  - or a simple `event already passed` message.

Why:

- The current weather logic is still oriented toward future dates.

How to test:

- Set the event date to a past date.
- Confirm the widget shows the chosen post-event behavior.

### Step 7. Add admin editing for the active event settings

What to do:

- Add a simple admin form for editing the active event row.

Why:

- This is the actual user-facing reason to move event settings into the
  database.

How to test:

- Update event values in the admin page.
- Confirm the homepage reflects the saved values.

### Step 8. Add manual-booking metadata and an admin audit log

What to do:

- Record more detail for manual admin changes, including:
  - which payment method was used for a manual booking,
  - which admin user created or changed the record,
  - what type of admin action happened.
- Store this in a clear audit-friendly structure instead of relying only on
  free-form notes.

Why:

- Once multiple admins use the dashboard, the project needs a reliable way to
  answer who changed what and when.
- This also makes manual bookings easier to review later.

How to test:

- Add a manual booking and confirm the chosen manual payment method is saved.
- Update or delete a booking and confirm an audit row is written with the
  acting admin user and timestamp.

### Step 9. Add small cleanup jobs for stale event and weather data

What to do:

- Add one safe cleanup path for old or no-longer-needed operational data.
- Start with weather cache cleanup first.
- Add booking cleanup rules later only when the retention rules are clear.

Why:

- The project should stay small enough for the Supabase free tier where
  practical.
- A cleanup step is easier to reason about when it is explicit instead of being
  handled informally.

How to test:

- Create stale weather cache rows.
- Run the cleanup command or job.
- Confirm only the intended stale rows are removed.

## Phase 3: Add Controlled Access To The Public Site

Goal:

- Keep the public site limited to invited users instead of making bookings,
  participant data, and images open to anyone on the internet.

### Step 1. Design the site-wide access gate (Completed 2026-03-20)

Completed work:

- Decide how invited users should unlock the public site.
- Start with one shared password for the whole event site.
- Decide which routes stay public and which routes require the access gate.
- Chose the same `/` route with conditional server-side rendering so locked
  visitors only receive the password screen, not the real homepage content.
- Chose a hashed shared password configuration instead of a plaintext password.

Why:

- The event is not meant for random outside visitors.
- A shared access gate lowers unnecessary exposure of participant-related
  information and previous-years images.

How to test:

- Visit the site in a private browser window and confirm access is blocked
  until the correct shared password is entered.

### Step 2. Add a public access session after the password is entered (Completed 2026-03-20)

Completed work:

- Store a session flag after a visitor enters the correct shared password.
- Keep the access behavior separate from the admin login flow.
- Added a dedicated `/unlock` route with rate limiting.
- Added a CLI command to generate the shared password hash.

Why:

- Admin login and visitor access solve different problems and should stay easy
  to reason about.

How to test:

- Unlock the site once and confirm the user can move around without entering
  the password again on every page refresh.

### Step 3. Apply the access gate to the public routes (Completed 2026-03-20)

Completed work:

- Protect the homepage and other public-facing routes that expose event or
  participant information.
- Protected the homepage, booking flow, and public JSON endpoints.
- Kept the admin login flow separate from the public access gate.

Why:

- The gate only helps if it actually covers the user-facing entry points.

How to test:

- Confirm an unlocked session can still use the booking flow and gallery.
- Confirm a locked session is redirected to the public access screen.

### Step 4. Protect gallery and ribbon images behind Flask routes later

What to do:

- Stop serving protected gallery and ribbon images directly from `/static/`.
- Add Flask routes for those image files so the same public access session can
  protect them too.

Why:

- The current shared password gate now protects the homepage and APIs, but the
  generated image files still live under public static paths.
- Moving those files behind Flask routes is the stronger version of the same
  access model.

How to test:

- Open the site in a locked browser session and confirm direct image URLs no
  longer load.
- Unlock the site and confirm the ribbon and gallery still work normally.

### Step 5. Let admins rotate the shared public password from the admin page

What to do:

- Add one admin workflow for generating and saving a new shared public-site
  password hash.
- Keep the stored value hashed so the plaintext password is never saved.

Why:

- If the shared public password leaks, a non-technical admin should be able to
  rotate it without editing source code manually.

How to test:

- Save a new shared public password through the admin page.
- Confirm the old password stops working and the new one unlocks the site.

## Phase 4: Make Booking Safety Explicit

Goal:

- Make overbooking protection clear and testable.

### Step 1. Add a race-condition test for the last available canoe

What to do:

- Add a test where two booking attempts compete for the final canoe.

Why:

- This is one of the most important business rules.

How to test:

- Confirm the test proves that only one booking can win.

### Step 2. Make the booking flow safe at the database level

What to do:

- Review and improve the availability logic so it stays correct under
  concurrent requests.

Why:

- Frontend timing is not enough to protect the last available canoe.

How to test:

- Re-run the race-condition test and confirm it passes reliably.

### Step 3. Add one optional Supabase-backed integration check

What to do:

- Add one integration check that only runs when the Supabase environment is
  intentionally enabled.

Why:

- Hosted Postgres behavior can differ from SQLite.

How to test:

- Run the check intentionally and confirm it passes against Supabase.

### Step 4. Re-test migration and seed flows against a clean Supabase state

What to do:

- Verify migrations and seed commands from a reset test database state.

Why:

- These are the real setup steps needed for a fresh environment.

How to test:

- Start from a clean database and confirm the setup commands work in order.

## Phase 4: Replace The Fake Payment Flow With Stripe

Goal:

- Make bookings depend on verified real payment.

### Step 1. Design the Stripe checkout and webhook flow

What to do:

- Define the order of:
  - booking intent creation,
  - Stripe checkout creation,
  - webhook handling,
  - booking finalization.

Why:

- The flow must be clear before the code changes.

How to test:

- Review the flow and confirm each state is understandable.

### Step 2. Add Stripe configuration and dependency

What to do:

- Add the Stripe SDK and required environment variables.

Why:

- The backend needs a clear integration point for Stripe.

How to test:

- Start the app and confirm Stripe configuration loads correctly.

### Step 3. Create a real Stripe Checkout session

What to do:

- Replace the fake redirect step with a Stripe Checkout session.

Why:

- Stripe Checkout is simpler and safer than collecting payment details inside
  the app.

How to test:

- Start a checkout and confirm Stripe returns a valid redirect URL.

### Step 4. Store the Stripe session reference in the database

What to do:

- Save the Stripe session ID and the local payment state on the booking order.

Why:

- The app needs a reliable local record of what happened.

How to test:

- Start a checkout and confirm the Stripe reference is stored.

### Step 5. Add a Stripe webhook endpoint

What to do:

- Add a webhook route for successful payment events.

Why:

- Webhooks are the reliable payment confirmation source.

How to test:

- Send a Stripe test webhook and confirm the app receives it.

### Step 6. Finalize bookings only after verified payment

What to do:

- Only mark bookings as confirmed after a verified Stripe success event.

Why:

- This prevents false bookings from incomplete or failed payments.

How to test:

- Complete a test payment and confirm the booking finalizes only after webhook
  handling.
