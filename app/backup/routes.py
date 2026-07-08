import os
import shutil
import sqlite3
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, request, jsonify, session, current_app
from app import db
from app.models import BackupLog, AuditLog, User
from app.decorators import admin_required

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')

_SAST = timezone(timedelta(hours=2))


def now_sast():
    return datetime.now(_SAST).replace(tzinfo=None)


def _get_db_path():
    return os.path.join(current_app.instance_path, 'app.db')


def _ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def _validate_backup_file(backup_path, live_db_path):
    try:
        backup_conn = sqlite3.connect(backup_path)
        live_conn = sqlite3.connect(live_db_path)
        tables_to_check = ['user', 'challenge', 'score']
        for table in tables_to_check:
            try:
                b_count = backup_conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                l_count = live_conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                if b_count != l_count:
                    backup_conn.close()
                    live_conn.close()
                    return 'fail', f'Record count mismatch in {table}: backup={b_count} live={l_count}'
            except sqlite3.OperationalError:
                pass
        backup_conn.close()
        live_conn.close()
        return 'pass', None
    except Exception as e:
        return 'fail', str(e)


def run_backup(backup_type='automated', user_id=None):
    with current_app.app_context():
        _ensure_backup_dir()
        db_path = _get_db_path()
        if not os.path.exists(db_path):
            return None
        timestamp = now_sast().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}_{backup_type}.db'
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        try:
            shutil.copy2(db_path, backup_path)
            file_size = os.path.getsize(backup_path)
            status, error_msg = _validate_backup_file(backup_path, db_path)
            log = BackupLog(
                backup_type=backup_type,
                file_path=backup_path,
                file_size=file_size,
                validation_status=status,
                created_at=now_sast(),
                created_by=user_id,
                error_message=error_msg
            )
            db.session.add(log)
            db.session.commit()
            db.session.refresh(log)
            result = type('BackupResult', (), {
                'id': log.id,
                'validation_status': log.validation_status,
                'file_path': log.file_path,
                'file_size': log.file_size,
                'error_message': log.error_message
            })()
            print(f"[Backup] {backup_type} backup {result.validation_status}: {result.file_path}")
            return result
        except Exception as e:
            log = BackupLog(
                backup_type=backup_type,
                file_path=backup_path if 'backup_path' in locals() else 'unknown',
                validation_status='fail',
                created_at=now_sast(),
                created_by=user_id,
                error_message=str(e)
            )
            db.session.add(log)
            db.session.commit()
            db.session.refresh(log)
            result = type('BackupResult', (), {
                'id': log.id,
                'validation_status': 'fail',
                'file_path': log.file_path,
                'file_size': None,
                'error_message': str(e)
            })()
            return result


@backup_bp.route('/')
@admin_required
def panel():
    admin_user = User.query.get(session['user_id'])
    backups = BackupLog.query.order_by(BackupLog.created_at.desc()).all()
    drift_result = session.pop('drift_result', None)
    return render_template('backup/panel.html', backups=backups,
                           admin_user=admin_user, drift_result=drift_result)


@backup_bp.route('/create', methods=['POST'])
@admin_required
def create_backup():
    log = run_backup(backup_type='manual', user_id=session['user_id'])
    audit = AuditLog(
        admin_id=session['user_id'],
        action_type='BACKUP_TRIGGERED',
        affected_record=f'backup_id:{log.id} status:{log.validation_status}',
        timestamp=now_sast()
    )
    db.session.add(audit)
    db.session.commit()
    return jsonify({
        'success': True,
        'status': log.validation_status,
        'path': log.file_path,
        'size': log.file_size,
        'error': log.error_message
    })


@backup_bp.route('/validate/<int:backup_id>', methods=['POST'])
@admin_required
def validate_backup(backup_id):
    log = BackupLog.query.get_or_404(backup_id)
    db_path = _get_db_path()
    if not os.path.exists(log.file_path):
        return jsonify({'error': 'Backup file not found on server.'}), 404
    status, error_msg = _validate_backup_file(log.file_path, db_path)
    log.validation_status = status
    log.error_message = error_msg
    db.session.commit()
    return jsonify({'success': True, 'status': status, 'error': error_msg})


@backup_bp.route('/restore/<int:backup_id>', methods=['POST'])
@admin_required
def restore_backup(backup_id):
    log = BackupLog.query.get_or_404(backup_id)
    if log.validation_status != 'pass':
        return jsonify({'error': 'Cannot restore from an unvalidated backup. Please validate first.'}), 400
    if not os.path.exists(log.file_path):
        return jsonify({'error': 'Backup file not found on server.'}), 404
    db_path = _get_db_path()
    log_file_path = log.file_path
    log_created_at = log.created_at.strftime('%Y-%m-%d %H:%M:%S')
    safety_log = run_backup(backup_type='pre_restore_safety', user_id=session['user_id'])
    safety_path = safety_log.file_path
    try:
        shutil.copy2(log_file_path, db_path)
        status, err = _validate_backup_file(db_path, log_file_path)
        if status == 'pass':
            audit = AuditLog(
                admin_id=session['user_id'],
                action_type='RESTORE_COMPLETED',
                affected_record=f'backup_id:{backup_id}',
                timestamp=now_sast()
            )
            db.session.add(audit)
            db.session.commit()
            return jsonify({'success': True, 'message': f'System restored to backup from {log_created_at} SAST.'})
        else:
            shutil.copy2(safety_path, db_path)
            return jsonify({'error': f'Post-restore validation failed. System reverted. Error: {err}'}), 500
    except Exception as e:
        try:
            shutil.copy2(safety_path, db_path)
        except Exception:
            pass
        return jsonify({'error': f'Restore failed and system was reverted. Error: {str(e)}'}), 500


@backup_bp.route('/drift-check', methods=['POST'])
@admin_required
def drift_check():
    db_path = _get_db_path()
    expected_tables = {
        'user': ['id', 'username', 'email', 'password_hash', 'role', 'is_active',
                 'created_at', 'last_login', 'show_wizard', 'reset_token', 'reset_token_expiration'],
        'challenge': ['id', 'name', 'description', 'solution', 'points'],
        'score': ['id', 'user_id', 'challenge_id', 'score', 'completed_at'],
        'backup_log': ['id', 'backup_type', 'file_path', 'file_size', 'validation_status',
                       'created_at', 'created_by', 'error_message'],
        'audit_log': ['id', 'admin_id', 'action_type', 'affected_record', 'timestamp'],
    }
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        live_tables = {row[0] for row in cursor.fetchall()}
        issues = []
        for table, expected_cols in expected_tables.items():
            if table not in live_tables:
                issues.append(f"Missing table: {table}")
                continue
            cursor.execute(f'PRAGMA table_info({table})')
            live_cols = {row[1] for row in cursor.fetchall()}
            for col in expected_cols:
                if col not in live_cols:
                    issues.append(f"Missing column: {table}.{col}")
        conn.close()
        audit = AuditLog(
            admin_id=session['user_id'],
            action_type='DRIFT_CHECK',
            affected_record=f'issues:{len(issues)}',
            timestamp=now_sast()
        )
        db.session.add(audit)
        db.session.commit()
        if issues:
            return jsonify({'status': 'drift', 'issues': issues})
        return jsonify({'status': 'clean', 'issues': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
