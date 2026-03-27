"""Tests for public-facing routes and booking flow."""

from datetime import timedelta
from types import SimpleNamespace

import stripe

from app import db
from app.util.db_models import (
    BookedCanoe,
    BookingOrder,
    Event,
    PublicSiteAccessSetting,
    get_current_utc_time,
)
from app.util.helper_functions import get_previous_year_image_metadata


def unlock_public_site(client):
    """Unlock the shared public-site gate for one test-client session."""

    return client.post(
        "/unlock",
        data={"password": "eventpass"},
        follow_redirects=True,
    )


def build_stripe_success_return_path(client) -> str:
    """Return the success URL that Stripe would redirect back to in tests."""

    with client.application.app_context():
        booking_order = BookingOrder.query.order_by(BookingOrder.id.desc()).first()
        assert booking_order is not None
        assert booking_order.payment_provider_session_id is not None
        return (
            "/payment-success"
            f"?order_ref={booking_order.public_booking_reference}"
            f"&session_id={booking_order.payment_provider_session_id}"
        )


def build_stripe_cancel_return_path(client) -> str:
    """Return the cancel URL that Stripe would redirect back to in tests."""

    with client.application.app_context():
        booking_order = BookingOrder.query.order_by(BookingOrder.id.desc()).first()
        assert booking_order is not None
        return f"/payment-cancel?order_ref={booking_order.public_booking_reference}"


def build_stripe_pay_path(client) -> str:
    """Return the local route that redirects from modal Step 3 to Stripe."""

    with client.application.app_context():
        booking_order = BookingOrder.query.order_by(BookingOrder.id.desc()).first()
        assert booking_order is not None
        return f"/checkout/{booking_order.public_booking_reference}/pay"


def build_stripe_payment_status_path(client) -> str:
    """Return the polling path used by the payment return page."""

    with client.application.app_context():
        booking_order = BookingOrder.query.order_by(BookingOrder.id.desc()).first()
        assert booking_order is not None
        assert booking_order.payment_provider_session_id is not None
        return (
            "/api/checkout-status"
            f"?order_ref={booking_order.public_booking_reference}"
            f"&session_id={booking_order.payment_provider_session_id}"
        )


def mark_latest_pending_booking_as_paid_for_test(client) -> None:
    """Simulate the later webhook confirmation for tests that need paid rows."""

    with client.application.app_context():
        booking_order = BookingOrder.query.order_by(BookingOrder.id.desc()).first()
        assert booking_order is not None
        booking_order.status = "paid"
        if not booking_order.payer_email:
            booking_order.payer_email = "testbetalning@example.com"
        for booked_canoe in booking_order.booked_canoes:
            booked_canoe.status = "confirmed"
        db.session.commit()


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
    assert "Tryck för att visa deltagare" in page
    assert "Visa bilder från tidigare år" in page
    assert "Steg 1 av 3" in page
    assert "Regler och vanliga frågor" in page
    assert "info@paddlingen.se" in page
    assert "Paddlingen" in page
    assert "20 mars 2026" in page
    assert 'id="heroCalendarAction"' in page
    assert "/event.ics" in page
    assert 'download="paddlingen-event.ics"' in page
    assert "Samlingsplats:" in page
    assert "Havsjömossen" in page
    assert "Visa bildinformation" in page
    assert "Bildinformation" in page
    assert "/previous-years-images/ribbon/" in page
    assert "/previous-years-images/gallery/" in page
    assert 'loading="lazy"' in page
    assert 'fetchpriority="low"' in page


def test_event_calendar_route_returns_ical_file(client):
    """Return one downloadable iCalendar file for the current event."""

    unlock_public_site(client)
    response = client.get("/event.ics")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/calendar")
    assert (
        response.headers["Content-Disposition"]
        == 'attachment; filename="paddlingen-event.ics"'
    )

    calendar_file = response.get_data(as_text=True)
    assert "BEGIN:VCALENDAR" in calendar_file
    assert "BEGIN:VEVENT" in calendar_file
    assert "SUMMARY:Paddlingen" in calendar_file
    assert "LOCATION:Havsjömossen" in calendar_file
    assert "URL:https://www.google.com/maps/dir/" in calendar_file
    assert "Bokningsreferens" not in calendar_file


