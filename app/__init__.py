"""Flask application factory and extension initialization.

This module exposes a :func:`create_app` function that builds the
Flask application, loads configuration, initializes extensions, and
registers routes.  Tests and scripts should call this factory rather
than importing a global ``app`` object.
"""

from __future__ import annotations

from datetime import timedelta
import secrets

from flask import Flask
from flask_wtf import CSRFProtect  # type: ignore[import-untyped]
from flask_login import LoginManager  # type: ignore[import-untyped]
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import click
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash

# Database models and session object
from .util.db_models import (
    BookedCanoe,
    BookingOrder,
    Event,
    EventWeatherCache,
    PublicSiteAccessSetting,
    User,
    db,
    get_current_utc_time,
)
from .util.event_settings import create_or_update_active_event_from_config

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

    if flask_application.config.get("TRUST_REVERSE_PROXY_HEADERS"):
        flask_application.wsgi_app = ProxyFix(  # type: ignore[assignment]
            flask_application.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
        )

    # Initialize extensions with this specific app instance.
    db.init_app(flask_application)
    csrf_protect.init_app(flask_application)
    login_manager.init_app(flask_application)
    login_manager.login_view = "main.login"
    login_manager.login_message = "Du måste logga in för att öppna den här sidan."
    login_manager.login_message_category = "error"
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
    flask_application.cli.add_command(seed_active_event_command)
    flask_application.cli.add_command(seed_admin_command)
    flask_application.cli.add_command(add_admin_user_command)
    flask_application.cli.add_command(generate_public_site_password_hash_command)
    flask_application.cli.add_command(reset_public_site_password_command)
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
    active_event, backfilled_booking_count = create_or_update_active_event_from_config()
    db.session.commit()
    click.echo(
        "Initialized the database and seeded active event "
        f"'{active_event.title}'. Backfilled {backfilled_booking_count} booking(s)."
    )


@click.command("seed-active-event")
def seed_active_event_command() -> None:
    """Create or refresh the active event row from ``config.py`` defaults."""

    active_event, backfilled_booking_count = create_or_update_active_event_from_config()
    db.session.commit()
    click.echo(
        "Seeded active event "
        f"'{active_event.title}' for {active_event.event_date.year}. "
        f"Backfilled {backfilled_booking_count} booking(s)."
    )


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

    create_admin_user(username=username, password=password)
    click.echo(f"Created admin '{username}'.")


def create_admin_user(username: str, password: str) -> User:
    """Create and store one admin user with a hashed password."""

    admin_user = User(username=username)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()
    return admin_user


@click.command("add-admin-user")
@click.option(
    "--username",
    prompt="New admin username",
    help="Username for the new admin account.",
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Password for the new admin account.",
)
def add_admin_user_command(username: str, password: str) -> None:
    """Create one additional admin user through interactive prompts."""

    normalized_username = username.strip()
    if not normalized_username:
        raise click.ClickException("Admin username cannot be empty.")

    if User.query.filter_by(username=normalized_username).first():
        raise click.ClickException(f"Admin '{normalized_username}' already exists.")

    create_admin_user(username=normalized_username, password=password)
    click.echo(f"Created admin '{normalized_username}'.")


@click.command("generate-public-site-password-hash")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Shared public-site password that should be converted into a hash.",
)
def generate_public_site_password_hash_command(password: str) -> None:
    """Generate a password hash for the shared public-site access gate."""

    click.echo(generate_password_hash(password))


def generate_random_public_site_password(length: int = 20) -> str:
    """Return a strong random password for the shared public-site gate.

    The character set avoids the most visually ambiguous characters so the
    printed password is easier to read and share safely with event staff.
    """

    alphabet = (
        "ABCDEFGHJKLMNPQRSTUVWXYZ" "abcdefghijkmnopqrstuvwxyz" "23456789" "!@$%*+-_=?"
    )
    return "".join(secrets.choice(alphabet) for _ in range(length))


@click.command("reset-public-site-password")
@click.option(
    "--password",
    help=(
        "Specific shared public-site password to store. "
        "If omitted, the command generates one automatically."
    ),
)
@click.option(
    "--length",
    default=20,
    type=click.IntRange(min=12, max=128),
    show_default=True,
    help="Length for the generated password when --password is omitted.",
)
def reset_public_site_password_command(password: str | None, length: int) -> None:
    """Store a new shared public-site password hash in the database.

    This command is the recovery path when the shared public-site password was
    rotated and later forgotten, which can otherwise block access to both the
    public page and the admin area.
    """

    new_password = password or generate_random_public_site_password(length)

    PublicSiteAccessSetting.__table__.create(bind=db.engine, checkfirst=True)
    password_setting = PublicSiteAccessSetting.query.order_by(
        PublicSiteAccessSetting.id.asc()
    ).first()

    if password_setting is None:
        password_setting = PublicSiteAccessSetting(
            password_hash=generate_password_hash(new_password)
        )
        db.session.add(password_setting)
    else:
        password_setting.password_hash = generate_password_hash(new_password)

    db.session.commit()
    click.echo("Saved a new shared public-site password in the database.")
    click.echo(
        "Store this password safely. The admin page cannot show it later "
        "because only the hash is stored."
    )
    click.echo(f"New password: {new_password}")


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

    active_event, _ = create_or_update_active_event_from_config()

    for booking_number in range(1, count + 1):
        booking_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="TEMP",
            status="paid",
            canoe_count=1,
            total_amount=float(active_event.price_per_canoe_sek),
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
    "Event",
    "EventWeatherCache",
    "User",
    "csrf_protect",
    "login_manager",
    "rate_limiter",
    "init_db_command",
    "seed_active_event_command",
    "seed_admin_command",
    "generate_public_site_password_hash_command",
    "seed_test_bookings_command",
    "clear_test_bookings_command",
]
