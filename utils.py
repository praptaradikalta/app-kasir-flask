# utils.py
import bcrypt
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Batasi akses rute hanya untuk role admin/owner. Kasir akan ditolak."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'owner'):
            flash('Kamu tidak punya akses ke halaman ini.', 'danger')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated


def catat_log(aksi, deskripsi=''):
    """
    Catat satu baris audit log. Dipanggil dari mana saja setelah aksi penting
    terjadi (login, hapus produk, ubah harga, dll).
    Gagal mencatat log TIDAK boleh menggagalkan aksi utama pengguna, jadi
    error di sini cuma di-print, tidak di-raise ulang.
    """
    from extensions import db
    from models import AuditLog
    try:
        log = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            aksi=aksi,
            deskripsi=deskripsi
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f">>> [AUDIT LOG ERROR] Gagal mencatat log '{aksi}': {e}")


def recalculate_hpp_cascade(bahan):
    """
    Dipanggil setelah harga sebuah BahanBaku berubah. Update HPP semua yang
    kena dampak, langsung maupun tidak langsung:
      1. Racikan (mis. "Kuah Miso") yang pakai bahan ini langsung di resepnya.
      2. Produk yang pakai bahan ini LANGSUNG di resepnya.
      3. Produk yang pakai Racikan dari langkah 1 (dampak tidak langsung, lewat racikan).
    """
    from models import ResepDetail

    # 1. Racikan yang pakai bahan ini -> hitung ulang HPP racikan itu
    racikan_terdampak = {rd.racikan for rd in bahan.detail_racikan}
    for racikan in racikan_terdampak:
        racikan.update_hpp()

    # 2. Produk yang pakai bahan ini langsung
    for detail in bahan.detail_resep:
        if detail.resep.produk:
            detail.resep.produk.update_hpp()

    # 3. Produk yang pakai racikan yang baru saja ke-update HPP-nya (dampak tidak langsung)
    for racikan in racikan_terdampak:
        for rd in ResepDetail.query.filter_by(racikan_id=racikan.id).all():
            if rd.resep.produk:
                rd.resep.produk.update_hpp()


def send_reset_email(user, token):
    """
    Kirim email berisi link reset password. Kalau pengiriman gagal (SMTP belum
    dikonfigurasi, kredensial salah, dll), jangan sampai error ini bocor ke
    pengguna dan menyingkap detail internal — cukup return False, dan pemanggil
    yang urus pesan ke pengguna.
    """
    from flask import url_for, current_app
    from flask_mail import Message
    from extensions import mail

    reset_link = url_for('user.reset_password', token=token, _external=True)

    try:
        msg = Message(
            subject='Reset Password - Kasir UKM',
            recipients=[user.email],
            body=(
                f'Halo {user.nama_lengkap or user.username},\n\n'
                f'Ada permintaan reset password untuk akun kamu.\n'
                f'Klik link berikut untuk membuat password baru (berlaku 1 jam):\n\n'
                f'{reset_link}\n\n'
                f'Kalau kamu tidak merasa meminta ini, abaikan saja email ini.\n'
            )
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f">>> [EMAIL ERROR] Gagal mengirim email reset password: {e}")
        return False

def hash_password(password):
 return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def parse_int(value, default=0):
    """
    Mencoba mengkonversi value ke integer.
    Jika gagal, kembalikan nilai default.
    Bisa menerima string angka desimal seperti '25.0'.
    """
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_float(value, default=0.0):
    """
    Mencoba mengkonversi value ke float.
    Jika gagal, kembalikan nilai default.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_bool(value, default=False):
    """
    Mengkonversi value ke boolean.
    Menerima nilai string '0', '1', 'true', 'false', integer 0 atau 1.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        val = value.strip().lower()
        if val in ['1', 'true', 'yes', 'on']:
            return True
        elif val in ['0', 'false', 'no', 'off']:
            return False
    return default


def validate_enum(value, enum_class, default=None):
    """
    Validasi apakah value ada di enum_class (Enum).
    Jika valid, kembalikan value, jika tidak kembalikan default.
    """
    valid_values = [e.value for e in enum_class]
    if value in valid_values:
        return value
    return default


def sanitize_string(value, default=''):
    """
    Membersihkan dan mengembalikan string yang sudah strip.
    Jika None atau bukan string, kembalikan default.
    """
    if isinstance(value, str):
        return value.strip()
    return default