def test_home_page_ignores_expired_holds_without_stripe_lookup(client, monkeypatch):
    """Render the homepage count from local data without Stripe cleanup calls."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        assert active_event is not None
        active_event.available_canoes = 5

        confirmed_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-2026-90001",
            status="paid",
            canoe_count=1,
            total_amount=1200,
            payment_provider="stripe_checkout",
        )
        confirmed_order.booked_canoes.append(
            BookedCanoe(
                participant_first_name="Alice",
                participant_last_name="Andersson",
                status="confirmed",
            )
        )

        expired_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-2026-90002",
            status="checkout_session_created",
            canoe_count=1,
            total_amount=1200,
            payment_provider="stripe_checkout",
            payment_provider_session_id="cs_test_home_expired",
            expires_at=get_current_utc_time() - timedelta(minutes=1),
        )
        expired_order.booked_canoes.append(
            BookedCanoe(
                participant_first_name="Bob",
                participant_last_name="Berg",
                status="reserved",
            )
        )

        db.session.add_all([confirmed_order, expired_order])
        db.session.commit()

    def fail_if_stripe_lookup_runs(*_args, **_kwargs):
        raise AssertionError("Homepage availability should not call Stripe.")

    monkeypatch.setattr(
        "app.routes.retrieve_stripe_checkout_session",
        fail_if_stripe_lookup_runs,
    )

    unlock_public_site(client)
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "1 / 5 kanoter bokade" in page
    assert 'id="progressBar"' in page
    assert "width: 20.0%" in page
    assert "background-color: hsl(96.00, 100%, 50%)" in page


def test_login_page(client):
    """Ensure the login route renders so users can start authentication."""
    unlock_public_site(client)
    response = client.get("/login")
    assert response.status_code == 200


def test_booking_count_api_ignores_expired_holds_without_stripe_lookup(
    client, monkeypatch
):
    """Return live availability counts without reconciling old Stripe sessions."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        assert active_event is not None
        active_event.available_canoes = 5

        confirmed_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-2026-90003",
            status="paid",
            canoe_count=1,
            total_amount=1200,
            payment_provider="stripe_checkout",
        )
        confirmed_order.booked_canoes.append(
            BookedCanoe(
                participant_first_name="Cecilia",
                participant_last_name="Carlsson",
                status="confirmed",
            )
        )

        expired_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-2026-90004",
            status="checkout_session_created",
            canoe_count=1,
            total_amount=1200,
            payment_provider="stripe_checkout",
            payment_provider_session_id="cs_test_api_expired",
            expires_at=get_current_utc_time() - timedelta(minutes=1),
        )
        expired_order.booked_canoes.append(
            BookedCanoe(
                participant_first_name="David",
                participant_last_name="Dahl",
                status="reserved",
            )
        )

        db.session.add_all([confirmed_order, expired_order])
        db.session.commit()

    def fail_if_stripe_lookup_runs(*_args, **_kwargs):
        raise AssertionError("Booking count API should not call Stripe.")

    monkeypatch.setattr(
        "app.routes.retrieve_stripe_checkout_session",
        fail_if_stripe_lookup_runs,
    )

    unlock_public_site(client)
    response = client.get("/api/booking-count")

    assert response.status_code == 200
    assert response.get_json() == {"count": 1}


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


