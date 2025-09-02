"""Flask application factory and extension initialization.

This module exposes a :func:`create_app` function that builds the
Flask application, loads configuration, initializes extensions, and
registers routes.  Tests and scripts should call this factory rather
than importing a global ``app`` object.
"""

from __future__ import annotations

from flask import Flask
from flask_wtf import CSRFProtect  # type: ignore[import-untyped]
from flask_login import LoginManager  # type: ignore[import-untyped]
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import click
import os

# Database models and session object
from .util.db_models import db, RentForm, PendingBooking, User

# Flask extension instances -------------------------------------------------
csrf_protect = CSRFProtect()
login_manager = LoginManager()
rate_limiter = Limiter(key_func=get_remote_address)


def create_app() -> Flask:
    """Create and configure a :class:`~flask.Flask` application instance.

        The factory pattern keeps application creation explicit and makes
    testing very easy.  Every caller gets a brand new app configured with
    our extensions and routes.

        Returns:
            Flask: A fully configured Flask application.
    """

    flask_application = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates",
    )

    # Load configuration values from the repository's ``config.py`` module.
    flask_application.config.from_object("config")

    # Initialize extensions with this specific app instance.
    db.init_app(flask_application)
    csrf_protect.init_app(flask_application)
    login_manager.init_app(flask_application)
    login_manager.login_view = "main.login"
    rate_limiter.init_app(flask_application)

    # Create database tables if they do not yet exist.
    with flask_application.app_context():
        db.create_all()

    # Import and register blueprints containing route definitions.
    from .routes import main_blueprint

    flask_application.register_blueprint(main_blueprint)

    # ------------------------------------------------------------------
    # Register custom ``flask`` command line interface (CLI) commands.
    # These commands allow developers to easily re-initialize the
    # database and seed an administrator account without writing
    # additional scripts.  See the docstrings of the command functions
    # below for detailed usage instructions.
    # ------------------------------------------------------------------
    flask_application.cli.add_command(init_db_command)
    flask_application.cli.add_command(seed_admin_command)

    return flask_application


@click.command("init-db")
def init_db_command() -> None:
    """Drop all database tables and create fresh ones.

    Running ``flask init-db`` from the command line clears out any
    existing tables and recreates them.  This is intended for
    development or testing environments where it's safe to lose data.
    """

    # ``drop_all`` removes tables if they exist; ``create_all`` then
    # builds the schema from the SQLAlchemy models.
    db.drop_all()
    db.create_all()
    click.echo("Initialized the database.")


@click.command("seed-admin")
def seed_admin_command() -> None:
    """Create the initial administrator user.

    The account credentials are read from the ``ADMIN_USERNAME`` and
    ``ADMIN_PASSWORD`` environment variables.  If either variable is
    missing the command aborts with a helpful error message.  Running
    ``flask seed-admin`` multiple times is safe; it will not create
    duplicate admin accounts.
    """

    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        raise click.ClickException(
            "ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required"
        )

    if User.query.filter_by(username=username).first():
        click.echo(f"Admin '{username}' already exists.")
        return

    admin_user = User(username=username)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()
    click.echo(f"Created admin '{username}'.")


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Return the :class:`User` instance for the given ``user_id``.

    Flask-Login uses this callback to reload the logged-in user from the
    session.  ``db.session.get`` is the SQLAlchemy 2.0 style for primary
    key lookups.
    """

    return db.session.get(User, int(user_id))


__all__ = [
    "create_app",
    "db",
    "RentForm",
    "PendingBooking",
    "User",
    "csrf_protect",
    "login_manager",
    "rate_limiter",
    "init_db_command",
    "seed_admin_command",
]
