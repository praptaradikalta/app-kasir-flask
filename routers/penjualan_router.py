# penjualan_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.produk_model import Produk
from models.penjualan import Penjualan
from models.penjualan_detail import PenjualanDetail
from models.stok import Stok
from models.stok_harian_model import StokHarian
from models.bukukas import BukuKas

penjualan = Blueprint('penjualan', __name__, url_prefix='/penjualan')

@penjualan.route('/')
@login_required
def index_kasir():
    # Menampilkan semua produk untuk dipilih kasir
    produk_list = Produk.query.all() 
    return render_template('penjualan/kasir.html', produk_list=produk_list)

@penjualan.route('/dapur')
@login_required
def antrean_dapur():
    # Filter hanya yang statusnya 'Dapur'
    pesanan_dapur = Penjualan.query.filter_by(status='Dapur').all()
    return render_template('penjualan/antrean_dapur.html', pesanan=pesanan_dapur)

# Fungsi untuk memindahkan pesanan dari Dapur ke Meja Kasir (Belum Lunas)
@penjualan.route('/siap_saji/<int:id>')
@login_required
def siap_saji(id):
    transaksi = Penjualan.query.get_or_404(id)
    transaksi.status = 'Belum Lunas' # Pindah ke daftar tagihan kasir
    db.session.commit()
    flash(f'Pesanan #{id} selesai dikerjakan dan siap di kasir.', 'info')
    return redirect(url_for('penjualan.antrean_dapur'))

@penjualan.route('/antrean')
@login_required
def antrean_pengerjaan():
    # Mengambil semua pesanan yang statusnya masih 'Dapur' (sedang disiapkan)
    pesanan_aktif = Penjualan.query.filter_by(status='Dapur').order_by(Penjualan.tanggal.asc()).all()
    return render_template('penjualan/antrean_pengerjaan.html', pesanan=pesanan_aktif)

@penjualan.route('/siap-item/<int:id>')
@login_required
def toggle_siap_item(id):
    item = PenjualanDetail.query.get_or_404(id)
    item.is_ready = not item.is_ready # Toggle status True/False
    db.session.commit()
    return redirect(url_for('penjualan.antrean_pengerjaan'))

@penjualan.route('/tagihan')
@login_required
def daftar_tagihan():
    # Filter hanya yang statusnya 'Belum Lunas'
    tagihan_aktif = Penjualan.query.filter_by(status='Belum Lunas').all()
    return render_template('penjualan/tagihan.html', orders=tagihan_aktif)

@penjualan.route('/cetak/<int:id>')
@login_required
def cetak_nota(id):
    # Ambil data penjualan berdasarkan ID
    transaksi = Penjualan.query.get_or_404(id)
    return render_template('penjualan/cetak_nota.html', t=transaksi)

@penjualan.route('/riwayat')
@login_required
def riwayat_penjualan():
    # Menampilkan daftar penjualan dari yang terbaru
    daftar_penjualan = Penjualan.query.order_by(Penjualan.tanggal.desc()).all()
    return render_template('penjualan/riwayat.html', daftar_penjualan=daftar_penjualan)