def test_booking_counts_active_pending_reservations_against_availability(client):
    """Reload home when a stale tab tries to reserve the last remaining canoe."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.available_canoes = 1
        db.session.commit()

    unlock_public_site(client)
    first_response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Bob",
            "canoe1_lname": "Berg",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert second_response.status_code == 409
    assert second_response.get_json() == {
        "ok": False,
        "message": (
            "Tyvärr, alla kanoter hann bli reserverade innan din reservation "
            "sparades. Sidan har uppdaterats så att du ser det senaste läget."
        ),
        "redirect_url": "/",
        "reload_page": True,
    }

    home_response = client.get("/", follow_redirects=True)
    home_page = home_response.get_data(as_text=True)
    assert (
        "Tyvärr, alla kanoter hann bli reserverade innan din reservation sparades."
        in home_page
    )
    assert "1 / 1 kanoter bokade" in home_page

    with client.application.app_context():
        assert BookingOrder.query.count() == 1
        assert BookedCanoe.query.count() == 1


def test_successful_booking_returns_pending_booking_data_for_modal_step_three(client):
    """Create a booking through XHR and return the Step 3 reservation payload."""
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
    response = client.post(
        "/create-checkout-session",
        data=booking_data,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["ok"] is True
    assert payload["pending_booking"]["open_on_load"] is True
    assert payload["pending_booking"]["canoe_count"] == 2
    assert payload["pending_booking"]["formatted_total_amount"] == "2 400 kr"
    assert payload["pending_booking"]["canoe_summaries"] == [
        {"canoe_number": 1, "participant_names": ["Alice Andersson"]},
        {"canoe_number": 2, "participant_names": ["Bob Berg"]},
    ]
    assert payload["pending_booking"]["pay_now_url"].endswith("/pay")
    assert payload["pending_booking"]["cancel_order_url"].endswith("/cancel")

    with client.application.app_context():
        names = [r.name for r in BookedCanoe.query.order_by(BookedCanoe.id)]
        assert "Alice Andersson" in names
        assert "Bob Berg" in names
        assert BookingOrder.query.count() == 1
        assert BookingOrder.query.first().status == "checkout_session_created"
        assert BookingOrder.query.first().event_id is not None
        assert BookingOrder.query.first().payment_provider == "stripe_checkout"
        assert BookingOrder.query.first().payment_provider_session_id is not None
        assert [
            canoe.status for canoe in BookedCanoe.query.order_by(BookedCanoe.id)
        ] == [
            "reserved",
            "reserved",
        ]


def test_review_page_can_redirect_into_real_stripe_checkout(client):
    """Use the Step 3 payment action to redirect into Stripe."""

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 200

    response = client.get(build_stripe_pay_path(client))

    assert response.status_code == 302
    assert "checkout.stripe.test" in response.headers["Location"]


def test_success_return_page_shows_processing_state_until_webhook(client):
    """Keep the visitor on a local processing state until the booking is paid."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response = client.get(build_stripe_success_return_path(client))

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Slutför din bokning" in page
    assert "Din betalning verifieras" not in page
    assert "js/payment_return.js" in page
    assert "payment-confirmation-badge" not in page
    assert "api/checkout-status" in page
    assert "css/stripe.css" in page

    with client.application.app_context():
        assert BookingOrder.query.first().status == "checkout_session_created"


def test_success_return_page_shows_confirmed_state_after_webhook(client):
    """Show a confirmed message and booking summary when the local booking is paid."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
            "canoe1_passenger2_fname": "Bob",
            "canoe1_passenger2_lname": "Berg",
            "canoe1_passenger3_fname": "Carin",
            "canoe1_passenger3_lname": "Carlsson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    mark_latest_pending_booking_as_paid_for_test(client)

    response = client.get(build_stripe_success_return_path(client))

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Din bokning är nu slutförd" in page
    assert "Orderbekräftelse skickas till testbetalning@example.com" in page
    assert "Bokningsöversikt" in page
    assert "Bokningsreferens" in page
    assert "Antal kanoter" in page
    assert "Totalt" in page
    assert "Kanotöversikt:" in page
    assert "Kanot 1" in page
    assert "Alice Andersson" in page
    assert "Bob Berg" in page
    assert "Carin Carlsson" in page
    assert (
        "Tack! Betalningen är bekräftad och din bokning är nu registrerad." not in page
    )
    assert "Betalningsretur" not in page
    assert "Tillbaka till hemsidan" in page
    assert "payment-confirmation-badge" in page
    assert "js/payment_return.js" not in page
    assert "Din betalning verifieras" not in page


def test_checkout_status_api_reports_pending_and_paid_states(client):
    """Return the local checkout status used by the post-Stripe polling page."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    pending_response = client.get(build_stripe_payment_status_path(client))
    assert pending_response.status_code == 200
    assert pending_response.get_json() == {"ok": True, "booking_status": "pending"}

    mark_latest_pending_booking_as_paid_for_test(client)

    paid_response = client.get(build_stripe_payment_status_path(client))
    assert paid_response.status_code == 200
    assert paid_response.get_json() == {"ok": True, "booking_status": "paid"}


