from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from sqlalchemy import func
from app import db
from app.models import User, Score, AuditLog, BackupLog
from app.decorators import admin_required

admin = Blueprint('admin', __name__, url_prefix='/admin')


def _log(action_type, affected_record=''):
    entry = AuditLog(admin_id=session['user_id'], action_type=action_type,
                     affected_record=affected_record, timestamp=datetime.utcnow())
    db.session.add(entry)


# ── Dashboard ─────────────────────────────────────────────────────────────────
@admin.route('/')
@admin.route('/dashboard')
@admin_required
def dashboard():
    admin_user = User.query.get(session['user_id'])
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admin_users': User.query.filter_by(role='admin').count(),
        'total_scores': db.session.query(func.sum(Score.score)).scalar() or 0,
        'total_backups': BackupLog.query.count(),
        'passed_backups': BackupLog.query.filter_by(validation_status='pass').count(),
    }
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    recent_backups = BackupLog.query.order_by(BackupLog.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_logs=recent_logs, recent_backups=recent_backups,
                           admin_user=admin_user)


# ── User Management ───────────────────────────────────────────────────────────
@admin.route('/users')
@admin_required
def users():
    admin_user = User.query.get(session['user_id'])
    q = request.args.get('q', '').strip()
    query = User.query
    if q:
        query = query.filter(
            (User.username.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%'))
        )
    all_users = query.order_by(User.created_at.desc()).all()
    user_scores = {}
    for u in all_users:
        user_scores[u.id] = db.session.query(func.sum(Score.score)).filter_by(user_id=u.id).scalar() or 0
    return render_template('admin/users.html', users=all_users,
                           user_scores=user_scores, admin_user=admin_user, q=q)


@admin.route('/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']:
        return jsonify({'error': 'Cannot deactivate your own account.'}), 400
    user.is_active = False
    _log('DEACTIVATE_USER', f'user:{user_id} ({user.username})')
    db.session.commit()
    return jsonify({'success': True})


@admin.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    _log('ACTIVATE_USER', f'user:{user_id} ({user.username})')
    db.session.commit()
    return jsonify({'success': True})


@admin.route('/users/<int:user_id>/promote', methods=['POST'])
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    _log('PROMOTE_TO_ADMIN', f'user:{user_id} ({user.username})')
    db.session.commit()
    return jsonify({'success': True})


@admin.route('/users/<int:user_id>/demote', methods=['POST'])
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']:
        return jsonify({'error': 'Cannot demote your own account.'}), 400
    user.role = 'user'
    _log('DEMOTE_FROM_ADMIN', f'user:{user_id} ({user.username})')
    db.session.commit()
    return jsonify({'success': True})


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account.'}), 400
    username = user.username
    db.session.delete(user)
    _log('DELETE_USER', f'user:{user_id} ({username})')
    db.session.commit()
    return jsonify({'success': True})


# ── Audit Log ─────────────────────────────────────────────────────────────────
@admin.route('/audit-log')
@admin_required
def audit_log():
    admin_user = User.query.get(session['user_id'])
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('admin/audit_log.html', logs=logs, admin_user=admin_user)
