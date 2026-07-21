# routers/bahanbaku_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import BahanBaku
<<<<<<< HEAD
from utils import admin_required, catat_log, recalculate_hpp_cascade
=======
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba

bahanbaku = Blueprint('bahanbaku', __name__)

@bahanbaku.route('/')
@login_required
<<<<<<< HEAD
@admin_required
=======
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba
def list_bahan():
    search = request.args.get('q', '')
    query = BahanBaku.query
    if search:
        query = query.filter(BahanBaku.nama_bahan.ilike(f'%{search}%'))
    bahan_list = query.order_by(BahanBaku.nama_bahan).all()
    return render_template('bahanbaku/list.html', bahan_list=bahan_list, search=search)

@bahanbaku.route('/tambah', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
=======
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba
def tambah_bahan():
    kode = request.form.get('kode', '').strip()
    nama = request.form.get('nama_bahan', '').strip()
    satuan = request.form.get('satuan', '').strip()

    if not nama:
        flash('Nama bahan wajib diisi.', 'danger')
        return redirect(url_for('bahanbaku.list_bahan'))

    if kode and BahanBaku.query.filter_by(kode=kode).first():
        flash('Kode bahan sudah dipakai.', 'danger')
        return redirect(url_for('bahanbaku.list_bahan'))

    try:
        harga = int(request.form.get('harga_beli_terakhir', 0) or 0)
        stok = float(request.form.get('stok', 0) or 0)
    except ValueError:
        flash('Harga dan stok harus berupa angka.', 'danger')
        return redirect(url_for('bahanbaku.list_bahan'))

    bahan = BahanBaku(
        kode=kode or None,
        nama_bahan=nama,
        satuan=satuan,
        harga_beli_terakhir=harga,
        stok=stok
    )
    db.session.add(bahan)
    db.session.commit()
    flash(f'Bahan baku "{nama}" berhasil ditambahkan!', 'success')
    return redirect(url_for('bahanbaku.list_bahan'))

@bahanbaku.route('/edit/<int:id>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def edit_bahan(id):
    bahan = BahanBaku.query.get_or_404(id)
    harga_lama = bahan.harga_beli_terakhir
=======
def edit_bahan(id):
    bahan = BahanBaku.query.get_or_404(id)
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba
    bahan.nama_bahan = request.form.get('nama_bahan', bahan.nama_bahan).strip()
    bahan.satuan = request.form.get('satuan', bahan.satuan).strip()
    try:
        bahan.harga_beli_terakhir = int(request.form.get('harga_beli_terakhir', 0) or 0)
    except ValueError:
        flash('Harga harus berupa angka.', 'danger')
        return redirect(url_for('bahanbaku.list_bahan'))

    db.session.commit()

<<<<<<< HEAD
    # Harga bahan berubah -> HPP racikan & produk yang pakai bahan ini (langsung
    # maupun tidak langsung lewat racikan) ikut disesuaikan otomatis
    recalculate_hpp_cascade(bahan)

    deskripsi = f'Mengubah bahan baku "{bahan.nama_bahan}".'
    if harga_lama != bahan.harga_beli_terakhir:
        deskripsi += f' Harga: Rp{harga_lama:,} -> Rp{bahan.harga_beli_terakhir:,}.'.replace(',', '.')
    catat_log('EDIT_BAHAN_BAKU', deskripsi)
=======
    # Harga bahan berubah -> HPP semua produk yang pakai bahan ini ikut disesuaikan
    for detail in bahan.detail_resep:
        if detail.resep.produk:
            detail.resep.produk.update_hpp()
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba

    flash(f'Bahan baku "{bahan.nama_bahan}" berhasil diupdate! HPP produk terkait ikut disesuaikan.', 'success')
    return redirect(url_for('bahanbaku.list_bahan'))

@bahanbaku.route('/restok', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
=======
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba
def restok_bahan():
    b_id = request.form.get('bahan_id')
    bahan = BahanBaku.query.get_or_404(b_id)
    try:
        qty_tambah = float(request.form.get('jumlah_tambah', 0))
        harga_baru = request.form.get('harga_beli_terakhir')
    except ValueError:
        flash('Jumlah harus berupa angka.', 'danger')
        return redirect(url_for('bahanbaku.list_bahan'))

    bahan.stok += qty_tambah
    if harga_baru:
        bahan.harga_beli_terakhir = int(harga_baru)
        db.session.commit()
<<<<<<< HEAD
        recalculate_hpp_cascade(bahan)
=======
        for detail in bahan.detail_resep:
            if detail.resep.produk:
                detail.resep.produk.update_hpp()
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba
    else:
        db.session.commit()

    flash(f'Stok bahan "{bahan.nama_bahan}" berhasil diperbarui!', 'success')
    return redirect(url_for('bahanbaku.list_bahan'))

@bahanbaku.route('/hapus/<int:id>')
@login_required
<<<<<<< HEAD
@admin_required
=======
>>>>>>> 47f79f93bd72a2496fbfbfbfcf5c782b714107ba
def hapus_bahan(id):
    bahan = BahanBaku.query.get_or_404(id)
    if bahan.detail_resep:
        flash(f'Bahan "{bahan.nama_bahan}" tidak bisa dihapus karena masih dipakai di resep produk.', 'danger')
        return redirect(url_for('bahanbaku.list_bahan'))
    db.session.delete(bahan)
    db.session.commit()
    flash('Bahan baku berhasil dihapus.', 'success')
    return redirect(url_for('bahanbaku.list_bahan'))
