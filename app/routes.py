import os
import json
import secrets
import requests
try:
    import boto3
except ImportError:
    boto3 = None
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from flask_mail import Message
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app import db, mail
from app.models import User, Challenge, Score, check_and_award_badges
from app.validation import validate_username, validate_email, validate_password, sanitise_cli_input
from app.decorators import login_required

main = Blueprint('main', __name__)


# ─── HOME ──────────────────────────────────────────────────────────────────────
@main.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    total_score = db.session.query(func.sum(Score.score)).filter_by(user_id=user.id).scalar() or 0
    completed_challenges = Score.query.filter_by(user_id=user.id).count()
    show_wizard = user.show_wizard
    return render_template('landing_page.html',
                           user=user,
                           total_score=total_score,
                           completed_challenges=completed_challenges,
                           show_wizard=show_wizard)


@main.route('/wizard-complete', methods=['POST'])
@login_required
def wizard_complete():
    """Mark the welcome wizard as seen for this user."""
    user = User.query.get(session['user_id'])
    if user:
        user.show_wizard = False
        db.session.commit()
    return jsonify({'success': True})


# ─── AUTH ──────────────────────────────────────────────────────────────────────
@main.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        # Generic error — do not reveal which field failed
        if not user or not user.check_password(password):
            return render_template('login.html', message='❌ Invalid username or password.')
        if not user.is_active:
            return render_template('login.html', message='❌ This account has been deactivated. Please contact the administrator.')
        session['user_id'] = user.id
        session['role'] = user.role
        session.permanent = True
        user.last_login = datetime.utcnow()
        db.session.commit()
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))
    return render_template('login.html')


@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Validate username
        ok, err = validate_username(username)
        if not ok:
            return render_template('signup.html', message=f'❌ {err}')

        # Validate email
        ok, err = validate_email(email)
        if not ok:
            return render_template('signup.html', message=f'❌ {err}')

        # Validate password
        ok, err = validate_password(password)
        if not ok:
            return render_template('signup.html', message=f'❌ {err}')

        # Passwords match
        if password != confirm:
            return render_template('signup.html', message='❌ Passwords do not match.')

        # Uniqueness checks
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', message='❌ Username already taken. Please choose a different one.')
        if User.query.filter_by(email=email).first():
            return render_template('signup.html',
                                   message='❌ Email already registered. Use the Forgot Password link to recover your account.',
                                   show_forgot_password=True)

        new_user = User(username=username, email=email, show_wizard=True)
        new_user.set_password(password)
        db.session.add(new_user)
        try:
            db.session.commit()
            session['user_id'] = new_user.id
            session['role'] = 'user'
            session.permanent = True
            new_user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            return render_template('signup.html', message=f'❌ Registration failed. Please try again.')

    return render_template('signup.html')


@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


# ─── PASSWORD RESET ────────────────────────────────────────────────────────────
@main.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        # Always show the same message regardless of whether email exists (prevents enumeration)
        if user:
            reset_token = secrets.token_urlsafe(32)
            user.set_reset_token(reset_token)
            db.session.commit()
            reset_link = url_for('main.reset_password', token=reset_token, _external=True)
            msg = Message(
                subject='Password Reset – AWS Community Labs',
                sender=('AWS Community Labs', 'no-reply@awslearningplatform.click'),
                recipients=[user.email]
            )
            msg.html = f"""
            <p>Hello {user.username},</p>
            <p>You requested a password reset for your AWS Community Labs account.</p>
            <p><a href="{reset_link}">Click here to reset your password</a></p>
            <p>This link expires in 1 hour. If you did not request this, ignore this email.</p>
            <p>— AWS Community Labs</p>
            """
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Reset email error: {e}")
        return render_template('forgot_password.html',
                               message='If an account with that email exists, reset instructions have been sent.')
    return render_template('forgot_password.html')


@main.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.is_reset_token_valid():
        return render_template('reset_password.html',
                               message='❌ This reset link is invalid or has expired. Please request a new one.')
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        ok, err = validate_password(new_password)
        if not ok:
            return render_template('reset_password.html', token=token, message=f'❌ {err}')
        if new_password != confirm:
            return render_template('reset_password.html', token=token, message='❌ Passwords do not match.')
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiration = None
        db.session.commit()
        return render_template('reset_password.html',
                               message='✅ Password reset successfully. You can now log in.')
    return render_template('reset_password.html', token=token)


# ─── CHALLENGES ────────────────────────────────────────────────────────────────
@main.route('/challenges')
@login_required
def challenges():
    user = User.query.get(session['user_id'])
    all_challenges = Challenge.query.all()
    completed = {s.challenge_id for s in Score.query.filter_by(user_id=user.id).all()}
    return render_template('challenges.html', challenges=all_challenges,
                           completed=completed, user=user)


