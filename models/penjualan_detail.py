# models/penjualan_detail.py
from extensions import db

class PenjualanDetail(db.Model):
    # definisi class PenjualanDetail
    __tablename__ = 'penjualan_detail'
    id = db.Column(db.Integer, primary_key=True)
    penjualan_id = db.Column(db.Integer, db.ForeignKey('penjualan.id'))
    produk_id = db.Column(db.Integer, db.ForeignKey('produk.id'))
    qty = db.Column(db.Integer, nullable=False)
    harga_satuan = db.Column(db.Integer, nullable=False)
