def test_admin_requires_login(client):
    """Try to open the admin dashboard without logging in.

    The test sends a GET request to '/admin' using the anonymous test client. The
    @login_required decorator should stop anonymous users and respond with an
    HTTP 302 redirect. The Location header in that redirect should include
    '/login', which proves unauthenticated visitors are sent to the login page.
    """
    response = client.get('/admin')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_login_fails_with_wrong_password(client):
    """Submit the login form with a bad password and check for failure.

    A POST request is sent to '/login' using the correct username but the wrong
    password. The app should not log the user in. Instead it re-renders the
    login page with an error message. We assert the page loads (status code 200),
    that the error text appears in the response body, and that we remain on the
    '/login' URL.
    """
    response = client.post('/login', data={'username': 'admin', 'password': 'wrong'}, follow_redirects=True)
    assert response.status_code == 200
    page_text = response.get_data(as_text=True)
    assert 'Felaktigt användarnamn eller lösenord' in page_text
    assert response.request.path == '/login'
