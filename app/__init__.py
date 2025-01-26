from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import secrets

# Define the global `db` instance
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Set the secret key
    # For development: Use a static key
    # For production: Use a random secure key or an environment variable
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')  # Replace 'dev-secret-key' in production

    # Initialize extensions
    db.init_app(app)

    # Import and register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app
