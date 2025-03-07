from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from sqlalchemy import func, CheckConstraint, Index
from sqlalchemy.event import listens_for



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)  # ✅ Use `password_hash` instead of `password`
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    created_at = db.Column(db.DateTime, server_default=db.func.now())
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
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

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
            if not user.password_hash.startswith('pbkdf2:sha256'):  # Check if already hashed
                user.password_hash = generate_password_hash(user.password_hash)
        db.session.commit()
        print("Updated all passwords to hashed format.")

    @classmethod
    def get_by_username(cls, username):
        """Retrieve user by username (case insensitive)."""
        return cls.query.filter(func.lower(cls.username) == username.lower()).first()

    
class Challenge(db.Model):
    __tablename__ = 'challenge'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    solution = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=10)
    
    # Relationships
    scores = db.relationship('Score', back_populates='challenge',
                           cascade='all, delete-orphan',
                           lazy='dynamic')

    def __repr__(self):
        return f'<Challenge {self.name}>'


class Score(db.Model):
    __tablename__ = 'score'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='scores')
    challenge = db.relationship('Challenge', back_populates='scores')

    # Constraints
    __table_args__ = (
        CheckConstraint('score >= 0', name='check_score_positive'),
        Index('idx_user_challenge', 'user_id', 'challenge_id', unique=True)
    )

    def __repr__(self):
        return f'<Score User:{self.user_id}, Challenge:{self.challenge_id}, Score:{self.score}>'

@listens_for(User, 'before_insert')
def hash_password_if_needed(mapper, connection, target):
    """Ensure password is hashed before inserting new user."""
    if target.password and not target.password.startswith('pbkdf2:sha256'):
        target.password = generate_password_hash(target.password)

def initialize_challenges():
    """Initialize challenges if they don't exist"""
    try:
        existing_challenges = {challenge.name for challenge in Challenge.query.all()}
        
        challenges_to_add = [
            {
                'name': 'Create a VPC',
                'description': 'Use the AWS CLI to create a new VPC.',
                'solution': 'aws ec2 create-vpc'
            },
            {
                'name': 'Create an RDS Instance',
                'description': 'Use the AWS CLI to create an RDS instance.',
                'solution': 'aws rds create-db-instance'
            },
            {
                'name': 'Create a Security Group',
                'description': 'Use the AWS CLI to create a security group.',
                'solution': 'aws ec2 create-security-group'
            },
            {
                'name': 'Create an IAM User',
                'description': 'Use the AWS CLI to create a new IAM user.',
                'solution': 'aws iam create-user --user-name'
            },
            {
                'name': 'Launch an EC2 instance',
                'description': 'Use the AWS CLI to launch an EC2 instance.',
                'solution': 'aws ec2 run-instances'
            },
            {
                'name': 'Create an S3 Bucket',
                'description': 'Use the AWS CLI to Create an S3 Bucket.',
                'solution': 'aws s3 mb'
            }
        ]
        
        for challenge_data in challenges_to_add:
            if challenge_data['name'] not in existing_challenges:
                new_challenge = Challenge(**challenge_data)
                db.session.add(new_challenge)
        
        db.session.commit()
        print("Successfully initialized challenges")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing challenges: {e}")