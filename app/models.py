from datetime import datetime, timedelta
import boto3
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from . import db 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize MySQL resource

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100))
    reset_token_expiration = db.Column(db.DateTime)
    
    # Relationships
    scores = db.relationship('Score', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password, password)
    
    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()


class Challenge(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    solution = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scores = db.relationship('Score', backref='challenge', lazy='dynamic')
    
    @staticmethod
    def get_all():
        try:
            challenges = Challenge.query.all()
            logger.info(f"Retrieved {len(challenges)} challenges from database")
            return challenges
        except Exception as e:
            logger.error(f"Error retrieving challenges: {str(e)}")
            return []

    @staticmethod
    def get_by_id(challenge_id):
        try:
            challenge = Challenge.query.get(challenge_id)
            logger.info(f"Retrieved challenge with ID {challenge_id}: {challenge is not None}")
            return challenge
        except Exception as e:
            logger.error(f"Error retrieving challenge {challenge_id}: {str(e)}")
            return None

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            logger.info(f"Successfully saved challenge '{self.name}' with ID {self.id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving challenge '{self.name}': {str(e)}")
            return False

class Score(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.String(36), db.ForeignKey('challenge.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

def initialize_challenges():
    challenges = [
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
            'description': 'Use the AWS CLI to create an S3 bucket.',
            'solution': 'aws s3 mb'
        }
    ]

    for challenge_data in challenges:
        # Check if challenge already exists
        existing = Challenge.query.filter_by(name=challenge_data['name']).first()
        if not existing:
            challenge = Challenge(**challenge_data)
            db.session.add(challenge)
    
    try:
        db.session.commit()
        logger.info("Successfully initialized challenges")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing challenges: {str(e)}")

def debug_challenges():
    """Utility function to check the state of challenges in the database"""
    try:
        challenges = Challenge.query.all()
        logger.info("=== Current Challenges in Database ===")
        for challenge in challenges:
            logger.info(f"ID: {challenge.id}")
            logger.info(f"Name: {challenge.name}")
            logger.info(f"Description: {challenge.description}")
            logger.info("---")
        return len(challenges)
    except Exception as e:
        logger.error(f"Error in debug_challenges: {str(e)}")
        return 0
