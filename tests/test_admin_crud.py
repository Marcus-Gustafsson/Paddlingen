"""Tests for CRUD operations in the admin interface."""

from html import unescape
from datetime import date

from app import BookedCanoe, BookingOrder, Event, db


def unlock_public_site(client):
    """Unlock the shared public-site gate for one test-client session."""

    return client.post(
        "/unlock",
        data={"password": "eventpass"},
        follow_redirects=True,
    )


def login(client):
    """Helper that logs the test client in as the administrator.

    This function simulates submitting the login form so that subsequent
    requests are authenticated.  It is intentionally tiny but having a
    docstring here helps new contributors understand what happens.

    Args:
        client (flask.testing.FlaskClient): The Flask test client used to send
            the POST request.

    Returns:
        werkzeug.wrappers.Response: The response object returned by the login
            request.  Tests generally ignore it but it can be inspected if
            needed.
    """

    unlock_public_site(client)
    return client.post(
        "/login",
        data={"username": "admin", "password": "password"},
        follow_redirects=True,
    )


def test_admin_crud_flow(client):
    """Verify that the admin interface supports the full CRUD cycle.

    The test logs in, creates a booking, edits that booking, and finally
    deletes it.  Each step asserts that the database and HTTP responses
    reflect the expected state, proving that Create, Read, Update and Delete
    all behave correctly.

    Args:
        client (flask.testing.FlaskClient): Authorized Flask test client
            provided by the ``client`` fixture.

    Returns:
        None: Pytest verifies behaviour using assertions rather than a return
            value.
    """

    login(client)

    # Add a booking
    response = client.post(
        "/admin/add",
        data={
            "participant_first_name": "Alice",
            "participant_last_name": "Andersson",
            "manual_payment_method": "stripe",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Alice" in response.data
    assert "Hantera bokningar" in response.get_data(as_text=True)
    booking = BookedCanoe.query.filter_by(participant_first_name="Alice").first()
    assert booking is not None
    assert BookingOrder.query.count() == 1
    assert booking.booking_order.payment_provider == "admin_manual_stripe"
    assert response.get_data(as_text=True).count(f"/admin/update/{booking.id}") == 1

    # Update the booking
    response = client.post(
        f"/admin/update/{booking.id}",
        data={
            "participant_first_name": "Bob",
            "participant_last_name": "Berg",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Bob" in response.data
    booking = db.session.get(BookedCanoe, booking.id)
    assert booking.participant_first_name == "Bob"
    assert booking.participant_last_name == "Berg"

    # Delete the booking
    response = client.post(f"/admin/delete/{booking.id}", follow_redirects=True)
    assert response.status_code == 200
    assert db.session.get(BookedCanoe, booking.id) is None
    assert BookingOrder.query.count() == 0


def test_admin_rejects_too_long_participant_names(client):
    """Reject manual admin bookings whose first or last name is too long."""

    login(client)

    response = client.post(
        "/admin/add",
        data={
            "participant_first_name": "A" * 21,
            "participant_last_name": "Andersson",
            "manual_payment_method": "cash",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Förnamn får vara högst 20 tecken långt." in response.get_data(as_text=True)
    assert BookingOrder.query.count() == 0


def test_admin_can_create_update_and_activate_events(client):
    """Verify that the event-management routes work from the admin dashboard."""

    login(client)

    active_event = Event.query.filter_by(is_active=True).first()
    assert active_event is not None

    create_response = client.post(
        "/admin/events/create",
        data={
            "source_event_id": active_event.id,
            "new_event_date": "2027-03-19",
            "new_title": "Paddlingen 2027",
            "new_subtitle": "Nästa års paddling",
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200
    assert "Nytt event skapades från den valda mallen." in create_response.get_data(
        as_text=True
    )

    created_event = Event.query.filter_by(event_date=date(2027, 3, 19)).first()
    assert created_event is not None
    assert created_event.is_active is False

    update_response = client.post(
        f"/admin/events/update/{created_event.id}",
        data={
            "title": "Paddlingen 2027 Uppdaterad",
            "subtitle": "",
            "event_date": "2027-03-19",
            "start_time": "11:30",
            "starting_location_name": "Ny startplats",
            "starting_location_url": "https://example.com/start",
            "end_location_name": "Ny slutplats",
            "end_location_url": "https://example.com/end",
            "available_canoes": "48",
            "price_per_canoe_sek": "1350.00",
            "max_canoes_per_booking": "4",
            "weather_forecast_days_before_event": "6",
            "weather_latitude": "59.8044",
            "weather_longitude": "15.1901",
            "faq_booking_text": "Första raden\nAndra raden",
            "faq_changes_and_questions_text": "Fråga ett\nFråga två",
            "rules_on_the_water_text": "Regel ett\nRegel två",
            "rules_after_paddling_text": "Efter ett\nEfter två",
            "contact_email": "admin@example.com",
            "contact_phone": "070-123 45 67",
        },
        follow_redirects=True,
    )
    assert update_response.status_code == 200
    assert "Eventet uppdaterades." in update_response.get_data(as_text=True)

    updated_event = db.session.get(Event, created_event.id)
    assert updated_event.title == "Paddlingen 2027 Uppdaterad"
    assert updated_event.subtitle == ""
    assert updated_event.available_canoes == 48
    assert str(updated_event.price_per_canoe_sek) == "1350.00"

    activate_response = client.post(
        f"/admin/events/activate/{created_event.id}",
        follow_redirects=True,
    )
    assert activate_response.status_code == 200
    assert 'Eventet "2027-03-19" är nu aktivt på hemsidan.' in unescape(
        activate_response.get_data(as_text=True)
    )

    refreshed_original_event = db.session.get(Event, active_event.id)
    refreshed_updated_event = db.session.get(Event, created_event.id)
    assert refreshed_updated_event.is_active is True
    assert refreshed_original_event.is_active is False


def test_admin_can_create_first_event_from_code_template_when_db_is_empty(client):
    """Allow the admin dashboard to create the first event without a source row."""

    login(client)

    for existing_event in Event.query.all():
        db.session.delete(existing_event)
    db.session.commit()

    create_response = client.post(
        "/admin/events/create",
        data={
            "new_event_date": "2028-03-17",
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200
    assert "Nytt event skapades från den valda mallen." in create_response.get_data(
        as_text=True
    )

    created_event = Event.query.filter_by(event_date=date(2028, 3, 17)).first()
    assert created_event is not None
    assert created_event.title == client.application.config["EVENT_TITLE"]
    assert created_event.subtitle == client.application.config["EVENT_SUBTITLE"]
    assert (
        created_event.available_canoes == client.application.config["AVAILABLE_CANOES"]
    )
    assert created_event.is_active is False


def test_admin_checklist_persists_partial_pickup_status_and_sorts_checked_first(client):
    """Persist checklist state and render checked canoes before unchecked ones."""

    login(client)

    active_event = Event.query.filter_by(is_active=True).first()
    assert active_event is not None

    booking_order = BookingOrder(
        event_id=active_event.id,
        public_booking_reference="PAD-TEST-CHECKLIST",
        status="paid",
        canoe_count=3,
        total_amount=3600,
        currency="sek",
        payment_provider="simulated",
    )
    db.session.add(booking_order)
    db.session.flush()

    first_canoe = BookedCanoe(
        booking_order_id=booking_order.id,
        participant_first_name="Klara",
        participant_last_name="Karlsson",
        status="confirmed",
    )
    second_canoe = BookedCanoe(
        booking_order_id=booking_order.id,
        participant_first_name="Klara",
        participant_last_name="Karlsson",
        status="confirmed",
    )
    third_canoe = BookedCanoe(
        booking_order_id=booking_order.id,
        participant_first_name="Klara",
        participant_last_name="Karlsson",
        status="confirmed",
    )
    db.session.add_all([first_canoe, second_canoe, third_canoe])
    db.session.commit()
    first_canoe_id = first_canoe.id
    second_canoe_id = second_canoe.id
    third_canoe_id = third_canoe.id

    partial_response = client.post(
        "/admin/checklist",
        data={
            "picked_up_booking_ids": [str(first_canoe_id), str(second_canoe_id)],
        },
        follow_redirects=True,
    )
    assert partial_response.status_code == 200
    assert "Checklistan uppdaterades." in partial_response.get_data(as_text=True)

    db.session.expire_all()
    refreshed_first_canoe = db.session.get(BookedCanoe, first_canoe_id)
    refreshed_second_canoe = db.session.get(BookedCanoe, second_canoe_id)
    refreshed_third_canoe = db.session.get(BookedCanoe, third_canoe_id)
    assert refreshed_first_canoe.picked_up is True
    assert refreshed_second_canoe.picked_up is True
    assert refreshed_third_canoe.picked_up is False

    partial_page = partial_response.get_data(as_text=True)
    first_checked_position = partial_page.index(f'value="{first_canoe_id}"')
    second_checked_position = partial_page.index(f'value="{second_canoe_id}"')
    third_unchecked_position = partial_page.index(f'value="{third_canoe_id}"')
    assert first_checked_position < third_unchecked_position
    assert second_checked_position < third_unchecked_position
    assert "2/3 kanoter avprickade" in partial_page

    complete_response = client.post(
        "/admin/checklist",
        data={
            "picked_up_booking_ids": [
                str(first_canoe_id),
                str(second_canoe_id),
                str(third_canoe_id),
            ],
        },
        follow_redirects=True,
    )
    assert complete_response.status_code == 200
    complete_page = complete_response.get_data(as_text=True)
    assert "3/3 kanoter avprickade" in complete_page
    assert "admin-checklist-row--complete" in complete_page
