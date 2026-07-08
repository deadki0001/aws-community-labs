import secrets
import string
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app import db
from app.models import now_sast
from app.models import User
from app.models_learning import (
    LearningPath, PathModule, ModuleSection, QuizQuestion,
    UserPathProgress, UserModuleProgress, Certificate
)
from app.decorators import login_required
from sqlalchemy import func

learning = Blueprint('learning', __name__)


def _current_user():
    return User.query.get(session['user_id'])


# ── Catalogue ─────────────────────────────────────────────────────────────────
@learning.route('/learning-paths')
@login_required
def catalogue():
    user = _current_user()
    paths = LearningPath.query.all()
    enrolled = {p.path_id: p for p in UserPathProgress.query.filter_by(user_id=user.id).all()}
    return render_template('learning_paths/catalogue.html', paths=paths, enrolled=enrolled, user=user)


# ── Path Detail ───────────────────────────────────────────────────────────────
@learning.route('/learning-paths/<slug>')
@login_required
def path_detail(slug):
    user = _current_user()
    path = LearningPath.query.filter_by(slug=slug).first_or_404()
    progress = UserPathProgress.query.filter_by(user_id=user.id, path_id=path.id).first()
    completed_modules = {}
    if progress:
        for mp in UserModuleProgress.query.filter_by(user_id=user.id).all():
            completed_modules[mp.module_id] = mp
    total = len(path.modules)
    done = sum(1 for m in path.modules if completed_modules.get(m.id) and completed_modules[m.id].completed)
    pct = int((done / total) * 100) if total else 0
    return render_template('learning_paths/path_detail.html', path=path, progress=progress,
                           completed_modules=completed_modules, completion_pct=pct, user=user)


# ── Enrol ─────────────────────────────────────────────────────────────────────
@learning.route('/learning-paths/<slug>/enrol', methods=['POST'])
@login_required
def enrol(slug):
    user = _current_user()
    path = LearningPath.query.filter_by(slug=slug).first_or_404()
    if not UserPathProgress.query.filter_by(user_id=user.id, path_id=path.id).first():
        db.session.add(UserPathProgress(user_id=user.id, path_id=path.id))
        db.session.commit()
    return jsonify({'success': True})


# ── Module View ───────────────────────────────────────────────────────────────
@learning.route('/learning-paths/<slug>/module/<int:module_id>')
@login_required
def module_view(slug, module_id):
    user = _current_user()
    path = LearningPath.query.filter_by(slug=slug).first_or_404()
    module = PathModule.query.get_or_404(module_id)
    if module.path_id != path.id:
        return redirect(url_for('learning.path_detail', slug=slug))
    if not UserPathProgress.query.filter_by(user_id=user.id, path_id=path.id).first():
        db.session.add(UserPathProgress(user_id=user.id, path_id=path.id))
        db.session.commit()
    mod_progress = UserModuleProgress.query.filter_by(user_id=user.id, module_id=module_id).first()
    modules = path.modules
    idx = next((i for i, m in enumerate(modules) if m.id == module_id), 0)
    prev_mod = modules[idx - 1] if idx > 0 else None
    next_mod = modules[idx + 1] if idx < len(modules) - 1 else None
    return render_template('learning_paths/module_view.html', path=path, module=module,
                           mod_progress=mod_progress, prev_mod=prev_mod, next_mod=next_mod, user=user)


# ── Mark Read ─────────────────────────────────────────────────────────────────
@learning.route('/learning-paths/<slug>/module/<int:module_id>/mark-read', methods=['POST'])
@login_required
def mark_module_read(slug, module_id):
    user = _current_user()
    mp = UserModuleProgress.query.filter_by(user_id=user.id, module_id=module_id).first()
    if not mp:
        db.session.add(UserModuleProgress(user_id=user.id, module_id=module_id))
        db.session.commit()
    return jsonify({'success': True})


# ── Quiz View ─────────────────────────────────────────────────────────────────
@learning.route('/learning-paths/<slug>/module/<int:module_id>/quiz')
@login_required
def quiz_view(slug, module_id):
    user = _current_user()
    path = LearningPath.query.filter_by(slug=slug).first_or_404()
    module = PathModule.query.get_or_404(module_id)
    if module.path_id != path.id:
        return redirect(url_for('learning.path_detail', slug=slug))
    mod_progress = UserModuleProgress.query.filter_by(user_id=user.id, module_id=module_id).first()
    questions = QuizQuestion.query.filter_by(module_id=module_id).all()
    return render_template('learning_paths/quiz.html', path=path, module=module,
                           questions=questions, mod_progress=mod_progress, user=user)


