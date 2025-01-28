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
    
    # Initialize database
    db.init_app(app)
    
    # Create application context and initialize database
    with app.app_context():
        db.create_all()  # Create tables
        
        # Import models here to avoid circular imports
        from app.models import initialize_challenges
        initialize_challenges()  # Initialize challenges after tables are created
    
    # Rest of your configuration...
    return app

# models.py - Add this at the end of your initialize_challenges function
def initialize_challenges():
    try:
        existing_challenges = {challenge.name for challenge in Challenge.query.all()}
        initial_challenges = [
            Challenge(
                name='Create a VPC',
                description='Use the AWS CLI to create a new VPC.',
                solution='aws ec2 create-vpc'
            ) if 'Create a VPC' not in existing_challenges else None,
            # ... rest of your challenges ...
        ]
        
        # Filter out None values (already existing challenges)
        initial_challenges = [c for c in initial_challenges if c]
        
        if initial_challenges:
            db.session.add_all(initial_challenges)
            db.session.commit()
            print("Successfully updated challenges in the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing challenges: {e}")

# routes.py - Update your validate route error handling
@main.route('/validate', methods=['POST'])
def validate_command():
    if 'user_id' not in session:
        return jsonify({"message": "You must be logged in to validate commands."}), 401

    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        challenge_id = data.get('challenge_id')
        
        # Proper error handling for challenge_id
        try:
            challenge_id = int(challenge_id)
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid challenge ID format"}), 400
            
        current_challenge = Challenge.query.get(challenge_id)
        if not current_challenge:
            return jsonify({"message": "Challenge not found"}), 404
            
        # Rest of your validation logic...
        
    except Exception as e:
        db.session.rollback()  # Roll back any failed transactions
        print(f"Error in validate_command: {e}")
        return jsonify({"message": "An error occurred processing your request"}), 500