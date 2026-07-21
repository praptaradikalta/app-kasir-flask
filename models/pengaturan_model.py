# models/pengaturan_model.py
from extensions import db

class Pengaturan(db.Model):
    """
    Tabel pengaturan toko. Didesain single-row (cuma 1 baris data)
    karena settingan ini berlaku global untuk 1 toko/cabang.
    """
    __tablename__ = 'pengaturan'
    id = db.Column(db.Integer, primary_key=True)

    # Informasi Toko
    nama_toko = db.Column(db.String(100), default='Toko Saya')
    alamat = db.Column(db.String(255), default='')
    no_telp = db.Column(db.String(20), default='')

    # Preferensi Transaksi
    mata_uang = db.Column(db.String(10), default='IDR')
    pajak_persen = db.Column(db.Float, default=0)          # PPN, contoh: 11 = 11%
    service_charge_persen = db.Column(db.Float, default=0) # Biaya layanan, contoh: 5 = 5%

    # Struk
    catatan_struk = db.Column(db.String(255), default='Terima kasih atas kunjungan Anda!')

    def __repr__(self):
        return f'<Pengaturan {self.nama_toko}>'

    @staticmethod
    def get_settings():
        """Ambil baris pengaturan yang ada, atau buat default kalau belum ada."""
        settings = Pengaturan.query.first()
        if not settings:
            settings = Pengaturan()
            db.session.add(settings)
            db.session.commit()
        return settings
