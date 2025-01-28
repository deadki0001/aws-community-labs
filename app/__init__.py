# __init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import os

# Define the global `db` instance
db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Get the absolute path to the application directory
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Configure SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set the secret key
    app.config['SECRET_KEY'] = 'dev-secret-key'

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
    
    with app.app_context():
        # Import models and create tables
        from . import models
        db.create_all()
        
        # Initialize challenges
        models.initialize_challenges()
        
        # Import and register blueprints
        from .routes import main
        app.register_blueprint(main)

    return app