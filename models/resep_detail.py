#models resep_detail.py
from extensions import db

class ResepDetail(db.Model):
    __tablename__ = 'resep_detail'
    id = db.Column(db.Integer, primary_key=True)
    resep_id = db.Column(db.Integer, db.ForeignKey('resep.id'), nullable=False)
    bahan_id = db.Column(db.Integer, db.ForeignKey('bahan_baku.id'), nullable=False)
    qty_pakai = db.Column(db.Float, nullable=False)  # 2.5 kg

    def __repr__(self):
        return f'<ResepDetail {self.id}>'