from flask_mail import Message
from flask import url_for, render_template
from app import create_app, mail
from app.models import User
import os

class EmailService:
    @staticmethod
    def send_welcome_email(user, password):
        app = create_app()
        with app.app_context():
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
            
            # Create the email message
            msg = Message(
                subject="Welcome to AWS CLI Learning Platform! 🌟",
                sender=("Devon Adkins via AWS CLI Learning Platform", app.config['MAIL_DEFAULT_SENDER']),
                recipients=[user.email]  # ✅ Corrected
            )
                        
            # Text body
            msg.body = f"""
            Hello {user['username']}! 👋

            🎉 Welcome to the AWS CLI Learning Platform! 🚀

            🔐 Your account has been successfully created. Here are your login details:

            👤 Username: {user['username']}
            🔑 Password: {password}

            📝 Please log in and change your password after your first login.

            🌈 Challenges await you! Start your AWS CLI learning journey now.

            🆘 If you have any issues, contact us at:
            devon@deadkithedeveloper.click

            🏆 Happy Learning!
            AWS CLI Learning Platform Team 💻

            ---
            Best regards,
            Devon Adkins
            AWS CLI Learning Platform
            https://deadkithedeveloper.click
            """
            
            # HTML version with signature
            msg.html = render_template(
                'welcome_email.html',
                user=user,
                password=password
            ) + signature
            
            # Attach an image if required
            aws_learning = os.path.join(os.path.dirname(__file__), 'static', 'aws.png')
            if os.path.exists(aws_learning):
                with open(aws_learning, 'rb') as f:
                    msg.attach("cloudlearning", "image/png", f.read(), "aws.png")    

            try:
                mail.send(msg)
                print(f"Welcome email sent to {user['email']}")
                return True
            except Exception as e:
                print(f"Error sending welcome email: {e}")
                return False
