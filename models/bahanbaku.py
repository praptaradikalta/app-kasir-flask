from extensions import db

class BahanBaku(db.Model):
    __tablename__ = 'bahan_baku'
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True)
    nama_bahan = db.Column(db.String(100), nullable=False)  # "Daging Giling"
    satuan = db.Column(db.String(20))  # kg, liter, pcs
    harga_beli_terakhir = db.Column(db.Integer, default=0)
    stok = db.Column(db.Float, default=0)
    detail_resep = db.relationship('ResepDetail', backref='bahan', lazy=True)

    def __repr__(self):
        return f'<BahanBaku {self.nama_bahan}>'
