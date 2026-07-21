# models/shift.py
from datetime import datetime
from extensions import db

class Shift(db.Model):
    """Catatan shift kerja kasir: kapan mulai/selesai, modal awal, dan kas akhir."""
    __tablename__ = 'shift'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    waktu_mulai = db.Column(db.DateTime, default=datetime.now)
    waktu_selesai = db.Column(db.DateTime, nullable=True)

    modal_awal = db.Column(db.Integer, default=0)       # uang kas pas mulai shift
    modal_akhir = db.Column(db.Integer, nullable=True)  # uang kas yang dihitung manual pas tutup shift

    status = db.Column(db.String(20), default='aktif')  # aktif, selesai
    catatan = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref='shifts')

    def __repr__(self):
        return f'<Shift {self.id} user_id={self.user_id} status={self.status}>'
