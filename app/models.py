from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from sqlalchemy import func, CheckConstraint, Index
from sqlalchemy.event import listens_for

class User(db.Model):
    """User model for storing user-related data."""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=True, unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    scores = db.relationship('Score', back_populates='user',
                           cascade='all, delete-orphan',
                           lazy='dynamic')

    def __init__(self, username, password, email=None):
        """Initialize a new user instance."""
        self.username = username
        self.email = email
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

class Challenge(db.Model):
    """Challenge model for storing challenge-related data."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    solution = db.Column(db.String(255), nullable=False)
    
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
    """Initialize default challenges if they don't exist."""
    existing_challenges = {challenge.name for challenge in Challenge.query.all()}
    initial_challenges = [
        Challenge(
            name='Create a VPC',
            description='Use the AWS CLI to create a new VPC.',
            solution='aws ec2 create-vpc'
        ) if 'Create a VPC' not in existing_challenges else None,
        Challenge(
            name='Create an RDS Instance',
            description='Use the AWS CLI to create an RDS instance.',
            solution='aws rds create-db-instance'
        ) if 'Create an RDS Instance' not in existing_challenges else None,
        Challenge(
            name='Create a Security Group',
            description='Use the AWS CLI to create a security group.',
            solution='aws ec2 create-security-group'
        ) if 'Create a Security Group' not in existing_challenges else None,
        Challenge(
            name='Create an IAM User',
            description='Use the AWS CLI to create a new IAM user.',
            solution='aws iam create-user --user-name'
        ) if 'Create an IAM User' not in existing_challenges else None,
        Challenge(
            name='Launch an EC2 instance',
            description='Use the AWS CLI to launch an EC2 instance.',
            solution='aws ec2 run-instances'
        ) if 'Launch an EC2 instance' not in existing_challenges else None,
        Challenge(
            name='Create an S3 Bucket',
            description='Use the AWS CLI to Create an S3 Bucket.',
            solution='aws s3 mb'
        ) if 'Create an S3 Bucket' not in existing_challenges else None
    ]
    
    # Filter out None values (already existing challenges)
    initial_challenges = [challenge for challenge in initial_challenges if challenge]
    
    if initial_challenges:
        db.session.add_all(initial_challenges)
        db.session.commit()
        print("Updated challenges in the database.")
