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
  - what type of admin action happened,
  - which admin changed the shared public-site password,
  - which admin added, updated, or removed a canoe booking,
  - which admin changed event settings or activated an event.
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

### Step 4. Protect gallery and ribbon images behind Flask routes (Completed 2026-03-21)

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

### Step 5. Let admins rotate the shared public password from the admin page (Completed 2026-03-21)

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

Implementation note:

- The admin page now writes the shared public-site password hash to the
  `public_site_access_settings` table.
- The app uses that database-backed value first and only falls back to
  `PUBLIC_SITE_PASSWORD_HASH` from the environment when no database value
  exists yet.
- A `reset-public-site-password` CLI command now acts as the manual recovery
  path if the shared password is forgotten and the admin page cannot be
  reached.

### Step 6. Use a production-grade rate-limit storage backend

What to do:

- Keep the existing request limits on `/unlock` and `/login`.
- Replace Flask-Limiter's in-memory storage with a shared backend for
  deployment, such as Redis.

Why:

- The brute-force protection routes already exist, but the current in-memory
  storage is only suitable for local development and very simple deployments.
- A shared backend keeps the limits consistent across restarts, multiple
  workers, or multiple app instances.

How to test:

- Trigger the `/unlock` and `/login` limits from the same IP address.
- Confirm the limit still applies correctly after an app restart or when using
  multiple app workers.

### Step 7. Add event-day checklist and PDF export support

What to do:

- Add one admin workflow for checking off booked canoes during the event.
- Support both an in-site checklist view and a printable PDF export.
- The in-site checklist now stores pickup state per `booked_canoes` row.
- Printable export is still pending.

Why:

- The old manual paper workflow should be replaced by something easier to use
  and easier to print when needed.

How to test:

- Generate the checklist from the admin page.
- Confirm the list can be used on screen and exported to PDF.

### Step 8. Support grouped participant overviews for multi-canoe bookings

What to do:

- Update the booking model and overview queries so one lead person can hold
  multiple canoes in the public participant view.
- Show the person name on the left and the canoe count on the right.

Why:

- The current participant list is still oriented toward one row per canoe.
- A grouped overview will matter once one person can book several canoes under
  their own name.

How to test:

- Create a booking where one person holds multiple canoes.
- Confirm the overview shows the grouped name plus canoe count correctly.

### Step 9. Support up to three named riders per canoe before Stripe

What to do:

- Change the meaning of one `booked_canoes` row so it represents one canoe,
  not just one displayed participant name.
- Keep the current required pickup person on the row.
- Add optional rider slots for rider two and rider three on the same row.
- Add model helper properties so the rest of the code can ask simple questions
  such as:
  - what the pickup person's full name is,
  - what rider two should display when blank,
  - whether the canoe has a third rider,
  - how to format the canoe's rider names for display.

Why:

- Stripe should be added only after the booking data shape matches the real
  canoe usage.
- Keeping one canoe on one row still matches the checklist and payment logic
  better than creating one row per rider.

How to test:

- Create or inspect a canoe row with only the required pickup person.
- Confirm the new optional rider fields can stay empty without breaking the
  model or existing routes.

### Step 10. Prepare grouped canoe-detail view models for overview and checklist

What to do:

- Keep grouping the public overview and admin checklist by pickup person.
- Add child detail rows under each group so one person can expand the grouped
  row and inspect each canoe separately.
- Make the grouped row itself a button, not only the name text.

Why:

- Grouping keeps the summary view compact.
- Expandable child rows expose the missing canoe-by-canoe detail without
  cluttering the default view.
- Making the whole row a button improves mobile usability, creates a larger
  click target, and is easier to use with a keyboard.

How to test:

- Build grouped data where one pickup person has two canoes.
- Confirm the grouped row count stays correct and that each canoe can still be
  listed separately in the child detail data.

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

### Step 1. Choose Stripe-hosted Checkout as the first payment UI

What to do:

- Use Stripe Checkout, where the user is redirected to a payment page hosted by
  Stripe.
- Do not start with a custom in-app card form.
- Keep the project open to a later upgrade to Stripe Elements or Payment
  Element only if the project later needs a more custom payment UI.

Why:

- This keeps card-entry handling on Stripe's side instead of inside the app.
- It reduces implementation complexity and lowers the payment risk surface for
  the project.
- It matches Stripe's own beginner-friendly Checkout examples.

How to test:

- Review the planned payment UX and confirm the public site only needs:
  - one booking summary step,
  - one redirect to Stripe,
  - one success return page,
  - one cancel return page.

### Step 2. Design the real booking and payment state flow

What to do:

- Define the exact order of:
  - availability check,
  - booking intent creation,
  - Stripe Checkout Session creation,
  - redirect to Stripe,
  - Stripe webhook confirmation,
  - final booking confirmation.
- Keep the redirect back from Stripe separate from the real payment
  confirmation logic.

Why:

- The app must not treat the success redirect alone as proof of payment.
- The flow needs to be explicit before the code changes start.

How to test:

- Review the flow and confirm each state is understandable and that the webhook
  is the final confirmation source.

### Step 3. Add Stripe configuration and dependency

What to do:

- Add the Stripe SDK.
- Add the required environment variables, starting with:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - one base public site URL for success and cancel redirects
- Keep all Stripe secrets server-side only.

