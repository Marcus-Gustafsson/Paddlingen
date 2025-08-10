from app import db, RentForm


def login(client):
    return client.post('/login', data={'username': 'admin', 'password': 'password'}, follow_redirects=True)


def test_admin_crud_flow(client):
    """Admin adds a booking, edits it, then deletes it to prove the CRUD cycle works."""
    login(client)

    # Add a booking
    response = client.post('/admin/add', data={'name': 'Alice'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Alice' in response.data
    booking = RentForm.query.filter_by(name='Alice').first()
    assert booking is not None

    # Update the booking
    response = client.post(f'/admin/update/{booking.id}', data={'name': 'Bob'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Bob' in response.data
    booking = RentForm.query.get(booking.id)
    assert booking.name == 'Bob'

    # Delete the booking
    response = client.post(f'/admin/delete/{booking.id}', follow_redirects=True)
    assert response.status_code == 200
    assert RentForm.query.get(booking.id) is None
