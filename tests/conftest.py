"""Common pytest fixtures for the Paddlingen test suite."""

from datetime import datetime, timedelta, timezone
import sys

import pytest
import os
from werkzeug.security import generate_password_hash

from app import create_app, db, User
from app.util.event_settings import create_or_update_active_event_from_config

# Ensure the instance directory exists so the app's SQLite database can be created
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)


class FakeStripeCheckoutSession:
    """Small fake Stripe Checkout Session used in tests.

    The public booking tests should not call the real Stripe API. This object
    mimics the small part of the Checkout Session shape that the routes use.
    """

    def __init__(
        self,
        session_id: str = "cs_test_fake_checkout_session",
        url: str = "https://checkout.stripe.test/session/cs_test_fake_checkout_session",
        payment_status: str = "unpaid",
        status: str = "open",
        expires_at: int | None = None,
    ) -> None:
        self.id = session_id
        self.url = url
        self.payment_status = payment_status
        self.status = status
        self.expires_at = expires_at or int(
            (datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()
        )


@pytest.fixture
def client():
    """Provide a Flask test client backed by an in-memory SQLite database.

    Tests should run in isolation and must not talk to any production
    database.  By setting ``DATABASE_URL`` to the special SQLite memory URI we
    ensure the application's configuration picks up this transient database
    instead of whatever the developer might have configured locally.

    Yields:
        flask.testing.FlaskClient: A client instance with a fresh application
            and database for each test case.
    """

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    # The config module reads environment variables at import time. When tests
    # run in one shared process, removing the cached module keeps each app
    # instance aligned with the environment values set in this fixture.
    sys.modules.pop("config", None)
    flask_application = create_app()
    flask_application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test",
        WTF_CSRF_SECRET_KEY="test",
        PUBLIC_SITE_PASSWORD_HASH=generate_password_hash("eventpass"),
        STRIPE_SECRET_KEY="sk_test_123",
        STRIPE_WEBHOOK_SECRET="whsec_test_123",
        STRIPE_PUBLIC_BASE_URL="http://127.0.0.1:5000",
        STRIPE_CHECKOUT_PRODUCT_ID="",
    )
    with flask_application.app_context():
        db.drop_all()
        db.create_all()
        create_or_update_active_event_from_config()
        admin_user = User(username="admin")
        admin_user.set_password("password")
        db.session.add(admin_user)
        db.session.commit()
    with flask_application.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def fake_stripe_checkout(monkeypatch):
    """Replace Stripe Checkout API calls with a predictable local fake."""

    from app import routes

    fake_checkout_session = FakeStripeCheckoutSession()

    monkeypatch.setattr(
        routes,
        "create_stripe_checkout_session",
        lambda **_: fake_checkout_session,
    )
    monkeypatch.setattr(
        routes,
        "retrieve_stripe_checkout_session",
        lambda checkout_session_id: FakeStripeCheckoutSession(
            session_id=checkout_session_id
        ),
    )
    monkeypatch.setattr(
        routes,
        "expire_stripe_checkout_session",
        lambda checkout_session_id: FakeStripeCheckoutSession(
            session_id=checkout_session_id,
            payment_status="unpaid",
            status="expired",
            url=None,
        ),
    )
