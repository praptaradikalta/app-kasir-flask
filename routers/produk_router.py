from utils import parse_int, parse_bool, validate_enum, sanitize_string
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.produk_model import Produk, KategoriEnum
from extensions import db
from flask_login import login_required
from models.stok import Stok
from models.stok_harian_model import StokHarian
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
def list_produk():
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

@produk.route('/tambah', methods=['POST'])
@login_required
def tambah_produk():
    print("\n>>> [DEBUG] Memulai proses tambah_produk...") # Indikator awal
    
    if request.method == 'POST':
        # 1. Ambil data dari Form
        kode = request.form.get('kode')
        nama = sanitize_string(request.form.get('nama_produk'))
        kategori = request.form.get('kategori')
        h_jual = parse_int(request.form.get('harga_jual'))
        h_beli = parse_int(request.form.get('harga_beli'))
        h_beli_supp = parse_int(request.form.get('harga_beli_supplier') or 0)
        is_konsinyasi = bool(int(request.form.get('is_konsinyasi', 0)))
        
        # PERBAIKAN: Ambil nilai stok dari form agar tidak undefined
        stok_awal = parse_int(request.form.get('stok') or 0) 
        
        # 2. Penanganan Gambar (Source [1])
        file = request.files.get('gambar')
        filename = secure_filename(file.filename) if file and file.filename != '' else None
        if filename:
            file.save(os.path.join('static/uploads', filename))
            print(f">>> [DEBUG] Gambar disimpan: {filename}")

        try:
            # 3. Buat Objek Produk
            print(">>> [DEBUG] Membuat objek Produk...")
            produk_baru = Produk(
                kode=kode,
                nama_produk=nama,
                kategori=kategori,
                harga_jual=h_jual,
                harga_beli=h_beli,
                harga_beli_supplier=h_beli_supp,
                is_konsinyasi=is_konsinyasi,
                gambar=filename
            )

            # PERBAIKAN: Gunakan nama variabel yang konsisten (produk_baru)
            db.session.add(produk_baru)
            db.session.flush() # Mendapatkan ID produk tanpa commit dulu
            print(f">>> [DEBUG] Produk berhasil di-flush. ID Baru: {produk_baru.id}")

            # 4. Inisialisasi Stok (Relasi)
            rekap = Stok(produk_id=produk_baru.id, jumlah=stok_awal)
            db.session.add(rekap)
            print(">>> [DEBUG] Inisialisasi tabel Stok...")

            # 5. Catat Sejarah Stok Awal
            rincian = StokHarian(produk_id=produk_baru.id, jumlah=stok_awal, keterangan="Stok Awal")
            db.session.add(rincian)
            print(">>> [DEBUG] Mencatat StokHarian...")

            # 6. Simpan Permanen (Source [2, 3])
            db.session.commit() 
            print(">>> [DEBUG] COMMIT BERHASIL! Data tersimpan di SQLite.")
            flash(f'Produk {nama} berhasil disimpan!', 'success')
            
            print(f">>> [DEBUG] Data diterima: Nama={nama}, Kode={kode}, Stok={stok_awal}")           
        except Exception as e:
            print(f">>> [DEBUG] ERROR saat ambil data form: {e}")
            db.session.rollback() # Batalkan semua jika ada satu saja yang gagal
            flash(f'Gagal menyimpan: {str(e)}', 'danger')
            print(f">>> [DEBUG] !!! DATABASE ERROR !!!: {str(e)}")

    print(">>> [DEBUG] Redirecting ke list_produk...\n")
    return redirect(url_for('produk.list_produk'))

# update edit_produk juga biar bisa ganti gambar
@produk.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_produk(id):
    produk = Produk.query.get_or_404(id)
    try:
        # 1. Update Data Dasar
        produk.nama_produk = request.form.get('nama_produk')
        produk.kategori = request.form.get('kategori')
        produk.harga_jual = int(request.form.get('harga_jual'))
        produk.harga_beli = int(request.form.get('harga_beli') or 0)
        produk.harga_beli_supplier = int(request.form.get('harga_beli_supplier') or 0)
        
        # 2. Logika Gambar (Jika ada upload baru)
        file = request.files.get('gambar')
        if file and file.filename:
            # Tambahkan fungsi validasi gambar Anda di sini
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            produk.gambar = filename

        db.session.commit()
        flash(f'Produk {produk.nama_produk} berhasil diupdate!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saat update: {str(e)}', 'danger')
        
    return redirect(url_for('produk.list_produk')) # Pastikan nama endpoint benar

@produk.route('/hapus/<int:id>')
@login_required
def hapus_produk(id):
    print(f"\n>>> [DEBUG] Memulai proses hapus_produk ID: {id}")
    
    # 1. Cari produk, jika tidak ada langsung 404
    produk = Produk.query.get_or_404(id)
    nama_produk = produk.nama_produk # Simpan nama untuk pesan flash

    try:
        # 2. Hapus data di tabel Stok (Rekap)
        print(f">>> [DEBUG] Menghapus data Stok untuk produk ID: {id}")
        Stok.query.filter_by(produk_id=id).delete()

        # 3. Hapus data di tabel StokHarian (Riwayat)
        print(f">>> [DEBUG] Menghapus riwayat StokHarian untuk produk ID: {id}")
        StokHarian.query.filter_by(produk_id=id).delete()

        # 4. Hapus Produk utama
        print(f">>> [DEBUG] Menghapus data Produk: {nama_produk}")
        db.session.delete(produk)

        # FINAL COMMIT
        db.session.commit()
        print(">>> [DEBUG] COMMIT BERHASIL! Produk dan relasinya terhapus.")
        flash(f'Produk {nama_produk} berhasil dihapus!', 'success')

    except Exception as e:
        db.session.rollback()
        print(f">>> [DEBUG] !!! GAGAL MENGHAPUS !!!: {str(e)}")
        # Gunakan kategori 'danger' agar muncul warna merah di Bootstrap
        flash(f'Gagal menghapus produk: {str(e)}', 'danger')

    print(">>> [DEBUG] Redirecting ke list_produk...\n")
    return redirect(url_for('produk.list_produk'))

@produk.route('/restok', methods=['POST'])
@login_required
def restok_produk():
    p_id = request.form.get('produk_id')
    qty_tambah = int(request.form.get('jumlah_tambah', 0))
    ket = request.form.get('keterangan', 'Restok Produk')

    try:
        # 1. Update Tabel STOK (Rekap)
        stok_obj = Stok.query.filter_by(produk_id=p_id).first()
        if stok_obj:
            stok_obj.jumlah += qty_tambah
        
        # 2. Tambah Baris ke STOK_HARIAN (Log)
        log = StokHarian(produk_id=p_id, jumlah=qty_tambah, keterangan=ket)
        db.session.add(log)
        
        db.session.commit()
        flash('Stok berhasil diperbarui!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui stok: {str(e)}', 'danger')
    
    return redirect(url_for('produk.list_produk'))