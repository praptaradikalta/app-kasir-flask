# app.py
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from extensions import db, bcrypt
from models import User
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Konfigurasi Database SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'kasir.db')

    # Inisialisasi Ekstensi
    db.init_app(app)
    bcrypt.init_app(app)
    migrate = Migrate(app, db)

    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'user.login' # Mengarah ke blueprint user

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrasi Blueprints
    from routers.user_router import user_bp
    from routers.produk_router import produk as produk_bp
    from routers.penjualan_router import penjualan as penjualan_bp
    from routers.laporan_router import laporan as laporan_bp
    from routers.pengaturan_router import pengaturan as pengaturan_bp

    # Mendaftarkan blueprint dengan prefix jika diperlukan
    app.register_blueprint(user_bp)
    app.register_blueprint(produk_bp, url_prefix='/produk')
    app.register_blueprint(penjualan_bp, url_prefix='/penjualan')
    app.register_blueprint(laporan_bp, url_prefix='/laporan')
    app.register_blueprint(pengaturan_bp, url_prefix='/pengaturan')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
