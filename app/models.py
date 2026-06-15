from datetime import datetime, timedelta
from app import db
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')   # 'user' or 'admin'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime, nullable=True)
    show_wizard = db.Column(db.Boolean, nullable=False, default=True)  # first-login wizard flag
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_reset_token(self, token):
        self.reset_token = token
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)

    def is_reset_token_valid(self):
        return (
            self.reset_token_expiration is not None and
            datetime.utcnow() < self.reset_token_expiration
        )

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


class Challenge(db.Model):
    __tablename__ = 'challenge'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    solution = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=10)

    def __repr__(self):
        return f'<Challenge {self.name}>'


class Score(db.Model):
    __tablename__ = 'score'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id', ondelete='RESTRICT'), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', backref=db.backref('scores', lazy=True, cascade='all, delete-orphan'))
    challenge = db.relationship('Challenge', backref=db.backref('scores', lazy=True))

    def __repr__(self):
        return f'<Score User:{self.user_id} Challenge:{self.challenge_id} Score:{self.score}>'


class BackupLog(db.Model):
    __tablename__ = 'backup_log'
    id = db.Column(db.Integer, primary_key=True)
    backup_type = db.Column(db.String(20), nullable=False)        # 'manual' or 'automated'
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)              # bytes
    validation_status = db.Column(db.String(10), nullable=False, default='pending')  # pass/fail/pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    creator = db.relationship('User', backref=db.backref('backup_logs', lazy=True))

    def __repr__(self):
        return f'<BackupLog {self.backup_type} {self.validation_status}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='RESTRICT'), nullable=False)
    action_type = db.Column(db.String(100), nullable=False)      # e.g. 'DEACTIVATE_USER'
    affected_record = db.Column(db.String(200), nullable=True)   # e.g. 'user:5 (testuser)'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship('User', backref=db.backref('audit_actions', lazy=True))

    def __repr__(self):
        return f'<AuditLog {self.action_type} by admin:{self.admin_id}>'


class Badge(db.Model):
    __tablename__ = 'badge'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(10), nullable=True)               # emoji
    trigger_condition = db.Column(db.String(200), nullable=True) # e.g. 'score>=10'

    def __repr__(self):
        return f'<Badge {self.name}>'


class UserBadge(db.Model):
    __tablename__ = 'user_badge'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id', ondelete='RESTRICT'), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('badges', lazy=True))
    badge = db.relationship('Badge', backref=db.backref('recipients', lazy=True))

    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id'),)

    def __repr__(self):
        return f'<UserBadge user:{self.user_id} badge:{self.badge_id}>'


def initialize_challenges():
    """Seed challenge data if not already present."""
    existing = {c.name for c in Challenge.query.all()}
    challenges = [
        Challenge(name='Create a VPC', description='Use the AWS CLI to create a new VPC.',
                  solution='aws ec2 create-vpc', points=10),
        Challenge(name='Create an RDS Instance', description='Use the AWS CLI to create an RDS instance.',
                  solution='aws rds create-db-instance', points=10),
        Challenge(name='Create a Security Group', description='Use the AWS CLI to create a security group.',
                  solution='aws ec2 create-security-group', points=10),
        Challenge(name='Create an IAM User', description='Use the AWS CLI to create a new IAM user.',
                  solution='aws iam create-user --user-name', points=10),
        Challenge(name='Launch an EC2 instance', description='Use the AWS CLI to launch an EC2 instance.',
                  solution='aws ec2 run-instances', points=10),
        Challenge(name='Create an S3 Bucket', description='Use the AWS CLI to Create an S3 Bucket.',
                  solution='aws s3 mb', points=10),
    ]
    new = [c for c in challenges if c.name not in existing]
    if new:
        db.session.add_all(new)
        db.session.commit()
        print(f"Seeded {len(new)} challenges.")


def initialize_badges():
    """Seed badge definitions if not already present."""
    existing = {b.name for b in Badge.query.all()}
    badges = [
        Badge(name='Cloud Warrior', description='Earned 10 or more points on challenges.',
              icon='🛡️', trigger_condition='score>=10'),
        Badge(name='Cloud Sorcerer', description='Earned 50 or more points on challenges.',
              icon='🌟', trigger_condition='score>=50'),
        Badge(name='First Steps', description='Completed your first challenge.',
              icon='👣', trigger_condition='challenges>=1'),
        Badge(name='Path Starter', description='Enrolled in your first learning path.',
              icon='📚', trigger_condition='paths>=1'),
        Badge(name='Certified', description='Earned your first learning path certificate.',
              icon='🏆', trigger_condition='certificates>=1'),
    ]
    new = [b for b in badges if b.name not in existing]
    if new:
        db.session.add_all(new)
        db.session.commit()
        print(f"Seeded {len(new)} badges.")


def check_and_award_badges(user_id):
    """Check badge triggers for a user and award any newly earned badges."""
    from sqlalchemy import func as sqlfunc
    user = User.query.get(user_id)
    if not user:
        return
    total_score = db.session.query(sqlfunc.sum(Score.score)).filter_by(user_id=user_id).scalar() or 0
    newly_awarded = []
    challenge_count = Score.query.filter_by(user_id=user_id).count()
    # Award score-based badges
    score_badges = [(10, 'Cloud Warrior'), (50, 'Cloud Sorcerer')]
    for threshold, badge_name in score_badges:
        if total_score >= threshold:
            badge = Badge.query.filter_by(name=badge_name).first()
            if badge:
                existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
                if not existing:
                    db.session.add(UserBadge(user_id=user_id, badge_id=badge.id))
                    newly_awarded.append(badge)
    if challenge_count >= 1:
        badge = Badge.query.filter_by(name='First Steps').first()
        if badge:
            existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
            if not existing:
                db.session.add(UserBadge(user_id=user_id, badge_id=badge.id))
                newly_awarded.append(badge)
    db.session.commit()
    # Send badge notification emails
    if user.email:
        try:
            from app.email_utils import send_badge_email
            for badge in newly_awarded:
                send_badge_email(user, badge)
        except Exception as e:
            print(f"[Badge email] Error: {e}")
