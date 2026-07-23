# routers/bukukas_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from extensions import db
from models import BukuKas

bukukas = Blueprint('bukukas', __name__)

@bukukas.route('/')
@login_required
def bukukas_list():
    # Filter tanggal (default: hari ini)
    tgl_str = request.args.get('tanggal', date.today().isoformat())
    try:
        tgl = datetime.strptime(tgl_str, '%Y-%m-%d').date()
    except ValueError:
        tgl = date.today()
        tgl_str = tgl.isoformat()

    entries = BukuKas.query.filter(
        db.func.date(BukuKas.tanggal) == tgl
    ).order_by(BukuKas.tanggal.asc()).all()

    total_masuk = sum(e.jumlah for e in entries if e.jenis == 'masuk')
    total_keluar = sum(e.jumlah for e in entries if e.jenis == 'keluar')
    saldo = total_masuk - total_keluar

    return render_template('bukukas/list.html',
                           entries=entries,
                           tanggal=tgl_str,
                           total_masuk=total_masuk,
                           total_keluar=total_keluar,
                           saldo=saldo)

@bukukas.route('/tambah', methods=['GET', 'POST'])
@login_required
def bukukas_add():
    if request.method == 'POST':
        jenis = request.form.get('jenis')
        keterangan = request.form.get('keterangan', '').strip()
        jumlah_raw = request.form.get('jumlah', '0')

        if jenis not in ('masuk', 'keluar'):
            flash('Jenis kas tidak valid.', 'danger')
            return redirect(url_for('bukukas.bukukas_add'))

        try:
            jumlah = int(jumlah_raw)
        except ValueError:
            flash('Jumlah harus berupa angka.', 'danger')
            return redirect(url_for('bukukas.bukukas_add'))

        if jumlah <= 0:
            flash('Jumlah harus lebih dari 0.', 'danger')
            return redirect(url_for('bukukas.bukukas_add'))

        if not keterangan:
            flash('Keterangan wajib diisi.', 'danger')
            return redirect(url_for('bukukas.bukukas_add'))

        entry = BukuKas(
            user_id=current_user.id,
            jenis=jenis,
            keterangan=keterangan,
            jumlah=jumlah
        )
        db.session.add(entry)
        db.session.commit()
        flash(f'Kas {"masuk" if jenis == "masuk" else "keluar"} berhasil dicatat!', 'success')
        return redirect(url_for('bukukas.bukukas_list'))

    return render_template('bukukas/add.html')

@bukukas.route('/hapus/<int:id>')
@login_required
def bukukas_delete(id):
    entry = BukuKas.query.get_or_404(id)

    # Entri yang otomatis tercatat dari transaksi penjualan tidak boleh dihapus manual,
    # supaya catatan kas tetap sinkron dengan riwayat penjualan.
    if entry.penjualan_id is not None:
        flash('Kas dari transaksi penjualan tidak bisa dihapus manual.', 'danger')
        return redirect(url_for('bukukas.bukukas_list'))

    db.session.delete(entry)
    db.session.commit()
    flash('Catatan kas berhasil dihapus.', 'success')
    return redirect(url_for('bukukas.bukukas_list'))
