#models resep_detail.py
from extensions import db

class ResepDetail(db.Model):
    __tablename__ = 'resep_detail'
    id = db.Column(db.Integer, primary_key=True)
    resep_id = db.Column(db.Integer, db.ForeignKey('resep.id'), nullable=False)

    # Satu baris resep menunjuk SALAH SATU dari dua ini (gak boleh dua-duanya
    # keisi atau dua-duanya kosong): bahan mentah langsung, ATAU racikan
    # semi-jadi (mis. "Kuah Miso") yang HPP-nya udah dihitung dari resepnya sendiri.
    bahan_id = db.Column(db.Integer, db.ForeignKey('bahan_baku.id'), nullable=True)
    racikan_id = db.Column(db.Integer, db.ForeignKey('racikan.id'), nullable=True)

    qty_pakai = db.Column(db.Float, nullable=False)  # 2.5 kg / 1 porsi racikan

    racikan_dipakai = db.relationship('Racikan', foreign_keys=[racikan_id], lazy=True)

    @property
    def harga_satuan_sumber(self):
        """Harga per satuan dari sumbernya (bahan baku ATAU racikan), siapapun yang keisi."""
        if self.bahan_id:
            return self.bahan.harga_beli_terakhir
        if self.racikan_id:
            return self.racikan_dipakai.harga_per_porsi
        return 0

    @property
    def nama_sumber(self):
        if self.bahan_id:
            return self.bahan.nama_bahan
        if self.racikan_id:
            return self.racikan_dipakai.nama_racikan
        return '-'

    def __repr__(self):
        return f'<ResepDetail {self.id}>'