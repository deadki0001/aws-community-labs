import os
from app import create_app
from app.models import initialize_challenges, User

# Set environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

app = create_app()

with app.app_context():
    try:
        initialize_challenges()  # Remove db parameter
        print("Challenges initialized successfully.")

        user_test = User.get_by_username("test_user")
        if user_test:
            print(f"Test user exists: {user_test.username}")  # Changed from dictionary to object access
        else:
            print("No test user found in database.")

    except Exception as e:
        print(f"An error occurred while initializing database: {e}")

if __name__ == "__main__":
    app.run(debug=True)
