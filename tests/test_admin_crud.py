"""Tests for CRUD operations in the admin interface."""

from app import RentForm


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
    response = client.post("/admin/add", data={"name": "Alice"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Alice" in response.data
    booking = RentForm.query.filter_by(name="Alice").first()
    assert booking is not None

    # Update the booking
    response = client.post(
        f"/admin/update/{booking.id}", data={"name": "Bob"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Bob" in response.data
    booking = RentForm.query.get(booking.id)
    assert booking.name == "Bob"

    # Delete the booking
    response = client.post(f"/admin/delete/{booking.id}", follow_redirects=True)
    assert response.status_code == 200
    assert RentForm.query.get(booking.id) is None
