import os
import pytest

# Ensure the instance directory exists so the app's SQLite database can be created
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)

from main import app, db, User

@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test',
        WTF_CSRF_SECRET_KEY='test'
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(username='admin')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
    with app.test_client() as client:
        yield client
