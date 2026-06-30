#models hutang_supplier
from datetime import datetime
from extensions import db

class HutangSupplier(db.Model):
    __tablename__ = 'hutang_supplier'
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    produk_id = db.Column(db.Integer, db.ForeignKey('produk.id'), nullable=False)
    penjualan_id = db.Column(db.Integer, db.ForeignKey('penjualan.id'), nullable=False)
    supplier = db.Column(db.String(100))  # "Pak Supir Chitato"
    qty_laku = db.Column(db.Integer)
    total_hutang = db.Column(db.Integer)  # qty_laku * harga_beli_supplier
    status = db.Column(db.String(20), default='belum_bayar')  # belum_bayar, lunas
    produk = db.relationship('Produk', lazy=True)
    penjualan = db.relationship('Penjualan', lazy=True)

    def __repr__(self):
        return f'<HutangSupplier {self.id}>'
