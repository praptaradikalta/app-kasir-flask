# models/penjualan.py
from datetime import datetime
from extensions import db

class Penjualan(db.Model):
    __tablename__ = 'penjualan'
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, default=datetime.utcnow)
    total_bayar = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

    # relasi
    user = db.relationship('User', backref='penjualan_user')
    customer = db.relationship('Customer', back_populates='penjualan')
    detail = db.relationship('PenjualanDetail', backref='penjualan', lazy=True)