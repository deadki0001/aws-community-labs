from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Define the global `db` instance
db = SQLAlchemy()

# Initialize Mail extension
mail = Mail()

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
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

    # Import and register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app