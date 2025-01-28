from datetime import datetime, timedelta
from app import db  # Import `db` directly from `app` to avoid creating a new instance
from sqlalchemy import func

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_reset_token(self, token):
        self.reset_token = token
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)

    def is_reset_token_valid(self):
        return self.reset_token_expiration and datetime.utcnow() < self.reset_token_expiration

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    solution = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=10)  # Add points field

    def __repr__(self):
        return f'<Challenge {self.name}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, server_default=db.func.now())

    # Add explicit relationship with backref to access username
    user = db.relationship('User', backref=db.backref('scores', lazy=True))
    challenge = db.relationship('Challenge', backref=db.backref('scores', lazy=True))

    def __repr__(self):
        return f'<Score User:{self.user_id}, Challenge:{self.challenge_id}, Score:{self.score}>'

def initialize_challenges():
    existing_challenges = {challenge.name for challenge in Challenge.query.all()}
    initial_challenges = [
        Challenge(
            name='Create a VPC',
            description='Use the AWS CLI to create a new VPC.',
            solution='aws ec2 create-vpc' #--cidr-block 10.0.0.0/16 --tag-specifications ResourceType=vpc,Tags=[{Key=Name,Value=MyVPC}]'
        ) if 'Create a VPC' not in existing_challenges else None,
        Challenge(
            name='Create an RDS Instance',
            description='Use the AWS CLI to create an RDS instance.',
            solution='aws rds create-db-instance' #--db-instance-identifier mydbinstance --allocated-storage 20 --db-instance-class db.t2.micro --engine mysql --master-username admin --master-user-password password123'
        ) if 'Create an RDS Instance' not in existing_challenges else None,
        Challenge(
            name='Create a Security Group',
            description='Use the AWS CLI to create a security group.',
            solution='aws ec2 create-security-group' #--group-name MySecurityGroup --description "Security group for demo purposes" --vpc-id vpc-12345678'
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