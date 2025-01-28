from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()

def create_app():
    app = Flask(__name__, static_folder='static')

    # Basic Flask configuration
    app.config['SECRET_KEY'] = 'dev-secret-key'

    # MySQL configuration (use pymysql)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/aws_cli_platform'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL debugging

    # Email configuration (Use environment variable for security)
    app.config['MAIL_SERVER'] = 'smtp.zoho.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_DEBUG'] = True
    app.config['MAIL_USERNAME'] = "no-reply@deadkithedeveloper.click"
    app.config['MAIL_PASSWORD'] = "Awsapp123!@#!"
    app.config['MAIL_DEFAULT_SENDER'] = "no-reply@deadkithedeveloper.click"

    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Import models
    from app.models import User, Challenge, Score, initialize_challenges
    
    # Apply migrations and initialize data
    with app.app_context():
        initialize_challenges()

    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app
