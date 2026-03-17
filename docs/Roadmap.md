# Paddlingen Roadmap

Last updated: 2026-03-17

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

### Step 2. Create a Supabase test project and collect the required credentials

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

### Step 3. Choose the correct Supabase database connection method

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

### Step 4. Add Supabase environment variables to the app configuration

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

### Step 5. Connect the current SQLAlchemy app to Supabase Postgres

What to do:

- Point `DATABASE_URL` to the chosen Supabase Postgres connection string.

Why:

- This lets the current backend use Supabase without rewriting the data layer.
- It matches how the app already works today.

How to test:

- Start the app and confirm it can read and write data in the Supabase-hosted
  database.

### Step 6. Run Alembic migrations against Supabase Postgres

What to do:

- Apply the existing schema to the Supabase database through Alembic.

Why:

- The current project already uses Alembic, so schema changes should remain
  migration-driven.

How to test:

- Run migrations successfully and confirm the expected tables appear in
  Supabase.

### Step 7. Test the current booking and admin flows against Supabase

What to do:

- Run the app locally with the Supabase-backed `DATABASE_URL`.
- Test the booking flow and the admin flow manually.

Why:

- This confirms the real hosted database works with the current code before any
  refactor is attempted.

How to test:

- Create a test booking, confirm it appears in the database and admin view, and
  verify the admin can still log in and edit data.

### Step 8. Update the README for the Docker + Supabase workflow

What to do:

- Replace outdated setup instructions with the current Supabase-based testing
  path.

Why:

- The documentation should match the real way the project is developed.

How to test:

- Follow the README from a clean state and confirm it works.

## Phase 3: Test The Docker Plus Supabase Stack Properly

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

## Phase 4: Add ngrok For Real Device And Webhook Testing

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

## Phase 5: Add Previous-Years Image Support

Goal:

- Show previous-years images in a simple way that fits the hosting plan.

Why this phase matters:

- Previous-years images are part of the website goal.
- It is easier to choose a simple image approach early than to bolt it on late.

### Step 1. Decide where images should live first

What to do:

- Decide between:
  - storing a small first set of images inside the project as static files,
  - or using Supabase Storage.

Why:

- This choice affects complexity, deployment, and how much Supabase is used at
  the start.

Recommended first choice:

- Start with static files if the number of images is small and you want the
  simplest first version.
- Move to Supabase Storage later if image management becomes annoying or you
  want uploads outside the codebase.

How to test:

- Write down the selected image approach and the reason for the choice.

### Step 2. Add the first previous-years images

What to do:

- Add a small set of real images from previous years using the chosen storage
  approach.

Why:

- We should prove the image plan works with real files, not just a placeholder
  idea.

How to test:

- Confirm the files are accessible in development.

### Step 3. Display the images on the website

What to do:

- Render the previous-years images in a clear section on the site.

Why:

- The goal is to show the images to visitors, not only store them somewhere.

How to test:

- Open the website and confirm the images render correctly.

### Step 4. Check image performance and maintenance effort

What to do:

- Decide whether the chosen image approach is still simple enough.

Why:

- It is better to evaluate this early before more images are added.

How to test:

- Review the result and decide whether to keep it or switch to Supabase Storage
  before launch.

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

1. Create the Supabase test project and collect the connection details and API
   details.
2. Add `DATABASE_URL` to the local `.env` file and keep the other Supabase
   values as optional placeholders for later.
3. Run the current app against Supabase before considering any SDK-based
   refactor.
