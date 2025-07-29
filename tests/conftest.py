import os
import pytest
from main import app, db, User

@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test'
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
