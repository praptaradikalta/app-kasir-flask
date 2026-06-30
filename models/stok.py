# models/stok.py
from extensions import db

class Stok(db.Model):
    __tablename__ = 'stok'
    id = db.Column(db.Integer, primary_key=True)
    produk_id = db.Column(db.Integer, db.ForeignKey('produk.id'))
    jumlah = db.Column(db.Integer, default=0)
