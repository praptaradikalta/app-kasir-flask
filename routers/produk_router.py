from utils import parse_int, parse_bool, validate_enum, sanitize_string
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.produk_model import Produk, KategoriEnum
from extensions import db
from flask_login import login_required
from models.stok import Stok
import os
from werkzeug.utils import secure_filename

produk = Blueprint('produk', __name__)

UPLOAD_FOLDER = 'static/uploads/produk'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@produk.route('/', methods=['GET'])
@login_required
def produk_list():
    search = request.args.get('q', '')
    kategori_filter = request.args.get('kategori', 'Semua')

    query = Produk.query
    if search:
        query = query.filter(Produk.nama_produk.ilike(f'%{search}%'))
    if kategori_filter != 'Semua':
        query = query.filter_by(kategori=kategori_filter)

    produk_per_kategori = {}
    for k in KategoriEnum:
        list_produk = query.filter_by(kategori=k.value).all()
        if list_produk:
            produk_per_kategori[k.value] = list_produk

    return render_template('produk/list_produk.html', 
        produk_per_kategori=produk_per_kategori,
        search=search,
        kategori_filter=kategori_filter,
        kategoris=['Semua'] + [k.value for k in KategoriEnum]
    )

@produk.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah_produk():
    kategoris = [kategori.value for kategori in KategoriEnum]
    if request.method == 'POST':
        nama = sanitize_string(request.form.get('nama_produk'))
        kategori = validate_enum(request.form.get('kategori'), KategoriEnum)
        stok_awal = parse_int(request.form.get('stok'))
        harga_beli = parse_int(request.form.get('harga_beli'))
        harga_jual = parse_int(request.form.get('harga_jual'))
        is_konsinyasi = bool(int(request.form.get('is_konsinyasi', 0)))
        file = request.files.get('gambar')

        if not nama:
            flash('Nama produk wajib diisi', 'error')
            return redirect(url_for('produk.tambah_produk'))
        if not kategori:
            flash('Kategori tidak valid', 'error')
            return redirect(url_for('produk.tambah_produk'))
        if harga_jual < harga_beli:
            flash('Harga jual tidak boleh lebih kecil dari harga beli!', 'error')
            return redirect(url_for('produk.tambah_produk'))

        gambar_url = None
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('File harus gambar (png, jpg, jpeg, gif)', 'error')
                return redirect(url_for('produk.tambah_produk'))
            if file.content_length > MAX_FILE_SIZE:
                flash('Ukuran file maksimal 2MB', 'error')
                return redirect(url_for('produk.tambah_produk'))
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            gambar_url = f'/static/uploads/produk/{filename}'

        produk_baru = Produk(
            nama_produk=nama,
            kategori=kategori,
            harga_beli=harga_beli,
            harga_jual=harga_jual,
            is_konsinyasi=is_konsinyasi,
            gambar=gambar_url
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
    return render_template('/add_produk.html', kategoris=kategoris)

# update edit_produk juga biar bisa ganti gambar
@produk.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_produk(id):
    produk = Produk.query.get_or_404(id)
    kategoris = [k.value for k in KategoriEnum]
    stok_obj = produk.stok[0] if produk.stok else None
    if request.method == 'POST':
        produk.nama_produk = request.form['nama_produk']
        produk.kategori = request.form['kategori']
        produk.harga_beli = int(float(request.form.get('harga_beli', produk.harga_beli or 0)))
        produk.harga_jual = int(float(request.form.get('harga_jual', produk.harga_jual or 0)))
        produk.is_konsinyasi = bool(int(request.form.get('is_konsinyasi', 0)))
        file = request.files.get('gambar')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('File harus gambar (png, jpg, jpeg, gif)', 'error')
                return redirect(url_for('produk.edit_produk', id=id))
            if file.content_length > MAX_FILE_SIZE:
                flash('Ukuran file maksimal 2MB', 'error')
                return redirect(url_for('produk.edit_produk', id=id))
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            produk.gambar = f'/static/uploads/produk/{filename}'
        try:
            db.session.commit()
            flash('Produk berhasil diupdate!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saat update produk: {e}', 'error')
        return redirect(url_for('produk.produk_list'))
    return render_template('produk/edit_produk.html', produk=produk, kategoris=kategoris, stok=stok_obj.jumlah if stok_obj else 0)

@produk.route('/hapus/<int:id>')
@login_required
def hapus_produk(id):
 produk = Produk.query.get_or_404(id)
 try:
     db.session.delete(produk)
     db.session.commit()
     flash('Produk berhasil dihapus!', 'success')
 except Exception as e:
     db.session.rollback()
     flash(f'Error saat hapus produk: {e}', 'error')
 return redirect(url_for('produk.produk_list'))

