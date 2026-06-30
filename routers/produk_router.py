#Kode produk_router.py
from utils import parse_int, parse_bool, validate_enum, sanitize_string
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.produk_model import Produk, KategoriEnum
from extensions import db
from flask_login import login_required
from models.stok import Stok

produk = Blueprint('produk', __name__)

from utils import parse_int, parse_bool, validate_enum, sanitize_string
from models.produk_model import KategoriEnum

@produk.route('/produk', methods=['GET', 'POST'])
@login_required
def produk_list():
    kategoris = [kategori.value for kategori in KategoriEnum]
    produks = Produk.query.all()

    if request.method == 'POST':
        nama = sanitize_string(request.form.get('nama_produk'))
        kategori = validate_enum(request.form.get('kategori'), KategoriEnum)
        stok_awal = parse_int(request.form.get('stok'))
        harga_beli = parse_int(request.form.get('harga_beli'))
        harga_jual = parse_int(request.form.get('harga_jual'))
        is_konsinyasi = bool(int(request.form.get('is_konsinyasi', 0)))

        if not nama:
            flash('Nama produk wajib diisi', 'error')
            return redirect(url_for('produk.produk_list'))

        if not kategori:
            flash('Kategori tidak valid', 'error')
            return redirect(url_for('produk.produk_list'))

        if harga_jual < harga_beli:
            flash('Harga jual tidak boleh lebih kecil dari harga beli!', 'error')
            return redirect(url_for('produk.produk_list'))

        produk_baru = Produk(
            nama_produk=nama,
            kategori=kategori,
            harga_beli=harga_beli,
            harga_jual=harga_jual,
            is_konsinyasi=is_konsinyasi
        )

        try:
            db.session.add(produk_baru)
            db.session.commit()

            if stok_awal > 0:
                stok_obj = Stok(produk_id=produk_baru.id, jumlah=stok_awal)
                db.session.add(stok_obj)
                db.session.commit()

            flash('Produk berhasil ditambah', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saat menyimpan produk: {e}', 'error')

        return redirect(url_for('produk.produk_list'))

    return render_template('produk/add_produk.html', produks=produks, kategoris=kategoris)


@produk.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_produk(id):
    produk = Produk.query.get_or_404(id)
    kategoris = [k.value for k in KategoriEnum]
    stok_obj = produk.stok

    if request.method == 'POST':
        produk.nama_produk = request.form['nama_produk']
        produk.kategori = request.form['kategori']
        produk.harga_beli = int(float(request.form.get('harga_beli', produk.harga_beli or 0)))
        produk.harga_jual = int(float(request.form.get('harga_jual', produk.harga_jual or 0)))
        produk.is_konsinyasi = bool(int(request.form.get('is_konsinyasi', 0)))
        produk.harga_beli_supplier = int(float(request.form.get('harga_beli_supplier', produk.harga_beli_supplier or 0)))

        stok_baru = int(float(request.form['stok']))
        if stok_obj:
            stok_obj.jumlah = stok_baru
        else:
            stok_obj = Stok(produk_id=produk.id, jumlah=stok_baru)
            db.session.add(stok_obj)

        try:
            db.session.commit()
            flash('Produk berhasil diupdate!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saat update produk: {e}', 'error')

        return redirect(url_for('produk.produk_list'))

    return render_template('produk/edit_produk.html',
                           produk=produk,
                           kategoris=kategoris,
                           stok=stok_obj.jumlah if stok_obj else 0)

@produk.route('/hapus/<int:id>')
@login_required
def hapus_produk(id):
    produk = Produk.query.get_or_404(id)
    db.session.delete(produk)
    db.session.commit()
    flash('Produk berhasil dihapus!', 'success')
    return redirect(url_for('produk.produk_list'))