def test_checkout_status_api_redirects_home_when_local_hold_has_expired(client):
    """Return a home redirect payload when the local Stripe hold has expired."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        booking_order.expires_at = get_current_utc_time() - timedelta(minutes=1)
        db.session.commit()

    expired_response = client.get(build_stripe_payment_status_path(client))

    assert expired_response.status_code == 200
    assert expired_response.get_json() == {
        "ok": True,
        "booking_status": "expired",
        "message": (
            "Reservationstiden gick ut medan betalningen var öppen. "
            "Gör en ny bokning om du vill fortsätta."
        ),
        "redirect_url": "/",
        "reload_page": True,
    }

    home_response = client.get("/", follow_redirects=True)
    home_page = home_response.get_data(as_text=True)
    assert "Reservationstiden gick ut medan betalningen var öppen." in home_page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
        assert BookedCanoe.query.count() == 0


def test_checkout_status_api_releases_unpaid_booking_after_confirmation_timeout(client):
    """Release the unpaid reservation immediately when the return page gives up waiting."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    response = client.get(
        build_stripe_payment_status_path(client) + "&finalize_failed=1"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "ok": True,
        "booking_status": "canceled",
        "heading": "Reservationen avbröts",
        "message": "Din reservation kunde inte slutföras automatiskt och har nu avbrutits.",
        "status_note": (
            "Kanoterna är inte längre reserverade för den här ordern. "
            "Gör en ny bokning från startsidan om du fortfarande vill boka en kanot."
        ),
    }

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
        assert BookedCanoe.query.count() == 0


def test_checkout_status_api_confirms_paid_booking_when_stripe_already_marks_payment_paid(
    client, monkeypatch
):
    """Confirm the booking locally when Stripe already says the session is paid."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        checkout_session_id = booking_order.payment_provider_session_id
        assert checkout_session_id is not None
        public_booking_reference = booking_order.public_booking_reference
        booking_order_id = booking_order.id

    from app import routes

    monkeypatch.setattr(
        routes,
        "retrieve_stripe_checkout_session",
        lambda checkout_session_id: SimpleNamespace(
            id=checkout_session_id,
            payment_status="paid",
            status="complete",
            metadata={
                "booking_order_id": str(booking_order_id),
                "public_booking_reference": public_booking_reference,
            },
            customer_details={
                "email": "alice@example.com",
                "name": "Alice Andersson",
            },
        ),
    )

    response = client.get(
        build_stripe_payment_status_path(client) + "&finalize_failed=1"
    )

    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "booking_status": "paid"}

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        assert booking_order.status == "paid"
        assert booking_order.payer_email == "alice@example.com"
        assert BookedCanoe.query.one().status == "confirmed"


def test_payment_success_confirms_paid_booking_directly_from_stripe_when_webhook_is_missing(
    client, monkeypatch
):
    """Render the final confirmation page when Stripe already shows the session as paid."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        checkout_session_id = booking_order.payment_provider_session_id
        assert checkout_session_id is not None
        public_booking_reference = booking_order.public_booking_reference
        booking_order_id = booking_order.id

    from app import routes

    monkeypatch.setattr(
        routes,
        "retrieve_stripe_checkout_session",
        lambda checkout_session_id: SimpleNamespace(
            id=checkout_session_id,
            payment_status="paid",
            status="complete",
            metadata={
                "booking_order_id": str(booking_order_id),
                "public_booking_reference": public_booking_reference,
            },
            customer_details={
                "email": "alice@example.com",
                "name": "Alice Andersson",
            },
        ),
    )

    response = client.get(build_stripe_success_return_path(client))

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Din bokning är nu slutförd" in page
    assert "Orderbekräftelse skickas till alice@example.com" in page
    assert "js/payment_return.js" not in page

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        assert booking_order.status == "paid"
        assert booking_order.payer_email == "alice@example.com"
        assert BookedCanoe.query.one().status == "confirmed"


