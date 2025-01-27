from flask import Flask
from flask_mail import Mail
from models import DynamoDBManager, initialize_challenges

# Initialize Mail extension
mail = Mail()

def create_app():
    app = Flask(__name__, static_folder='static')

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

    # Initialize Mail
    mail.init_app(app)

    # Initialize DynamoDB and set up tables
    dynamo_manager = DynamoDBManager()
    dynamo_manager.create_tables()
    initialize_challenges()

    # Import and register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app
