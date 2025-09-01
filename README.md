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
   # Optional: use PostgreSQL instead of the default SQLite database
   # DATABASE_URL=postgresql+psycopg://paddlingen:password@localhost:5432/paddlingen
   ```

   `DATABASE_URL` controls which database is used. Leave it unset to store data in `instance/paddlingen.db` (SQLite). To develop against a local PostgreSQL server, set it to a connection string like the example above.

   ### PostgreSQL example

   1. **Create the database**

      ```bash
      createdb -U <your_postgres_user> paddlingen
      ```

   2. **Set the connection string** – add a `DATABASE_URL` to your `.env` file (replace the placeholders):

      ```
      DATABASE_URL=postgresql+psycopg://<username>:<password>@<host>:5432/paddlingen
      ```

      The `psycopg[binary]` driver is already declared in `pyproject.toml`; ensure it is installed via `uv sync` or `make install`.

   Tests continue to use an in-memory SQLite database via [`tests/conftest.py`](tests/conftest.py), so `pytest` runs without requiring PostgreSQL.

4. **Initialize the database**
   ```bash
   uv run python init_db.py
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

## Deployment

See [docs/deployment.md](docs/deployment.md) for deployment instructions.

## WSL

See [docs/wsl.md](docs/wsl.md) for WSL-specific development notes (mostly how to view website on phone).
