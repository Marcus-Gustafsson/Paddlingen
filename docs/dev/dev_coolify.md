# Hetzner And Coolify Deployment

Last updated: 2026-03-23

## Purpose

This document explains a practical first production path for this project:

- Hetzner VPS
- Coolify
- Cloudflare
- this repository's Dockerfile
- Supabase Postgres as the database

It is written as a chain of small, testable steps so you can validate each
piece before moving on.

## Recommended First Production Shape

For this project, the simplest realistic first production setup is:

- one Hetzner VPS running Coolify,
- one app container deployed by Coolify,
- Cloudflare in front of the public domains,
- Supabase Postgres kept outside the VPS,
- DNS managed through Cloudflare and app routing handled by Coolify's reverse
  proxy.

Why this is the current recommendation:

- The app is small and server-rendered.
- The booking flow is database-backed and should use real Postgres in
  production.
- Coolify gives a simpler operational path than manually managing Docker and
  reverse-proxy config on the VPS.
- Cloudflare adds a useful extra edge layer for DNS, TLS, and basic DDoS
  protection without forcing a more complex app architecture.
- Keeping the database external reduces risk on a small VPS.

## Is Hetzner CX23 Enough?

For this app, a `CX23` is a reasonable starting point when you use Supabase as
the database.

`CX23` currently gives:

- 2 vCPU
- 4 GB RAM
- 40 GB SSD

That is usually enough for:

- Coolify itself,
- one small Flask/Gunicorn container,
- low-to-moderate public traffic,
- a few admins,
- ordinary booking bursts for a small event site.

It is not a comfortable size if you also want on the same VPS:

- PostgreSQL,
- Redis,
- backups,
- monitoring stack,
- multiple deployed apps.

## Should The Database Live On The Same VPS?

Technically: yes.

Pragmatically on `CX23`: not as the first production choice.

Why:

- Coolify already uses some memory and disk.
- The app container also needs memory.
- PostgreSQL needs stable RAM and disk headroom.
- Backups and future monitoring add even more pressure.

For a `CX23`, the better first split is:

- VPS for Coolify + app
- Supabase for Postgres

If you later want to self-host Postgres too, move up to at least a larger VPS
such as `CX33`, or use a second server just for the database.

## Is Supabase Free Tier Enough?

For early production testing of this project, probably yes.

The important limit for this repo is the database side, not the auth side.

This app currently uses Supabase mainly as managed Postgres through
`DATABASE_URL`. It is not using Supabase Auth as the primary user system.

That means the most important free-tier constraints are:

- database size,
- compute size,
- egress,
- operational limits such as backup features.

For a small canoe-event site, the free tier can be enough if:

- bookings stay well under the 500 MB database limit,
- image storage is not moved into Supabase too aggressively,
- you accept that the free tier is still a limited environment.

The `50,000 monthly active users` figure matters much less here than the
database size and operational features.

## Production Changes Needed For Coolify

These changes are now implemented in the repo:

1. The Docker container now uses Gunicorn instead of `flask run`.
2. The app can optionally trust reverse-proxy headers through
   `TRUST_REVERSE_PROXY_HEADERS=True`.

Why these matter:

- `flask run` is a development server and should not be used for production.
- Coolify sits behind a reverse proxy, so Flask should be able to read the
  original request scheme and host when you explicitly trust that proxy.

Relevant files:

- `Dockerfile`
- `app/__init__.py`
- `config.py`

## Required Environment Variables In Coolify

At minimum, set these in the Coolify application environment:

```env
FLASK_ENV=production
SECRET_KEY=replace-with-a-long-random-secret
STRIPE_SECRET_KEY=sk_live_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me
STRIPE_PUBLIC_BASE_URL=https://your-public-domain.example
ADMIN_USERNAME=your-bootstrap-admin-username
ADMIN_PASSWORD=your-bootstrap-admin-password
PUBLIC_SITE_PASSWORD_HASH=the-fallback-shared-password-hash
DATABASE_URL=postgresql+psycopg://...
RATELIMIT_STORAGE_URI=redis://redis:6379/0
SESSION_COOKIE_SECURE=True
TRUST_REVERSE_PROXY_HEADERS=True
PORT=8080
GUNICORN_WORKERS=2
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=60
```

