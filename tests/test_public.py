
def test_home_page(client):
    res = client.get('/')
    assert res.status_code == 200


def test_login_page(client):
    res = client.get('/login')
    assert res.status_code == 200
