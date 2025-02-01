from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.models import User, Challenge, Score
from app import db
import os
import json
import requests
import secrets
from app.email_utils import EmailService
from datetime import datetime
from flask_mail import Message
from app import mail
from sqlalchemy import func
import boto3

main = Blueprint('main', __name__)

# Route for the homepage
@main.route('/')
def index():
    if 'user_id' not in session:
        print("No user_id in session, redirecting to signup")  # Debug log
        return redirect(url_for('main.signup'))
    
    user = User.query.get(session['user_id'])
    if not user:
        print(f"No user found for id {session['user_id']}, clearing session")  # Debug log
        session.clear()
        return redirect(url_for('main.signup'))
    
    print(f"Rendering landing page for user {user.username}")  # Debug log
    return render_template('landing_page.html')

@main.route('/challenges')
def challenges():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.login'))

    challenges = Challenge.query.all()  # Fetch all challenges from the database
    return render_template('challenges.html', challenges=challenges)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt for user: {username}")  # Debug log
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session.permanent = True  # Make session persistent
            print(f"Login successful for user {username}")  # Debug log
            return redirect(url_for('main.index'))  # Redirects to landing_page.html
        
        print("Login failed: invalid credentials")  # Debug log
        return render_template('login.html', message="❌ Invalid username or password.")

    return render_template('login.html')

@main.route('/labs')
def labs():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.login'))
    
    return render_template('hands_on_labs.html')

# Route for the sign-up page
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', message="❌ Username already exists.")

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', 
                               message="❌ Email already registered. Click 'Forgot Password' to recover your account.", 
                               show_forgot_password=True)

        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        
        try:
            db.session.commit()
            # Send welcome email
            EmailService.send_welcome_email(new_user, password)
            session['user_id'] = new_user.id
            return redirect(url_for('main.index'))  # Redirects to landing_page.html
        except Exception as e:
            db.session.rollback()
            return render_template('signup.html', 
                               message=f"❌ Registration failed: {str(e)}")

    return render_template('signup.html')

# Leaderboard Route - ok
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
            user.password = generate_password_hash(new_password)  # ✅ Hash the password
            user.reset_token = None  # Clear the reset token
            user.reset_token_expiration = None
            db.session.commit()
            return render_template('reset_password.html', message='Password reset successful. You can now log in.')
        else:
            return render_template('reset_password.html', message='Invalid or expired reset token.')

    return render_template('reset_password.html')

# Logout Route
@main.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.login'))

## Starting Lab Sessions

@main.route('/start-lab-session')
def start_lab_session():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))  # Redirect to login if not authenticated
    
    try:
        # Explicitly create a fresh boto3 session
        session = boto3.Session()
        sts = session.client('sts')

        # Assume the SandboxUserRole
        response = sts.assume_role(
            RoleArn="arn:aws:iam::010526269452:role/SandboxUserRole",
            RoleSessionName=f"user-{session['user_id']}",
            Tags=[
                {'Key': 'LabSession', 'Value': 'active'},
                {'Key': 'UserID', 'Value': str(session['user_id'])}
            ],
            DurationSeconds=3600
        )

        # Extract credentials
        credentials = response['Credentials']
        access_key = credentials['AccessKeyId']
        secret_key = credentials['SecretAccessKey']
        session_token = credentials['SessionToken']

        # Set environment variables to ensure the role is used
        boto3.setup_default_session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )

        # Generate sign-in token
        signin_token_url = "https://signin.aws.amazon.com/federation"
        session_json = json.dumps({
            "sessionId": access_key,
            "sessionKey": secret_key,
            "sessionToken": session_token
        })
        
        signin_token_response = requests.get(
            signin_token_url,
            params={
                "Action": "getSigninToken",
                "Session": session_json
            }
        )
        signin_token = signin_token_response.json().get("SigninToken")

        if not signin_token:
            return jsonify({"error": "Failed to generate AWS sign-in token"}), 500

        # Construct AWS Console Login URL
        console_url = f"https://signin.aws.amazon.com/federation?Action=login&Issuer=AWSCLI-LearningPlatform&Destination=https%3A%2F%2Fconsole.aws.amazon.com%2F&SigninToken={signin_token}"

        # Redirect the user to AWS Console
        return redirect(console_url)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Debugging: Print available routes
@main.route('/debug-routes')
def debug_routes():
    routes = [rule.endpoint for rule in main.url_map.iter_rules()]
    return jsonify({"routes": routes})