def test_successful_booking_stores_optional_rider_names(client):
    """Store rider-two and rider-three names on the booked canoe row."""

    unlock_public_site(client)
    booking_data = {
        "canoeCount": "1",
        "canoe1_fname": "Marcus",
        "canoe1_lname": "Gustafsson",
        "canoe1_passenger2_fname": "Mathias",
        "canoe1_passenger2_lname": "Axelsson",
        "canoe1_passenger3_fname": "Tom",
        "canoe1_passenger3_lname": "Lundberg",
    }

    client.post(
        "/create-checkout-session",
        data=booking_data,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booked_canoe = BookedCanoe.query.one()
        assert booked_canoe.pickup_person_name == "Marcus Gustafsson"
        assert booked_canoe.passenger_two_first_name == "Mathias"
        assert booked_canoe.passenger_two_last_name == "Axelsson"
        assert booked_canoe.passenger_three_first_name == "Tom"
        assert booked_canoe.passenger_three_last_name == "Lundberg"


def test_home_page_pending_booking_step_three_lists_all_names_per_canoe(client):
    """Render all entered rider names in the Step 3 canoe overview."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Marcus",
            "canoe1_lname": "Gustafsson",
            "canoe1_passenger2_fname": "Mathias",
            "canoe1_passenger2_lname": "Axelsson",
            "canoe1_passenger3_fname": "Tom",
            "canoe1_passenger3_lname": "Lundberg",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    response = client.get("/?pending_checkout=1")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Kanot 1" in page
    assert "Marcus Gustafsson" in page
    assert "Mathias Axelsson" in page
    assert "Tom Lundberg" in page


def test_booking_ignores_browser_sent_price_fields(client):
    """Store the local order total from the event row, not from form data."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.price_per_canoe_sek = 1500
        db.session.commit()

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "2",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
            "canoe2_fname": "Bob",
            "canoe2_lname": "Berg",
            "totalAmount": "1",
            "unitAmount": "1",
            "currency": "usd",
        },
    )

    assert response.status_code == 302

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        assert float(booking_order.total_amount) == 3000.0
        assert booking_order.currency == "sek"


def test_payment_cancel_removes_pending_booking_and_renders_return_page(client):
    """Delete the temporary pending booking and return home with a toast."""

    unlock_public_site(client)
    booking_data = {
        "canoeCount": "1",
        "canoe1_fname": "Alice",
        "canoe1_lname": "Andersson",
    }

    client.post(
        "/create-checkout-session",
        data=booking_data,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response = client.get(
        build_stripe_cancel_return_path(client), follow_redirects=True
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Betalningen avbröts och reservationen släpptes." in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
        assert BookedCanoe.query.count() == 0


def test_stripe_webhook_rejects_missing_signature_header(client):
    """Reject webhook requests that do not include Stripe's signature header."""

    response = client.post("/stripe/webhook", data=b"{}")

    assert response.status_code == 400
    assert "Missing Stripe-Signature header." in response.get_data(as_text=True)


def test_stripe_webhook_rejects_invalid_signature(client, monkeypatch):
    """Reject webhook requests when signature verification fails."""

    from app import routes

    def raise_invalid_signature(payload, signature_header):
        raise stripe.SignatureVerificationError(
            "No signatures found matching the expected signature for payload.",
            signature_header,
            payload,
        )

    monkeypatch.setattr(
        routes,
        "construct_stripe_webhook_event",
        raise_invalid_signature,
    )

    response = client.post(
        "/stripe/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "t=1,v1=invalid"},
    )

    assert response.status_code == 400
    assert "Invalid signature." in response.get_data(as_text=True)


def test_completed_webhook_finalizes_pending_booking(client, monkeypatch):
    """Confirm the local booking only after a verified Stripe event."""

    from app import routes

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        checkout_session_id = booking_order.payment_provider_session_id
        assert checkout_session_id is not None
        stripe_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": checkout_session_id,
                    "payment_status": "paid",
                    "metadata": {
                        "booking_order_id": str(booking_order.id),
                        "public_booking_reference": booking_order.public_booking_reference,
                    },
                    "customer_details": {
                        "email": "alice@example.com",
                        "name": "Alice Andersson",
                    },
                }
            },
        }

    monkeypatch.setattr(
        routes,
        "construct_stripe_webhook_event",
        lambda payload, signature_header: stripe_event,
    )

    response = client.post(
        "/stripe/webhook",
        data=b'{"id":"evt_test_paid"}',
        headers={"Stripe-Signature": "t=1,v1=valid"},
    )

    assert response.status_code == 200

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        assert booking_order.status == "paid"
        assert booking_order.paid_at is not None
        assert booking_order.expires_at is None
        assert booking_order.payer_email == "alice@example.com"
        assert booking_order.payer_full_name == "Alice Andersson"
        assert [canoe.status for canoe in booking_order.booked_canoes] == ["confirmed"]


