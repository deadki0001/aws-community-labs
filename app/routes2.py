from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.models import User, Challenge, Score
from app import db
import os
import uuid
import secrets
from app.email_utils import EmailService
from datetime import datetime
from flask_mail import Message
from app import mail
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

main = Blueprint('main', __name__)

# Route for the homepage
@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:  # Ensure user exists in the database
            challenges = Challenge.query.all()
            return render_template('challenges.html', challenges=challenges, message="Welcome to AWS CLI Learning Platform!", username=user.username)
        else:
            # If the user ID is invalid, clear the session and redirect to signup
            session.pop('user_id', None)
            return redirect(url_for('main.signup'))
    return redirect(url_for('main.signup'))


# Route for the sign-up page
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check for existing username or email
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', message="❌ Username already exists.")
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', 
                                   message="❌ Email already registered. Click 'Forgot Password' to recover your account.", 
                                   show_forgot_password=True)

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)  # Hash the password

        try:
            db.session.add(new_user)
            db.session.commit()
            # Send welcome email (optional)
            EmailService.send_welcome_email(new_user, password)
            session['user_id'] = new_user.id
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            return render_template('signup.html', 
                                   message=f"❌ Registration failed: {str(e)}")

    return render_template('signup.html')

# Leaderboard Route
@main.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    # Get total scores per user, ordered by total score descending
    leaderboard_data = db.session.query(
        User.username, 
        func.sum(Score.score).label('total_score')
    ).join(Score, User.id == Score.user_id)\
     .group_by(User.username)\
     .order_by(func.sum(Score.score).desc())\
     .limit(10)\
     .all()

    # Convert to list with enumeration
    leaderboard_with_rank = list(enumerate(leaderboard_data, 1))

    return render_template('leaderboard.html', leaderboard=leaderboard_with_rank)


@main.route('/user_info')
def user_info():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user = User.query.get(session['user_id'])
    total_score = db.session.query(func.sum(Score.score)).filter_by(user_id=user.id).scalar() or 0
    
    return jsonify({
        "username": user.username,
        "total_score": total_score
    })

# Update the initialization function to track any potential duplicates
def initialize_challenges():
    existing_challenges = {challenge.name for challenge in Challenge.query.all()}
    initial_challenges = [
        Challenge(
            name='Create a VPC',
            description='Use the AWS CLI to create a new VPC.',
            solution='aws ec2 create-vpc --cidr-block 10.0.0.0/16'
        ) if 'Create a VPC' not in existing_challenges else None,
        Challenge(
            name='Create an RDS Instance',
            description='Use the AWS CLI to create an RDS instance.',
            solution='aws rds create-db-instance --db-instance-identifier <identifier> --allocated-storage 20 --db-instance-class db.t2.micro --engine mysql --master-username admin --master-user-password password'
        ) if 'Create an RDS Instance' not in existing_challenges else None,
        Challenge(
            name='Create a Security Group',
            description='Use the AWS CLI to create a security group.',
            solution='aws ec2 create-security-group --group-name <group-name> --description "Security group for demo purposes"'
        ) if 'Create a Security Group' not in existing_challenges else None,
        Challenge(
            name='Create an IAM User',
            description='Use the AWS CLI to create a new IAM user.',
            solution='aws iam create-user --user-name <user-name>'
        ) if 'Create an IAM User' not in existing_challenges else None,
    ]
    
    # Filter out None values (already existing challenges)
    initial_challenges = [challenge for challenge in initial_challenges if challenge]
    
    if initial_challenges:
        db.session.add_all(initial_challenges)
        db.session.commit()
        print("Updated challenges in the database.")

# Forgot password
@main.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate a secure reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Save the reset token with expiration
            user.set_reset_token(reset_token)
            db.session.commit()
            
            # Construct reset link
            reset_link = url_for('main.reset_password', token=reset_token, _external=True)
            
            # Email signature HTML
            signature = """
            <div style="font-family: Arial, sans-serif; font-size: 12px; color: #666; 
                        border-top: 1px solid #e0e0e0; padding-top: 10px; margin-top: 20px;">
                <p>Best regards,<br>
                Devon Adkins<br>
                <strong>AWS CLI Learning Platform</strong><br>
                <a href="https://deadkithedeveloper.click">deadkithedeveloper.click</a><br>
                📧 devon@deadkithedeveloper.click</p>
            </div>
            """
            
            # Prepare email
            msg = Message(
                subject="Password Reset Instructions - AWS CLI Learning Platform",
                sender=("Devon Adkins via AWS CLI Learning Platform", "no-reply@deadkithedeveloper.click"),
                recipients=[user.email]
            )
            
            # Text body
            msg.body = f"""
            Hello {user.username},
            
            You have requested a password reset for your AWS CLI Learning Platform account.
            
            Please click the link below to reset your password:
            {reset_link}
            
            If you did not request this password reset, please ignore this email.
            
            This link will expire in 1 hour.
            
            Best regards,
            Devon Adkins
            AWS CLI Learning Platform
            https://deadkithedeveloper.click
            """
            
            # HTML body with signature
            msg.html = f"""
            <p>Hello {user.username},</p>
            
            <p>You have requested a password reset for your AWS CLI Learning Platform account.</p>
            
            <p>Please click the link below to reset your password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            
            <p>If you did not request this password reset, please ignore this email.</p>
            
            <p>This link will expire in 1 hour.</p>
            """ + signature
            
            try:
                mail.send(msg)
                return render_template('forgot_password.html', 
                                       message="Password reset instructions sent to your email.")
            except Exception as e:
                print(f"Error sending reset email: {e}")
                return render_template('forgot_password.html', 
                                       message="Failed to send reset instructions. Please try again.")
        else:
            return render_template('forgot_password.html', 
                                   message="No account found with this email.")
    
    return render_template('forgot_password.html')

