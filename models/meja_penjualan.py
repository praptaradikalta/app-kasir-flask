# models/meja_penjualan.py
from extensions import db

class MejaPenjualan(db.Model):
    __tablename__ = 'meja_penjualan'
    meja_id = db.Column(db.Integer, db.ForeignKey('meja.id'), primary_key=True)
    penjualan_id = db.Column(db.Integer, db.ForeignKey('penjualan.id'), primary_key=True)
    