@main.route('/validate', methods=['POST'])
@login_required
def validate_command():
    try:
        user_id = session['user_id']
        data = request.get_json()
        command = sanitise_cli_input(data.get('command', ''))
        challenge_id = data.get('challenge_id', '')
        if not challenge_id:
            return jsonify({'message': '❌ No challenge selected.'}), 400
        try:
            challenge_id = int(challenge_id)
        except ValueError:
            return jsonify({'message': '❌ Invalid challenge ID.'}), 400
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return jsonify({'message': '❌ Challenge not found.'}), 404
        if command.lower().startswith(challenge.solution.strip().lower()):
            existing = Score.query.filter_by(user_id=user_id, challenge_id=challenge.id).first()
            if not existing:
                score = Score(user_id=user_id, challenge_id=challenge.id,
                              score=challenge.points, completed_at=datetime.now())
                db.session.add(score)
                db.session.commit()
                check_and_award_badges(user_id)
                total = db.session.query(func.sum(Score.score)).filter_by(user_id=user_id).scalar() or 0
                return jsonify({'message': f"✅ Correct! '{challenge.name}' completed! +{challenge.points} pts",
                                'total_score': total})
            else:
                return jsonify({'message': 'ℹ️ You have already completed this challenge.'})
        else:
            links = {
                'Create a VPC': 'https://docs.aws.amazon.com/cli/latest/reference/ec2/create-vpc.html',
                'Create an S3 Bucket': 'https://docs.aws.amazon.com/cli/latest/reference/s3api/create-bucket.html',
                'Create an RDS Instance': 'https://docs.aws.amazon.com/cli/latest/reference/rds/create-db-instance.html',
                'Create a Security Group': 'https://docs.aws.amazon.com/cli/latest/reference/ec2/create-security-group.html',
                'Create an IAM User': 'https://docs.aws.amazon.com/cli/latest/reference/iam/create-user.html',
                'Launch an EC2 instance': 'https://docs.aws.amazon.com/cli/latest/reference/ec2/run-instances.html',
            }
            return jsonify({'message': (
                f"❌ Incorrect command for '{challenge.name}'.\n"
                f"📖 Docs: {links.get(challenge.name, 'https://aws.amazon.com/cli/')}"
            )})
    except Exception as e:
        return jsonify({'message': f'❌ An error occurred: {str(e)}'}), 500


# ─── MISC ──────────────────────────────────────────────────────────────────────
@main.route('/labs')
@login_required
def labs():
    user = User.query.get(session['user_id'])
    return render_template('hands_on_labs.html', user=user)


@main.route('/leaderboard')
@login_required
def leaderboard():
    user = User.query.get(session['user_id'])
    data = db.session.query(
        User.username,
        func.sum(Score.score).label('total_score')
    ).join(Score, User.id == Score.user_id)\
     .group_by(User.username)\
     .order_by(func.sum(Score.score).desc())\
     .limit(10).all()
    ranked = list(enumerate(data, 1))
    return render_template('leaderboard.html', leaderboard=ranked, user=user)


@main.route('/user_info')
@login_required
def user_info():
    user = User.query.get(session['user_id'])
    total = db.session.query(func.sum(Score.score)).filter_by(user_id=user.id).scalar() or 0
    return jsonify({'username': user.username, 'total_score': total})


@main.route('/start-lab-session')
@login_required
def start_lab_session():
    try:
        aws_session = boto3.Session()
        sts = aws_session.client('sts')
        response = sts.assume_role(
            RoleArn='arn:aws:iam::988176743547:role/SandboxUserRole',
            RoleSessionName=f'user-{session["user_id"]}',
            DurationSeconds=900
        )
        creds = response['Credentials']
        session_json = json.dumps({
            'sessionId': creds['AccessKeyId'],
            'sessionKey': creds['SecretAccessKey'],
            'sessionToken': creds['SessionToken']
        })
        token_resp = requests.get('https://signin.aws.amazon.com/federation',
                                  params={'Action': 'getSigninToken', 'Session': session_json})
        signin_token = token_resp.json().get('SigninToken')
        if not signin_token:
            return jsonify({'error': 'Failed to generate AWS sign-in token'}), 500
        console_url = (
            f'https://signin.aws.amazon.com/federation?Action=login'
            f'&Issuer=AWSCLI-LearningPlatform'
            f'&Destination=https%3A%2F%2Fconsole.aws.amazon.com%2F'
            f'&SigninToken={signin_token}'
        )
        return redirect(console_url)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main.route('/health')
def health():
    return 'OK', 200
