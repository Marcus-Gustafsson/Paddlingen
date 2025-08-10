import os
import pytest

from app import create_app, db, User

# Ensure the instance directory exists so the app's SQLite database can be created
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)


@pytest.fixture
def client():
    """Provide a Flask test client with an in-memory database."""
    flask_application = create_app()
    flask_application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test',
        WTF_CSRF_SECRET_KEY='test'
    )
    with flask_application.app_context():
        db.drop_all()
        db.create_all()
        admin_user = User(username='admin')
        admin_user.set_password('password')
        db.session.add(admin_user)
        db.session.commit()
    with flask_application.test_client() as test_client:
        yield test_client
