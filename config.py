# config.py
import os

class Config:
    # Konfigurasi aplikasi
    SECRET_KEY = 'rahasia_banget'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = None

    # --- Konfigurasi Email (buat fitur Reset Password) ---
    # Isi lewat environment variable, JANGAN hardcode password email di sini.
    # Contoh kalau pakai Gmail:
    #   1. Aktifkan 2-Step Verification di akun Gmail kamu
    #   2. Buat "App Password" khusus di https://myaccount.google.com/apppasswords
    #   3. Set environment variable sebelum jalanin aplikasi:
    #        export MAIL_USERNAME="emailtokokamu@gmail.com"
    #        export MAIL_PASSWORD="app_password_16_digit_dari_google"
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
