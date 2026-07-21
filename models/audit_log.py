# models/audit_log.py
from datetime import datetime
from extensions import db

class AuditLog(db.Model):
    """Mencatat aktivitas penting: siapa, ngapain, kapan."""
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    aksi = db.Column(db.String(50), nullable=False)      # LOGIN, LOGOUT, HAPUS_PRODUK, dst
    deskripsi = db.Column(db.String(255))
    waktu = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.aksi} by user_id={self.user_id}>'
