# Paddlingen

A small Flask application for managing canoe rentals. The app lets visitors book canoes and provides a simple admin interface to review and edit bookings.

## Prerequisites

- Python 3.10 or newer
- `git` for cloning the repository

## Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/paddlingen.git
   cd paddlingen
   ```

2. **Install dependencies**

   The project uses [uv](https://github.com/astral-sh/uv) for dependency management. It will create a `.venv` automatically.

   ```bash
   make install   # or: uv sync
   ```

   Legacy `pip` requirement files are available under `pip_files/` for reference.

3. **Configure environment variables**

   Create a `.env` file in the project root and add your secrets:

   ```
   SECRET_KEY=replace-me
   PAYMENT_API_KEY=replace-me
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=changeme
   FLASK_DEBUG=True
   SESSION_COOKIE_SECURE=False
   DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<database-password>@<host>:5432/postgres?sslmode=require
   # Optional later if you test Supabase API features
   SUPABASE_URL=https://<project-ref>.supabase.co
   SUPABASE_ANON_KEY=replace-me-if-needed-later
   SUPABASE_SERVICE_ROLE_KEY=replace-me-if-needed-later
   ```

   `DATABASE_URL` controls which database is used. Leave it unset to store data in `instance/paddlingen.db` (SQLite). To test the current app against Supabase, set it to the Supabase Postgres connection string.

   ### Supabase setup for the current implementation

   1. **Open your Supabase project dashboard**
      Go to your project and find the database connection details.

   2. **Choose the database connection method**
      For the current Flask app, use a normal Postgres connection string. If direct connection support is awkward in your environment, use the Supavisor session pooler connection string instead.

   3. **Set the connection string** – add a `DATABASE_URL` to your `.env` file (replace the placeholders):

      ```
      DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<database-password>@<host>:5432/postgres?sslmode=require
      ```

      The `psycopg[binary]` driver is already declared in `pyproject.toml`; ensure it is installed via `uv sync` or `make install`.

      Important note:

      Supabase often shows the URL in the generic form `postgresql://...`.
      For this project, change that prefix to `postgresql+psycopg://...` so
      SQLAlchemy uses the installed `psycopg` v3 driver instead of looking for
      `psycopg2`.

      If the direct host fails with an error showing an IPv6 address and
      `Network is unreachable`, switch to the Supavisor session pooler
      connection string from the Supabase dashboard. That usually works better
      from local WSL and home-network setups that do not have working IPv6
      connectivity.

   4. **Keep the API-style Supabase variables optional for now**
      `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` are only needed later if you decide to test Supabase API features such as Storage. They are not required for the current SQLAlchemy-based setup.

   Tests continue to use an in-memory SQLite database via [`tests/conftest.py`](tests/conftest.py), so `pytest` runs without requiring Supabase.

4. **Initialize the database**
   ```bash
   uv run python init_db.py
   ```
   This helper drops and recreates tables, then seeds the admin user. It is
   meant for fresh local setup or quick resets.

   If you already ran Alembic migrations against Supabase, seed the admin user
   without resetting the schema:
   ```bash
   uv run flask --app wsgi seed-admin
   ```

5. **Start the development server**
   ```bash
   uv run flask --app wsgi --debug run
   ```
   The application will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

6. **Run tests**
   ```bash
   make test   # or: uv run -m pytest
   ```

## Docker

If you want to run the app in Docker, there are now two simple choices.

### Option 1: Run one named container directly

```bash
docker build -t paddlingen-web .
docker run --rm --name paddlingen-web -p 8080:8080 --env-file .env paddlingen-web
```

What to expect:

- The app logs will appear in your terminal because this runs in attached mode.
- Docker Desktop will show the same logs because it reads the same container
  output.
- Press `Ctrl+C` to stop the container.

If you want your terminal back immediately, run it in the background:

```bash
docker run -d --rm --name paddlingen-web -p 8080:8080 --env-file .env paddlingen-web
docker logs -f paddlingen-web
docker stop paddlingen-web
```

### Option 2: Run through Docker Compose

```bash
docker compose up --build
```

Why this exists:

- The root `compose.yaml` gives the project a stable Docker Desktop grouping
  named `paddlingen`.
- This is useful even though there is only one service right now.
- Compose becomes more helpful later if the project adds more services.

Useful follow-up commands:

```bash
docker compose up --build -d
docker compose logs -f web
docker compose ps
docker compose down
```

## Database migrations

Paddlingen uses [Alembic](https://alembic.sqlalchemy.org/) to keep the database schema in sync with your models.

1. **Create a migration** – whenever you change a model, ask Alembic to generate a migration script:
   ```bash
   uv run alembic revision --autogenerate -m "describe your change"
   ```
   The command inspects the `db` models and stores a new migration file in `migrations/versions`.

2. **Apply migrations** – run pending migrations to update the database to the latest schema:
   ```bash
   uv run alembic upgrade head
   ```

3. **Roll back** – undo the last migration if something went wrong:
   ```bash
   uv run alembic downgrade -1
   ```
   Replace `-1` with a specific revision identifier to roll back to an exact point in history.

For more background see the [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## Project docs

- [docs/TechnicalOverview.md](docs/TechnicalOverview.md) explains how the app is currently built.
- [docs/Roadmap.md](docs/Roadmap.md) tracks the planned implementation steps.
- [docs/dev_doc.md](docs/dev_doc.md) is the practical development commands and workflow document.
