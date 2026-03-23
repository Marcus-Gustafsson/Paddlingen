"""Tests for public-facing routes and booking flow."""

from app import db
from app.util.db_models import (
    BookedCanoe,
    BookingOrder,
    Event,
    PublicSiteAccessSetting,
)
from app.util.helper_functions import get_previous_year_image_metadata


def unlock_public_site(client):
    """Unlock the shared public-site gate for one test-client session."""

    return client.post(
        "/unlock",
        data={"password": "eventpass"},
        follow_redirects=True,
    )


def test_locked_home_page_shows_password_gate(client):
    """Show the public lock screen before the shared password is entered."""

    response = client.get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Öppna sidan" in page
    assert "Lösenord" in page
    assert "Välkommen" not in page
    assert "Boka kanot" not in page
    assert "Visa bilder från tidigare år" not in page


def test_home_page(client):
    """Send GET '/' and verify the unlocked public landing page responds."""

    unlock_public_site(client)
    response = client.get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Boka kanot" in page
    assert "Tryck för att se deltagare" in page
    assert "Visa bilder från tidigare år" in page
    assert "Steg 1 av 2" in page
    assert "Regler och vanliga frågor" in page
    assert "info@paddlingen.se" in page
    assert "Paddlingen" in page
    assert "20 mars 2026" in page
    assert "Visa bildinformation" in page
    assert "Bildinformation" in page
    assert "/previous-years-images/ribbon/" in page
    assert "/previous-years-images/gallery/" in page
    assert 'loading="lazy"' in page
    assert 'fetchpriority="low"' in page


def test_login_page(client):
    """Ensure the login route renders so users can start authentication."""
    unlock_public_site(client)
    response = client.get("/login")
    assert response.status_code == 200


def test_booking_over_limit_shows_error(client):
    """Request too many canoes and confirm an error message is shown.

    This test temporarily lowers ``AVAILABLE_CANOES`` to a very small number to
    simulate a fully booked day. It then posts a form asking for more canoes
    than are available. Flask should respond with a flash error on the home
    page and refuse to create any booking order records.
    """
    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.available_canoes = 1
        client.application.config["AVAILABLE_CANOES"] = 1
        client.application.config["CANOE_PRICE_SEK"] = 1200
        client.application.config["MAX_CANOES_PER_BOOKING"] = 5

        db.session.commit()

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={"canoeCount": "2"},
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert "Tyvärr, bara 1 kanot(er) kvar" in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0


def test_booking_over_per_booking_limit_shows_error(client):
    """Reject bookings larger than the configured per-order limit."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.available_canoes = 20
        client.application.config["AVAILABLE_CANOES"] = 20
        client.application.config["MAX_CANOES_PER_BOOKING"] = 5

        db.session.commit()

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={"canoeCount": "6"},
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert "Du kan boka högst 5 kanoter åt gången." in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0


def test_successful_booking_creates_records(client):
    """Complete a booking and verify database tables are updated.

    The test submits a valid booking for two canoes, then simulates the user
    returning from payment by calling ``/payment-success``. One order row and
    two confirmed :class:`BookedCanoe` rows should exist afterwards.
    """
    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.available_canoes = 3
        client.application.config["AVAILABLE_CANOES"] = 3

        db.session.commit()

    unlock_public_site(client)
    booking_data = {
        "canoeCount": "2",
        "canoe1_fname": "Alice",
        "canoe1_lname": "Andersson",
        "canoe2_fname": "Bob",
        "canoe2_lname": "Berg",
    }
    client.post("/create-checkout-session", data=booking_data)

    client.get("/payment-success")

    with client.application.app_context():
        names = [r.name for r in BookedCanoe.query.order_by(BookedCanoe.id)]
        assert "Alice Andersson" in names
        assert "Bob Berg" in names
        assert BookingOrder.query.count() == 1
        assert BookingOrder.query.first().status == "paid"
        assert BookingOrder.query.first().event_id is not None


def test_booking_rejects_participant_names_longer_than_twenty_characters(client):
    """Reject participant names that exceed the public booking length limit."""

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "A" * 21,
            "canoe1_lname": "Andersson",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Förnamnet för kanot 1 får vara högst 20 tecken." in response.get_data(
        as_text=True
    )

    with client.application.app_context():
        assert BookingOrder.query.count() == 0


def test_home_page_uses_database_event_values(client):
    """Render the homepage using values from the active event row."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.title = "Sjöfärden 2027"
        active_event.subtitle = "Databasstyrd undertitel"
        active_event.contact_email = "db@example.com"
        active_event.available_canoes = 77
        active_event.price_per_canoe_sek = 1500
        active_event.max_canoes_per_booking = 4
        active_event.weather_forecast_days_before_event = 5

        db.session.commit()

    unlock_public_site(client)
    response = client.get("/")
    page = response.get_data(as_text=True)
    assert "Sjöfärden 2027" in page
    assert "Databasstyrd undertitel" in page
    assert "db@example.com" in page
    assert "0 / 77 kanoter bokade" in page
    assert "1500 kr" in page