# Route for validating a challenge command
@main.route('/validate', methods=['POST'])
def validate_command():
    if 'user_id' not in session:
        return jsonify({"message": "❌ You must be logged in to validate commands."}), 401

    try:
        user_id = session['user_id']
        print(f"Session User ID: {user_id}")

        data = request.get_json()
        command = data.get('command', '').strip()
        challenge_id = data.get('challenge_id', '')

        print(f"Received command: '{command}', Challenge ID: '{challenge_id}'")

        # Validate challenge_id
        if not challenge_id:
            return jsonify({"message": "❌ No challenge selected."}), 400

        try:
            challenge_id = int(challenge_id)  # Ensure it's an integer for SQLite
        except ValueError:
            print(f"Invalid challenge_id received: {challenge_id}")
            return jsonify({"message": "❌ Invalid challenge ID format."}), 400

        # Find the challenge in the database
        current_challenge = Challenge.query.get(challenge_id)
        if not current_challenge:
            print(f"Challenge with ID {challenge_id} not found in the database.")
            return jsonify({"message": "❌ Challenge not found."}), 404

        print(f"Current Challenge: {current_challenge.name}")

        # Validate the command for the current challenge
        if command.lower().startswith(current_challenge.solution.strip().lower()):
            # Check if the user already completed this challenge
            existing_score = Score.query.filter_by(
                user_id=user_id,
                challenge_id=current_challenge.id
            ).first()

            if not existing_score:
                # Add a score for the challenge
                score = Score(
                    user_id=user_id,
                    challenge_id=current_challenge.id,
                    score=current_challenge.points,
                    completed_at=datetime.now()
                )
                db.session.add(score)
                db.session.commit()

                # Calculate total score
                total_score = db.session.query(func.sum(Score.score)).filter_by(user_id=user_id).scalar() or 0
                print(f"Total score for user {user_id}: {total_score}")

                # Check badge conditions
                cloud_warrior_achieved = total_score >= 10 and total_score < 20
                cloud_sorcerer_achieved = total_score >= 50

                if cloud_warrior_achieved:
                    print("Cloud Warrior badge conditions met")
                    user = User.query.get(user_id)
                    send_cloud_warrior_badge(user)

                if cloud_sorcerer_achieved:
                    print("Cloud Sorcerer badge conditions met")
                    user = User.query.get(user_id)
                    send_cloud_sorcerer_badge(user)

                return jsonify({
                    "message": f"✅ Correct! Challenge '{current_challenge.name}' completed!",
                    "total_score": total_score,
                    "cloud_warrior": cloud_warrior_achieved
                })
            else:
                return jsonify({"message": "\nYou've already completed this challenge."})
        else:
            # If the command is incorrect, provide specific feedback for the challenge
            links = {
                'Create a VPC': "https://docs.aws.amazon.com/cli/latest/reference/ec2/create-vpc.html",
                'Create an S3 Bucket': "https://docs.aws.amazon.com/cli/latest/reference/s3api/create-bucket.html",
                'Create an RDS Instance': "https://docs.aws.amazon.com/cli/latest/reference/rds/create-db-instance.html",
                'Create a Security Group': "https://docs.aws.amazon.com/cli/latest/reference/ec2/create-security-group.html",
                'Create an IAM User': "https://docs.aws.amazon.com/cli/latest/reference/iam/create-user.html",
                'Launch an EC2 instance': "https://docs.aws.amazon.com/cli/latest/reference/ec2/run-instances.html",
                'AWS CLI Guide': "https://docs.aws.amazon.com/cli/v1/userguide/cli-services-ec2-instances.html"
            }
            videos = {
                'Create a VPC': "https://www.youtube.com/watch?v=ctwO-CMGkxg",
                'Create an S3 Bucket': "https://www.youtube.com/watch?v=RODg8GWKU2Q",
                'Create an RDS Instance': "https://www.youtube.com/watch?v=QtouOs4tzNk",
                'Create a Security Group': "https://www.youtube.com/watch?v=XXXXX",
                'Create an IAM User': "https://www.youtube.com/watch?v=ZQMpSICUEcw",
                'Launch an EC2 instance': "https://www.youtube.com/watch?v=crNyDkR3ulU",
            }           

            return jsonify({
                "message": (
                    f"❌ Incorrect command for challenge: '{current_challenge.name}'\n"
                    f"📖 Refer to the AWS documentation here:\n {links.get(current_challenge.name, 'https://aws.amazon.com/cli/')}\n"
                    f"🎥 Watch this video tutorial:\n {videos.get(current_challenge.name, 'https://www.youtube.com')}"                    
                )
            }), 200
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
    

