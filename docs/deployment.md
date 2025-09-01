# Deployment

## Preparing PostgreSQL on PythonAnywhere
1. Log into PythonAnywhere and open the **Databases** tab.
2. Create a new PostgreSQL database and user.
3. Note the connection string. It follows the pattern:
   `postgresql+psycopg://<user>:<password>@<user>-<id>.postgres.pythonanywhere-services.com/<user>$<dbname>`

## Setting environment variables
Configure the application by setting environment variables on the host:

```
export DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>/<user>$<dbname>
export SECRET_KEY=your-secret
export PAYMENT_API_KEY=your-payment-key
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=changeme
export FLASK_DEBUG=False
export SESSION_COOKIE_SECURE=True
```

## Installing dependencies
Install locked production dependencies using [uv](https://github.com/astral-sh/uv):

```bash
uv sync --frozen --no-dev
```



## Running database migrations
From a PythonAnywhere console, run migrations to bring the database up to date:

```
cd /path/to/app
uv run alembic upgrade head
```

## Starting the app
Start the application using the WSGI entrypoint:

```
uv run python wsgi.py
```

or with Gunicorn:

```
uv run gunicorn wsgi:application
```