def test_home_page_keeps_subtitle_blank_when_event_subtitle_is_empty(client):
    """Do not fall back to config.py when the active event subtitle is blank."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.subtitle = ""
        db.session.commit()

    unlock_public_site(client)
    response = client.get("/")
    page = response.get_data(as_text=True)
    assert "Bästa dagen på hela året!" not in page
    assert 'class="main-subtitle no-select"' not in page


def test_previous_year_image_metadata_has_stable_ids(client):
    """Return image metadata entries with stable IDs and matching filenames."""

    with client.application.app_context():
        image_metadata = get_previous_year_image_metadata()

    assert image_metadata
    assert all(
        metadata_entry["id"].startswith("IMG-") for metadata_entry in image_metadata
    )
    assert len({metadata_entry["id"] for metadata_entry in image_metadata}) == len(
        image_metadata
    )
    assert all(metadata_entry["filename"] for metadata_entry in image_metadata)


def test_locked_previous_year_image_returns_forbidden(client):
    """Block direct image fetches until the shared public password is unlocked."""

    with client.application.app_context():
        image_metadata = get_previous_year_image_metadata()

    image_id = image_metadata[0]["id"]
    response = client.get(f"/previous-years-images/ribbon/{image_id}.webp")
    assert response.status_code == 403


def test_locked_legacy_static_previous_year_image_returns_forbidden(client):
    """Block the old static ribbon/gallery paths before the site is unlocked."""

    with client.application.app_context():
        image_metadata = get_previous_year_image_metadata()

    image_id = image_metadata[0]["id"]
    response = client.get(f"/static/images/previous_years/ribbon/{image_id}.webp")
    assert response.status_code == 403


def test_unlocked_previous_year_image_is_served(client):
    """Allow protected ribbon/gallery images after the shared gate is unlocked."""

    with client.application.app_context():
        image_metadata = get_previous_year_image_metadata()

    unlock_public_site(client)
    image_id = image_metadata[0]["id"]
    response = client.get(f"/previous-years-images/gallery/{image_id}.webp")
    assert response.status_code == 200
    assert response.mimetype == "image/webp"


def test_invalid_form_data_returns_flash_error(client):
    """Submit empty form data and expect an error without database changes.

    The payment route needs a ``canoeCount`` field. This test posts an empty
    form to ``/create-checkout-session`` to simulate a broken or tampered
    submission. Flask should flash an "Ogiltigt antal kanoter." message and
    redirect back to the home page. No booking rows are added.

    Args:
        client (FlaskClient): Test client used to simulate browser requests.

    Returns:
        None: This test relies on assertions instead of returning a value.

    """
    unlock_public_site(client)
    response = client.post("/create-checkout-session", data={}, follow_redirects=True)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Ogiltigt antal kanoter." in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0


def test_unlock_rejects_wrong_public_password(client):
    """Keep the homepage locked when the shared password is wrong."""

    response = client.post(
        "/unlock",
        data={"password": "wrong-password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Fel lösenord. Försök igen." in page
    assert "Öppna sidan" in page
    assert "Boka kanot" not in page


def test_unlock_rate_limit_exceeded(client):
    """Block repeated shared-password attempts from the same IP address."""

    test_ip = "203.0.113.44"
    for _ in range(5):
        response = client.post(
            "/unlock",
            data={"password": "wrong-password"},
            environ_overrides={"REMOTE_ADDR": test_ip},
            follow_redirects=False,
        )
        assert response.status_code == 302

    limited_response = client.post(
        "/unlock",
        data={"password": "wrong-password"},
        environ_overrides={"REMOTE_ADDR": test_ip},
        follow_redirects=False,
    )
    assert limited_response.status_code == 429


def test_public_site_gate_falls_back_when_access_settings_table_is_missing(client):
    """Keep the public gate working if the new settings table is not migrated yet."""

    with client.application.app_context():
        PublicSiteAccessSetting.__table__.drop(db.engine)

    response = client.get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Öppna sidan" in page
    assert "Boka kanot" not in page