Notes:

- `STRIPE_SECRET_KEY` is the server-side Stripe API key. Never expose it in
  client-side code or public repositories.
- `STRIPE_WEBHOOK_SECRET` will come from Stripe after you create a webhook
  endpoint later in the payment implementation.
- `STRIPE_PUBLIC_BASE_URL` should be the public HTTPS root URL of the site, not
  a deeper path.
- `RATELIMIT_STORAGE_URI` should point at the shared Redis service used by
  Flask-Limiter inside Coolify. If Coolify shows a `Redis URL (Internal)` for
  the Redis resource, prefer copying that exact value instead of typing the URL
  manually.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` are still required by the current
  production config validation, even if you later add more admin users through
  the CLI.
- `PUBLIC_SITE_PASSWORD_HASH` stays as the fallback source if the database does
  not yet contain an admin-managed public-site password.
- `PORT=8080` matches the container configuration used by this repo.

## Ports To Care About

For a basic Coolify VPS setup, think in terms of:

- `22` for SSH
- `80` for HTTP and certificate issuance
- `443` for HTTPS
- `8000` only for initial Coolify setup before the dashboard has its domain

After Coolify is reachable through its own domain, you should not keep `8000`
publicly open unless you have a clear reason.

## Step-By-Step Deployment Plan

### Step 1. Verify the production container locally

What to do:

- Build the Docker image locally.
- Run it with production-like environment variables.

Commands:

```bash
docker build -t paddlingen-web .
docker run --rm --name paddlingen-web -p 8080:8080 --env-file .env paddlingen-web
```

What to test:

- open `http://127.0.0.1:8080`
- confirm the homepage loads
- confirm `/login` loads
- confirm the admin page works after login

Do not continue until this passes.

### Step 2. Prepare the Supabase database

What to do:

- Create the Supabase project.
- Copy the Postgres connection string.
- Convert the prefix to `postgresql+psycopg://` if Supabase shows
  `postgresql://`.

What to test:

- confirm the final `DATABASE_URL` is accepted by the app locally

### Step 3. Apply the schema manually

What to do:

- Point your local shell to the production `DATABASE_URL`.
- Run the migrations manually.

Command:

```bash
uv run alembic upgrade head
```

What to test:

- confirm all tables exist in Supabase

Do not seed or deploy the app before the schema is correct.

### Step 4. Seed the event and the first admin manually

What to do:

- Seed the active event row.
- Seed the initial admin account.

Commands:

```bash
uv run flask --app wsgi seed-active-event
uv run flask --app wsgi seed-admin
```

What to test:

- confirm the event exists in the database
- confirm the admin user exists

### Step 5. Create the Hetzner VPS

What to do:

- Create one Ubuntu LTS VPS.
- Start with `CX23` if you keep the database external.
- Add your SSH key.

What to test:

- confirm you can SSH into the server

### Step 6. Install Coolify

What to do:

- Install Coolify on the VPS.
- Log in through the initial dashboard.
- Set a proper domain for the Coolify instance itself.

What to test:

- confirm the Coolify dashboard works through HTTPS on its own domain

### Step 7. Put Cloudflare in front of the public domains

What to do:

- Move DNS for the public app domain into Cloudflare.
- Enable Cloudflare proxying for the public domain.
- Decide whether the Coolify admin domain should also sit behind Cloudflare or
  stay directly pointed at the VPS.

Why:

- Cloudflare adds a safer first edge layer for a small VPS deployment:
  - DNS management,
  - TLS handling help,
  - CDN behavior for public traffic,
  - basic DDoS protection.

What to test:

- confirm the public domain resolves through Cloudflare
- confirm the app still reaches the Hetzner origin correctly

