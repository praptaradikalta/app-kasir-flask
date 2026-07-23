# routes/user_route.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from forms.user_form import UserForm
from extensions import db
from models import User # Gunakan satu sumber impor saja
from models.penjualan import Penjualan
from models.produk_model import Produk
from models.shift import Shift
from utils import admin_required, catat_log, send_reset_email
from sqlalchemy import func
from datetime import date

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login berhasil!', 'success')
            catat_log('LOGIN', f'User "{username}" berhasil login.')
            
            # Perbaikan: Gunakan namespace blueprint 'user.dashboard'
            # Dan arahkan ke next_page jika ada
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
        else:
            flash('Username atau password salah', 'danger')
            catat_log('LOGIN_GAGAL', f'Percobaan login gagal untuk username "{username}".')
    return render_template('login.html')

@user_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first() if email else None

        # PENTING: pesan yang ditampilkan HARUS SAMA baik email-nya ketemu atau
        # tidak. Kalau beda, orang bisa "menebak" email mana yang terdaftar di
        # sistem (email enumeration) tinggal coba-coba lewat form ini.
        pesan_generik = 'Kalau email itu terdaftar, link reset password sudah dikirim. Silakan cek inbox (atau folder spam) kamu.'

        if user:
            token = user.generate_reset_token()
            db.session.commit()
            terkirim = send_reset_email(user, token)
            if terkirim:
                catat_log('MINTA_RESET_PASSWORD', f'Link reset password dikirim ke email user "{user.username}".')
            else:
                # Email gagal terkirim (SMTP belum dikonfigurasi dsb) - jangan
                # bocorkan detail teknis ke pengguna, cukup log di server.
                print(">>> [WARNING] Gagal kirim email reset. Cek konfigurasi MAIL_* di config.py / environment variable.")

        flash(pesan_generik, 'info')
        return redirect(url_for('user.login'))

    return render_template('forgot_password.html')

@user_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash('Link reset password tidak valid atau sudah kedaluwarsa. Silakan minta link baru.', 'danger')
        return redirect(url_for('user.forgot_password'))

    if request.method == 'POST':
        password_baru = request.form.get('password', '')
        konfirmasi = request.form.get('konfirmasi_password', '')

        if len(password_baru) < 6:
            flash('Password minimal 6 karakter.', 'danger')
            return render_template('reset_password.html', token=token)

        if password_baru != konfirmasi:
            flash('Konfirmasi password tidak cocok.', 'danger')
            return render_template('reset_password.html', token=token)

        user.set_password(password_baru)
        user.clear_reset_token()
        db.session.commit()
        catat_log('RESET_PASSWORD', f'User "{user.username}" berhasil reset password lewat email.')
        flash('Password berhasil diganti. Silakan login dengan password baru.', 'success')
        return redirect(url_for('user.login'))

    return render_template('reset_password.html', token=token)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    from routers.produk_router import BATAS_STOK_MENIPIS

    hari_ini = date.today()

    # Pendapatan & jumlah transaksi HARI INI (cuma yang beneran udah Lunas)
    ringkasan_hari_ini = db.session.query(
        func.sum(Penjualan.total_bayar).label('total_pendapatan'),
        func.count(Penjualan.id).label('total_transaksi')
    ).filter(
        func.date(Penjualan.tanggal) == hari_ini,
        Penjualan.status == 'Lunas'
    ).first()

    pendapatan_hari_ini = ringkasan_hari_ini.total_pendapatan or 0
    transaksi_hari_ini = ringkasan_hari_ini.total_transaksi or 0

    # Meja yang lagi ada pesanan aktif (belum lunas / masih di dapur) saat ini
    meja_terisi = db.session.query(Penjualan.meja_id).filter(
        Penjualan.status.in_(['Dapur', 'Belum Lunas']),
        Penjualan.meja_id.isnot(None)
    ).distinct().count()

    # Produk dengan stok di bawah batas menipis
    semua_produk = Produk.query.all()
    stok_menipis = len([
        p for p in semua_produk
        if (p.rekap_stok.jumlah if p.rekap_stok else 0) < BATAS_STOK_MENIPIS
    ])

    shift_aktif = Shift.query.filter_by(user_id=current_user.id, status='aktif').first()

    # Kalau shift yang aktif ternyata dibuka di hari sebelumnya (kelupaan ditutup),
    # kasih tau di dashboard biar kasir sadar & segera tutup shift lama itu.
    shift_lupa_ditutup = bool(shift_aktif and shift_aktif.waktu_mulai.date() != hari_ini)

    # Uang yang HARUSNYA ada di laci sekarang, berdasarkan shift kasir yang login
    # (modal awal + kas masuk - kas keluar dari Buku Kas sejak shift itu mulai)
    uang_di_laci = None
    if shift_aktif:
        from routers.shift_router import hitung_ringkasan_kas
        ringkasan_kas = hitung_ringkasan_kas(shift_aktif)
        uang_di_laci = ringkasan_kas['perkiraan_kas']

    return render_template('dashboard.html',
                           user=current_user,
                           pendapatan_hari_ini=pendapatan_hari_ini,
                           transaksi_hari_ini=transaksi_hari_ini,
                           meja_terisi=meja_terisi,
                           stok_menipis=stok_menipis,
                           shift_aktif=shift_aktif,
                           shift_lupa_ditutup=shift_lupa_ditutup,
                           uang_di_laci=uang_di_laci)

