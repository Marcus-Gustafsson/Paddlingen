
def test_home_page(client):
    """Request the landing page and ensure it is publicly reachable."""
    res = client.get('/')
    assert res.status_code == 200


def test_login_page(client):
    """Confirm the login page renders so users can authenticate."""
    res = client.get('/login')
    assert res.status_code == 200
