from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.models import User, Challenge, Score
from app import db
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
        challenges = Challenge.query.all()
        return render_template('index.html', challenges=challenges, message="Welcome to AWS CLI Learning Platform!")
    return redirect(url_for('main.signup'))

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
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            return render_template('signup.html', 
                                   message=f"❌ Registration failed: {str(e)}")

    return render_template('signup.html')

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
        if user and user.password == password:
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
        challenge_id = int(data.get('challenge_id', 0))

        print(f"Validating command for User ID: {user_id}, Challenge ID: {challenge_id}, Command: {command}")

        current_challenge = Challenge.query.get(challenge_id)

        if current_challenge:
            if command.lower() == current_challenge.solution.strip().lower():
                score = Score(
                    user_id=user_id,
                    challenge_id=current_challenge.id,
                    score=10,
                    completed_at=datetime.now()
                )
                db.session.add(score)
                db.session.commit()

                return jsonify({"message": f"✅ Correct! Challenge '{current_challenge.name}' completed!"})
            
            message = (
                "❌ Incorrect command for challenge: 'Launch an EC2 instance'\n"
                "Please refer to the AWS documentation here:\n"
                "📖 AWS CLI Guide: https://docs.aws.amazon.com/cli/v1/userguide/cli-services-ec2-instances.html\n"
                "Additionally, you can watch this video for a demo:\n"
                "🎥 YouTube - Stephen Maarek: https://www.youtube.com/watch?v=crNyDkR3ulU"
            )
            return jsonify({"message": message})

        print(f"Challenge with ID {challenge_id} not found.")
        return jsonify({"message": "❌ Challenge not found."})
    except Exception as e:
        print(f"Error processing validation: {e}")
        return jsonify({"message": f"❌ An error occurred: {str(e)}"}), 500

# Route for fetching user info
@main.route('/user_info')
def user_info():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        total_score = db.session.query(db.func.sum(Score.score)).filter_by(user_id=user_id).scalar() or 0

        return jsonify({
            "username": user.username,
            "total_score": total_score
        })
    return jsonify({"message": "User not logged in"}), 401

# Route for the leaderboard
@main.route('/leaderboard')
def leaderboard():
    scores = User.query.join(Score)\
        .with_entities(User.username, db.func.sum(Score.score).label('total_score'))\
        .group_by(User.id).order_by(db.func.sum(Score.score).desc()).all()

    return render_template('leaderboard.html', scores=scores, enumerate=enumerate)