import pytest
import os
os.environ['FLASK_ENV'] = 'testing'

from app import create_app, db as _db
from app.models import User, Challenge, initialize_challenges, initialize_badges

@pytest.fixture(scope='session')
def app():
    """Create a test application with an in-memory database."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'MAIL_SUPPRESS_SEND': True,
        'SECRET_KEY': 'test-secret-key',
    })
    with app.app_context():
        _db.create_all()
        initialize_challenges()
        initialize_badges()
        # Create admin user
        admin = User(username='testadmin', email='admin@test.com', role='admin', is_active=True)
        admin.set_password('Admin@1234!')
        _db.session.add(admin)
        # Create standard user
        user = User(username='testuser', email='user@test.com', role='user', is_active=True)
        user.set_password('User@1234!')
        _db.session.add(user)
        _db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client, app):
    """Client logged in as standard user."""
    with app.app_context():
        client.post('/login', data={'username':'testuser','password':'User@1234!'})
    return client

@pytest.fixture
def admin_client(client, app):
    """Client logged in as admin."""
    with app.app_context():
        client.post('/login', data={'username':'testadmin','password':'Admin@1234!'})
    return client
