# Paddlingen Technical Overview

Last updated: 2026-03-17

## Purpose

This document explains how the Paddlingen application is currently built.

It is meant for someone who:

- has not worked on the project in a long time,
- is new to web development,
- wants to understand how the parts connect,
- wants to know why the current structure looks the way it does.

This is a technical overview, not a deployment guide. The goal is to explain
the current architecture and design choices in plain language.

## What The Application Is

Paddlingen is a small Flask web application for a canoe event.

At a high level, the application does five things:

1. Shows a public event website.
2. Lets visitors start a canoe booking.
3. Stores booking data in a database.
4. Lets an admin log in and manage bookings.
5. Shows photos and event-related information from current and previous years.

## The Main Building Blocks

The project is built from a few core layers:

1. Flask application setup
   This creates the app and wires together extensions like the database,
   login system, CSRF protection, and rate limiting.

2. Routes
   These are the URL handlers. They decide what happens when a user visits `/`,
   submits the booking form, logs in, or uses the admin area.

3. Templates
   These are the HTML files rendered by Flask and sent to the browser.

4. Static files
   These include CSS, JavaScript, and images.

5. Database models
   These define the tables and data structure used by the app.

6. Configuration
   This controls secrets, database connection, debug mode, cookie settings,
   and other environment-specific values.

7. Tests
   These verify the most important flows so changes can be made more safely.

## High-Level Request Flow

The easiest way to understand the app is to follow one request from start to
finish.

### Public page flow

1. A browser requests the homepage at `/`.
2. Flask receives the request.
3. The route in `app/routes.py` loads booking data and image lists.
4. Flask renders `templates/index.html`.
5. The browser receives the HTML.
6. The browser then loads CSS and JavaScript from `static/`.
7. JavaScript calls API routes like `/api/booking-count` to update parts of the
   page dynamically.

### Booking flow

1. A visitor opens the booking modal on the homepage.
2. JavaScript builds the booking form fields in the browser.
3. The form is submitted to `/create-checkout-session`.
4. Flask checks the requested canoe count against current availability.
5. A temporary `PendingBooking` row is stored in the database.
6. The `pending_booking_id` is stored in the user session.
7. The user is redirected to `/payment-success`.
8. The app reads the pending booking from the database and converts it into
   permanent `RentForm` rows.

Important note:

- This is currently a placeholder flow.
- It simulates successful payment instead of using a real payment provider.
- The roadmap already plans to replace this with Stripe.

### Admin flow

1. An admin visits `/login`.
2. Flask validates the username and password against the `User` table.
3. Flask-Login stores the authenticated user in the session.
4. The admin can visit `/admin`.
5. The admin page loads current bookings.
6. The admin can add, update, or delete bookings through form submissions.

## Project Structure

This is the current role of the main files and folders.

### Root files

- `AGENTS.md`
  Repository-level instructions for coding style, workflow expectations, WSL
  assumptions, and documentation upkeep.

- `README.md`
  The current top-level setup document. Some parts are now outdated and will
  need to be refreshed as the roadmap progresses.

- `pyproject.toml`
  Defines the Python project, dependencies, and some tool configuration.

- `uv.lock`
  Locks dependency versions so installs stay consistent.

- `Makefile`
  Provides shortcut commands like install, test, lint, and type-check.

- `config.py`
  Central place for configuration values.

- `wsgi.py`
  Production-style entrypoint that exposes the Flask application object.

- `init_db.py`
  Convenience script for initializing the database and seeding the admin user.

### Application package

- `app/__init__.py`
  Builds the Flask app and connects extensions.

- `app/routes.py`
  Contains the route handlers for the public site, booking flow, auth, API
  endpoints, weather endpoint, and admin interface.

- `app/util/db_models.py`
  Defines the SQLAlchemy models.

- `app/util/helper_functions.py`
  Contains helper logic, currently including image lookup for year folders.

### Frontend files

- `templates/index.html`
  Public website page.

- `templates/login.html`
  Admin login page.

- `templates/admin.html`
  Admin dashboard page.

- `static/css/`
  Stylesheets for the public site and admin area.

