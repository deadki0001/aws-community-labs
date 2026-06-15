"""
Run once after deployment to create the admin account.
Usage: flask shell < seed_db.py
  OR:  python seed_db.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Drop everything and rebuild fresh (Option A)
    db.drop_all()
    db.create_all()

    from app.models import initialize_challenges, initialize_badges
    from app.models_learning import seed_learning_paths, seed_aws_associate_paths
    initialize_challenges()
    initialize_badges()
    seed_learning_paths()
    seed_aws_associate_paths()

    # Create admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@awslearningplatform.click',
                     role='admin', is_active=True, show_wizard=False)
        admin.set_password('Admin@2026!')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created — username: admin / password: Admin@2026!")
    else:
        print("ℹ️  Admin user already exists.")

    print(f"✅ Database seeded. Users: {User.query.count()}")
