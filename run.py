import os
from app import create_app, db
from app.models import initialize_challenges, User

# Set environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'  # Enable debug mode

# Create the Flask app instance
app = create_app()

# Initialize database and seed initial data
with app.app_context():  # Ensure app context is active
    try:
        # Create all tables based on models
        db.create_all()
        print("Database tables created successfully.")

        # Seed initial challenges
        initialize_challenges()  # This now executes in the same app context
        print("Challenges initialized.")

        # Debugging: Check for existing users
        user_test = User.query.first()
        if user_test:
            print(f"Test user exists: {user_test.username}")
        else:
            print("No users found in the database.")

    except Exception as e:
        print(f"An error occurred while initializing the database: {e}")

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