- `static/js/script.js`
  Frontend behavior such as modals, booking form logic, progress bar updates,
  image gallery behavior, and weather widget requests.

- `static/images/`
  Current storage location for event images grouped by year.

### Database and migrations

- `migrations/`
  Alembic migration setup.

- `migrations/versions/`
  Stores migration files that describe schema changes over time.

- `alembic.ini`
  Alembic configuration file.

### Tests

- `tests/`
  Contains automated tests for public pages, authentication, admin CRUD, APIs,
  and CLI commands.

### Documentation

- `docs/Roadmap.md`
  Forward-looking implementation plan for the next stages of the project.

- `docs/TechnicalOverview.md`
  Ground-up explanation of how the current application is built.

- `docs/dev_doc.md`
  Development reference for commands, setup steps, and workflow updates.

## How The Flask App Is Created

The application is built using the Flask application factory pattern.

The main function is `create_app()` in `app/__init__.py`.

This function currently does the following:

1. Creates a new Flask app instance.
2. Loads configuration from `config.py`.
3. Initializes these extensions:
   - Flask-SQLAlchemy
   - Flask-WTF CSRF protection
   - Flask-Login
   - Flask-Limiter
4. Calls `db.create_all()`.
5. Registers the main blueprint from `app/routes.py`.
6. Registers CLI commands for database initialization and admin creation.

### Why use an application factory?

This is a common Flask pattern because it makes the app easier to:

- test,
- configure,
- reuse in scripts and tools,
- initialize in different environments.

Instead of importing one global app object everywhere, the project creates an
app instance when needed.

### Why this choice is good

- It scales better than putting everything in one global file.
- It works well with testing.
- It fits Flask best practices.

### Important current limitation

The app factory currently calls `db.create_all()` automatically.

Why that was probably done:

- It makes development easy because tables appear automatically.

Why this matters now:

- The project also has Alembic migrations.
- In a more mature setup, migrations should become the main schema-management
  path instead of relying on automatic table creation.

## Configuration And Environment Variables

`config.py` is the central configuration file.

### What it currently controls

