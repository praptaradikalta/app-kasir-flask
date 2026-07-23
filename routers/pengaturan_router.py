# pengaturan_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Pengaturan
from utils import admin_required, catat_log, backup_database
import os

pengaturan = Blueprint('pengaturan', __name__)

@pengaturan.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def pengaturan_list():
    settings = Pengaturan.get_settings()

    if request.method == 'POST':
        settings.nama_toko = request.form.get('nama_toko', '').strip() or settings.nama_toko
        settings.alamat = request.form.get('alamat', '').strip()
        settings.no_telp = request.form.get('no_telp', '').strip()
        settings.mata_uang = request.form.get('mata_uang', 'IDR')

        try:
            settings.pajak_persen = float(request.form.get('pajak_persen', 0) or 0)
            settings.service_charge_persen = float(request.form.get('service_charge_persen', 0) or 0)
        except ValueError:
            flash('Pajak dan biaya layanan harus berupa angka.', 'danger')
            return render_template('pengaturan.html', settings=settings)

        settings.catatan_struk = request.form.get('catatan_struk', '').strip()

        db.session.commit()
        catat_log('EDIT_PENGATURAN', f'Mengubah pengaturan toko (nama: {settings.nama_toko}, pajak: {settings.pajak_persen}%, service charge: {settings.service_charge_persen}%).')
        flash('Pengaturan berhasil disimpan!', 'success')
        return redirect(url_for('pengaturan.pengaturan_list'))

    # Daftar backup yang udah ada, buat ditampilkan di halaman
    backup_dir = os.path.join('instance', 'backups')
    daftar_backup = []
    if os.path.isdir(backup_dir):
        for fn in sorted(os.listdir(backup_dir), reverse=True):
            fp = os.path.join(backup_dir, fn)
            if os.path.isfile(fp):
                daftar_backup.append({
                    'nama': fn,
                    'ukuran_kb': round(os.path.getsize(fp) / 1024, 1)
                })

    return render_template('pengaturan.html', settings=settings, daftar_backup=daftar_backup)


@pengaturan.route('/backup-sekarang', methods=['POST'])
@login_required
@admin_required
def backup_sekarang():
    backup_database()
    catat_log('BACKUP_MANUAL', 'Backup database dijalankan manual dari halaman Pengaturan.')
    flash('Backup database berhasil dibuat! Cek folder instance/backups/.', 'success')
    return redirect(url_for('pengaturan.pengaturan_list'))
