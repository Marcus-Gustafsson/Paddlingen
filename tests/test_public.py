"""Tests for public-facing routes and booking flow."""

from app.util.db_models import BookedCanoe, BookingOrder


def test_home_page(client):
    """Send GET '/' and verify the public landing page responds with 200."""
    response = client.get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Boka kanot" in page
    assert "Tryck för att se deltagare" in page
    assert "Visa bilder från tidigare år" in page
    assert "Steg 1 av 2" in page
    assert "Regler och vanliga frågor" in page
    assert "info@paddlingen.se" in page


def test_login_page(client):
    """Ensure the login route renders so users can start authentication."""
    response = client.get("/login")
    assert response.status_code == 200


def test_booking_over_limit_shows_error(client):
    """Request too many canoes and confirm an error message is shown.

    This test temporarily lowers ``AVAILABLE_CANOES`` to a very small number to
    simulate a fully booked day. It then posts a form asking for more canoes
    than are available. Flask should respond with a flash error on the home
    page and refuse to create any booking order records.
    """
    client.application.config["AVAILABLE_CANOES"] = 1

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

    client.application.config["AVAILABLE_CANOES"] = 20
    client.application.config["MAX_CANOES_PER_BOOKING"] = 5

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
    client.application.config["AVAILABLE_CANOES"] = 3

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
    response = client.post("/create-checkout-session", data={}, follow_redirects=True)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Ogiltigt antal kanoter." in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
