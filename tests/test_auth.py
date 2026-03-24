"""Authentication-related tests for the application."""

from sqlalchemy import inspect
from werkzeug.security import check_password_hash

from app.util.db_models import PublicSiteAccessSetting, db
from app.util.db_models import BookedCanoe, BookingOrder, Event


def unlock_public_site(client):
    """Unlock the shared public-site gate for one test-client session."""

    return client.post(
        "/unlock",
        data={"password": "eventpass"},
        follow_redirects=True,
    )


def login_admin(client):
    """Unlock the public site and log in as the seeded admin user."""

    unlock_public_site(client)
    return client.post(
        "/login",
        data={"username": "admin", "password": "password"},
        follow_redirects=True,
    )


def test_admin_requires_login(client):
    """Try to open the admin dashboard without logging in.

    The test sends a GET request to '/admin' using the anonymous test client. The
    @login_required decorator should stop anonymous users and respond with an
    HTTP 302 redirect. The Location header in that redirect should include
    '/login', which proves unauthenticated visitors are sent to the login page.
    """
    unlock_public_site(client)
    response = client.get("/admin")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_checklist_renders_hidden_canoe_detail_rows(client):
    """Render grouped canoe-detail text in the admin checklist panel."""

    with client.application.app_context():
        active_event = Event.query.filter_by(is_active=True).first()
        booking_order = BookingOrder(
            event_id=active_event.id,
            public_booking_reference="PAD-TEST-CHECKLIST-DETAILS",
            status="paid",
            canoe_count=1,
            total_amount=1200,
            currency="sek",
            payment_provider="simulated",
        )
        db.session.add(booking_order)
        db.session.flush()
        db.session.add(
            BookedCanoe(
                booking_order_id=booking_order.id,
                participant_first_name="Marcus",
                participant_last_name="Gustafsson",
                passenger_two_first_name="Mathias",
                passenger_two_last_name="Axelsson",
                status="confirmed",
            )
        )
        db.session.commit()

    login_admin(client)
    response = client.get("/admin?panel=checklist")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-toggle-grouped-details" in page
    assert "Kanot 1" in page
    assert "Marcus Gustafsson &amp; Mathias Axelsson" in page


