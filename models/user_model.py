#Model/user_model.py
from flask_login import UserMixin
from extensions import db, bcrypt

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='kasir')  # kasir, admin, owner
    nama_lengkap = db.Column(db.String(100))
    penjualan = db.relationship('Penjualan', backref='kasir', lazy=True, overlaps="penjualan_user")
    buku_kas = db.relationship('BukuKas', back_populates='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __init__(self, username, password, role='kasir', nama_lengkap=None):
        self.username = username
        self.set_password(password)
        self.role = role
        self.nama_lengkap = nama_lengkap

    def __repr__(self):
        return f'<User {self.username}>'
    
