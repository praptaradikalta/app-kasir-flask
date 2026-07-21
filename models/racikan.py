# models/racikan.py
from extensions import db

class Racikan(db.Model):
    """
    Komponen semi-jadi hasil olahan sendiri (mis. Kuah Miso, Toping Semur,
    Bakwan) yang dipakai sebagai 'bahan' di resep beberapa menu berbeda.
    Beda dari BahanBaku (yang dibeli langsung), Racikan dibikin dari campuran
    beberapa BahanBaku lewat resepnya sendiri, dan HPP-nya dihitung otomatis
    sama seperti Produk.
    """
    __tablename__ = 'racikan'
    id = db.Column(db.Integer, primary_key=True)
    nama_racikan = db.Column(db.String(100), nullable=False)  # "Kuah Miso", "Toping Semur"
    satuan_hasil = db.Column(db.String(20), default='porsi')  # porsi, mangkuk, sdm, dll
    porsi_hasil = db.Column(db.Integer, default=1)
    harga_per_porsi = db.Column(db.Integer, default=0)  # HPP per satuan_hasil, dihitung otomatis

    detail = db.relationship('RacikanDetail', backref='racikan', lazy=True)

    def update_hpp(self):
        """Hitung ulang HPP racikan ini berdasarkan bahan baku yang dipakai."""
        if not self.porsi_hasil:
            return
        total_batch = sum(d.qty_pakai * d.bahan.harga_beli_terakhir for d in self.detail)
        self.harga_per_porsi = int(total_batch // self.porsi_hasil)
        db.session.commit()

    def __repr__(self):
        return f'<Racikan {self.nama_racikan}>'


class RacikanDetail(db.Model):
    __tablename__ = 'racikan_detail'
    id = db.Column(db.Integer, primary_key=True)
    racikan_id = db.Column(db.Integer, db.ForeignKey('racikan.id'), nullable=False)
    bahan_id = db.Column(db.Integer, db.ForeignKey('bahan_baku.id'), nullable=False)
    qty_pakai = db.Column(db.Float, nullable=False)

    bahan = db.relationship('BahanBaku', backref='detail_racikan', lazy=True)

    def __repr__(self):
        return f'<RacikanDetail {self.id}>'