@main.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            return render_template('reset_password.html', message='Passwords do not match.')

        # Validate the token and find the user
        user = User.query.filter_by(reset_token=token).first()
        if user and user.is_reset_token_valid():
            user.password = new_password
            user.reset_token = None  # Clear the reset token
            user.reset_token_expiration = None
            db.session.commit()
            return render_template('reset_password.html', message='Password reset successful. You can now log in.')
        else:
            return render_template('reset_password.html', message='Invalid or expired reset token.')

    return render_template('reset_password.html')

# Route for the login page
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):  # Use hashed password check
            session['user_id'] = user.id
            return redirect(url_for('main.index'))
        return render_template('login.html', message="❌ Invalid username or password.")

    return render_template('login.html')

# Route for logging out
@main.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.login'))

# Route for validating a challenge command

@main.route('/validate', methods=['POST'])
def validate_command():
    if 'user_id' not in session:
        return jsonify({"message": "❌ You must be logged in to validate commands."}), 401

    try:
        user_id = session['user_id']
        data = request.get_json()
        command = data.get('command', '').strip()
        challenge_id = data.get('challenge_id')

        # Convert challenge_id to int if it's not already
        try:
            challenge_id = int(challenge_id)
        except (ValueError, TypeError):
            return jsonify({"message": "❌ Invalid challenge ID format."}), 400

        print(f"Validating command for User ID: {user_id}, Command: {command}")

        current_challenge = Challenge.query.get(challenge_id)

        if not current_challenge:
            return jsonify({"message": "❌ Challenge not found."}), 404
        # Validate the command
        is_valid_command = command.lower().startswith(current_challenge.solution.strip().lower())
        if is_valid_command:
            # Check if the user has already completed the challenge
            existing_score = Score.query.filter_by(user_id=user_id, challenge_id=current_challenge.id).first()
            if existing_score:
                return jsonify({"message": "✅ You've already completed this challenge."})

            try:
                # Add new score for the challenge
                new_score = Score(
                    id=str(uuid.uuid4()),  # Generate a unique ID for the score entry
                    user_id=user_id,
                    challenge_id=current_challenge.id,
                    score=10,
                    completed_at=datetime.utcnow()
                )
                db.session.add(new_score)
                db.session.commit()

                # Calculate total score
                total_score = db.session.query(db.func.sum(Score.score)).filter_by(user_id=user_id).scalar() or 0

                # Check and send badges if conditions are met
                cloud_warrior_achieved = 10 <= total_score < 50
                cloud_sorcerer_achieved = total_score >= 50

                if cloud_warrior_achieved:
                    send_cloud_warrior_badge(User.query.get(user_id))
                if cloud_sorcerer_achieved:
                    send_cloud_sorcerer_badge(User.query.get(user_id))

                return jsonify({
                    "message": f"✅ Correct! Challenge '{current_challenge.name}' completed!",
                    "total_score": total_score,
                    "cloud_warrior": cloud_warrior_achieved,
                    "cloud_sorcerer": cloud_sorcerer_achieved
                })

            except IntegrityError as e:
                db.session.rollback()
                print(f"Database error during score insertion: {e}")
                return jsonify({"message": "❌ A database error occurred. Please ensure the challenge exists and try again."}), 500

        # Documentation links for incorrect responses
        links = {
            'Create a VPC': "https://docs.aws.amazon.com/cli/latest/reference/ec2/create-vpc.html",
            'Create an S3 Bucket': "https://docs.aws.amazon.com/cli/latest/reference/s3api/create-bucket.html",
            'Create an RDS Instance': "https://docs.aws.amazon.com/cli/latest/reference/rds/create-db-instance.html",
            'Create a Security Group': "https://docs.aws.amazon.com/cli/latest/reference/ec2/create-security-group.html",
            'Create an IAM User': "https://docs.aws.amazon.com/cli/latest/reference/iam/create-user.html",
            'Launch an EC2 instance': "https://docs.aws.amazon.com/cli/latest/reference/ec2/run-instances.html"
        }

        videos = {
            'Create a VPC': "https://www.youtube.com/watch?v=ctwO-CMGkxg",
            'Create an S3 Bucket': "https://www.youtube.com/watch?v=RODg8GWKU2Q",
            'Create an RDS Instance': "https://www.youtube.com/watch?v=QtouOs4tzNk",
            'Create a Security Group': "https://www.youtube.com/watch?v=XXXXX",
            'Create an IAM User': "https://www.youtube.com/watch?v=ZQMpSICUEcw",
            'Launch an EC2 instance': "https://www.youtube.com/watch?v=crNyDkR3ulU"
        }

        incorrect_message = (
            f"❌ Incorrect command for challenge: '{current_challenge.name}'\n"
            f"📖 AWS Documentation: {links.get(current_challenge.name, 'https://aws.amazon.com/cli/')}\n"
            f"🎥 Video Tutorial: {videos.get(current_challenge.name, 'https://www.youtube.com/')}"
        )
        return jsonify({"message": incorrect_message}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"❌ An unexpected error occurred: {str(e)}"}), 500
