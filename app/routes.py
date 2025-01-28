from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Challenge, Score, db
import os
import secrets
from app.email_utils import EmailService
from datetime import datetime
from flask_mail import Message
from app import mail

main = Blueprint('main', __name__)

# Route for the homepage
@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.filter_by(username=session['user_id']).first()
        if user:
            challenges = Challenge.get_all()
            return render_template('index.html', challenges=challenges, username=user.username)
        else:
            session.pop('user_id', None)
            return redirect(url_for('main.signup'))
    return redirect(url_for('main.signup'))

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', message="❌ Username already exists.")
        
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', 
                                message="❌ Email already registered. Click 'Forgot Password' to recover your account.",
                                show_forgot_password=True)

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)  # Using the password hashing method from User model
        
        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = username
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            print(f"Error saving user: {e}")
            return render_template('signup.html', message="❌ Registration failed. Please try again.")

    return render_template('signup.html')

# Leaderboard Route
def leaderboard():
    try:
        # Get all scores grouped by user with total score
        leaderboard_data = db.session.query(
            User.username,
            db.func.sum(Score.score).label('total_score')
        ).join(Score).group_by(User.username).order_by(
            db.func.sum(Score.score).desc()
        ).all()

        # Format the data with rankings
        leaderboard_with_rank = [
            {
                'rank': rank + 1,
                'username': entry[0],
                'total_score': int(entry[1])
            }
            for rank, entry in enumerate(leaderboard_data)
        ]

        return render_template('leaderboard.html', leaderboard=leaderboard_with_rank)
    except Exception as e:
        print(f"Error retrieving leaderboard: {e}")
        return render_template('leaderboard.html', leaderboard=[], error="Error loading leaderboard.")

@main.route('/user_info')
def user_info():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        # Get user from DynamoDB using the username stored in session
        user = User.get_by_username(session['user_id'])
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get scores for the user from DynamoDB
        scores_table = dynamodb.Table('Scores')
        response = scores_table.scan(
            FilterExpression=Attr('user_id').eq(session['user_id'])
        )
        
        # Calculate total score
        total_score = sum(int(score['score']) for score in response.get('Items', []))
        
        return jsonify({
            "username": user['username'],
            "total_score": total_score
        })
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return jsonify({"error": "Failed to fetch user information"}), 500

@main.route('/user_info')
def user_info():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        user = User.query.filter_by(username=session['user_id']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Calculate total score
        total_score = db.session.query(db.func.sum(Score.score)).filter_by(user_id=user.id).scalar() or 0
        
        return jsonify({
            "username": user.username,
            "total_score": total_score
        })
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return jsonify({"error": "Failed to fetch user information"}), 500

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
            user.reset_token = reset_token
            user.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
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
            
            msg = Message(
                subject="Password Reset Instructions - AWS CLI Learning Platform",
                recipients=[user.email]
            )
            
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

        user = User.query.filter_by(reset_token=token).first()
        if user and user.reset_token_expiration > datetime.utcnow():
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()
            return render_template('reset_password.html', message='Password reset successful. You can now log in.')
        else:
            return render_template('reset_password.html', message='Invalid or expired reset token.')

    return render_template('reset_password.html')
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):  # Using the password check method from User model
            session['user_id'] = username
            return redirect(url_for('main.index'))

        return render_template('login.html', message="❌ Invalid username or password.")

    return render_template('login.html')

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
        challenge_id = data.get('challenge_id', '0')

        print(f"Validating command for User ID: {user_id}, Challenge ID: {challenge_id}, Command: {command}")

        # Get challenge from database
        current_challenge = Challenge.query.get(challenge_id)

        if current_challenge:
            # Check if command is valid
            is_valid_command = False
            if current_challenge.name == 'Create an IAM User':
                is_valid_command = (
                    command.lower().startswith('aws iam create-user --user-name') and
                    len(command.split()) > 4
                )
            else:
                is_valid_command = command.lower().startswith(current_challenge.solution.strip().lower())

            if is_valid_command:
                # Check if user has already completed this challenge
                user = User.query.filter_by(username=user_id).first()
                existing_score = Score.query.filter_by(
                    user_id=user.id,
                    challenge_id=challenge_id
                ).first()

                if not existing_score:
                    # Add new score
                    new_score = Score(
                        user_id=user.id,
                        challenge_id=challenge_id,
                        score=10,
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(new_score)
                    db.session.commit()

                    # Calculate total score
                    total_score = db.session.query(db.func.sum(Score.score)).filter_by(user_id=user.id).scalar() or 0

                    # Check for badges
                    cloud_warrior_achieved = total_score >= 10 and total_score < 50
                    cloud_sorcerer_achieved = total_score >= 50

                    # Send badge emails if achieved
                    if cloud_warrior_achieved:
                        send_cloud_warrior_badge(user)

                    if cloud_sorcerer_achieved:
                        send_cloud_sorcerer_badge(user)

                    return jsonify({
                        "message": f"✅ Correct! Challenge '{current_challenge.name}' completed!",
                        "total_score": total_score,
                        "cloud_warrior": cloud_warrior_achieved,
                        "cloud_sorcerer": cloud_sorcerer_achieved
                    })
                else:
                    return jsonify({"message": "\nYou've already completed this challenge."})

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
                f"Please refer to the AWS documentation here:\n"
                f"📖 AWS CLI Guide: {links.get(current_challenge.name, 'https://aws.amazon.com/cli/')}\n"
                f"🎥 Video Tutorial: {videos.get(current_challenge.name, 'https://www.youtube.com')}"
            )

            return jsonify({"message": incorrect_message}), 200

        return jsonify({"message": "❌ Challenge not found."}), 404

    except Exception as e:
        print(f"Error validating command: {e}")
        return jsonify({"message": f"❌ An error occurred: {str(e)}"}), 500

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
    
