from datetime import datetime, timedelta
from app import db  # Import `db` directly from `app` to avoid creating a new instance

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # New columns for password reset
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

    def __repr__(self):
        return f'<Challenge {self.name}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('scores', lazy=True))
    challenge = db.relationship('Challenge', backref=db.backref('scores', lazy=True))

    def __repr__(self):
        return f'<Score User:{self.user_id}, Challenge:{self.challenge_id}, Score:{self.score}>'

# Initialize challenges if needed
def initialize_challenges():
    # This function assumes the app context is already active
    if Challenge.query.count() == 0:
        initial_challenges = [
            Challenge(name='Launch an EC2 instance', description='Use the AWS CLI to launch an EC2 instance.', solution='aws ec2 run-instances'),
            Challenge(name='List S3 buckets', description='List all S3 buckets in your account.', solution='aws s3 ls'),
        ]
        db.session.add_all(initial_challenges)
        db.session.commit()
        print("Initialized database with challenges.")
