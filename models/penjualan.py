# models/penjualan.py
from datetime import datetime
from extensions import db

class Penjualan(db.Model):
    __tablename__ = 'penjualan'
    id = db.Column(db.Integer, primary_key=True)
    # Gunakan DateTime agar waktu transaksi terekam lebih detail (jam & menit)
    tanggal = db.Column(db.DateTime, default=datetime.now)
    total_bayar = db.Column(db.Integer, nullable=False, default=0)
    bayar = db.Column(db.Integer, default=0) # Untuk mencatat uang tunai yang diterima
    kembalian = db.Column(db.Integer, default=0)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    meja_id = db.Column(db.Integer, db.ForeignKey('meja.id'), nullable=True) # Kaitan ke meja
    
    tipe_pesanan = db.Column(db.String(20)) # 'Take Away', 'Dine In', 'Reservasi'
    status = db.Column(db.String(20), default='Pending')# Lunas, Pending, dll

    # Relasi
    user = db.relationship('User', backref='penjualan_user')
    
    # Gunakan overlaps="meja" jika Anda juga menggunakan Many-to-Many di model Meja
    customer = db.relationship('Customer', backref='penjualan_list')
   
    # Relasi ke item pesanan
    items = db.relationship('PenjualanDetail', backref='penjualan', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Penjualan ID: {self.id} | Total: {self.total_bayar}>'

