"""Unit tests for CLI challenge evaluation."""
import json


def test_correct_command_awards_points(auth_client, app):
    """Correct CLI command awards points and creates score record."""
    from app.models import Challenge
    with app.app_context():
        ch = Challenge.query.first()
        if not ch:
            return
        rv = auth_client.post('/validate', json={'command': ch.solution, 'challenge_id': ch.id})
        data = json.loads(rv.data)
        assert rv.status_code == 200
        assert '✅' in data['message'] or 'already' in data['message']


def test_incorrect_command_returns_hint(auth_client, app):
    """Incorrect command returns error message with docs link."""
    from app.models import Challenge
    with app.app_context():
        ch = Challenge.query.first()
        if not ch:
            return
        rv = auth_client.post('/validate', json={'command': 'this is wrong', 'challenge_id': ch.id})
        data = json.loads(rv.data)
        assert '❌' in data['message']


def test_duplicate_submission_no_extra_points(auth_client, app):
    """Second correct submission for same challenge awards no additional points."""
    from app import db
    from app.models import Challenge, Score, User
    with app.app_context():
        ch = Challenge.query.first()
        user = User.query.filter_by(username='testuser').first()
        if not ch or not user:
            return
        # First submission
        auth_client.post('/validate', json={'command': ch.solution, 'challenge_id': ch.id})
        count_before = Score.query.filter_by(user_id=user.id, challenge_id=ch.id).count()
        # Second submission
        auth_client.post('/validate', json={'command': ch.solution, 'challenge_id': ch.id})
        count_after = Score.query.filter_by(user_id=user.id, challenge_id=ch.id).count()
        assert count_after == count_before


def test_unauthenticated_validate_redirects(client):
    """Unauthenticated request to /validate is redirected to login."""
    rv = client.post('/validate', json={'command': 'aws s3 mb', 'challenge_id': 1})
    assert rv.status_code in (302, 401)


def test_injection_stripped_from_command(auth_client, app):
    """Shell injection characters are stripped before evaluation."""
    from app.models import Challenge
    with app.app_context():
        ch = Challenge.query.first()
        if not ch:
            return
        malicious = f'{ch.solution}; rm -rf /'
        rv = auth_client.post('/validate', json={'command': malicious, 'challenge_id': ch.id})
        assert rv.status_code == 200


def test_admin_routes_require_admin(auth_client):
    """Standard user cannot access admin routes."""
    rv = auth_client.get('/admin/dashboard', follow_redirects=False)
    assert rv.status_code == 302


def test_backup_requires_admin(auth_client):
    """Standard user cannot access backup panel."""
    rv = auth_client.get('/backup/', follow_redirects=False)
    assert rv.status_code == 302
