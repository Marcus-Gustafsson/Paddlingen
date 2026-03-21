# Paddlingen Technical Overview

Last updated: 2026-03-20

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
4. Lets an admin log in, manage bookings, and edit event settings.
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
3. The route in `app/routes.py` loads booking data and the image lists needed
   for the previous-years ribbon and gallery.
4. Flask renders `templates/index.html`.
5. The browser receives the HTML.
6. The browser then loads CSS and JavaScript from `static/`.
7. JavaScript calls API routes like `/api/booking-count` to update parts of the
   page dynamically.

Current homepage note:

- The public page is being simplified into one main landing section.
- The current direction is:
  - one centered hero for the current event,
  - weather in the top-left corner area,
  - information and contact actions in the top-right area,
  - a clickable progress bar that opens the participant list,
  - and a previous-years image ribbon below the booking action.
- The older sidebar and multi-section archive styling has now been removed from
  the active homepage CSS so the new hero layout is easier to reason about.
- The previous-years ribbon now loops continuously through the available image
  list instead of using the older preview-only ribbon animation.
- On phone-width screens, the layout now shifts to a portrait-first stacked
  layout so the weather widget and icon buttons sit above the title instead of
  competing with it from the sides.
- On tablet-width screens, the hero now uses its own breakpoint so the center
  content can sit lower and feel more balanced on devices such as iPad Pro in
  landscape mode.
- The FAQ and contact popups now share the same darker card-based style
  direction as the booking modal so the public UI feels more consistent.
- The contact popup currently uses direct `mailto:` and phone links instead of
  an in-site message form.

### Booking flow

1. A visitor opens the booking modal on the homepage.
2. The first booking step lets the visitor choose the number of canoes.
3. The second booking step collects first and last names for each canoe and
   shows a booking summary before submission.
4. One booking is now limited to at most 5 canoes, so larger groups must make
   more than one booking.
5. The form is submitted to `/create-checkout-session`.
6. Flask checks the requested canoe count against current confirmed
   availability.
7. Flask creates one `BookingOrder` row with status `pending_payment`.
8. The order is linked to the active `Event` row when one exists.
9. Flask creates one `BookedCanoe` row per participant with status `reserved`.
10. The `pending_booking_order_id` is stored in the user session.
11. The user is redirected to `/payment-success`.
12. The app reads the pending order from the database and marks the order as
   `paid` and the canoe rows as `confirmed`.

Important note:

- This is currently a placeholder flow.
- It simulates successful payment instead of using a real payment provider.
- The roadmap already plans to replace this with Stripe.

### Admin flow

1. An admin visits `/login`.
2. Flask validates the username and password against the `User` table.
3. Flask-Login stores the authenticated user in the session.
4. The admin can visit `/admin`.
5. The dashboard shows two main actions:
   - booking management,
   - event management.
6. The booking panel lets admins add manual bookings, edit names, and remove
   bookings for the active event.
7. The event panel lets admins select an event, update its settings, create a
   new event by copying an existing one, and switch which event is active.
8. A few low-change event settings still stay in the database only and are not
   shown in the admin form, so the admin UI remains simpler for non-technical
   users.

Important admin-format note:

- The admin event form uses explicit Swedish text inputs for date and time
  (`YYYY-MM-DD` and `HH:MM`) instead of browser-native date and time pickers.
- This keeps the admin input format consistent even when a browser would
  otherwise show English locale formatting such as `03/22/2025` or `10:00 AM`.
- The admin JavaScript also adds Swedish validation messages for these fields
  so format errors do not fall back to the browser's default English wording.
- The subtitle field is optional and can be saved as an empty value.
- If the active event subtitle is blank, the homepage leaves the subtitle area
  empty instead of falling back to the older `config.py` subtitle.

## Project Structure

This is the current role of the main files and folders.

### Root files

- `AGENTS.md`
  Repository-level instructions for coding style, workflow expectations, WSL
  assumptions, and documentation upkeep.

- `Dockerfile`
  First application container definition for running the Flask app in Docker.

- `compose.yaml`
  Docker Compose definition for the current app container. It gives the project
  a stable Docker Desktop grouping and a clearer service name.

