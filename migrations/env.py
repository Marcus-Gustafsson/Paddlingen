"""Alembic environment file for Paddlingen.

This config uses the Flask application's SQLAlchemy metadata so that
`alembic revision --autogenerate` works out of the box.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context

# Add the application to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db  # noqa: E402

# Load the Flask application and push an application context.  This gives
# Alembic access to the SQLAlchemy metadata and database configuration.
app = create_app()
app.app_context().push()

# Alembic Config object, which provides access to the values within the
# alembic.ini file.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the SQLAlchemy URL from the Flask app's configuration.
config.set_main_option("sqlalchemy.url", str(app.config["SQLALCHEMY_DATABASE_URI"]))

# Set target metadata for 'autogenerate'.
target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = db.engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