def send_cloud_warrior_badge(user):
    """
    Send Cloud Warrior badge email
    """
    signature = """
    <div style="font-family: Arial, sans-serif; font-size: 12px; color: #666; 
                border-top: 1px solid #e0e0e0; padding-top: 10px; margin-top: 20px;">
        <p>Best regards,<br>
        Devon Adkins<br>
        <strong>AWS CLI Learning Platform</strong><br>
        <a href="https://deadkithedeveloper.click">deadkithedeveloper.click</a><br>
        📧 devon@deadkithedeveloper.click</p>
    </div>
    """
    
    # Prepare email
    msg = Message(
        subject="🏆 Congratulations! You've Unlocked the Cloud Warrior Badge!",
        sender=("Devon Adkins via AWS CLI Learning Platform", "no-reply@deadkithedeveloper.click"),
        recipients=[user.email]
    )
    
    # Text body
    msg.body = f"""
    Congratulations, {user.username}! 🎉

    You've just earned the prestigious Cloud Warrior Badge! 🛡️

    By completing AWS CLI challenges and accumulating 10 points, 
    you've proven your skills and dedication to cloud technology.

    Keep learning, keep growing!

    Best regards,
    AWS CLI Learning Platform Team
    """
    
    # HTML body with signature and badge
    msg.html = f"""
    <div style="text-align: center; font-family: Arial, sans-serif;">
        <h1>🏆 Cloud Warrior Badge Unlocked! 🏆</h1>
        <p>Congratulations, {user.username}!</p>
        <p>You've earned the prestigious Cloud Warrior Badge by mastering AWS CLI challenges!</p>
        <img src="cid:cloud_warrior_badge" alt="Cloud Warrior Badge" style="max-width: 300px;">
    </div>
    """ + signature

    # Attach badge image
    badge_path = os.path.join(os.path.dirname(__file__), 'static', 'badge.png')
    with open(badge_path, 'rb') as f:
        msg.attach("cloud_warrior_badge", "image/png", f.read(), "Cloud_Warrior_Badge.png")

    try:
        mail.send(msg)
        print(f"Cloud Sorcerer Badge email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Error sending Cloud Sorcerer badge email: {e}")
        return False        

def send_cloud_sorcerer_badge(user):
    """
    Send Cloud Sorcerer badge email
    """
    signature = """
    <div style="font-family: Arial, sans-serif; font-size: 12px; color: #666; 
                border-top: 1px solid #e0e0e0; padding-top: 10px; margin-top: 20px;">
        <p>Best regards,<br>
        Devon Adkins<br>
        <strong>AWS CLI Learning Platform</strong><br>
        <a href="https://deadkithedeveloper.click">deadkithedeveloper.click</a><br>
        📧 devon@deadkithedeveloper.click</p>
    </div>
    """
    
    # Prepare email
    msg = Message(
        subject="🌟 Congratulations! You've Unlocked the Cloud Sorcerer Badge!",
        sender=("Devon Adkins via AWS CLI Learning Platform", "no-reply@deadkithedeveloper.click"),
        recipients=[user.email]
    )
    
    # Text body
    msg.body = f"""
    Congratulations, {user.username}! 🎉

    You've just earned the legendary Cloud Sorcerer Badge! 🌟

    By mastering every AWS CLI challenge and demonstrating unparalleled expertise, 
    you've ascended to the pinnacle of cloud proficiency.

    We are thrilled to have you as part of our elite community of cloud enthusiasts!

    Best regards,
    AWS CLI Learning Platform Team
    """
    
    # HTML body with signature and badge
    msg.html = f"""
    <div style="text-align: center; font-family: Arial, sans-serif;">
        <h1>🌟 Cloud Sorcerer Badge Unlocked! 🌟</h1>
        <p>Congratulations, {user.username}!</p>
        <p>You've reached the summit of AWS CLI mastery and earned the legendary Cloud Sorcerer Badge!</p>
        <img src="cid:cloud_sorcerer_badge" alt="Cloud Sorcerer Badge" style="max-width: 300px;">
    </div>
    """ + signature

    # Attach badge image
    badge_path = os.path.join(os.path.dirname(__file__), 'static', 'magic.png')
    with open(badge_path, 'rb') as f:
        msg.attach("cloud_sorcerer_badge", "image/png", f.read(), "magic.png")

    try:
        mail.send(msg)
        print(f"Cloud Warrior Badge email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Error sending Cloud Warrior badge email: {e}")
        return False
    