- `.dockerignore`
  Prevents local caches, docs, tests, and other unnecessary files from being
  copied into the Docker build context.

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
  Central place for configuration values and fallback defaults used if the
  active database event row is missing.

- `wsgi.py`
  Production-style entrypoint that exposes the Flask application object.

- `init_db.py`
  Convenience script for initializing the database, seeding the active event,
  and then seeding the admin user.

### Application package

- `app/__init__.py`
  Builds the Flask app and connects extensions.

- `app/routes.py`
  Contains the route handlers for the public site, booking flow, auth, API
  endpoints, weather endpoint, and admin interface.

- `app/util/db_models.py`
  Defines the SQLAlchemy models, including `Event`, `EventWeatherCache`,
  `BookingOrder`, `BookedCanoe`, and `User`.

- `app/util/event_settings.py`
  Contains shared helper logic for reading the active event, falling back to
  `config.py`, and seeding the first active event row. It now covers both
  display fields and yearly operational values such as canoe price, booking
  limit, forecast window, and weather coordinates.

- `app/util/helper_functions.py`
  Contains helper logic, including image lookup and stable image metadata for
  the flattened `static/images/previous_years/` folder.

### Frontend files

- `templates/index.html`
  Public website page. It now centers the current event hero and uses a
  previous-years image ribbon instead of the older sidebar-heavy structure.

- `templates/login.html`
  Admin login page.

- `templates/admin.html`
  Admin dashboard page. It now groups admin work into one booking panel and one
  event panel.

- `static/css/`
  Stylesheets for the public site and admin area.

- `static/css/base.css`
  Shared foundation styles such as the font import, reset rules, and small
  utility classes.

- `static/css/home.css`
  Styles for the public homepage hero and layout, including the weather card,
  top-right utility buttons, event heading block, progress area, and small
  homepage-only helpers such as the scroll animation classes.

- `static/css/modals.css`
  Shared popup styles for the public site, including the general modal shell,
  FAQ and contact popup styling, and the participant overview popup.

- `static/css/booking.css`
  Styles for the booking modal, including the two-step layout, quantity
  selector, participant cards, summary panel, and booking action buttons.

- `static/css/gallery.css`
  Styles for the previous-years image ribbon and the full-screen gallery
  lightbox.

- `static/js/booking_progress.js`
  Small standalone module for fetching the confirmed booking count and
  rendering the homepage booking progress bar.

- `static/js/weather.js`
  Small standalone module for the homepage weather widget. It either shows the
  countdown until the forecast becomes available or fetches the forecast from
  the backend.

- `static/js/admin_dashboard.js`
  Small standalone module for opening and closing the admin booking and event
  panels.

- `static/js/modals.js`
  Small standalone module for the public FAQ, contact, and participant
  overview popups.

- `static/js/gallery.js`
  Small standalone module for the previous-years ribbon animation and the
  gallery lightbox. It also preloads the next and previous gallery image so
  image navigation feels faster without loading the whole gallery at once.

- `static/js/booking.js`
  Small standalone module for the two-step public booking modal.

- `static/js/main.js`
  Small entry file for the public homepage. It initializes the split feature
  modules and contains the scroll animation helper.

- `static/images/`
  Static image root. The homepage background image now lives directly in this
  folder as `nitten.png`, while older gallery images live in the flattened
  `static/images/previous_years/` folder.

- `data/previous_year_images.json`
  Stores stable public image IDs such as `IMG-0001` together with the matching
  filenames for the previous-years gallery. The gallery modal shows each image
  ID through a separate `?` help popup so users can reference the correct image
  when contacting the admin.

- `static/images/previous_years/ribbon/`
  Stores generated WebP ribbon variants keyed by stable image ID.

- `static/images/previous_years/gallery/`
  Stores generated WebP gallery variants keyed by stable image ID.

### Database and migrations

- `migrations/`
  Alembic migration setup.

- `migrations/versions/9f8c4d3b2a11_add_event_settings_tables.py`
  Adds the `events` table, the `event_weather_cache` table, and the optional
  `booking_orders.event_id` link used by the new event-backed flow.

- `migrations/versions/`
  Stores migration files that describe schema changes over time.