@penjualan.route('/tambah', methods=['POST'])
@login_required
def proses_transaksi():
    if request.method == 'POST':
        # 1. Ambil data Header Penjualan
        meja_id = request.form.get('meja_id')
        customer_id = request.form.get('customer_id')
        tipe_pesanan = request.form.get('tipe_pesanan') # 'Makan di Tempat' atau 'Bungkus'
        total_bayar = int(request.form.get('total_bayar', 0))
        
        # --- LOGIKA STATUS DISISIPKAN DI SINI ---
        if tipe_pesanan == 'Makan di Tempat':
            # Jika Dine In, status awal masuk ke antrean pengerjaan
            status_awal = 'Dapur'
            uang_diterima = 0
            uang_kembalian = 0
        else:
            # Jika Take Away/Bungkus, diasumsikan langsung bayar di tempat
            status_awal = 'Lunas'
            uang_diterima = int(request.form.get('bayar', 0))
            uang_kembalian = uang_diterima - total_bayar
        # ----------------------------------------

        # 2. Ambil list produk
        produk_ids = request.form.getlist('produk_id[]')
        qtys = request.form.getlist('qty[]')
        varians = request.form.getlist('varian[]')

        try:
            # 3. Simpan Induk Penjualan (Gunakan variabel status_awal)
            baru = Penjualan(
                total_bayar=total_bayar,
                bayar=uang_diterima,
                kembalian=uang_kembalian,
                user_id=current_user.id,
                customer_id=customer_id if customer_id else None,
                meja_id=meja_id if meja_id else None,
                tipe_pesanan=tipe_pesanan,
                status=status_awal # Menggunakan logika status otomatis
            )
            db.session.add(baru)
            db.session.flush()

            # 4. Loop Simpan Detail & Potong Stok
            for i in range(len(produk_ids)):
                p_id = int(produk_ids[i])
                p_qty = int(qtys[i])
                p_varian = varians[i] if i < len(varians) else None
                produk_obj = Produk.query.get(p_id)
                
                # Logika Biaya Tambahan Mie Pansit
                harga_final = produk_obj.harga_jual
                if p_varian == 'Mie Pansit' and ('Miso' in produk_obj.nama_produk or 'Bakso' in produk_obj.nama_produk):
                   harga_final += 1000 # Tambah seribu rupiah

                detail = PenjualanDetail(
                    penjualan_id=baru.id,
                    produk_id=p_id,
                    qty=p_qty,
                    harga_satuan=harga_final, # Gunakan harga yang sudah ditambah biaya pansit
                    varian=p_varian,
                    is_ready=False # Default item belum dimasak [Riwayat]
                )
                db.session.add(detail)

                # 5. Potong Stok
                stok_item = Stok.query.filter_by(produk_id=p_id).first()
                if stok_item:
                    stok_item.jumlah -= p_qty # Kurangi stok
                    riwayat = StokHarian(
                        produk_id=p_id,
                        jumlah=-p_qty,
                        keterangan=f"Pesanan Nota #{baru.id} ({p_varian})"
                    )
                    db.session.add(riwayat)  

            db.session.commit() 
            
            # Pesan Flash yang lebih dinamis
            if status_awal == 'Dapur':
                flash(f'Pesanan Meja {meja_id} berhasil dikirim ke Dapur & Bar!', 'success')
            else:
                flash(f'Transaksi berhasil! Kembalian: Rp {uang_kembalian:,}', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal: {str(e)}', 'danger')

    return redirect(url_for('user.dashboard'))

@penjualan.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_nota(id):
    # Mengambil data nota utama
    nota = Penjualan.query.get_or_404(id)
    
    # --- DEBUG 1: Informasi Dasar Nota (GET & POST) ---
    print(f"\n[DEBUG EDIT] Memproses Nota ID: {id}")
    print(f"[DEBUG EDIT] Nomor Meja: {nota.meja_id}")
    print(f"[DEBUG EDIT] Jumlah item dalam database: {len(nota.items)}")
    
    if request.method == 'POST':
        # Simpan informasi header
        nota.meja_id = request.form.get('meja_id') 
        nota.tipe_pesanan = request.form.get('tipe_pesanan')
           
        # --- DEBUG 2: Data yang Diterima dari Form ---
        produk_ids = request.form.getlist('produk_id[]')
        varians = request.form.getlist('varian[]')
        qtys = request.form.getlist('qty[]')
        
        print(f"[DEBUG POST] Diterima {len(produk_ids)} jenis produk dari keranjang.")
        print(f"[DEBUG POST] Data Diterima: IDs={produk_ids}, Varians={varians}, Qtys={qtys}")

        if not produk_ids:
            print("[DEBUG POST] PERINGATAN: Tidak ada produk yang diterima dari form!")

        # --- Hitung qty LAMA per produk (sebelum diedit), untuk keperluan
        #     penyesuaian stok. Wajib diambil SEBELUM detail lama dihapus.
        qty_lama_per_produk = {}
        for d in PenjualanDetail.query.filter_by(penjualan_id=id).all():
            qty_lama_per_produk[d.produk_id] = qty_lama_per_produk.get(d.produk_id, 0) + d.qty

        # 1. Hapus detail lama agar tidak ganda
        PenjualanDetail.query.filter_by(penjualan_id=id).delete()
        print(f"[DEBUG POST] Menghapus detail lama untuk nota #{id}")
        
        total_baru = 0
        qty_baru_per_produk = {}
        for i in range(len(produk_ids)):
            p_id = int(produk_ids[i])
            p_qty = int(qtys[i])
            p_varian = varians[i]
            produk_obj = Produk.query.get(p_id)
            
            # Logika perhitungan harga
            harga_item = produk_obj.harga_jual
            if p_varian == 'Mie Pansit' and ('Miso' in produk_obj.nama_produk or 'Bakso' in produk_obj.nama_produk):
                harga_item += 1000
            
            subtotal = harga_item * p_qty
            total_baru += subtotal
            qty_baru_per_produk[p_id] = qty_baru_per_produk.get(p_id, 0) + p_qty
            
            print(f"   -> Item {i+1}: {produk_obj.nama_produk} | Varian: {p_varian} | Qty: {p_qty} | Subtotal: {subtotal}")
            
            # Simpan detail baru
            detail = PenjualanDetail(penjualan_id=id, produk_id=p_id, qty=p_qty, 
                                     harga_satuan=harga_item, varian=p_varian)
            db.session.add(detail)

        # --- Sesuaikan stok berdasarkan SELISIH qty lama vs qty baru ---
        # Kalau qty nambah (mis. 2 -> 5): stok DIKURANGI 3 (barang tambahan terjual).
        # Kalau qty berkurang (mis. 5 -> 2): stok DIKEMBALIKAN 3 (batal terjual).
        semua_produk_id = set(qty_lama_per_produk.keys()) | set(qty_baru_per_produk.keys())
        for p_id in semua_produk_id:
            qty_lama = qty_lama_per_produk.get(p_id, 0)
            qty_baru = qty_baru_per_produk.get(p_id, 0)
            selisih = qty_baru - qty_lama  # positif = tambah terjual, negatif = dibatalkan

            if selisih == 0:
                continue

            stok_item = Stok.query.filter_by(produk_id=p_id).first()
            if stok_item:
                stok_item.jumlah -= selisih

            riwayat = StokHarian(
                produk_id=p_id,
                jumlah=-selisih,
                keterangan=f'Edit Order Nota #{id}' + (' (tambah item)' if selisih > 0 else ' (kurangi item)')
            )
            db.session.add(riwayat)
        
        nota.total_bayar = total_baru

        # Kalau form ini dibuka dari tombol "PROSES BAYAR", catat pembayarannya
        # dan tandai transaksi sebagai Lunas. Kalau cuma "Edit Order" biasa,
        # status transaksi tidak diubah (tetap Belum Lunas / apa adanya).
        aksi = request.args.get('aksi')
        if aksi == 'bayar':
            uang_diterima = int(request.form.get('bayar', 0))
            nota.bayar = uang_diterima
            nota.kembalian = uang_diterima - total_baru
            nota.status = 'Lunas'
            print(f"[DEBUG POST] Pelunasan diproses. Bayar: {uang_diterima}, Kembalian: {nota.kembalian}")

            # Catat otomatis ke Buku Kas sebagai kas masuk dari transaksi penjualan
            kas_masuk = BukuKas(
                user_id=current_user.id,
                penjualan_id=nota.id,
                jenis='masuk',
                keterangan=f'Penjualan Meja {nota.meja_id} (Nota #{nota.id})',
                jumlah=total_baru
            )
            db.session.add(kas_masuk)

        db.session.commit()
        print(f"[DEBUG POST] Sukses Update! Total Bayar Akhir: Rp {total_baru}")
        
        flash('Pembayaran berhasil diproses!' if aksi == 'bayar' else 'Nota berhasil diperbarui!', 'success')
        return redirect(url_for('penjualan.daftar_tagihan'))
        
    # Logika untuk tampilan (GET)
    produk_list = Produk.query.all() 
    
    # --- DEBUG 3: Verifikasi Data Sebelum Template Dimuat ---
    print(f"[DEBUG GET] Produk List tersedia: {len(produk_list)} menu")
    print(f"[DEBUG GET] Item yang dikirim ke HTML:")
    for item in nota.items:
        print(f"   - {item.produk.nama_produk} (ID: {item.produk_id}) | Varian: {item.varian}")
    print("--- END DEBUG ---\n")
    
    return render_template('penjualan/kasir.html', 
                           edit_mode=True, 
                           nota=nota, 
                           produk_list=produk_list,
                           mode_bayar=(request.args.get('aksi') == 'bayar'))

@penjualan.route('/hapus/<int:id>', methods=['POST'])
@login_required
def hapus_transaksi(id):
    transaksi = Penjualan.query.get_or_404(id)
    
    try:
        # 1. Logika Kembalikan Stok (Sangat Penting!)
        for detail in transaksi.items:
            stok_item = Stok.query.filter_by(produk_id=detail.produk_id).first()
            if stok_item:
                stok_item.jumlah += detail.qty # Tambahkan kembali stok yang terjual
                
                # Catat ke Riwayat Stok Harian sebagai penyesuaian (nilai positif)
                riwayat = StokHarian(
                    produk_id=detail.produk_id,
                    jumlah=detail.qty,
                    keterangan=f"Pembatalan/Hapus Nota #{id}"
                )
                db.session.add(riwayat)
        
        # 2. Hapus detail transaksi terlebih dahulu jika tidak diatur cascade
        for detail in transaksi.items:
            db.session.delete(detail)
            
        # 3. Hapus induk penjualan
        db.session.delete(transaksi)
        db.session.commit()
        flash(f'Nota #{id} berhasil dihapus dan stok dikembalikan.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus transaksi: {str(e)}', 'danger')
        
    return redirect(url_for('penjualan.riwayat_penjualan'))

"""
Ringkasan Alur Berdasarkan Status:
Status: Dapur
Pesanan muncul di layar tablet Dapur/Stand Minuman [602, Riwayat Percakapan].
Orang dapur melihat rincian menu dan varian mie (Mie Kuning/Putih) untuk dimasak [Riwayat Percakapan].

Status: Belum Lunas
Setelah dapur klik "Selesai", pesanan hilang dari layar dapur dan muncul di Meja Kasir (Daftar Tagihan) [Riwayat Percakapan].
Kasir tahu meja mana saja yang sedang makan dan belum bayar.

Status: Lunas
Setelah pelanggan membayar, kasir menginput uang tunai dan mengubah status menjadi 'Lunas' [28, Riwayat Percakapan].
Hanya pesanan berstatus 'Lunas' yang akan dihitung masuk ke Laporan Penjualan Harian [604, Riwayat Percakapan].

Apa saja yang berubah?
Penentuan status_awal: Sekarang sistem mengecek tipe_pesanan. 
Jika "Makan di Tempat", status otomatis diset menjadi 'Dapur' [Riwayat Percakapan].
Penanganan Uang: Untuk status 'Dapur', 
nilai bayar dan kembalian dipaksa menjadi 0 karena pembayaran belum terjadi saat order diinput [Riwayat Percakapan].
Kolom is_ready: Saya menambahkan is_ready=False 
pada saat membuat PenjualanDetail agar bagian Dapur/Bar bisa menandai porsi yang sudah selesai menggunakan fitur centang per item yang kita bahas tadi [Riwayat Percakapan].
Pesan Notifikasi: Kasir akan mendapatkan konfirmasi bahwa pesanan sudah terkirim 
ke dapur untuk pesanan Dine In, bukan sekadar info kembalian [Riwayat Percakapan].

"""