Why:

- The backend needs a clear integration point for Stripe before any payment
  routes are changed.

How to test:

- Start the app and confirm the Stripe configuration loads correctly without
  exposing secrets to the client.

### Step 4. Keep price, quantity, and booking rules on the server

What to do:

- Build the Stripe line item data from the server-side event settings and the
  validated canoe count.
- Do not trust price, currency, or final amount from the browser.
- Keep the existing booking rules in force before a Checkout Session is created,
  including:
  - active event requirement,
  - canoe availability,
  - maximum five canoes in one booking,
  - maximum five canoes for the same participant name.

Why:

- Stripe should charge only for a server-validated booking attempt.
- This prevents client-side price manipulation and keeps the payment flow easy
  to reason about.

How to test:

- Try to start checkout with valid and invalid booking inputs and confirm only
  valid server-approved bookings can proceed.

### Step 5. Create a real Stripe Checkout Session

What to do:

- Replace the fake redirect step with a server-created Stripe Checkout Session.
- Use `mode=payment`.
- Redirect the user to the Stripe-hosted Checkout URL returned by Stripe.

Why:

- This is Stripe's intended starting point for a simple one-time payment flow.
- It is safer and simpler than collecting card details inside the app.

How to test:

- Start a checkout and confirm Stripe returns a valid redirect URL and that the
  browser is sent to Stripe Checkout.

### Step 6. Store Stripe session references locally before redirect

What to do:

- Save the Stripe Checkout Session ID on the local booking order.
- Save the local payment state in a way that clearly distinguishes:
  - booking intent created,
  - checkout session created,
  - payment confirmed,
  - payment canceled,
  - payment failed or expired.

Why:

- The app needs a reliable local record of what happened before and after the
  external payment step.

How to test:

- Start a checkout and confirm the Stripe session reference and local pending
  state are stored before the redirect happens.

### Step 7. Add success and cancel return handling

What to do:

- Add a success page for users who return from Stripe after a completed
  Checkout flow.
- Add a cancel path for users who return without completing payment.
- Keep these pages informational only.
- Do not finalize bookings from the success redirect alone.

Why:

- Users need a clear result after leaving Stripe Checkout.
- Stripe redirect behavior and Stripe webhook confirmation solve different
  problems and should stay separate.

How to test:

- Use Stripe's hosted flow and confirm:
  - successful test payments return to the success page,
  - canceled payments return to the cancel page,
  - the booking is not finalized only because the browser reached the success
    page.

### Step 8. Add a Stripe webhook endpoint with signature verification

What to do:

- Add a webhook route that verifies Stripe's signature header before processing
  the event.
- Start with the events needed for the first real payment flow, especially:
  - `checkout.session.completed`
- Keep the webhook logic idempotent so a duplicate event does not duplicate the
  booking finalization.

Why:

- Webhooks are the reliable payment confirmation source.
- Signature verification and idempotent handling are required for a safe
  payment flow.

How to test:

- Send Stripe test webhooks and confirm:
  - invalid signatures are rejected,
  - valid events are accepted,
  - duplicate deliveries do not create duplicate confirmed bookings.

### Step 9. Finalize bookings only after a verified Stripe event

What to do:

- Only mark the booking order as paid after a verified Stripe webhook confirms
  the payment.
- Only mark the reserved canoe rows as confirmed after that verified event.
- Keep the success page as a user-facing confirmation page, not the backend's
  final source of truth.

Why:

- This prevents false bookings from incomplete, failed, or interrupted payment
  flows.

How to test:

- Complete a Stripe test payment and confirm the booking finalizes only after
  webhook handling, not from the browser redirect alone.

### Step 10. Re-test the full payment flow with Stripe's test cards

What to do:

- Re-test the real booking flow using Stripe's test card scenarios, including:
  - successful payment,
  - 3D Secure / SCA-required payment,
  - declined payment,
  - user-canceled checkout.
- Keep the test cases documented in the dev docs so they are easy to repeat.

Why:

- A payment flow is not done when only the happy path works.

How to test:

- Run the documented Stripe test scenarios and confirm each one leaves the
  booking order in the expected local state.

### Step 11. Add refund handling as the first post-payment admin operation

What to do:

- Start by defining the operational refund flow in Stripe Dashboard first.
- Add API-backed refund support from the admin side only if the manual
  Dashboard workflow becomes too slow.
- Store enough local payment references to make refunds traceable later.

Why:

- Refunds are a real business operation, but they should not block the first
  working payment launch.
- Stripe already provides a safe operational path through the Dashboard.

How to test:

- Complete a test payment, issue a refund in Stripe's test mode, and confirm
  the project has the local reference data needed to identify that payment.

### Step 12. Review payouts and adaptive pricing as later expansion work

What to do:

- Treat payout configuration as an operational Stripe account setup step first,
  not an in-app feature.
- Review manual payouts later only if the business flow really requires them.
- Review adaptive pricing later only if the event expands beyond the current
  Swedish audience and SEK-first pricing model.

Why:

- Both features are useful, but they are not part of the smallest safe payment
  launch.
- They should be added only when they solve a real operational problem.

How to test:

- Review the post-launch needs and confirm whether either feature is justified
  before implementation starts.
