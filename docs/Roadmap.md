# Paddlingen Roadmap

Last updated: 2026-03-18

## Goal

This roadmap only contains the work that should be done going forward.

It is written to be:

- beginner friendly,
- step-by-step,
- easy to test after each change,
- aligned with the current direction:
  - local development with Docker,
  - Supabase as the first hosted database to test with,
  - later deployment experiments with Google Cloud Run,
  - Supabase API features used only later if they clearly help,
  - Stripe for payments,
  - proper logging and monitoring before public launch.

## Core Website Goals

These are the main goals the roadmap should support:

- Build a simple booking website for the canoe event.
- Store booking information safely in a database.
- Prevent overbooking, including race conditions around the last available
  canoe.
- Use Stripe so payment handling stays outside the app as much as possible.
- Add logging and monitoring so problems are visible quickly.
- Show pictures from previous years on the website.

Important development rule:

- We will use the Supabase test project as the first real hosted database to
  validate the application.
- We will keep the current SQLAlchemy and Alembic architecture unless there is a
  strong reason to rewrite it.

Why:

- The current app already uses SQLAlchemy models and Alembic migrations.
- That means the easiest Supabase path is to treat Supabase as hosted Postgres
  first.
- This avoids rewriting the whole backend before we know it is necessary.

## Phase 1: Understand The Current Project

Goal:


### Step 1. Fix obvious inconsistencies (Completed 2026-03-17)

What to do:

- Fix mismatches like:
  - wrong hardcoded dates,
  - placeholder values that should not stay,
  - outdated assumptions in the app.

Why:

- Small inconsistencies create confusion and make later testing harder.

How to test:

- Refresh the site and confirm the visible data matches the intended event year
  and current logic.

Completed work:

- Centralized important current-event settings in `config.py`.
- Standardized the canoe-limit setting to `AVAILABLE_CANOES`.
- Fixed the current-year date mismatch between the backend/template values and
  the frontend weather logic.
- Updated the README to remove references to deleted docs.

## Phase 2: Standardize Local Development With Docker And Supabase

Goal:

- Make local development reproducible while testing against a real hosted
  Supabase project.

Why this phase matters:

- Docker gives us a predictable setup.
- Supabase lets us test against the database platform we want to evaluate
  without waiting until final deployment.

### Step 1. Add a Dockerfile for the Flask app (Completed 2026-03-17)

What to do:

- Define how the web app is built and started inside a container.

Why:

- The app should run the same way on any machine.

How to test:

- Build the image successfully.

Completed work:

- Added a first `Dockerfile` for the Flask application.
- Added a `.dockerignore` so local caches and development-only files are not
  copied into the Docker build context.

Current note:

- This step only containerizes the Flask app.
- Supabase database wiring still belongs to the next roadmap steps.

### Step 2. Create a Supabase test project and collect the required credentials (Completed 2026-03-17)

What to do:

- Use the existing Supabase account and create one test project for this app.
- Collect:
  - project URL,
  - database password,
  - connection string,
  - anon key,
  - service role key.

Why:

- We need one real hosted environment to test against before deployment.
- The credentials must be identified clearly before the app can connect.

How to test:

- Confirm you can view the project details in the Supabase dashboard and locate
  the connection information and API keys.

### Step 3. Choose the correct Supabase database connection method (Completed 2026-03-18)

What to do:

- Decide whether to use:
  - direct connection, or
  - Supavisor session pooler.

Why:

- Supabase recommends connection strings for Postgres clients.
- For persistent backend services, direct connection is preferred when IPv6 is
  supported; otherwise the session pooler is the safer choice.

How to test:

- Write down which connection string will be used and why.

Completed work:

- Selected the Supavisor session pooler connection for the current setup.
- Confirmed this is the safer choice for the WSL-based development environment
  after the direct IPv6 connection failed.

### Step 4. Add Supabase environment variables to the app configuration (Completed 2026-03-17)

What to do:

- Add the environment variables needed for the first Supabase test.
- Required now:
  - `DATABASE_URL`
