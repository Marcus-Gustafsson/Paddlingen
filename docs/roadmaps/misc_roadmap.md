# Misc Roadmap

Last updated: 2026-03-20

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

### Step 1. Add an ngrok development guide (Completed 2026-03-20)

Completed work:

- Added `docs/dev/dev_ngrok.md`.
- Documented the WSL workflow for:
  - running the local app first,
  - verifying the local port,
  - starting ngrok on the matching port,
  - sharing the public URL with testers.
- Updated the development overview so the ngrok guide is easy to find.

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

## Phase 3: Add Privacy And Content-Governance Basics

Goal:

- Keep the project easier to manage when handling participant data and event
  photos.

### Step 1. Add a simple privacy and personal-data information page

What to do:

- Add one clear page that explains:
  - what personal data the site handles,
  - why it is handled,
  - who to contact with questions,
  - and how removal or correction requests are handled.

Why:

- The site stores booking names and shows identifiable event photos.
- Even for a small event project, the handling should be explained clearly.

How to test:

- Open the page and confirm a non-technical user can understand how to ask
  about their data.

### Step 2. Add a documented photo-removal workflow

What to do:

- Define how someone asks about a photo or asks for it to be removed.
- Use the stable public image ID in that workflow.

Why:

- The organizer needs one consistent way to identify the correct picture and
  act on the request.

How to test:

- Pick one image ID and confirm the request flow is clear from the public site.

### Step 3. Keep the site on necessary cookies only

What to do:

- Avoid adding analytics or marketing cookies for now.
- Keep the current cookie use limited to necessary site behavior such as
  sessions and CSRF protection.

Why:

- This keeps the privacy setup simpler until a stronger reason exists to add
  more tracking.

How to test:

- Review the app behavior and confirm the site still works without any
  non-essential cookie features.

## Phase 4: Add Monitoring, Logging, And Alerts

Goal:

- Make production failures visible and easier to debug.

### Step 1. Add structured application logging

What to do:

- Improve logging for important app events and errors.
- Make sure later admin actions can be attributed to the logged-in admin user,
  including:
  - public-site password changes,
  - manual booking creation,
  - booking updates and deletions,
  - event edits and event activation.

Why:

- Logs help explain what went wrong later.
- Named admin accounts make those logs much more useful once several admins use
  the dashboard.

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

## Phase 5: Test Deployment On Hetzner + Coolify + Cloudflare

Goal:

- Verify that the app can run safely in the planned first production setup
  after Stripe payment has been implemented and tested.

Current note:

- The likely first real deployment path is now:
  - Hetzner VPS,
  - Coolify,
  - Cloudflare in front of the public domains,
  - Supabase as managed Postgres.

### Step 1. Prepare the app container for the real deployment path

What to do:

- Confirm the Docker image, startup command, and environment variables work for
  the Coolify deployment path.

Why:

- The deployment path should be verified locally before a VPS is involved.

How to test:

- Run the production-like container locally and confirm the app starts.

### Step 2. Connect the production config to Supabase

What to do:

- Prepare the production `DATABASE_URL` and confirm the deployed app will use
  Supabase.

Why:

- The app should use managed Postgres before the hosting side is introduced.

How to test:

- Confirm the app can create and read data against the production-like
  database settings.

### Step 3. Apply migrations in the deployed environment

What to do:

- Make sure the planned production database uses the correct schema.

Why:

- Deployment is not complete unless the database schema is correct.

How to test:

- Confirm the migrated database is usable before the VPS deployment starts.

### Step 4. Seed the first production event and admin access manually

What to do:

- Seed the active event and the first admin account into the production
  database.

Why:

- The deployed app should not come up against an empty production database by
  surprise.

How to test:

- Confirm the event and the first admin user exist before deployment.

### Step 5. Create the Hetzner VPS and install Coolify

What to do:

- Create the VPS, add SSH access, and install Coolify.

Why:

- This is the actual hosting base for the first production route.

How to test:

- Confirm the VPS is reachable and the Coolify dashboard opens correctly.

### Step 6. Put Cloudflare in front of the public domains

What to do:

- Move DNS to Cloudflare.
- Put Cloudflare proxying in front of the public app domain.
- Keep Coolify reachable through its own controlled domain as well.

Why:

- Cloudflare adds DNS management, basic CDN behavior, and useful DDoS
  protection in front of a small VPS deployment.

How to test:

- Confirm the app domain resolves through Cloudflare and still reaches the
  origin correctly.

### Step 7. Deploy the app through Coolify

What to do:

- Connect the repo to Coolify.
- Configure environment variables.
- Deploy the application container to the Hetzner VPS.

Why:

- This is the first full end-to-end deployment step.

How to test:

- Confirm the deployed app starts and serves the site correctly through the
  real domain.

### Step 8. Review HTTPS, firewall, and origin exposure

What to do:

- Verify HTTPS behavior across Cloudflare and Coolify.
- Lock down the VPS firewall.
- Minimize direct exposure of the origin server.

Why:

- A public deployment should not go live without a basic network and security
  review.

How to test:

- Verify HTTPS works, the expected ports are open, and the old temporary access
  path is no longer needed.

### Step 9. Review Supabase exposure settings and Row Level Security

What to do:

- Review exposed tables.
- Enable Row Level Security where needed.

Why:

- Supabase can expose tables through its API layer, even if the app mainly uses
  direct database connections.

How to test:

- Confirm the chosen tables have the intended RLS setting.

## Phase 6: Prepare For Public Launch

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
