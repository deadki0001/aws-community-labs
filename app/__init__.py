import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import timedelta

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__, static_folder='static')

    # Ensure instance folder exists before defining the database path
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Define the correct database path inside the instance folder
    db_path = os.path.join(app.instance_path, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Set the secret key
    app.config['SECRET_KEY'] = 'dev-secret-key'

    # Session configuration
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    

    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.zoho.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_DEBUG'] = True
    app.config['MAIL_USERNAME'] = "no-reply@deadkithedeveloper.click"
    app.config['MAIL_PASSWORD'] = "Awsapp123!@#!"
    app.config['MAIL_DEFAULT_SENDER'] = "no-reply@deadkithedeveloper.click"

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Import and register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app
