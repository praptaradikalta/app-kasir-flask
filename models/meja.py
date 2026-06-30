#models meja.py
from extensions import db

class Meja(db.Model):
    __tablename__ = 'meja'
    id = db.Column(db.Integer, primary_key=True)
    nomor_meja = db.Column(db.String(20), unique=True, nullable=False)  # "1", "Teras 3"
    status = db.Column(db.String(20), default='kosong')  # kosong, terisi, reserved
    penjualan = db.relationship('Penjualan', secondary='meja_penjualan', backref='meja')
    def __repr__(self):
        return f'<Meja {self.nomor_meja}>'
