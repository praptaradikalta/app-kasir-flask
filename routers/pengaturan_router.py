# pengaturan_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Pengaturan

pengaturan = Blueprint('pengaturan', __name__)

@pengaturan.route('/', methods=['GET', 'POST'])
@login_required
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
        flash('Pengaturan berhasil disimpan!', 'success')
        return redirect(url_for('pengaturan.pengaturan_list'))

    return render_template('pengaturan.html', settings=settings)
