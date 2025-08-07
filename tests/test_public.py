
import main
from main import app, RentForm, PendingBooking


def test_home_page(client):
    """Send GET '/' and verify the public landing page responds with 200."""
    res = client.get('/')
    assert res.status_code == 200


def test_login_page(client):
    """Ensure the login route renders so users can start authentication."""
    res = client.get('/login')
    assert res.status_code == 200


def test_booking_over_limit_shows_error(client):
    """Request too many canoes and confirm an error message is shown.

    This test temporarily lowers ``MAX_CANOEES`` to a very small number to
    simulate a fully booked day. It then posts a form asking for more canoes
    than are available. Flask should respond with a flash error on the home
    page and refuse to create any :class:`PendingBooking` records.
    """
    app.config['MAX_CANOEES'] = 1
    main.MAX_CANOEES = 1

    res = client.post(
        '/create-checkout-session',
        data={'canoeCount': '2'},
        follow_redirects=True,
    )
    page = res.get_data(as_text=True)
    assert 'Tyvärr, bara 1 kanot(er) kvar' in page

    with app.app_context():
        assert PendingBooking.query.count() == 0


def test_successful_booking_creates_records(client):
    """Complete a booking and verify database tables are updated.

    The test submits a valid booking for two canoes, then simulates the user
    returning from payment by calling ``/payment-success``. Two permanent
    :class:`RentForm` rows should be created and the temporary
    :class:`PendingBooking` table left empty.
    """
    app.config['MAX_CANOEES'] = 3
    main.MAX_CANOEES = 3

    booking_data = {
        'canoeCount': '2',
        'canoe1_fname': 'Alice',
        'canoe1_lname': 'Andersson',
        'canoe2_fname': 'Bob',
        'canoe2_lname': 'Berg',
    }
    client.post('/create-checkout-session', data=booking_data)

    client.get('/payment-success')

    with app.app_context():
        names = [r.name for r in RentForm.query.order_by(RentForm.id)]
        assert 'Alice Andersson' in names
        assert 'Bob Berg' in names
        assert PendingBooking.query.count() == 0
