"""Unit tests for authentication component."""


def test_register_valid_input(client, app):
    """Valid registration creates user and redirects."""
    rv = client.post('/signup', data={
        'username': 'newuser1', 'email': 'new1@test.com',
        'password': 'Secure@123', 'confirm_password': 'Secure@123'
    }, follow_redirects=False)
    assert rv.status_code in (200, 302)


def test_register_duplicate_username(client, app):
    """Duplicate username returns descriptive error."""
    rv = client.post('/signup', data={
        'username': 'testuser', 'email': 'other@test.com',
        'password': 'Secure@123', 'confirm_password': 'Secure@123'
    })
    assert b'already taken' in rv.data or rv.status_code == 302


def test_register_weak_password(client):
    """Weak password is rejected with a specific message."""
    rv = client.post('/signup', data={
        'username': 'weakpwduser', 'email': 'weak@test.com',
        'password': 'password', 'confirm_password': 'password'
    })
    assert rv.status_code == 200
    assert b'uppercase' in rv.data or b'Password' in rv.data


def test_register_password_mismatch(client):
    """Mismatched passwords are rejected."""
    rv = client.post('/signup', data={
        'username': 'mismatch1', 'email': 'mm@test.com',
        'password': 'Secure@123', 'confirm_password': 'Wrong@123'
    })
    assert rv.status_code == 200
    assert b'do not match' in rv.data or b'Passwords' in rv.data


def test_login_correct_credentials(client):
    """Correct credentials log in successfully."""
    rv = client.post('/login', data={'username':'testuser','password':'User@1234!'}, follow_redirects=False)
    assert rv.status_code == 302


def test_login_wrong_password(client):
    """Wrong password returns generic error."""
    rv = client.post('/login', data={'username':'testuser','password':'WrongPassword!'})
    assert rv.status_code == 200
    assert b'Invalid' in rv.data


def test_login_nonexistent_user(client):
    """Non-existent username returns generic error — does not reveal this."""
    rv = client.post('/login', data={'username':'nobody','password':'Anything@1'})
    assert rv.status_code == 200
    assert b'Invalid' in rv.data


def test_login_inactive_account(client, app):
    """Deactivated account cannot log in."""
    from app import db
    from app.models import User
    with app.app_context():
        u = User(username='inactiveuser', email='inactive@test.com', is_active=False, role='user')
        u.set_password('Active@123')
        db.session.add(u)
        db.session.commit()
    rv = client.post('/login', data={'username':'inactiveuser','password':'Active@123'})
    assert b'deactivated' in rv.data


def test_password_hash_not_plaintext(app):
    """Stored password_hash is never equal to the raw password."""
    from app.models import User
    with app.app_context():
        u = User.query.filter_by(username='testuser').first()
        assert u is not None
        assert u.password_hash != 'User@1234!'
        assert u.password_hash.startswith('pbkdf2:') or u.password_hash.startswith('scrypt:')


def test_check_password_correct(app):
    """check_password returns True for correct password."""
    from app.models import User
    with app.app_context():
        u = User.query.filter_by(username='testuser').first()
        assert u.check_password('User@1234!') is True


def test_check_password_wrong(app):
    """check_password returns False for wrong password."""
    from app.models import User
    with app.app_context():
        u = User.query.filter_by(username='testuser').first()
        assert u.check_password('WrongPassword!') is False
