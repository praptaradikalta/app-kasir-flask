#Model/stok_harian_model.py
from extensions import db
from datetime import date

class StokHarian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produk_id = db.Column(db.Integer, db.ForeignKey('produk.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False, default=date.today)
    jumlah = db.Column(db.Integer, nullable=False)  # + masuk, - keluar
    keterangan = db.Column(db.String(100))  # 'Restock awal', 'Penjualan', 'Retur', dll
    
    produk = db.relationship('Produk', backref='riwayat_stok')