def test_completed_webhook_is_idempotent_for_paid_booking(client, monkeypatch):
    """Accept duplicate Stripe deliveries without changing the final result."""

    from app import routes

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        checkout_session_id = booking_order.payment_provider_session_id
        assert checkout_session_id is not None
        stripe_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": checkout_session_id,
                    "payment_status": "paid",
                    "metadata": {
                        "booking_order_id": str(booking_order.id),
                        "public_booking_reference": booking_order.public_booking_reference,
                    },
                }
            },
        }

    monkeypatch.setattr(
        routes,
        "construct_stripe_webhook_event",
        lambda payload, signature_header: stripe_event,
    )

    first_response = client.post(
        "/stripe/webhook",
        data=b'{"id":"evt_test_paid"}',
        headers={"Stripe-Signature": "t=1,v1=valid"},
    )
    second_response = client.post(
        "/stripe/webhook",
        data=b'{"id":"evt_test_paid_duplicate"}',
        headers={"Stripe-Signature": "t=1,v1=valid"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        assert booking_order.status == "paid"
        assert BookingOrder.query.count() == 1
        assert BookedCanoe.query.count() == 1


def test_expired_webhook_releases_pending_booking(client, monkeypatch):
    """Release an unpaid reservation when Stripe expires the Checkout Session."""

    from app import routes

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        checkout_session_id = booking_order.payment_provider_session_id
        assert checkout_session_id is not None
        stripe_event = {
            "type": "checkout.session.expired",
            "data": {
                "object": {
                    "id": checkout_session_id,
                    "metadata": {
                        "booking_order_id": str(booking_order.id),
                        "public_booking_reference": booking_order.public_booking_reference,
                    },
                }
            },
        }

    monkeypatch.setattr(
        routes,
        "construct_stripe_webhook_event",
        lambda payload, signature_header: stripe_event,
    )

    response = client.post(
        "/stripe/webhook",
        data=b'{"id":"evt_test_expired"}',
        headers={"Stripe-Signature": "t=1,v1=valid"},
    )

    assert response.status_code == 200

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
        assert BookedCanoe.query.count() == 0


def test_start_stripe_checkout_keeps_original_local_hold_expiry(client):
    """Keep the same local expiry when the visitor continues into Stripe."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        original_expires_at = booking_order.expires_at

    response = client.get(build_stripe_pay_path(client))
    assert response.status_code == 302

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        assert booking_order.expires_at is not None
        assert original_expires_at is not None
        assert booking_order.expires_at == original_expires_at


def test_payment_success_redirects_home_when_local_hold_has_expired(client):
    """Return home with a toast when Stripe finishes after the local hold expired."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        booking_order.expires_at = get_current_utc_time() - timedelta(minutes=1)
        db.session.commit()

    response = client.get(
        build_stripe_success_return_path(client), follow_redirects=True
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Reservationstiden gick ut medan betalningen var öppen." in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
        assert BookedCanoe.query.count() == 0


def test_step_three_cancel_button_releases_pending_booking(client):
    """Allow the user to cancel from booking Step 3."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response = client.post(
        build_stripe_pay_path(client).replace("/pay", "/cancel"),
        follow_redirects=True,
        data={"cancellation_reason": "manual"},
    )

    assert response.status_code == 200
    assert "Ordern avbröts. Du kan nu gå tillbaka och boka på nytt." in (
        response.get_data(as_text=True)
    )

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
        assert BookedCanoe.query.count() == 0


def test_booking_requires_active_database_event_for_checkout(client):
    """Block checkout creation when no active event row exists."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.is_active = False
        db.session.commit()

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Det finns inget aktivt event att boka just nu." in response.get_data(
        as_text=True
    )

    with client.application.app_context():
        assert BookingOrder.query.count() == 0


def test_grouped_overview_renders_hidden_canoe_detail_rows(client):
    """Render the canoe-detail text in the overview modal for later expansion."""

    unlock_public_site(client)
    booking_data = {
        "canoeCount": "2",
        "canoe1_fname": "Marcus",
        "canoe1_lname": "Gustafsson",
        "canoe1_passenger2_fname": "Mathias",
        "canoe1_passenger2_lname": "Axelsson",
        "canoe2_fname": "Marcus",
        "canoe2_lname": "Gustafsson",
    }

    client.post("/create-checkout-session", data=booking_data)
    mark_latest_pending_booking_as_paid_for_test(client)

    response = client.get("/")
    page = response.get_data(as_text=True)

    assert "data-toggle-grouped-details" in page
    assert "Kanot 1" in page
    assert "Marcus Gustafsson &amp; Mathias Axelsson" in page
    assert "Kanot 2" in page
    assert "Marcus Gustafsson &amp; ?" in page


def test_booking_rejects_partial_optional_second_rider_name(client):
    """Reject a rider-two row when only one of the two name fields is filled in."""

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Marcus",
            "canoe1_lname": "Gustafsson",
            "canoe1_passenger2_fname": "Mathias",
            "canoe1_passenger2_lname": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        "Andra personen i kanot 1 måste ha både för- och efternamn"
        in response.get_data(as_text=True)
    )

    with client.application.app_context():
        assert BookingOrder.query.count() == 0


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


def test_booking_rejects_same_name_above_total_canoe_limit(client):
    """Reject bookings that would push one exact name above five total canoes."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        booking_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-TEST-NAME-LIMIT",
            status="paid",
            canoe_count=5,
            total_amount=6000,
            currency="sek",
            payment_provider="simulated",
        )
        db.session.add(booking_order)
        db.session.flush()
        for _ in range(5):
            db.session.add(
                BookedCanoe(
                    booking_order_id=booking_order.id,
                    participant_first_name="Marcus",
                    participant_last_name="Gustafsson",
                    status="confirmed",
                )
            )
        db.session.commit()

    unlock_public_site(client)
    response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Marcus",
            "canoe1_lname": "Gustafsson",
        },
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Marcus Gustafsson har redan 5 bokade kanoter." in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 1


def test_home_page_includes_active_pending_reservations_in_progress_count(client):
    """Render the current blocked-canoe count including active unpaid holds."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.available_canoes = 77
        db.session.commit()

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    response = client.get("/")
    page = response.get_data(as_text=True)
    assert "1 / 77 kanoter bokade" in page


def test_booking_name_limit_counts_active_pending_reservations(client):
    """Count active unpaid reservation holds against the five-canoe name limit."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        active_event.available_canoes = 10
        db.session.commit()

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "5",
            "canoe1_fname": "Marcus",
            "canoe1_lname": "Gustafsson",
            "canoe2_fname": "Marcus",
            "canoe2_lname": "Gustafsson",
            "canoe3_fname": "Marcus",
            "canoe3_lname": "Gustafsson",
            "canoe4_fname": "Marcus",
            "canoe4_lname": "Gustafsson",
            "canoe5_fname": "Marcus",
            "canoe5_lname": "Gustafsson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    response = client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Marcus",
            "canoe1_lname": "Gustafsson",
        },
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert "Marcus Gustafsson har redan 5 bokade kanoter." in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 1


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


def test_expired_pending_booking_is_cleaned_up_before_home_page_counting(client):
    """Release expired pending holds before the homepage count is rendered."""

    unlock_public_site(client)
    client.post(
        "/create-checkout-session",
        data={
            "canoeCount": "1",
            "canoe1_fname": "Alice",
            "canoe1_lname": "Andersson",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    with client.application.app_context():
        booking_order = BookingOrder.query.one()
        booking_order.expires_at = get_current_utc_time() - timedelta(minutes=1)
        db.session.commit()

    response = client.get("/", follow_redirects=True)
    page = response.get_data(as_text=True)
    assert "Reservationstiden gick ut." in page
    assert "0 / 50 kanoter bokade" in page

    with client.application.app_context():
        assert BookingOrder.query.count() == 0
        assert BookedCanoe.query.count() == 0


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


def test_home_page_groups_participant_overview_by_name(client):
    """Show grouped canoe counts while also rendering hidden canoe details."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        booking_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-TEST-OVERVIEW",
            status="paid",
            canoe_count=3,
            total_amount=3600,
            currency="sek",
            payment_provider="simulated",
        )
        db.session.add(booking_order)
        db.session.flush()
        db.session.add_all(
            [
                BookedCanoe(
                    booking_order_id=booking_order.id,
                    participant_first_name="Saga",
                    participant_last_name="Svensson",
                    status="confirmed",
                ),
                BookedCanoe(
                    booking_order_id=booking_order.id,
                    participant_first_name="Saga",
                    participant_last_name="Svensson",
                    status="confirmed",
                ),
                BookedCanoe(
                    booking_order_id=booking_order.id,
                    participant_first_name="Olle",
                    participant_last_name="Olsson",
                    status="confirmed",
                ),
            ]
        )
        db.session.commit()

    unlock_public_site(client)
    response = client.get("/")
    page = response.get_data(as_text=True)
    assert "participant-overview-modal-card" in page
    assert "data-toggle-grouped-details" in page
    assert "Saga Svensson" in page
    assert "Olle Olsson" in page
    assert 'participant-overview-count">2<' in page
    assert 'participant-overview-count">1<' in page
    assert "Kanot 1" in page
    assert "Kanot 2" in page


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
