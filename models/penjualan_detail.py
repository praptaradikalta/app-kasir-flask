# models/penjualan_detail.py

from extensions import db

class PenjualanDetail(db.Model):
    __tablename__ = 'penjualan_detail'
    
    id = db.Column(db.Integer, primary_key=True)
    penjualan_id = db.Column(db.Integer, db.ForeignKey('penjualan.id'), nullable=False)
    produk_id = db.Column(db.Integer, db.ForeignKey('produk.id'), nullable=False)
    
    # Gunakan 'qty' sesuai skema SQLite Anda
    qty = db.Column(db.Integer, nullable=False)
    harga_satuan = db.Column(db.Integer, nullable=False)
    
    # FIELD BARU: Untuk menyimpan pilihan Mie Kuning, Mie Putih, dll.
    varian = db.Column(db.String(50), nullable=True)
    
    # TAMBAHAN FIELD BARU : untuk menampung ceklist
    is_ready = db.Column(db.Boolean, default=False) # Tambahkan ini

    # Relasi balik (Opsional tapi berguna)
    # produk = db.relationship('Produk', backref='penjualan_details')

    # Di dalam class PenjualanDetail
    @property
    def subtotal(self):
        return self.qty * self.harga_satuan

    def __repr__(self):
        return f'<Detail ID: {self.id} | Produk ID: {self.produk_id} | Varian: {self.varian}>'