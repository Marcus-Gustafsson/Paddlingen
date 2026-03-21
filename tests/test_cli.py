"""Tests for custom Flask command line interface commands."""

from app import BookedCanoe, BookingOrder, Event, User, db
from werkzeug.security import check_password_hash


def test_init_db_command_resets_tables(client):
    """Invoke ``flask init-db`` and ensure tables are recreated.

    The application recreates the schema and also seeds the active event row
    from the current config defaults. The admin user table should be cleared.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.

    Returns:
        None: Assertions check that the database was cleared.

    """
    with client.application.app_context():
        assert User.query.count() == 1

    runner = client.application.test_cli_runner()
    with client.application.app_context():
        result = runner.invoke(args=["init-db"])
        assert "Initialized the database and seeded active event" in result.output
        assert User.query.count() == 0
        assert Event.query.filter_by(is_active=True).count() == 1


def test_seed_active_event_command_creates_or_updates_event(client):
    """Ensure ``seed-active-event`` creates a usable active event row."""

    runner = client.application.test_cli_runner()

    with client.application.app_context():
        Event.query.delete()
        db.session.commit()

        result = runner.invoke(args=["seed-active-event"])

        assert "Seeded active event" in result.output
        active_event = Event.query.filter_by(is_active=True).first()
        assert active_event is not None
        assert active_event.title == "Paddlingen"


def test_seed_admin_command_creates_user(client, monkeypatch):
    """Invoke ``flask seed-admin`` to add a new administrator.

    The command reads credentials from environment variables. The test sets
    these variables, runs the command and checks that a user with the given
    username now exists in the database.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.
        monkeypatch (pytest.MonkeyPatch): Utility to set environment variables.

    Returns:
        None: Assertions verify the creation of the admin user.

    """
    runner = client.application.test_cli_runner()
    monkeypatch.setenv("ADMIN_USERNAME", "cliadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")

    with client.application.app_context():
        result = runner.invoke(args=["seed-admin"])
        assert "Created admin 'cliadmin'." in result.output
        assert User.query.filter_by(username="cliadmin").first() is not None


def test_seed_admin_command_requires_env_vars(client, monkeypatch):
    """Ensure ``seed-admin`` fails when credentials are missing.

    If ``ADMIN_USERNAME`` or ``ADMIN_PASSWORD`` is absent the command should
    abort with an error message. This prevents accidental creation of accounts
    with empty credentials.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.
        monkeypatch (pytest.MonkeyPatch): Used to clear environment variables.

    Returns:
        None: Assertions confirm the command fails and prints a helpful message.

    """
    runner = client.application.test_cli_runner()
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    with client.application.app_context():
        result = runner.invoke(args=["seed-admin"])
        assert result.exit_code != 0
        assert (
            "ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required"
            in result.output
        )


def test_generate_public_site_password_hash_command_outputs_valid_hash(client):
    """Generate one shared public-site password hash from CLI input."""

    runner = client.application.test_cli_runner()

    result = runner.invoke(
        args=["generate-public-site-password-hash"],
        input="hemligt-losenord\nhemligt-losenord\n",
    )

    assert result.exit_code == 0
    generated_hash = result.output.strip().splitlines()[-1]
    assert generated_hash.startswith("scrypt:")
    assert check_password_hash(generated_hash, "hemligt-losenord")


def test_seed_test_bookings_command_creates_marked_bookings(client):
    """Create seeded development bookings and verify the marker fields.

    The command should create one paid order and one confirmed canoe row per
    requested booking. The orders must be marked with
    ``payment_provider='dev_seed'`` so they can be safely removed later.
    """

    runner = client.application.test_cli_runner()

    with client.application.app_context():
        result = runner.invoke(args=["seed-test-bookings", "--count", "3"])
        assert "Created 3 seeded test booking(s)." in result.output
        assert BookingOrder.query.filter_by(payment_provider="dev_seed").count() == 3
        assert BookedCanoe.query.filter_by(status="confirmed").count() == 3


def test_clear_test_bookings_command_removes_only_seeded_bookings(client):
    """Delete only seeded development bookings and leave real ones intact."""

    runner = client.application.test_cli_runner()

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        real_booking_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-2026-00001",
            status="paid",
            canoe_count=1,
            total_amount=1200.0,
            currency="sek",
            payment_provider="simulated",
        )
        db.session.add(real_booking_order)
        db.session.flush()
        db.session.add(
            BookedCanoe(
                booking_order_id=real_booking_order.id,
                participant_first_name="Real",
                participant_last_name="Booking",
                status="confirmed",
            )
        )
        db.session.commit()

        runner.invoke(args=["seed-test-bookings", "--count", "2"])
        result = runner.invoke(args=["clear-test-bookings"])

        assert "Removed 2 seeded test booking order(s)." in result.output
        assert BookingOrder.query.filter_by(payment_provider="dev_seed").count() == 0
        assert BookingOrder.query.filter_by(payment_provider="simulated").count() == 1
