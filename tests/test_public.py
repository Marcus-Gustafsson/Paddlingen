
def test_home_page(client):
    """Send GET '/' and verify the public landing page responds with 200."""
    res = client.get('/')
    assert res.status_code == 200


def test_login_page(client):
    """Ensure the login route renders so users can start authentication."""
    res = client.get('/login')
    assert res.status_code == 200
