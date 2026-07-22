#Model/user_model.py
from flask_login import UserMixin
from extensions import db, bcrypt
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='kasir')  # kasir, admin, owner
    nama_lengkap = db.Column(db.String(100))
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    penjualan = db.relationship('Penjualan', backref='kasir', lazy=True, overlaps="penjualan_user")
    buku_kas = db.relationship('BukuKas', back_populates='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        """Bikin token reset password acak, berlaku 1 jam."""
        import secrets
        from datetime import timedelta
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return token

    def verify_reset_token(self, token):
        """Cek token reset masih cocok & belum kedaluwarsa."""
        if not self.reset_token or self.reset_token != token:
            return False
        if not self.reset_token_expiry or datetime.utcnow() > self.reset_token_expiry:
            return False
        return True

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None

    def __init__(self, username, password, role='kasir', nama_lengkap=None, email=None):
        self.username = username
        self.set_password(password)
        self.role = role
        self.nama_lengkap = nama_lengkap
        self.email = email

    def __repr__(self):
        return f'<User {self.username}>'
    