- `alembic.ini`
  Alembic configuration file.

### Tests

- `tests/`
  Contains automated tests for public pages, authentication, admin CRUD, APIs,
  and CLI commands.

### Documentation

- `docs/roadmaps/`
  Detailed split roadmaps for backend work, frontend work, and misc or
  project-maintenance work.

- `docs/TechnicalOverview.md`
  Ground-up explanation of how the current application is built.

- `docs/dev/`
  Split development documents for overview, Docker, ngrok, database work, and
  testing.

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
4. Registers the main blueprint from `app/routes.py`.
5. Registers CLI commands for database initialization and admin creation.

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

The app no longer creates tables automatically during normal startup.

Why this matters now:

- Alembic is now the intended schema-management path for real environments.
- The convenience commands still support `drop_all()` and `create_all()` for
  quick local resets, but normal app startup should not silently create
  database tables.

## Configuration And Environment Variables

`config.py` is the central configuration file.

### What it currently controls

- event date, time, location, canoe count, and price
- `SECRET_KEY`
- `PAYMENT_API_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `PUBLIC_SITE_PASSWORD_HASH`
- `DATABASE_URL`
- `FLASK_DEBUG`
- `SESSION_COOKIE_SECURE`
- session security settings
- CSRF settings
- `AVAILABLE_CANOES`

### Why configuration is separated from route code

This is a standard and good design choice.

It allows the app to:

- behave differently in development and production,
- keep secrets outside source code,
- swap database backends without rewriting route logic.

It also makes yearly event updates easier because important event-specific
values can now be changed in one obvious place instead of being hardcoded in
multiple files.

### Current database behavior

If `DATABASE_URL` is set:

- the app uses that database.

If `DATABASE_URL` is not set:

- the app falls back to SQLite in `instance/paddlingen.db`.

Important note:

- The roadmap now plans to move the project toward Docker for the app, with
  Supabase as the first hosted database to test against.

## Database Design

The current database layer uses Flask-SQLAlchemy and SQLAlchemy models.

There are three main models.

### 1. `BookingOrder`

Purpose:

- Stores one booking attempt or simulated checkout session.

Current fields:

- `id`
- `public_booking_reference`
- `status`
- `canoe_count`
- `total_amount`
- `currency`
- `payer_full_name`
- `payer_email`
- `payment_provider`
- `payment_provider_session_id`
- `expires_at`
- `paid_at`
- `created_at`
- `updated_at`

What this means in practice:

- The app now has one parent row that represents the whole booking.
- This makes future Stripe integration much easier because payment-related
  status belongs to the order, not to each canoe row.
- Some payment-related columns are currently placeholders until Stripe is
  implemented properly.

### 2. `BookedCanoe`

Purpose:

- Stores one participant name per canoe.

Current fields:

- `id`
- `booking_order_id`
- `participant_first_name`
- `participant_last_name`
- `status`
- `created_at`

Why this model exists:

- One canoe row should represent one participant slot.
- This keeps the participant names structured instead of hiding them inside a
  JSON string.
- It gives the admin view a clearer, more future-proof booking structure.

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
  Handles booking submission and creates a pending booking order plus reserved
  canoe rows.

- `/payment-success`
  Finalizes a booking after the current simulated payment flow.

### API routes

- `/api/booking-count`
  Returns the number of bookings as JSON.

- `/api/forecast`
  Calls the MET Norway weather API and returns simplified forecast data.

### Authentication routes

- `/`
  Conditionally renders either the public password gate or the real homepage,
  depending on whether the visitor already unlocked the shared public session.
  The lock view reuses the same hero layout structure as the homepage so the
  title, subtitle, password field, and unlock button can transition into the
  real homepage with less visible layout shift. The lock view uses anonymized
  placeholders instead of real homepage details so the hidden layout geometry
  is preserved without exposing more content than necessary before unlock.

- `/unlock`
  Verifies the shared public-site password and stores one session flag when the
  password is correct.

- `/login`
  Handles admin login. It now only accepts local internal `next` redirect
  targets after login so the route cannot be used as an open redirect to an
  external site.

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

- the total number of booked canoes must not exceed `AVAILABLE_CANOES`.

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
- previous-years ribbon,
- booking modal,
- two-step booking flow with summary,
- participant overview modal,
- FAQ modal,
- contact modal,
- gallery modal,
- weather widget area.

Why this matters:

- It works, but the file is becoming large.
- As the project grows, it may become better to split pieces into smaller
  templates or partials.

### Frontend JavaScript

The public JavaScript is currently split like this:

- `static/js/booking_progress.js`
  Handles the booking count API calls and homepage booking progress bar.
- `static/js/weather.js`
  Handles the weather countdown and weather forecast updates.
- `static/js/modals.js`
  Handles the FAQ, contact, and participant overview popup behavior.
- `static/js/gallery.js`
  Handles the previous-years ribbon animation and gallery lightbox behavior.
- `static/js/booking.js`
  Handles the two-step booking modal, participant field generation, and
  booking summary updates.
- `static/js/main.js`
  Handles:
  - scroll animations,
  - the page initialization sequence.

Why this matters:

- The current approach is functional and simple to deploy.
- But the script is already doing many unrelated things, which increases future
  maintenance cost.

## Image Handling

Images are currently stored under `static/images/`, with two main roles:

1. `static/images/nitten.png` is the current homepage background image.
2. `static/images/previous_years/` contains the original previous-years images.
3. `static/images/previous_years/ribbon/` contains generated small WebP
   variants used by the homepage ribbon.
4. `static/images/previous_years/gallery/` contains generated medium WebP
   variants used by the gallery lightbox.

There is a helper function in `app/util/helper_functions.py` that:

1. reads the flattened `previous_years` source folder,
2. loads stable image metadata from `data/previous_year_images.json`,
3. returns stable image IDs plus the matching generated variant paths.

Why this was likely chosen:

- It is simple.
- It avoids needing a separate image storage system.
- It keeps the public ribbon lighter than the full gallery.
- It lets the homepage ribbon use lazy-loaded `<img>` elements instead of
  eagerly loaded CSS background images.
- It removes the old year-folder dependency from the gallery code.
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

The app registers several custom Flask CLI commands.

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

### `seed-test-bookings`

What it does:

- Removes any older seeded development bookings.
- Creates a chosen number of confirmed test bookings marked with
  `payment_provider = "dev_seed"`.

Why it exists:

- It gives a fast way to test the booking UI near capacity without manually
  creating many bookings in the browser.

### `clear-test-bookings`

What it does:

- Removes all development bookings marked with `payment_provider = "dev_seed"`.

Why it exists:

- It gives a clean reset for booking-UI testing without touching real bookings.

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
- But hosted Postgres behavior can differ from local SQLite.
- The roadmap therefore includes testing against Supabase as the first hosted
  database platform.

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

### Current design choice

The project now treats Alembic as the main schema path for real environments.

Practical note:

- The CLI reset helpers still use `drop_all()` and `create_all()` for quick
  local resets.
- Supabase and other shared environments should be managed through Alembic
  migrations instead of ad hoc table creation.

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

- Move toward Docker for the app plus Supabase as the first hosted database
  workflow to validate.
- Keep SQLAlchemy and Alembic as the default path for booking-critical data.

### Monitoring

Current state:

- Basic Python logging only.

Planned improvement:

- Add better structured logging, Sentry, uptime checks, and alerts.

### Cloud deployment

Current state:

- Early container support now exists through the root `Dockerfile`, but the
  full local Docker stack is not finished yet.

Planned improvement:

- Test a Cloud Run deployment with Supabase.

## What Someone New Should Understand First

If you are new to the project, focus on these ideas first:

1. The app is currently a single Flask backend that renders HTML pages and also
   serves some JSON endpoints.
2. The public site, booking flow, admin area, and simple APIs all live in the
   same Flask application.
3. The database currently stores booking orders, canoe participant rows, and
   admin users.
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
6. `static/js/booking_progress.js`
7. `static/js/weather.js`
8. `static/js/main.js`
9. `tests/`
10. `docs/roadmaps/backend_roadmap.md`
11. `docs/dev/dev_overview.md`
12. `docs/dev/dev_ngrok.md`

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
