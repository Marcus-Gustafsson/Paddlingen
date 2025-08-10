"""Flask application factory and extension initialization.

This module exposes a :func:`create_app` function that builds the
Flask application, loads configuration, initializes extensions, and
registers routes.  Tests and scripts should call this factory rather
than importing a global ``app`` object.
"""

from __future__ import annotations

from flask import Flask
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
    return flask_application


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
]