@user_bp.route('/logout')
@login_required
def logout():
    catat_log('LOGOUT', f'User "{current_user.username}" logout.')
    logout_user()
    return redirect(url_for('user.login'))

@user_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.all()
    return render_template('user/list.html', users=users)

@user_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def user_add():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username sudah dipakai, pilih username lain.', 'danger')
            return render_template('user/add.html', form=form)

        if form.email.data and User.query.filter_by(email=form.email.data).first():
            flash('Email sudah dipakai user lain.', 'danger')
            return render_template('user/add.html', form=form)

        if not form.password.data:
            flash('Password wajib diisi untuk user baru.', 'danger')
            return render_template('user/add.html', form=form)

        user = User(
            username=form.username.data,
            password=form.password.data,
            role=form.role.data,
            nama_lengkap=form.nama_lengkap.data,
            email=form.email.data or None
        )
        db.session.add(user)
        db.session.commit()
        catat_log('TAMBAH_USER', f'Menambahkan user "{user.username}" dengan role {user.role}.')
        flash('User berhasil ditambahkan!', 'success')
        return redirect(url_for('user.user_list'))
    return render_template('user/add.html', form=form)

@user_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(id):
    user = User.query.get_or_404(id) # Gunakan get_or_404 agar lebih aman
    form = UserForm(obj=user)
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing and existing.id != user.id:
            flash('Username sudah dipakai user lain.', 'danger')
            return render_template('user/edit.html', form=form, user=user)

        if form.email.data:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email and existing_email.id != user.id:
                flash('Email sudah dipakai user lain.', 'danger')
                return render_template('user/edit.html', form=form, user=user)

        user.username = form.username.data
        user.email = form.email.data or None
        user.role = form.role.data
        user.nama_lengkap = form.nama_lengkap.data
        password_diubah = bool(form.password.data)
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        catat_log('EDIT_USER', f'Mengubah data user "{user.username}"' + (' (termasuk ganti password).' if password_diubah else '.'))
        flash('User berhasil diupdate!', 'success')
        return redirect(url_for('user.user_list'))
    return render_template('user/edit.html', form=form, user=user)

@user_bp.route('/users/delete/<int:id>')
@login_required
@admin_required
def user_delete(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Kamu tidak bisa menghapus akunmu sendiri.', 'danger')
        return redirect(url_for('user.user_list'))
    username_dihapus = user.username
    db.session.delete(user)
    db.session.commit()
    catat_log('HAPUS_USER', f'Menghapus user "{username_dihapus}".')
    flash('User berhasil dihapus!', 'success')
    return redirect(url_for('user.user_list'))