from datetime import datetime
from extensions import db
from enum import Enum
from models.stok import Stok

class KategoriEnum(Enum):
    MAKANAN = 'Makanan'
    MINUMAN = 'Minuman'
    SNACK = 'Snack'

class Produk(db.Model):
    __tablename__ = 'produk'
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True)
    nama_produk = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(30), nullable=False)  # ganti ke 30 biar sesuai enum
    harga_jual = db.Column(db.Integer, nullable=False)
    harga_beli = db.Column(db.Integer, default=0)  # HPP final per pcs/mangkok
    harga_beli_supplier = db.Column(db.Integer, default=0)  # Khusus konsinyasi
    is_konsinyasi = db.Column(db.Boolean, default=False)  # True = titip, False = beli/resep
    gambar = db.Column(db.Text)  # tambahin field gambar
    resep = db.relationship('Resep', backref='produk', uselist=False, lazy=True)
    detail = db.relationship('PenjualanDetail', backref='produk', lazy=True)
    stok = db.relationship('Stok', back_populates='produk', lazy=True)

    def update_hpp(self):
        """Hitung HPP otomatis kalo ada resep"""
        if self.kategori in ['Makanan', 'Minuman'] and self.resep and not self.is_konsinyasi:
            total_hpp_batch = sum(
                d.qty_pakai * d.bahan.harga_beli_terakhir for d in self.resep.detail
            )
            self.harga_beli = total_hpp_batch // self.resep.porsi_hasil
            db.session.commit()

    def get_stok(self):
        s = Stok.query.filter_by(produk_id=self.id).first()
        return s.jumlah if s else 0

    def __repr__(self):
        return f'<Produk {self.nama_produk}>'