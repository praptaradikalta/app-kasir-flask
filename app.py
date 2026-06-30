#Kode app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from sqlalchemy import text
from models import User
from models import Produk

# Import ekstensi dari extensions.py
from extensions import db, bcrypt

app = Flask(__name__)
app.config.from_object('config.Config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.instance_path + '/kasir.db'

# Inisialisasi ekstensi dulu
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

# Import blueprint
from routers.user_router import user_bp
from routers.produk_router import produk
from routers.penjualan_router import penjualan
from routers.laporan_router import laporan
from routers.pengaturan_router import pengaturan

app.register_blueprint(user_bp)
app.register_blueprint(produk)
app.register_blueprint(penjualan)
app.register_blueprint(laporan)
app.register_blueprint(pengaturan)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Tambahkan route dan logika aplikasi di sini...
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        print(user)
        print(user.check_password(password))
        if user and user.check_password(password):
            login_user(user)
            flash('Login berhasil!', 'success')
            print('Login success')
            next_page = request.args.get('next')
            print('next page dah lewat')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        omzet = 0
        cash = 0      
        return render_template('dashboard.html', omzet=omzet, cash=cash, user=current_user)
    except Exception as e:
        flash(f"Error: {e}", 'error')
        return render_template('dashboard.html', omzet=0, cash=0, user=current_user)
    


@app.route('/input_penjualan', methods=['GET', 'POST'])
@login_required
def input_penjualan():
    if request.method == 'POST':
        try:
            db.session.execute('INSERT INTO penjualan (tanggal, total_bayar, user_id) VALUES (DATE("now"), :total, :user_id)', {'total': request.form['total'], 'user_id': current_user.id})
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Error: {e}", 'error')
    return render_template('input_penjualan.html')

@app.route('/penjualan')
def penjualan():
    return render_template('penjualan.html')

@app.route('/laporan')
def laporan():
    return render_template('laporan.html')

@app.route('/pengaturan')
def pengaturan():
    return render_template('pengaturan.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

