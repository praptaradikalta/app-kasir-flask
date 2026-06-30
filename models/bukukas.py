#models bukukas.py
from datetime import datetime
from extensions import db

class BukuKas(db.Model):
    __tablename__ = 'buku_kas'
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    penjualan_id = db.Column(db.Integer, db.ForeignKey('penjualan.id'), nullable=True)
    jenis = db.Column(db.String(20))  # masuk, keluar
    keterangan = db.Column(db.String(200))
    jumlah = db.Column(db.Integer)
    user = db.relationship('User', back_populates='buku_kas')

    def __repr__(self):
        return f'<BukuKas {self.id}>'