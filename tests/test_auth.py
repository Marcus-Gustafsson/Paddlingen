"""Authentication-related tests for the application."""


def unlock_public_site(client):
    """Unlock the shared public-site gate for one test-client session."""

    return client.post(
        "/unlock",
        data={"password": "eventpass"},
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
