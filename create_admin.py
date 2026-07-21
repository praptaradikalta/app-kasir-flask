# create_admin.py
# Script buat bikin akun admin PERTAMA lewat terminal.
# Dipakai kalau database masih kosong / baru pertama kali setup,
# soalnya menu "Tambah User" di web cuma bisa diakses kalau udah ada
# admin yang login (ayam-telur).
#
# Cara pakai:
#   python create_admin.py

from app import app, db
from models import User
import getpass

with app.app_context():
    print("=== Buat Akun Admin ===\n")

    username = input("Username: ").strip()
    if not username:
        print("Username tidak boleh kosong.")
        raise SystemExit(1)

    if User.query.filter_by(username=username).first():
        print(f'Username "{username}" sudah dipakai. Pilih username lain atau login pakai akun itu.')
        raise SystemExit(1)

    password = getpass.getpass("Password (minimal 6 karakter): ")
    if len(password) < 6:
        print("Password minimal 6 karakter.")
        raise SystemExit(1)

    konfirmasi = getpass.getpass("Konfirmasi Password: ")
    if password != konfirmasi:
        print("Password dan konfirmasi tidak cocok.")
        raise SystemExit(1)

    nama_lengkap = input("Nama Lengkap (boleh kosong): ").strip()
    email = input("Email (boleh kosong, tapi wajib diisi kalau mau bisa reset password lewat email): ").strip()

    if email and User.query.filter_by(email=email).first():
        print(f'Email "{email}" sudah dipakai user lain.')
        raise SystemExit(1)

    admin = User(
        username=username,
        password=password,
        role='admin',
        nama_lengkap=nama_lengkap or None,
        email=email or None
    )
    db.session.add(admin)
    db.session.commit()

    print(f'\nBerhasil! Akun admin "{username}" sudah dibuat.')
    print("Sekarang kamu bisa login ke aplikasi pakai akun ini.")
