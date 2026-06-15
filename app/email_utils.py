from flask_mail import Message
from flask import render_template
from app import mail
import os


def send_welcome_email(user):
    """Send welcome email to newly registered user."""
    signature = """
    <div style="font-family:Arial,sans-serif;font-size:12px;color:#666;
                border-top:1px solid #e0e0e0;padding-top:10px;margin-top:20px;">
        <p>Best regards,<br>
        Devon Adkins<br>
        <strong>AWS Learning Platform</strong><br>
        <a href="https://awslearningplatform.click">awslearningplatform.click</a><br>
        devon@awslearningplatform.click</p>
    </div>
    """
    try:
        msg = Message(
            subject="Welcome to the AWS Learning Platform!",
            sender=("Devon Adkins via AWS Learning Platform",
                    "no-reply@awslearningplatform.click"),
            recipients=[user.email]
        )
        msg.body = f"""
Hello {user.username}!

Welcome to the AWS CLI Learning Platform!

Your account has been successfully created.

Username: {user.username}

Please log in and start your AWS learning journey at:
https://awslearningplatform.click

If you have any issues, contact us at:
devon@awslearningplatform.click

Happy Learning!
AWS Learning Platform Team
        """
        msg.html = render_template('welcome_email.html', user=user) + signature

        aws_img = os.path.join(os.path.dirname(__file__), 'static', 'aws.png')
        if os.path.exists(aws_img):
            with open(aws_img, 'rb') as f:
                msg.attach("cloudlearning", "image/png", f.read(), "aws.png")

        mail.send(msg)
        print(f"[Email] Welcome email sent to {user.email}")
        return True
    except Exception as e:
        print(f"[Email] Failed to send welcome email: {e}")
        return False


def send_badge_email(user, badge):
    """Send badge unlock notification email."""
    try:
        msg = Message(
            subject=f"Congratulations! You've Unlocked the {badge.name} Badge!",
            sender=("Devon Adkins via AWS CLI Learning Platform",
                    "no-reply@awslearningplatform.click"),
            recipients=[user.email]
        )
        msg.body = f"""
Hello {user.username}!

Congratulations! You've earned the {badge.name} badge!

{badge.description}

Keep going - more badges and challenges await you at:
https://awslearningplatform.click

AWS Learning Platform Team
        """
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
            <h1 style="color:#FF9900;text-align:center;">
                {badge.icon or '🏆'} {badge.name} Unlocked! {badge.icon or '🏆'}
            </h1>
            <p style="text-align:center;font-size:18px;">
                <strong>Congratulations</strong>, {user.username}!
            </p>
            <p style="text-align:center;color:#555;">
                You've earned the prestigious <strong>{badge.name}</strong> by mastering AWS CLI challenges!
            </p>
            <p>{badge.description}</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="https://awslearningplatform.click"
                   style="background:#FF9900;color:#000;padding:12px 30px;
                          border-radius:8px;text-decoration:none;font-weight:bold;">
                    Continue Learning
                </a>
            </div>
        </div>
        """

        aws_img = os.path.join(os.path.dirname(__file__), 'static', 'badge.png')
        if os.path.exists(aws_img):
            with open(aws_img, 'rb') as f:
                msg.attach("badge", "image/png", f.read(), "badge.png")

        mail.send(msg)
        print(f"[Email] Badge email sent to {user.email} for badge: {badge.name}")
        return True
    except Exception as e:
        print(f"[Email] Failed to send badge email: {e}")
        return False
