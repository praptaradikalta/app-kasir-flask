#models resep.py
from extensions import db

class Resep(db.Model):
    __tablename__ = 'resep'
    id = db.Column(db.Integer, primary_key=True)
    produk_id = db.Column(db.Integer, db.ForeignKey('produk.id'))
    porsi_hasil = db.Column(db.Integer, default=1)
    detail = db.relationship('ResepDetail', backref='resep', lazy=True)
