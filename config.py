# config.py
class Config:
    # Konfigurasi aplikasi
    SECRET_KEY = 'rahasia_banget'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = None