### Step 8. Lock down the VPS firewall

What to do:

- Keep only the ports you need open publicly.

Recommended public ports:

- `22`
- `80`
- `443`

What to test:

- confirm the app and Coolify still work through their domains
- confirm direct access to the temporary unsecured setup path is no longer
  needed

### Step 9. Add this repo as an application in Coolify

What to do:

- Deploy from GitHub through the existing `Dockerfile`.
- Use the container port `8080`.
- Set the app domain in Coolify.
- Add all required environment variables.

What to test:

- trigger a deployment
- confirm the container starts
- confirm the domain serves the app over HTTPS

### Step 10. Add Redis for shared rate limiting

What to do:

- Create one Redis resource in Coolify.
- Give it a simple name, for example `redis`, so it is easy to recognize later.
- Open the Redis resource in Coolify and go to its general configuration.
- Copy the value labeled `Redis URL (Internal)` if Coolify shows it.
- If Coolify does not show that value, build the URL from the internal service
  name, for example `redis://redis:6379/0` when the resource is named `redis`.
- Add that value to the Flask application environment as
  `RATELIMIT_STORAGE_URI`.
- Redeploy the Flask application after saving the new environment variable.

Why:

- Flask-Limiter uses this backend to keep request counters shared across
  multiple Gunicorn workers and across app restarts.
- The local `memory://` backend is fine for development, but it is not suitable
  for the deployed VPS setup.
- Using Coolify's internal Redis URL is safer than guessing the hostname,
  because it follows Coolify's own service/network configuration.

Step-by-step inside Coolify:

1. Open the project where the Flask application lives.
2. Create a new database resource and choose `Redis`.
3. Give the resource a clear name such as `redis`.
4. Deploy the Redis resource.
5. Open the Redis resource settings and find the internal connection string.
6. Copy the internal Redis URL.
7. Open the Flask application resource.
8. Add or update this environment variable:

```env
RATELIMIT_STORAGE_URI=redis://redis:6379/0
```

9. Replace the example value above with the exact internal URL from Coolify if
   it differs.
10. Save the environment variable.
11. Redeploy the Flask application.

What to test:

- Open the public unlock page and submit the wrong password repeatedly until the
  `/unlock` limit is reached.
- Open the admin login page and trigger the `/login` limit from the same IP.
- Confirm both routes still return HTTP 429 when the limit is exceeded.
- Restart or redeploy the Flask application and repeat the test.
- Confirm the limiter still works after the restart, which shows the counters
  are no longer stored only inside one app process.

### Step 11. Run smoke tests against the live app

What to test:

Public side:

- unlock the public site
- open FAQ and contact modals
- open the participant overview
- complete one test booking

Admin side:

- log in
- open the booking panel
- open the event panel
- open the checklist panel
- change the public-site password

Database side:

- confirm the new booking appears
- confirm admin changes persist

### Step 11. Set up backups before public launch

For Supabase free tier, do not assume you have the same recovery features as a
paid production database.

At minimum:

- keep the migration history in git,
- export database backups regularly,
- store exports somewhere outside the VPS,
- document how to restore.

Minimum practical backup command example:

```bash
pg_dump "postgresql://..." > paddlingen-backup.sql
```

Use your real production connection details when you run it.

What to test:

- confirm a backup file is created
- confirm the restore steps are written down clearly

## Recommended First Rollout Order

If you want the safest route, use this order:

1. local production container test
2. Supabase connection test
3. schema migration
4. seed event and admin
5. VPS + Coolify install
6. Cloudflare setup
7. app deployment
8. live smoke test
9. backup check

That keeps each step small and easy to debug.

## Current Recommendation Summary

For this project right now:

- `Hetzner CX23 + Coolify + Cloudflare + Supabase` is a sensible first
  production route.
- `Supabase free` is likely enough for early real-world testing.
- self-hosting Postgres on the same `CX23` is possible, but not the route I
  would choose first.