# ── Quiz Submit ───────────────────────────────────────────────────────────────
@learning.route('/learning-paths/<slug>/module/<int:module_id>/quiz/submit', methods=['POST'])
@login_required
def quiz_submit(slug, module_id):
    user = _current_user()
    path = LearningPath.query.filter_by(slug=slug).first_or_404()
    module = PathModule.query.get_or_404(module_id)
    data = request.get_json()
    answers = data.get('answers', {})
    questions = QuizQuestion.query.filter_by(module_id=module_id).all()
    total = len(questions)
    if total == 0:
        return jsonify({'error': 'No questions found'}), 400
    correct = sum(1 for q in questions
                  if str(q.id) in answers and answers[str(q.id)].upper() == q.correct_answer)
    score_pct = int((correct / total) * 100)
    passed = score_pct >= 70
    feedback = [{'id': q.id, 'question': q.question_text,
                 'your_answer': answers.get(str(q.id), '').upper(),
                 'correct_answer': q.correct_answer,
                 'is_correct': answers.get(str(q.id), '').upper() == q.correct_answer,
                 'explanation': q.explanation,
                 'options': {'A': q.option_a, 'B': q.option_b, 'C': q.option_c, 'D': q.option_d}}
                for q in questions]
    mp = UserModuleProgress.query.filter_by(user_id=user.id, module_id=module_id).first()
    if not mp:
        mp = UserModuleProgress(user_id=user.id, module_id=module_id)
        db.session.add(mp)
    mp.quiz_attempts = (mp.quiz_attempts or 0) + 1
    if mp.quiz_score is None or score_pct > mp.quiz_score:
        mp.quiz_score = score_pct
    points_awarded = 0
    if passed and not mp.quiz_passed:
        mp.quiz_passed = True
        mp.completed = True
        mp.completed_at = now_sast()
        mp.points_earned = module.points
        points_awarded = module.points
        pp = UserPathProgress.query.filter_by(user_id=user.id, path_id=path.id).first()
        if not pp:
            pp = UserPathProgress(user_id=user.id, path_id=path.id)
            db.session.add(pp)
        pp.total_points_earned = (pp.total_points_earned or 0) + module.points
        all_done = all(
            UserModuleProgress.query.filter_by(user_id=user.id, module_id=m.id, completed=True).first()
            for m in path.modules
        )
        if all_done and not pp.completed_at:
            pp.completed_at = now_sast()
            _issue_certificate(user, path, pp)
    db.session.commit()
    return jsonify({'score': score_pct, 'correct': correct, 'total': total,
                    'passed': passed, 'feedback': feedback, 'points_earned': points_awarded})


def _issue_certificate(user, path, path_progress):
    if Certificate.query.filter_by(user_id=user.id, path_id=path.id).first():
        return
    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    cert = Certificate(user_id=user.id, path_id=path.id, cert_code=code,
                       recipient_full_name=user.username,
                       total_points=path_progress.total_points_earned or 0)
    db.session.add(cert)


# ── Certificate ───────────────────────────────────────────────────────────────
@learning.route('/certificate/<cert_code>')
def view_certificate(cert_code):
    cert = Certificate.query.filter_by(cert_code=cert_code).first_or_404()
    return render_template('learning_paths/certificate.html', cert=cert)


@learning.route('/my-certificates')
@login_required
def my_certificates():
    user = _current_user()
    certs = Certificate.query.filter_by(user_id=user.id).all()
    return render_template('learning_paths/my_certificates.html', certs=certs, user=user)


@learning.route('/certificate/<cert_code>/set-name', methods=['POST'])
@login_required
def set_cert_name(cert_code):
    user = _current_user()
    cert = Certificate.query.filter_by(cert_code=cert_code, user_id=user.id).first_or_404()
    data = request.get_json()
    full_name = (data.get('full_name') or '').strip()
    if not full_name:
        return jsonify({'error': 'Name required'}), 400
    cert.recipient_full_name = full_name
    db.session.commit()
    return jsonify({'success': True})


# ── Progress API ──────────────────────────────────────────────────────────────
@learning.route('/api/my-progress')
@login_required
def my_progress_api():
    user = _current_user()
    result = []
    for pp in UserPathProgress.query.filter_by(user_id=user.id).all():
        path = LearningPath.query.get(pp.path_id)
        total_mods = len(path.modules)
        done_mods = sum(1 for m in path.modules
                        if UserModuleProgress.query.filter_by(
                            user_id=user.id, module_id=m.id, completed=True).first())
        result.append({'path_id': path.id, 'slug': path.slug, 'title': path.title,
                       'icon': path.icon, 'total_modules': total_mods,
                       'completed_modules': done_mods,
                       'pct': int((done_mods / total_mods) * 100) if total_mods else 0,
                       'points_earned': pp.total_points_earned,
                       'completed': pp.completed_at is not None})
    return jsonify(result)


# ── Stats API (used by dashboard cert + badge counts) ─────────────────────────
@learning.route('/api/my-stats')
@login_required
def my_stats_api():
    from app.models_learning import Certificate
    from app.models import UserBadge
    user = _current_user()
    cert_count = Certificate.query.filter_by(user_id=user.id).count()
    badge_count = UserBadge.query.filter_by(user_id=user.id).count()
    return jsonify({'cert_count': cert_count, 'badge_count': badge_count})
