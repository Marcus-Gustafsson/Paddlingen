"""Flask application factory and extension initialization.

This module exposes a :func:`create_app` function that builds the
Flask application, loads configuration, initializes extensions, and
registers routes.  Tests and scripts should call this factory rather
than importing a global ``app`` object.
"""

from __future__ import annotations

from datetime import timedelta

from flask import Flask, current_app
from flask_wtf import CSRFProtect  # type: ignore[import-untyped]
from flask_login import LoginManager  # type: ignore[import-untyped]
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import click
import os

# Database models and session object
from .util.db_models import (
    BookedCanoe,
    BookingOrder,
    User,
    db,
    get_current_utc_time,
)

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
    flask_application.cli.add_command(seed_test_bookings_command)
    flask_application.cli.add_command(clear_test_bookings_command)

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


def clear_seed_test_bookings() -> int:
    """Delete all development seed bookings and return the deleted order count.

    Returns:
        int: Number of seeded booking orders removed.
    """

    seeded_booking_orders = BookingOrder.query.filter_by(
        payment_provider="dev_seed"
    ).all()
    deleted_order_count = len(seeded_booking_orders)

    for seeded_booking_order in seeded_booking_orders:
        db.session.delete(seeded_booking_order)

    db.session.commit()
    return deleted_order_count


@click.command("seed-test-bookings")
@click.option(
    "--count",
    default=1,
    type=click.IntRange(min=1),
    show_default=True,
    help="How many confirmed test canoes to create.",
)
def seed_test_bookings_command(count: int) -> None:
    """Create a repeatable set of confirmed development-only test bookings.

    The command first removes any older seeded test bookings marked with
    ``payment_provider='dev_seed'``. It then creates one paid order and one
    confirmed canoe row per requested test booking so the booking UI can be
    tested near capacity without creating manual bookings one by one.
    """

    deleted_order_count = clear_seed_test_bookings()
    if deleted_order_count:
        click.echo(f"Removed {deleted_order_count} old seeded booking order(s).")

    for booking_number in range(1, count + 1):
        booking_order = BookingOrder(
            public_booking_reference="TEMP",
            status="paid",
            canoe_count=1,
            total_amount_ore=current_app.config["CANOE_PRICE_SEK"] * 100,
            currency="sek",
            payment_provider="dev_seed",
            payer_full_name=f"Testbokning {booking_number:03d}",
            payer_email=f"testbokning{booking_number:03d}@example.invalid",
            paid_at=get_current_utc_time(),
            expires_at=get_current_utc_time() + timedelta(minutes=15),
        )
        db.session.add(booking_order)
        db.session.flush()

        booking_order.public_booking_reference = f"TEST-{booking_order.id:05d}"
        db.session.add(
            BookedCanoe(
                booking_order_id=booking_order.id,
                participant_first_name="Test",
                participant_last_name=f"Booking {booking_number:03d}",
                status="confirmed",
            )
        )

    db.session.commit()
    click.echo(f"Created {count} seeded test booking(s).")


@click.command("clear-test-bookings")
def clear_test_bookings_command() -> None:
    """Remove all development-only seeded bookings from the database."""

    deleted_order_count = clear_seed_test_bookings()
    click.echo(f"Removed {deleted_order_count} seeded test booking order(s).")


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
    "BookedCanoe",
    "BookingOrder",
    "User",
    "csrf_protect",
    "login_manager",
    "rate_limiter",
    "init_db_command",
    "seed_admin_command",
    "seed_test_bookings_command",
    "clear_test_bookings_command",
]