def test_locked_login_redirects_back_to_public_gate(client):
    """Keep `/login` behind the shared public password gate."""

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_locked_admin_redirects_back_to_public_gate(client):
    """Keep `/admin` behind the shared public password gate."""

    response = client.get("/admin", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_login_fails_with_wrong_password(client):
    """Submit the login form with a bad password and check for failure.

    A POST request is sent to '/login' using the correct username but the wrong
    password. The app should not log the user in. Instead it re-renders the
    login page with an error message. We assert the page loads (status code 200),
    that the error text appears in the response body, and that we remain on the
    '/login' URL.
    """
    unlock_public_site(client)
    response = client.post(
        "/login", data={"username": "admin", "password": "wrong"}, follow_redirects=True
    )
    assert response.status_code == 200
    page_text = response.get_data(as_text=True)
    assert "Felaktigt användarnamn eller lösenord" in page_text
    assert response.request.path == "/login"


def test_login_rate_limit_exceeded(client):
    """Make six requests to '/login' and expect the last one to be blocked.

    The login view is protected by a rate limiter that allows only five
    requests per minute from the same IP address. This test performs six GET
    requests using a fixed ``REMOTE_ADDR`` value. The first five should return
    HTTP 200, but the sixth should trigger the limiter and respond with
    status code 429 (Too Many Requests).

    Args:
        client (FlaskClient): Test client used to mimic browser interactions.

    Returns:
        None: Assertions verify that rate limiting works as intended.

    """
    test_ip = "203.0.113.1"
    unlock_public_site(client)
    for _ in range(5):
        ok_response = client.get("/login", environ_overrides={"REMOTE_ADDR": test_ip})
        assert ok_response.status_code == 200
    limited_response = client.get("/login", environ_overrides={"REMOTE_ADDR": test_ip})
    assert limited_response.status_code == 429


def test_login_rejects_external_next_redirect(client):
    """Block external `next` URLs so login cannot be used as an open redirect."""

    unlock_public_site(client)
    response = client.post(
        "/login?next=http://google.com",
        data={"username": "admin", "password": "password"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin")


def test_login_allows_internal_next_redirect(client):
    """Allow safe internal `next` paths after a successful login."""

    unlock_public_site(client)
    response = client.post(
        "/login?next=/admin",
        data={"username": "admin", "password": "password"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin")


def test_admin_can_rotate_public_site_password(client):
    """Allow the admin dashboard to replace the shared public-site password."""

    login_admin(client)
    response = client.post(
        "/admin/public-site-password",
        data={
            "new_public_site_password": "New-event-pass-123",
            "confirm_public_site_password": "New-event-pass-123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Hemsidans gemensamma lösenord har uppdaterats." in response.get_data(
        as_text=True
    )

    with client.application.app_context():
        password_setting = PublicSiteAccessSetting.query.first()
        assert password_setting is not None
        assert check_password_hash(
            password_setting.password_hash,
            "New-event-pass-123",
        )

    with client.application.test_client() as new_browser_session:
        wrong_password_response = new_browser_session.post(
            "/unlock",
            data={"password": "eventpass"},
            follow_redirects=True,
        )
        assert "Fel lösenord. Försök igen." in wrong_password_response.get_data(
            as_text=True
        )

        correct_password_response = new_browser_session.post(
            "/unlock",
            data={"password": "New-event-pass-123"},
            follow_redirects=True,
        )
        assert "Boka kanot" in correct_password_response.get_data(as_text=True)


def test_admin_public_site_password_rejects_mismatched_confirmation(client):
    """Require the confirmation field to match the new shared password."""

    login_admin(client)
    response = client.post(
        "/admin/public-site-password",
        data={
            "new_public_site_password": "Another-pass-123!",
            "confirm_public_site_password": "Different-pass-123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Lösenorden matchar inte." in response.get_data(as_text=True)


def test_admin_public_site_password_recreates_missing_table(client):
    """Keep password rotation working on an older database that lacks the table."""

    with client.application.app_context():
        PublicSiteAccessSetting.__table__.drop(db.engine)

    login_admin(client)
    response = client.post(
        "/admin/public-site-password",
        data={
            "new_public_site_password": "Recreated-pass-123!",
            "confirm_public_site_password": "Recreated-pass-123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Hemsidans gemensamma lösenord har uppdaterats." in response.get_data(
        as_text=True
    )

    with client.application.app_context():
        assert inspect(db.engine).has_table(PublicSiteAccessSetting.__tablename__)
        password_setting = PublicSiteAccessSetting.query.first()
        assert password_setting is not None
        assert check_password_hash(
            password_setting.password_hash,
            "Recreated-pass-123!",
        )


def test_admin_can_change_own_login_password(client):
    """Allow a logged-in admin to update their own login password."""

    login_admin(client)
    response = client.post(
        "/admin/account-password",
        data={
            "new_admin_password": "Updated-admin-pass-123!",
            "confirm_admin_password": "Updated-admin-pass-123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Ditt adminlösenord har uppdaterats." in response.get_data(as_text=True)

    client.get("/logout", follow_redirects=True)
    wrong_password_response = client.post(
        "/login",
        data={"username": "admin", "password": "password"},
        follow_redirects=True,
    )
    assert "Felaktigt användarnamn eller lösenord" in wrong_password_response.get_data(
        as_text=True
    )

    correct_password_response = client.post(
        "/login",
        data={"username": "admin", "password": "Updated-admin-pass-123!"},
        follow_redirects=False,
    )
    assert correct_password_response.status_code == 302
    assert correct_password_response.headers["Location"].endswith("/admin")
