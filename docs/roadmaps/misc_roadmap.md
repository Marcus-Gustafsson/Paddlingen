# Misc Roadmap

Last updated: 2026-03-19

## Goal

Handle the project-maintenance and operational work that does not fit cleanly
into the frontend or backend roadmaps.

This roadmap covers:

- project structure,
- documentation structure,
- ngrok workflow,
- monitoring and alerts,
- deployment,
- launch preparation.

## Completed Foundation Work

These misc/project-maintenance milestones are already done:

- Public CSS has been split into focused files.
- Public JavaScript has been split into focused files.
- Previous-years images have been flattened into
  `static/images/previous_years/`.
- The roadmap has now been split into focused roadmap documents.
- The development documentation has now been split into focused documents.
- The temporary refactor checklist has been retired after the permanent docs
  were updated.

## Phase 1: Split The Development Documentation (Completed 2026-03-19)

Completed work:

- Created:
  - `docs/dev/dev_overview.md`
  - `docs/dev/dev_docker.md`
  - `docs/dev/dev_database.md`
  - `docs/dev/dev_testing.md`
- Removed the old `docs/dev_doc.md` file.
- Updated AGENTS, README, and overview docs to point to the new development
  document structure.

## Phase 2: Add ngrok For Real Device And Webhook Testing

Goal:

- Make local development easier to test from a phone and with external
  services.

### Step 1. Add an ngrok development guide

What to do:

- Document the basic ngrok workflow for local testing.

Why:

- This creates one standard way to expose the local app during development.

How to test:

- Start ngrok and open the public URL.

### Step 2. Confirm ngrok works for webhook development

What to do:

- Make sure later webhook testing can target the ngrok URL.

Why:

- This will be needed once Stripe webhooks are added.

How to test:

- Send a test request through the public tunnel and confirm the app receives
  it.

## Phase 3: Add Monitoring, Logging, And Alerts

Goal:

- Make production failures visible and easier to debug.

### Step 1. Add structured application logging

What to do:

- Improve logging for important app events and errors.

Why:

- Logs help explain what went wrong later.

How to test:

- Trigger a few actions and confirm the logs are readable.

### Step 2. Add Sentry for application errors

What to do:

- Capture exceptions and stack traces in a hosted error monitoring service.

Why:

- This makes debugging production failures much easier.

How to test:

- Trigger a test exception and confirm it appears in Sentry.

### Step 3. Add uptime monitoring

What to do:

- Add a service that checks whether the site is reachable.

Why:

- Not all failures appear as app exceptions.

How to test:

- Point the monitor at a test URL and confirm checks are recorded.

### Step 4. Add alerting by email first

What to do:

- Configure alerts for downtime and important failures.

Why:

- Email is the easiest alert channel to start with.

How to test:

- Trigger a test alert and confirm it arrives.

## Phase 4: Test Deployment On Google Cloud Run

Goal:

- Verify that the app can run safely in a cloud environment close to the
  planned production setup.

### Step 1. Prepare the app for Cloud Run

What to do:

- Confirm the container, startup command, and environment variables work for
  Cloud Run.

Why:

- Cloud Run expects clear container runtime behavior.

How to test:

- Deploy a test version and confirm the app starts.

### Step 2. Connect Cloud Run to Supabase

What to do:

- Connect the deployed app to Supabase.

Why:

- This tests the planned deployment path end to end.

How to test:

- Create and read data through the deployed app.

### Step 3. Apply migrations in the deployed environment

What to do:

- Make sure the deployed environment uses the correct schema.

Why:

- Deployment is not complete unless the database schema is correct.

How to test:

- Confirm the deployed app works against the migrated database.

### Step 4. Review public HTTPS access and basic security

What to do:

- Check HTTPS, secret handling, and admin access behavior.

Why:

- A public deployment should not go live without a basic security review.

How to test:

- Verify HTTPS works and secrets are not exposed.

### Step 5. Review Supabase exposure settings and Row Level Security

What to do:

- Review exposed tables.
- Enable Row Level Security where needed.

Why:

- Supabase can expose tables through its API layer, even if the app mainly uses
  direct database connections.

How to test:

- Confirm the chosen tables have the intended RLS setting.

## Phase 5: Prepare For Public Launch

Goal:

- Make the release process safe and predictable.

### Step 1. Add a deployment checklist

What to do:

- Create a checklist for:
  - environment variables,
  - migrations,
  - admin setup,
  - monitoring,
  - payment,
  - smoke tests.

Why:

- Checklists reduce deployment mistakes.

How to test:

- Run the checklist once in a test environment.

### Step 2. Add a rollback and backup plan

What to do:

- Decide how to recover from a bad deployment or broken database state.

Why:

- Recovery planning is part of launch readiness.

How to test:

- Write the steps clearly and confirm they are realistic.

### Step 3. Run a full end-to-end prelaunch test

What to do:

- Test:
  - visit site,
  - book canoe,
  - pay,
  - confirm booking,
  - verify admin visibility,
  - verify logs and alerts.

Why:

- This is the best final confidence check before launch.

How to test:

- Complete the full flow successfully.

### Step 4. Launch the smallest stable version first

What to do:

- Launch only what real users need first.

Why:

- A smaller stable release is safer than a bigger unstable one.

How to test:

- Monitor the first real usage period closely.
