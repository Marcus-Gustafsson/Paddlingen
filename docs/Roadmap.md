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
  - local PostgreSQL for development and testing,
  - later deployment experiments with Google Cloud Run,
  - later managed PostgreSQL testing with Neon or Supabase,
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

- We should still use a local PostgreSQL database in Docker as the main
  development database.
- Later, we should also create a free Neon or Supabase project for integration
  testing before deployment.

Why:

- Local PostgreSQL makes development faster, cheaper, and more predictable.
- Neon or Supabase should be treated as deployment-like environments, not as the
  main place where everyday development happens.
- This gives us both:
  - a stable local workflow,
  - and realistic cloud testing before launch.

## Phase 1: Understand The Current Project

Goal:


### Step 1. Fix obvious inconsistencies

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

## Phase 2: Standardize Local Development With Docker And PostgreSQL

Goal:

- Make local development reproducible and closer to production.

Why this phase matters:

- Docker gives us a predictable setup.
- Local PostgreSQL helps us practice the same database type we expect to use in
  the cloud.

### Step 1. Add a Dockerfile for the Flask app

What to do:

- Define how the web app is built and started inside a container.

Why:

- The app should run the same way on any machine.

How to test:

- Build the image successfully.

### Step 2. Add a PostgreSQL service in Docker Compose

What to do:

- Add a PostgreSQL container for local development.

Why:

- The database should run as a separate service from the app.

How to test:

- Start the database container and confirm it is reachable.

### Step 3. Add Docker Compose for app + database together

What to do:

- Create a single local command that starts the whole stack.

Why:

- This reduces setup mistakes and makes development easier to repeat.

How to test:

- Start both containers and load the website in the browser.

### Step 4. Move configuration into a Docker-friendly setup

What to do:

- Make sure environment variables work clearly with the containers.

Why:

- The app needs predictable configuration for database connection, secrets, and
  admin credentials.

How to test:

- Change configuration values through environment variables and confirm the app
  still starts correctly.

### Step 5. Configure the app to use local PostgreSQL by default in Docker

What to do:

- Point the app container to the PostgreSQL container.

Why:

- This becomes the default local development path.

How to test:

- Start the stack and confirm the app can read and write data in PostgreSQL.

### Step 6. Make migrations the normal schema workflow

What to do:

- Make sure schema changes are applied through Alembic migrations.

Why:

- This is the safer long-term way to manage database changes.

How to test:

- Run migrations against the local PostgreSQL container and confirm the schema
  is created correctly.

### Step 7. Update the README for the Docker-first workflow

What to do:

- Replace old setup instructions with the new local workflow.

Why:

- The documentation should match the real way the project is developed.

How to test:

- Follow the README from a clean state and confirm it works.

## Phase 3: Test The Local Stack Properly

Goal:

- Make sure the new local environment is stable before adding cloud services.

Why this phase matters:

- We should trust the local setup before we start testing cloud-specific
  behavior.

### Step 1. Make the automated tests pass with the new setup

What to do:

- Run the test suite and fix anything broken by the Docker/PostgreSQL changes.

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

### Step 4. Add at least one PostgreSQL integration test

What to do:

- Add one test that verifies key database behavior against PostgreSQL.

Why:

- SQLite and PostgreSQL can behave differently.

How to test:

- Run the test against the local PostgreSQL setup and confirm it passes.

### Step 5. Test database reset and seed flows

What to do:

- Verify initialization, migrations, and admin seeding in the Docker setup.

Why:

- These are the commands needed when setting up a fresh environment.

How to test:

- Start from an empty database and confirm setup commands work.

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

## Phase 5: Test Managed PostgreSQL In The Cloud

Goal:

- Verify that the app also works with a real hosted PostgreSQL provider.

Why this phase matters:

- Local PostgreSQL is the main development setup.
- Neon or Supabase should be the next test step before deployment.

### Step 1. Compare Neon and Supabase for this project

What to do:

- Choose one provider to test first.

Why:

- Both are useful, but it is better to test one properly than both at once.

Suggested first choice:

- Start with Neon if the main focus is simple hosted PostgreSQL.
- Start with Supabase if storage for images may soon matter as well.

How to test:

- Write down the selected provider and the reason for the choice.

### Step 2. Create one free managed PostgreSQL project

What to do:

- Create a free account and one test database project.

Why:

- This gives us a realistic cloud database to test against.

How to test:

- Confirm you can connect to the database from the app locally.

### Step 3. Run migrations against the managed database

What to do:

- Apply the schema to the hosted database.

Why:

- We need to confirm the real cloud database works with our migration flow.

How to test:

- Run migrations successfully and inspect the created tables.

### Step 4. Run the app locally against the managed database

What to do:

- Point the local app container to Neon or Supabase.

Why:

- This tests a production-like database setup without deploying the app yet.

How to test:

- Create and read bookings successfully through the app.

### Step 5. Decide how images should be stored

What to do:

- Decide between:
  - keeping images as app static files for now,
  - or moving them to object storage later.

Why:

- This affects hosting simplicity and future maintainability.

How to test:

- Confirm the chosen approach works for at least one image example.

### Step 6. Implement the previous-years image display approach

What to do:

- Implement the chosen image setup so previous-year images actually render in
  the website using the selected source.

Why:

- The website goal is not just to store images, but to show them correctly to
  visitors.

How to test:

- Open the website and confirm previous-year sections display images correctly.

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

### Step 2. Connect Cloud Run to the managed database

What to do:

- Connect the deployed app to Neon or Supabase.

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

1. Define what booking information must be stored.
2. Verify the current booking and admin flows manually.
3. Then implement the Docker + local PostgreSQL setup.
