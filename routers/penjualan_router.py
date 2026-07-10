# penjualan_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.penjualan import Penjualan
from models.meja import Meja
from sqlalchemy import text # import text

# Inisialisasi Blueprint
penjualan = Blueprint('penjualan', __name__)

@penjualan.route('/order/buat', methods=['GET', 'POST'])
@login_required
def buat_order():
    if request.method == 'POST':
        # 1. Mengambil data dari form HTML
        tipe = request.form.get('tipe_pesanan')
        meja_id = request.form.get('meja_id')
        
        # 2. Inisialisasi Transaksi Baru di tabel Penjualan
        order_baru = Penjualan(
            user_id=current_user.id, # Mencatat kasir yang melayani [1]
            tipe_pesanan=tipe,
            status='Proses',
            total_bayar=0
        )

        # 3. Logika Khusus jika "Dine In" atau "Reservasi"
        if tipe != 'Take Away' and meja_id:
            order_baru.meja_id = int(meja_id)
            
            # Update status meja menjadi 'terisi' secara otomatis
            meja = db.session.get(Meja, int(meja_id))
            if meja:
                meja.status = 'terisi'

        try:
            # 4. Simpan ke Database [2]
            db.session.add(order_baru)
            db.session.commit()
            
            flash(f'Pesanan {tipe} berhasil dibuat!', 'success') # [3]
            
            # 5. Arahkan ke halaman pemilihan menu produk
            return redirect(url_for('penjualan.pilih_menu', order_id=order_baru.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')
            return redirect(url_for('penjualan.buat_order'))

    # Jika metode GET: Tampilkan form dan daftar meja yang kosong
    meja_tersedia = Meja.query.filter_by(status='kosong').all()
    return render_template('penjualan/buat_order.html', meja_tersedia=meja_tersedia)

@penjualan.route('/')
def penjualan_list():
    data = db.session.execute(text("SELECT * FROM penjualan")).fetchall()
    return render_template('penjualan.html', penjualan=data)