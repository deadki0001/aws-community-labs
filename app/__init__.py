import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import timedelta

db = SQLAlchemy()
mail = Mail()


def create_app():
    app = Flask(__name__, static_folder='static')

    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.zoho.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_DEBUG'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'no-reply@awslearningplatform.click')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'Sydney2026!@#')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@awslearningplatform.click')

    db.init_app(app)
    mail.init_app(app)

    # Blueprints
    from app.routes import main
    app.register_blueprint(main)

    from app.routes_learning import learning
    app.register_blueprint(learning)

    from app.admin.routes import admin
    app.register_blueprint(admin)

    from app.backup.routes import backup_bp
    app.register_blueprint(backup_bp)

    from app.reports.routes import reports
    app.register_blueprint(reports)

    # Database + Seed
    with app.app_context():
        db.create_all()
        from app.models import initialize_challenges, initialize_badges
        from app.models_learning import seed_learning_paths, seed_aws_associate_paths
        initialize_challenges()
        initialize_badges()
        seed_learning_paths()
        seed_aws_associate_paths()

    # APScheduler - daily automated backup at 00:00 UTC (02:00 SAST)
    _start_scheduler(app)

    return app


def _start_scheduler(app):
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            def _auto_backup():
                with app.app_context():
                    from app.backup.routes import run_backup
                    run_backup(backup_type='automated', user_id=None)

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(func=_auto_backup, trigger='cron', hour=0, minute=0,
                              id='daily_backup', replace_existing=True)
            scheduler.start()
            print("[Scheduler] Daily automated backup job registered (00:00 UTC).")
        except Exception as e:
            print(f"[Scheduler] Could not start: {e}")
