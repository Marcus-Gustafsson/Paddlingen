"""Tests for JSON API endpoints.

These tests cover the application's simple JSON endpoints. They verify both
successful responses and common error conditions so that the frontend can
rely on stable and predictable behavior.
"""

from app import db, RentForm


def test_booking_count_api_returns_number(client):
    """Count bookings via the ``/api/booking-count`` endpoint.

    The test inserts a sample booking into the database and then calls the
    API endpoint. The JSON response should include a ``count`` field that
    matches the number of bookings stored in the database.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.

    Returns:
        None: Assertions validate the returned data.

    """
    with client.application.app_context():
        db.session.add(RentForm(name="Test", transaction_id="t1"))
        db.session.commit()

    response = client.get("/api/booking-count")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 1


def test_forecast_api_returns_data(client, monkeypatch):
    """Fetch weather information for a given date.

    The real endpoint contacts an external weather API. To keep the test fast
    and deterministic, we monkeypatch :func:`requests.get` to return a small
    JSON payload. The endpoint should parse this data and respond with a
    dictionary containing temperature, rain chance and an emoji icon.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.
        monkeypatch (pytest.MonkeyPatch): Utility to replace ``requests.get``.

    Returns:
        None: Assertions confirm correct parsing of the mocked data.

    """
    sample_payload = {
        "properties": {
            "timeseries": [
                {
                    "time": "2024-07-01T10:00:00Z",
                    "data": {
                        "instant": {"details": {"air_temperature": 15}},
                        "next_6_hours": {
                            "details": {"precipitation_amount": 0.1},
                            "summary": {"symbol_code": "fair_day"},
                        },
                    },
                }
            ]
        }
    }

    def fake_get(url, headers=None, params=None):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return sample_payload

        return FakeResponse()

    monkeypatch.setattr("requests.get", fake_get)

    response = client.get("/api/forecast?date=2024-07-01")
    assert response.status_code == 200
    data = response.get_json()
    assert data["temperature"] == 15
    assert data["rainChance"] == "0,1"
    assert data["icon"] == "🌤️"


def test_forecast_api_missing_date(client):
    """Call ``/api/forecast`` without the required date parameter.

    The route expects a ``date`` query argument formatted as YYYY-MM-DD. If it
    is missing, the endpoint should return HTTP 400 along with a helpful error
    message so that the frontend can correct the request.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.

    Returns:
        None: The test checks response status and JSON content.

    """
    response = client.get("/api/forecast")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_forecast_api_no_data(client, monkeypatch):
    """Return 404 when the weather API lacks the requested timestamp.

    The mocked API response omits the 10:00 and 12:00 UTC entries that the
    application expects. In this case the endpoint should indicate that no
    forecast is available by responding with HTTP 404.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.
        monkeypatch (pytest.MonkeyPatch): Utility to stub out ``requests.get``.

    Returns:
        None: Assertions verify the 404 behavior.

    """
    sample_payload = {
        "properties": {"timeseries": [{"time": "2024-07-01T09:00:00Z", "data": {}}]}
    }

    def fake_get(url, headers=None, params=None):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return sample_payload

        return FakeResponse()

    monkeypatch.setattr("requests.get", fake_get)

    response = client.get("/api/forecast?date=2024-07-01")
    assert response.status_code == 404
    assert "error" in response.get_json()
