# routers/audit_router.py
from flask import Blueprint, render_template, request
from flask_login import login_required
from extensions import db
from models import AuditLog, User
from utils import admin_required
from datetime import datetime

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/')
@login_required
@admin_required
def audit_list():
    user_id_filter = request.args.get('user_id', type=int)
    aksi_filter = request.args.get('aksi', '')
    tgl_str = request.args.get('tanggal', '')

    query = AuditLog.query
    if user_id_filter:
        query = query.filter_by(user_id=user_id_filter)
    if aksi_filter:
        query = query.filter_by(aksi=aksi_filter)
    if tgl_str:
        try:
            tgl = datetime.strptime(tgl_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(AuditLog.waktu) == tgl)
        except ValueError:
            tgl_str = ''

    logs = query.order_by(AuditLog.id.desc()).limit(300).all()
    semua_user = User.query.order_by(User.username).all()
    semua_aksi = [row[0] for row in AuditLog.query.with_entities(AuditLog.aksi).distinct().order_by(AuditLog.aksi).all()]

    return render_template('audit/list.html',
                           logs=logs,
                           semua_user=semua_user,
                           semua_aksi=semua_aksi,
                           user_id_filter=user_id_filter,
                           aksi_filter=aksi_filter,
                           tanggal=tgl_str)
