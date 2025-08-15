from app.util.db_models import RentForm, PendingBooking


def test_home_page(client):
    """Send GET '/' and verify the public landing page responds with 200."""
    response = client.get('/')
    assert response.status_code == 200


def test_login_page(client):
    """Ensure the login route renders so users can start authentication."""
    response = client.get('/login')
    assert response.status_code == 200


def test_booking_over_limit_shows_error(client):
    """Request too many canoes and confirm an error message is shown.

    This test temporarily lowers ``MAX_CANOEES`` to a very small number to
    simulate a fully booked day. It then posts a form asking for more canoes
    than are available. Flask should respond with a flash error on the home
    page and refuse to create any :class:`PendingBooking` records.
    """
    client.application.config['MAX_CANOEES'] = 1

    response = client.post(
        '/create-checkout-session',
        data={'canoeCount': '2'},
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert 'Tyvärr, bara 1 kanot(er) kvar' in page

    with client.application.app_context():
        assert PendingBooking.query.count() == 0


def test_successful_booking_creates_records(client):
    """Complete a booking and verify database tables are updated.

    The test submits a valid booking for two canoes, then simulates the user
    returning from payment by calling ``/payment-success``. Two permanent
    :class:`RentForm` rows should be created and the temporary
    :class:`PendingBooking` table left empty.
    """
    client.application.config['MAX_CANOEES'] = 3

    booking_data = {
        'canoeCount': '2',
        'canoe1_fname': 'Alice',
        'canoe1_lname': 'Andersson',
        'canoe2_fname': 'Bob',
        'canoe2_lname': 'Berg',
    }
    client.post('/create-checkout-session', data=booking_data)

    client.get('/payment-success')

    with client.application.app_context():
        names = [r.name for r in RentForm.query.order_by(RentForm.id)]
        assert 'Alice Andersson' in names
        assert 'Bob Berg' in names
        assert PendingBooking.query.count() == 0

def test_invalid_form_data_returns_flash_error(client):
    """Submit empty form data and expect an error without database changes.

    The payment route needs a ``canoeCount`` field. This test posts an empty
    form to ``/create-checkout-session`` to simulate a broken or tampered
    submission. Flask should flash an "Ogiltigt antal kanoter." message and
    redirect back to the home page. No ``PendingBooking`` rows are added.

    Args:
        client (FlaskClient): Test client used to simulate browser requests.

    Returns:
        None: This test relies on assertions instead of returning a value.

    """
    response = client.post('/create-checkout-session', data={}, follow_redirects=True)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Ogiltigt antal kanoter." in page

    with client.application.app_context():
        assert PendingBooking.query.count() == 0