- `SECRET_KEY`
- `PAYMENT_API_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `DATABASE_URL`
- `FLASK_DEBUG`
- `SESSION_COOKIE_SECURE`
- session security settings
- CSRF settings
- `MAX_CANOEES`

### Why configuration is separated from route code

This is a standard and good design choice.

It allows the app to:

- behave differently in development and production,
- keep secrets outside source code,
- swap database backends without rewriting route logic.

### Current database behavior

If `DATABASE_URL` is set:

- the app uses that database.

If `DATABASE_URL` is not set:

- the app falls back to SQLite in `instance/paddlingen.db`.

Important note:

- The roadmap now plans to move the project toward Docker plus PostgreSQL as the
  default development path, so this area will likely change.

## Database Design

The current database layer uses Flask-SQLAlchemy and SQLAlchemy models.

There are three main models.

### 1. `RentForm`

Purpose:

- Stores confirmed bookings.

Current fields:

- `id`
- `name`
- `transaction_id`

What this means in practice:

- The current confirmed-booking model is still quite simple.
- It does not yet store the richer booking information the roadmap wants, such
  as email, explicit payment status, or clearer order-level data.

### 2. `PendingBooking`

Purpose:

- Stores temporary booking data before payment is confirmed.

Current fields:

- `id`
- `canoe_count`
- `participant_names`
- `status`

Why this model exists:

- Earlier designs often store temporary booking state in browser session data.
- This app instead stores the important booking details on the server and only
  keeps a reference ID in the session.

Why this is a good design choice:

- It reduces client-side tampering risk.
- It gives the server control over booking data before confirmation.

### 3. `User`

Purpose:

- Stores admin accounts.

Current fields:

- `id`
- `username`
- `pw_hash`

Why password hashes are used:

- Passwords should never be stored in plain text.
- The app uses Werkzeug helpers to hash and verify passwords.

## Route Structure

Almost all route logic currently lives in `app/routes.py`.

This keeps routing in one place, which is easy to find as a beginner, although
the file is now growing large enough that it may later need to be split.

### Public routes

- `/`
  Renders the homepage and passes bookings and image lists to the template.

- `/create-checkout-session`
  Handles booking submission and creates a temporary pending booking.

- `/payment-success`
  Finalizes a booking after the current simulated payment flow.

### API routes

- `/api/booking-count`
  Returns the number of bookings as JSON.

- `/api/forecast`
  Calls the MET Norway weather API and returns simplified forecast data.

### Authentication routes

- `/login`
  Handles admin login.

- `/logout`
  Logs out the current admin user.

### Admin routes

- `/admin`
  Shows the booking management page.

- `/admin/add`
  Adds a booking.

- `/admin/update/<id>`
  Updates a booking.

- `/admin/delete/<id>`
  Deletes a booking.

## Booking Logic And Business Rules

The main business rule is simple:

- the total number of booked canoes must not exceed `MAX_CANOEES`.

### Where availability is currently checked

Availability is currently checked in two places:

1. When the booking form is submitted.
2. Again during `payment_success`.

Why that was probably done:

- The first check gives fast user feedback.
- The second check tries to prevent overbooking if the situation changed between
  steps.

### Why this is not the final solution yet

- It is better than checking only once.
- But it is not yet a complete database-level race-condition strategy.
- The roadmap already includes explicit steps to test and harden this area.

## Frontend Structure

The frontend is currently server-rendered HTML plus vanilla CSS and vanilla
JavaScript.

### Why that approach was likely chosen

- It keeps the stack simpler than introducing a separate frontend framework.
- It is easier to host and reason about for a small project.
- It works well for a content-heavy site with a modest amount of interactivity.

### Public template

`templates/index.html` handles a lot of responsibilities:

- event presentation,
- yearly sections,
- booking modal,
- overview panel,
- FAQ modal,
- contact modal,
- gallery modal,
- weather widget area.

Why this matters:

- It works, but the file is becoming large.
- As the project grows, it may become better to split pieces into smaller
  templates or partials.

### Frontend JavaScript

`static/js/script.js` currently handles:

- booking progress bar,
- booking count API calls,
- weather widget updates,
- sidebar behavior,
- scroll animations,
- modal open/close logic,
- gallery behavior,
- booking form field generation and validation.

Why this matters:

- The current approach is functional and simple to deploy.
- But the script is already doing many unrelated things, which increases future
  maintenance cost.

## Image Handling

Images are currently stored under `static/images/` in year-specific folders.

There is a helper function in `app/util/helper_functions.py` that:

1. looks inside a year folder,
2. filters valid image file types,
3. shuffles them,
4. returns a limited subset.

Why this was likely chosen:

- It is simple.
- It avoids needing a separate image storage system.
- It works well when image uploads are not happening through the website itself.

Why this may change later:

- If the image set grows or needs easier management, object storage may become a
  better long-term solution.

## Authentication And Security Features

The project already includes several important security-related features.

### 1. Password hashing

Admin passwords are hashed before storage.

### 2. CSRF protection

Flask-WTF CSRF protection is enabled, which helps stop cross-site request
forgery on forms.

### 3. Session security settings

`config.py` sets:

- secure cookies,
- HTTP-only cookies,
- same-site cookie policy.

### 4. Rate limiting

Flask-Limiter is used to rate-limit some routes, such as login and booking.

Important current limitation:

- The current limiter backend is in-memory.
- That is acceptable for local development, but not ideal for a real deployed
  production setup with multiple instances.

## CLI Commands

The app registers two custom Flask CLI commands.

### `init-db`

What it does:

- Drops all tables and recreates them.

Why it exists:

- Fast local reset during development.

Important warning:

- This destroys existing data.

### `seed-admin`

What it does:

- Creates the first admin user from environment variables.

Why it exists:

- It gives a quick way to bootstrap admin access without manually editing the
  database.

## Testing Strategy

The project already has a useful automated test suite.

### What is currently tested

- public homepage access,
- booking behavior,
- authentication,
- login rate limiting,
- admin CRUD,
- JSON API endpoints,
- custom CLI commands.

### How tests currently work

The main test fixture in `tests/conftest.py`:

1. sets `DATABASE_URL` to an in-memory SQLite database,
2. creates a fresh app,
3. recreates the schema,
4. seeds an admin user,
5. returns a Flask test client.

### Why this was likely chosen

- It keeps tests fast.
- It avoids needing a real database server to run tests.
- It makes local testing simple.

### Why this will probably evolve

- SQLite is convenient for fast tests.
- But PostgreSQL can behave differently.
- The roadmap therefore includes adding PostgreSQL-focused integration tests.

## Migrations

The project uses Alembic for schema migrations.

### Why migrations matter

Migrations give a record of how the database schema changes over time.

This is important because:

- production databases should not be changed manually,
- schema changes need to be repeatable,
- different environments need to stay in sync.

### Current state

- Alembic is configured.
- There is currently one initial migration.

### Current design tension

Right now the project has both:

- automatic table creation with `db.create_all()`, and
- Alembic migrations.

This is workable during early development, but eventually one clearer migration
strategy should become the normal path.

## Weather Integration

The app includes a weather feature powered by the MET Norway API.

### How it works

1. The frontend asks `/api/forecast?date=YYYY-MM-DD`.
2. Flask calls the MET API.
3. Flask extracts a selected forecast time.
4. Flask returns simplified JSON with:
   - temperature,
   - rain amount,
   - weather icon.

### Why this is useful

- It adds event-specific information to the homepage without requiring manual
  updates every day.

### Current limitation

- It depends on an external service.
- It currently has only basic failure handling.
- It does not yet include caching or monitoring.

## Why The Current Stack Makes Sense

For a first website, the current stack is understandable and practical.

### Backend

- Flask is lightweight and beginner-friendly.
- Flask-SQLAlchemy is a common way to add database support.
- Flask-Login is a straightforward admin authentication solution.

### Frontend

- Server-rendered HTML is simpler than building a separate frontend app.
- Vanilla CSS and JavaScript avoid extra framework complexity.

### Tooling

- `uv` keeps dependency management fast and reproducible.
- Pytest provides automated safety checks.
- Ruff, Black, and mypy improve code quality.

## Current Simplifications And Planned Improvements

This section explains what is intentionally still simple today.

### Payment flow

Current state:

- Simulated.

Planned improvement:

- Replace with Stripe Checkout and Stripe webhooks.

### Booking data model

Current state:

- Minimal.

Planned improvement:

- Expand the stored booking data and clarify what one booking actually means.

### Database setup

Current state:

- SQLite fallback exists and tests use SQLite in memory.

Planned improvement:

- Move toward Docker plus PostgreSQL as the main local workflow.

### Monitoring

Current state:

- Basic Python logging only.

Planned improvement:

- Add better structured logging, Sentry, uptime checks, and alerts.

### Cloud deployment

Current state:

- Not yet standardized.

Planned improvement:

- Test a Cloud Run deployment with Neon or Supabase.

## What Someone New Should Understand First

If you are new to the project, focus on these ideas first:

1. The app is currently a single Flask backend that renders HTML pages and also
   serves some JSON endpoints.
2. The public site, booking flow, admin area, and simple APIs all live in the
   same Flask application.
3. The database currently stores confirmed bookings, pending bookings, and admin
   users.
4. The payment system is not real yet and should be treated as temporary.
5. The project already has a good foundation, but the roadmap is about making it
   more production-ready step by step.

## Recommended Reading Order

If you want to understand the codebase from the ground up, this is a good order:

1. `app/__init__.py`
2. `config.py`
3. `app/util/db_models.py`
4. `app/routes.py`
5. `templates/index.html`
6. `static/js/script.js`
7. `tests/`
8. `docs/Roadmap.md`

## Summary

Paddlingen is currently a small server-rendered Flask application with a simple
but functional structure:

- Flask handles routing, templates, auth, and APIs.
- SQLAlchemy handles database access.
- Alembic handles schema migrations.
- Vanilla HTML, CSS, and JavaScript power the frontend.
- Tests cover the main behaviors.

The current codebase is already a usable foundation. The next stage is not to
replace everything, but to improve it carefully:

- standardize the local environment,
- harden booking logic,
- add real Stripe payment flow,
- add monitoring,
- and test a real cloud deployment.