- Optional later:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`

Why:

- The current app only needs the database connection string.
- The API-style Supabase variables can wait until we actually test features
  like Storage or other Supabase services.

How to test:

- Start the app with the new variables present and confirm configuration loads
  correctly.

### Step 5. Connect the current SQLAlchemy app to Supabase Postgres (Completed 2026-03-17)

What to do:

- Point `DATABASE_URL` to the chosen Supabase Postgres connection string.

Why:

- This lets the current backend use Supabase without rewriting the data layer.
- It matches how the app already works today.

How to test:

- Start the app and confirm it can read and write data in the Supabase-hosted
  database.

### Step 6. Run Alembic migrations against Supabase Postgres (Completed 2026-03-17)

What to do:

- Apply the existing schema to the Supabase database through Alembic.

Why:

- The current project already uses Alembic, so schema changes should remain
  migration-driven.

How to test:

- Run migrations successfully and confirm the expected tables appear in
  Supabase.

Current note:

- The schema now uses `booking_orders`, `booked_canoes`, and `admin_users`.
- The payment flow is still simulated, so the order/payment columns are only
  partly populated until Stripe is implemented.
- If an older Supabase test database already contains the previous
  `rent_form`, `pending_booking`, and `users` tables, those old tables and the
  `alembic_version` table must be removed before rerunning the new initial
  migration.

### Step 7. Test the current booking and admin flows against Supabase (Completed 2026-03-18)

What to do:

- Run the app locally with the Supabase-backed `DATABASE_URL`.
- Test the booking flow and the admin flow manually.

Why:

- This confirms the real hosted database works with the current code before any
  refactor is attempted.

How to test:

- Create a test booking, confirm it appears in the database and admin view, and
  verify the admin can still log in and edit data.

Completed work:

- Tested the public booking flow against Supabase.
- Confirmed new bookings are written to the `booking_orders` and
  `booked_canoes` tables.
- Tested the current admin CRUD flow and confirmed add, edit, and delete
  actions update the database correctly.

### Step 8. Update the README for the Docker + Supabase workflow (Completed 2026-03-18)

What to do:

- Replace outdated setup instructions with the current Supabase-based testing
  path.

Why:

- The documentation should match the real way the project is developed.

How to test:

- Follow the README from a clean state and confirm it works.

Completed work:

- Updated the README to match the current Docker plus Supabase workflow.
- Added clearer notes about Docker usage, Supabase setup, and the migration
  flow.

## Phase 3: Redesign The Public And Admin Interface

Goal:

- Modernize the visual design so the site feels cleaner, more focused, and more
  current before deeper payment and deployment work continues.

Why this phase matters:

- The current website works, but the visual structure feels old and too busy.
- It is better to improve the information hierarchy now before more features
  are added on top of the current layout.
- A simpler single-page public layout will make the site easier to understand
  for visitors and easier to maintain.

### Step 1. Redesign the landing section and current-year hero

What to do:

- Rework the first visible section of the website into one strong landing view.
- Keep the focus on:
  - event identity,
  - event date and location,
  - availability context,
  - one clear booking action.
- Use the current-year section as the main page instead of spreading the first
  impression across several older sections.

Why:

- The current landing area contains useful information, but the visual
  presentation does not feel modern or intentional.
- A stronger hero section gives the website a clearer first impression and
  makes the booking action easier to find.

Design direction:

- Use one full-width hero section with a strong background image.
- Add a readable dark or tinted overlay so text stays clear.
- Keep the main content centered or carefully aligned with strong spacing.
- Show only the most important information at first glance.
- Use one clear primary booking button and reduce competing elements.

How to test:

- Open the homepage on desktop and mobile.
- Confirm the first screen clearly communicates what the event is, when it
  happens, and where the user should click to book.

### Step 2. Replace the old previous-years navigation with a single image ribbon

What to do:

- Remove the sidebar for previous years.
- Remove the long stacked previous-years page sections.
- Replace them with one simpler image area placed below the main booking call
  to action.
- Start with a rolling strip, ribbon, or banner style presentation of selected
  images from previous years.

Why:

- The old structure makes the page feel heavier and less focused.
- A single curated image area supports the story of the event without taking
  over the page structure.

How to test:

- Open the homepage and confirm the site now reads as one main page instead of
  a long multi-section archive.
- Confirm the image ribbon works on both desktop and mobile.

### Step 3. Simplify the public page structure into one clear flow

What to do:

- Reorder the page so it reads in a simple sequence:
  - hero,
  - booking call to action,
  - short practical event information,
  - previous-years image ribbon,
  - footer.
- Remove sections that no longer support the simplified design direction.

Why:

- The website should guide the visitor through one clear path instead of making
  them scan many unrelated sections.

How to test:

- Scroll through the full page and confirm the content order feels natural and
  easy to follow.

### Step 4. Refresh the booking area so it matches the new design

What to do:

- Update the booking button, booking modal, and nearby supporting text so they
  match the new landing-page style.
- Keep the booking flow simple and easy to scan.

Why:

- A redesigned hero will feel inconsistent if the booking interface still looks
  much older than the rest of the page.

How to test:

- Open the booking flow from the redesigned landing page and confirm the visual
  style feels consistent.

### Step 5. Redesign the admin login page

What to do:

- Replace the current admin login page with a cleaner and more minimal layout.
- Focus on:
  - a clear title,
  - one centered login card or panel,
  - clear input labels,
  - obvious submit action,
  - restrained use of color.

Why:

- The current login page works, but it looks outdated and does not match the
  direction of the public site.

How to test:

- Open the admin login page and confirm it feels visually cleaner while still
  being easy to use.

### Step 6. Redesign the admin dashboard for simple booking management

What to do:

- Update the admin page so it feels like a small internal dashboard instead of a
  basic form page.
- Focus on:
  - clearer section spacing,
  - more readable booking rows,
  - obvious add, edit, and delete actions,
  - room for future payment and status fields.

Why:

- The admin page is functional now, but it needs a cleaner layout before more
  booking and payment information is added.

How to test:

- Log in as admin and confirm the page is easier to read and use for booking
  changes.

### Step 7. Test the redesigned public and admin views on desktop and mobile

What to do:

- Manually test the new layouts on desktop and phone-sized screens.
- Use the existing Docker and `ngrok` workflow later when needed for real phone
  checks.

Why:

- Layout issues are easier to catch immediately after the redesign than after
  more features have been added.

How to test:

- Check the main page, booking flow, admin login, and admin dashboard on both
  desktop and mobile sizes.

## Phase 4: Test The Docker Plus Supabase Stack Properly

Goal:

- Make sure the new Docker plus Supabase setup is stable before adding payment
  and deployment work.

Why this phase matters:

- We should trust the core development setup before we build more features on
  top of it.

### Step 1. Make the automated tests pass with the new setup

What to do:

- Run the test suite and fix anything broken by the Docker and Supabase-related
  changes.

Why:

- Existing behavior should remain correct while infrastructure changes.

How to test:

- All tests pass.

### Step 2. Add a race-condition test for the last available canoe

What to do:

- Add a test that simulates two booking attempts competing for the last
  available canoe.

Why:

- Preventing overbooking is one of the most important business rules in the
  project.
- This is best tested explicitly instead of assuming the current logic is
  enough.

How to test:

- The test should prove that only one booking can succeed when one canoe
  remains.

### Step 3. Make the booking flow safe against overbooking at the database level

What to do:

- Review and improve the booking confirmation logic so it stays correct even
  when two users act at nearly the same time.

Why:

- Database-backed protection is more reliable than frontend-only or timing-based
  protection.

How to test:

- Re-run the race-condition test and confirm it passes reliably.

### Step 4. Add at least one optional Supabase-backed integration check

What to do:

- Add one integration test or verification script that runs only when the
  Supabase test environment variables are present.
- Use it to verify one important database behavior against the hosted Supabase
  database.

Why:

- SQLite and hosted Postgres can behave differently.
- This should not make normal local test runs depend on the internet or a cloud
  account, so the check should stay optional.

How to test:

- Run the Supabase-backed check intentionally and confirm it passes.

### Step 5. Test migration and seed flows against the Supabase test database

What to do:

- Verify migrations and admin seeding against a disposable Supabase test
  database or clearly reset test data between runs.

Why:

- These are the commands needed when preparing a fresh hosted environment.

How to test:

- Start from a clean Supabase test state and confirm setup commands work.

## Phase 5: Add ngrok For Real Device And Webhook Testing

Goal:

- Make local development easier to test from a phone and with external services.

Why this phase matters:

- Phone testing should happen on a real phone.
- Stripe webhook testing is much easier when the local app has a public HTTPS
  URL.

### Step 1. Add an `ngrok` development guide

What to do:

- Document the basic `ngrok` workflow for local testing.

Why:

- This creates one standard way to expose the local app safely during
  development.

How to test:

- Start `ngrok` and open the public URL.

### Step 2. Test the homepage on a real phone

What to do:

- Open the local site through `ngrok` on a phone.

Why:

- Real devices often reveal layout issues that desktop testing misses.

How to test:

- Load the site on the phone and confirm it renders correctly.

### Step 3. Confirm `ngrok` works for webhook development

What to do:

- Prepare the app so future webhook testing can target the `ngrok` URL.

Why:

- This will later be needed for Stripe.

How to test:

- Confirm the app can receive a test request through the public tunnel.

## Phase 6: Replace The Fake Payment Flow With Stripe

Goal:

- Make booking confirmation depend on real payment confirmation.

Why this phase matters:

- The current payment flow is only a placeholder and should not be used for real
  users.

### Step 1. Design the Stripe booking flow

What to do:

- Decide what should happen in order:
  - create booking intent,
  - create Stripe checkout session,
  - receive webhook,
  - finalize booking.

Why:

- The flow should be clear before code is changed.

How to test:

- Review the flow and confirm each state is understandable.

### Step 2. Add the Stripe SDK and configuration

What to do:

- Add Stripe as a dependency and configure the required environment variables.

Why:

- The app needs a clean way to talk to Stripe.

How to test:

- Start the app and confirm Stripe configuration loads correctly.

### Step 3. Create a Stripe Checkout session

What to do:

- Replace the fake checkout step with a real Stripe session creation step.

Why:

- Stripe Checkout is simpler and safer than building a custom card form.

How to test:

- Start a checkout session and confirm Stripe returns a valid redirect URL.

### Step 4. Store payment references in the database

What to do:

- Save the Stripe session ID and payment status.

Why:

- We need a reliable record of what happened.

How to test:

- Start a checkout and confirm the payment reference is stored.

### Step 5. Add a Stripe webhook endpoint

What to do:

- Add a webhook route that listens for successful payment events.

Why:

- Webhooks are the reliable source of truth for completed payments.

How to test:

- Send a Stripe test webhook and confirm the app receives it.

### Step 6. Finalize bookings only after verified payment

What to do:

- Only convert pending bookings into real bookings after Stripe confirms
  payment.

Why:

- This prevents false bookings.

How to test:

- Complete a test payment and confirm the booking is finalized only after the
  webhook is handled.

## Phase 7: Add Monitoring, Logging, And Alerts

Goal:

- Make production failures visible and easier to debug.

Why this phase matters:

- If something breaks during the booking period, you need to know quickly.

### Step 1. Add structured application logging

What to do:

- Improve logging for important app events and errors.

Why:

- Logs help explain what went wrong later.

How to test:

- Trigger a few actions and confirm the logs are useful and readable.

### Step 2. Add Sentry for application errors

What to do:

- Capture exceptions and stack traces in a hosted error monitoring service.

Why:

- This makes debugging production crashes much easier.

How to test:

- Trigger a test exception and confirm it appears in Sentry.

### Step 3. Add uptime monitoring

What to do:

- Add a service that checks if the website is reachable.

Why:

- Not all failures appear as app exceptions.

How to test:

- Point the monitor at a test URL and confirm checks are being recorded.

### Step 4. Add alerting by email first

What to do:

- Configure alerts for downtime and important failures.

Why:

- Email is the easiest and cheapest alert channel to start with.

How to test:

- Trigger a test alert and confirm it arrives.

### Step 5. Decide later if SMS is necessary

What to do:

- Revisit SMS only if email alerts are not enough.

Why:

- SMS often adds cost and complexity.

How to test:

- This step does not need implementation yet unless email proves insufficient.

## Phase 8: Test Deployment On Google Cloud Run

Goal:

- Verify that the app can run safely in a cloud environment close to the planned
  production setup.

Why this phase matters:

- We should test deployment before the final launch window.

### Step 1. Prepare the app for Cloud Run

What to do:

- Make sure the container, startup command, and environment variables work for
  Cloud Run.

Why:

- Cloud Run expects a containerized app with clear runtime behavior.

How to test:

- Deploy a test version and confirm the app starts.

### Step 2. Connect Cloud Run to Supabase

What to do:

- Connect the deployed app to Supabase.

Why:

- This tests the full deployment path we are considering.

How to test:

- Create and read data through the deployed app.

### Step 3. Apply migrations for the deployed environment

What to do:

- Make sure the deployed environment uses the correct schema.

Why:

- Deployment is not complete unless the database schema is correct.

How to test:

- Confirm the deployed app works against the migrated database.

### Step 4. Verify public HTTPS access and basic security

What to do:

- Check security-related settings and public access behavior.

Why:

- A public deployment should not go live without basic security review.

How to test:

- Verify HTTPS works, secrets are not exposed, and admin access behaves as
  expected.

### Step 5. Review Supabase exposure settings and Row Level Security

What to do:

- Review which tables live in the exposed Supabase schema.
- Enable Row Level Security where it is needed.
- Document whether tables are only accessed through the Flask backend or also
  through Supabase APIs later.

Why:

- Supabase can expose tables through its API layer.
- Even if the current app mainly uses a direct database connection, this should
  be reviewed before public launch so tables are not accidentally left too open.

How to test:

- Confirm the chosen tables have the intended RLS setting and that access still
  works the way the app expects.

## Phase 9: Prepare For Public Launch

Goal:

- Make sure the site is safe and understandable before real users depend on it.

Why this phase matters:

- Launch should be calm and controlled, not rushed.

### Step 1. Add a deployment checklist

What to do:

- Create a checklist for:
  - environment variables,
  - database migration,
  - admin setup,
  - monitoring,
  - payment,
  - quick smoke tests.

Why:

- Checklists reduce mistakes.

How to test:

- Run through the checklist once in a test environment.

### Step 2. Add a rollback and backup plan

What to do:

- Decide how to recover from a bad deployment or broken database state.

Why:

- Recovery planning is part of deployment readiness.

How to test:

- Write the steps clearly and confirm they are realistic.

### Step 3. Run a full end-to-end test

What to do:

- Test the complete flow:
  - visit site,
  - book canoe,
  - pay,
  - confirm booking,
  - verify admin visibility,
  - verify alerts and logs.

Why:

- This is the best final confidence check before launch.

How to test:

- Complete the full flow successfully.

### Step 4. Launch the smallest stable version first

What to do:

- Launch only what is necessary for real users.

Why:

- A smaller stable release is better than a bigger unstable one.

How to test:

- Monitor the first real usage period closely.

## Current Recommended Next Step

The next best step is:

1. Continue the temporary frontend refactor checklist in
   `docs/temp_refactor_checklist.md`, moving from the completed JavaScript
   split into the image-folder refactor.
2. Flatten the previous-years images into `static/images/previous_years/` and
   update the backend image lookup.
3. After the image structure is cleaner, continue with the admin redesign
   work.
