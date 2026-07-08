import io
from datetime import datetime
from flask import Blueprint, render_template, send_file, request, session
from sqlalchemy import func
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

from app import db
from app.models import now_sast
from app.models import User, Score, BackupLog, AuditLog
from app.decorators import admin_required

reports = Blueprint('reports', __name__, url_prefix='/reports')

# Brand colours
AWS_ORANGE = colors.HexColor('#FF9900')
AWS_DARK   = colors.HexColor('#232F3E')
BLUE       = colors.HexColor('#1A4E8C')
LIGHT_BLUE = colors.HexColor('#EBF3FA')


def _doc_header(elements, title):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                 fontSize=18, textColor=AWS_DARK,
                                 spaceAfter=6)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                               fontSize=10, textColor=colors.gray,
                               spaceAfter=20)
    elements.append(Paragraph('AWS Community Labs - awslearningplatform.click', sub_style))
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f'Generated: {now_sast().strftime("%Y-%m-%d %H:%M")} UTC', sub_style))
    elements.append(Spacer(1, 0.4 * cm))


def _table_style(header_rows=1):
    return TableStyle([
        ('BACKGROUND',   (0, 0), (-1, header_rows - 1), AWS_DARK),
        ('TEXTCOLOR',    (0, 0), (-1, header_rows - 1), colors.white),
        ('FONTNAME',     (0, 0), (-1, header_rows - 1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, header_rows), (-1, -1), [colors.white, LIGHT_BLUE]),
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ALIGN',        (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
        ('LEFTPADDING',  (0, 0), (-1, -1), 6),
    ])


# ── Reports Panel ─────────────────────────────────────────────────────────────
@reports.route('/')
@admin_required
def panel():
    admin_user = User.query.get(session['user_id'])
    return render_template('reports/panel.html', admin_user=admin_user)


# ── Report 1: User Registration ───────────────────────────────────────────────
@reports.route('/users')
@admin_required
def user_registration_report():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    _doc_header(elements, 'User Registration Report')

    users = User.query.order_by(User.created_at.desc()).all()
    user_scores = {u.id: db.session.query(func.sum(Score.score)).filter_by(user_id=u.id).scalar() or 0
                   for u in users}

    data = [['#', 'Username', 'Email', 'Role', 'Status', 'Points', 'Registered', 'Last Login']]
    for i, u in enumerate(users, 1):
        data.append([
            str(i),
            u.username,
            u.email or '-',
            u.role.upper(),
            'Active' if u.is_active else 'Inactive',
            str(user_scores[u.id]),
            u.created_at.strftime('%Y-%m-%d') if u.created_at else '-',
            u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else 'Never',
        ])

    col_widths = [1*cm, 3.5*cm, 5*cm, 2*cm, 2.2*cm, 2*cm, 3*cm, 4*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style())
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f'Total users: {len(users)}', getSampleStyleSheet()['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'user_report_{now_sast().strftime("%Y%m%d")}.pdf',
                     mimetype='application/pdf')


# ── Report 2: System Activity ──────────────────────────────────────────────────
@reports.route('/activity')
@admin_required
def system_activity_report():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    _doc_header(elements, 'System Activity Report')

    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    data = [['#', 'Admin', 'Action', 'Affected Record', 'Timestamp (UTC)']]
    for i, log in enumerate(logs, 1):
        admin = User.query.get(log.admin_id)
        data.append([
            str(i),
            admin.username if admin else f'ID:{log.admin_id}',
            log.action_type,
            log.affected_record or '-',
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '-',
        ])

    col_widths = [1*cm, 3*cm, 4*cm, 7*cm, 4.5*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style())
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f'Total entries: {len(logs)}', getSampleStyleSheet()['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'activity_report_{now_sast().strftime("%Y%m%d")}.pdf',
                     mimetype='application/pdf')


# ── Report 3: Backup Integrity ────────────────────────────────────────────────
@reports.route('/backups')
@admin_required
def backup_integrity_report():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    _doc_header(elements, 'Backup Integrity Report')

    backups = BackupLog.query.order_by(BackupLog.created_at.desc()).all()
    data = [['#', 'Type', 'Status', 'Size (KB)', 'Created By', 'Timestamp (UTC)', 'Notes']]
    for i, b in enumerate(backups, 1):
        creator = User.query.get(b.created_by) if b.created_by else None
        data.append([
            str(i),
            b.backup_type.upper(),
            b.validation_status.upper(),
            str(round(b.file_size / 1024, 1)) if b.file_size else '-',
            creator.username if creator else 'Automated',
            b.created_at.strftime('%Y-%m-%d %H:%M:%S') if b.created_at else '-',
            (b.error_message[:40] + '…') if b.error_message and len(b.error_message) > 40
            else (b.error_message or '-'),
        ])

    col_widths = [1*cm, 3*cm, 2.5*cm, 2.5*cm, 3*cm, 4.5*cm, 5.5*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = _table_style()
    # Colour pass/fail cells
    for row_idx, b in enumerate(backups, 1):
        cell_color = colors.HexColor('#2E7D32') if b.validation_status == 'pass' else colors.HexColor('#C62828')
        style.add('BACKGROUND', (2, row_idx), (2, row_idx), cell_color)
        style.add('TEXTCOLOR', (2, row_idx), (2, row_idx), colors.white)
        style.add('FONTNAME', (2, row_idx), (2, row_idx), 'Helvetica-Bold')
    t.setStyle(style)
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))
    passed = sum(1 for b in backups if b.validation_status == 'pass')
    elements.append(Paragraph(f'Total: {len(backups)} | Passed: {passed} | Failed: {len(backups)-passed}',
                               getSampleStyleSheet()['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'backup_report_{now_sast().strftime("%Y%m%d")}.pdf',
                     mimetype='application/pdf')
