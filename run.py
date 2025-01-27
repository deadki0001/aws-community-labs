import os
from app import create_app
from app.models import initialize_challenges, User

# Set environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'  # Enable debug mode

# Create the Flask app instance
app = create_app()

# Initialize DynamoDB and seed initial data
with app.app_context():  # Ensure app context is active
    try:
        # Seed initial challenges in the DynamoDB table
        initialize_challenges()
        print("Challenges initialized successfully.")

        # Debugging: Check for existing users
        user_test = User.get_by_username("test_user")  # Replace "test_user" with a sample username to check
        if user_test:
            print(f"Test user exists: {user_test['username']}")
        else:
            print("No test user found in DynamoDB.")

    except Exception as e:
        print(f"An error occurred while initializing DynamoDB: {e}")

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
