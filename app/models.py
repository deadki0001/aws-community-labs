from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from sqlalchemy import func, CheckConstraint, Index
from sqlalchemy.event import listens_for



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    password = db.Column(db.String(255), nullable=False)  # Stores hashed password
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    # Relationships
    scores = db.relationship('Score', back_populates='user',
                             cascade='all, delete-orphan',
                             lazy='dynamic')

    def __init__(self, username, email, password=None):
        """Initialize a new user instance with a hashed password."""
        self.username = username
        self.email = email
        if password:  # Ensure password is hashed before storing
            self.set_password(password)

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hashed password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_reset_token(self, token):
        """Set password reset token with 1-hour expiration."""
        self.reset_token = token
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)

    def is_reset_token_valid(self):
        """Check if reset token is valid and not expired."""
        return (self.reset_token_expiration and 
                datetime.utcnow() < self.reset_token_expiration)

    def get_total_score(self):
        """Calculate total score for the user."""
        return db.session.query(func.sum(Score.score))\
            .filter_by(user_id=self.id)\
            .scalar() or 0

    def get_completed_challenges(self):
        """Get list of completed challenges for the user."""
        return db.session.query(Challenge)\
            .join(Score)\
            .filter(Score.user_id == self.id)\
            .all()

    @staticmethod
    def update_unhashed_passwords():
        """Update any existing users with unhashed passwords."""
        users = User.query.all()
        for user in users:
            if not user.password.startswith('pbkdf2:sha256'):  # Check if already hashed
                user.password = generate_password_hash(user.password)
        db.session.commit()
        print("Updated all passwords to hashed format.")

    @classmethod
    def get_by_username(cls, username):
        """Retrieve user by username (case insensitive)."""
        return cls.query.filter(func.lower(cls.username) == username.lower()).first()

    
class Challenge(db.Model):
    """Challenge model for storing challenge-related data."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    solution = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=0)
    
    # Relationships
    scores = db.relationship('Score', back_populates='challenge',
                           cascade='all, delete-orphan',
                           lazy='dynamic')

    def __repr__(self):
        return f'<Challenge {self.name}>'

class Score(db.Model):
    """Score model for tracking user progress on challenges."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    user = db.relationship('User', back_populates='scores')
    challenge = db.relationship('Challenge', back_populates='scores')

    # Constraints
    __table_args__ = (
        CheckConstraint('score >= 0', name='check_score_positive'),
    )

    def __repr__(self):
        return f'<Score User:{self.user_id}, Challenge:{self.challenge_id}, Score:{self.score}>'

def initialize_challenges():
    """Ensure all challenges exist in the database."""
    existing_challenges = {challenge.name for challenge in Challenge.query.all()}

    initial_challenges = [
        Challenge(
            id=str(uuid.uuid4()),  # Generate valid UUID
            name="Create a VPC",
            description="Use the AWS CLI to create a VPC.",
            solution="aws ec2 create-vpc"
        ) if "Create a VPC" not in existing_challenges else None,

        Challenge(
            id=str(uuid.uuid4()),
            name="Create an S3 Bucket",
            description="Use the AWS CLI to create an S3 bucket.",
            solution="aws s3 mb"
        ) if "Create an S3 Bucket" not in existing_challenges else None,

        Challenge(
            id=str(uuid.uuid4()),
            name="Create a Security Group",
            description="Use the AWS CLI to create a security group.",
            solution="aws ec2 create-security-group"
        ) if "Create a Security Group" not in existing_challenges else None,

        Challenge(
            id=str(uuid.uuid4()),
            name="Launch an EC2 instance",
            description="Use the AWS CLI to launch an EC2 instance.",
            solution="aws ec2 run-instances"
        ) if "Launch an EC2 instance" not in existing_challenges else None
    ]

    initial_challenges = [c for c in initial_challenges if c]

    if initial_challenges:
        db.session.add_all(initial_challenges)
        db.session.commit()
        print("Challenges added successfully.")

        app = create_app() 
        
        with app.app_context():
            from app.models import initialize_challenges
            initialize_challenges()  # ✅ Now runs inside the Flask app context