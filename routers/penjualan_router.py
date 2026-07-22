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
from utils import catat_log, admin_required

penjualan = Blueprint('penjualan', __name__, url_prefix='/penjualan')

@penjualan.route('/')
@login_required
def index_kasir():
    # Menampilkan semua produk untuk dipilih kasir, dikelompokkan per kategori
    # biar kasir gak perlu scroll panjang buat nyari menu (terutama di HP).
    produk_list = Produk.query.order_by(Produk.nama_produk).all()

    produk_per_kategori = {}
    for p in produk_list:
        produk_per_kategori.setdefault(p.kategori, []).append(p)

    return render_template('penjualan/kasir.html', produk_list=produk_list, produk_per_kategori=produk_per_kategori)

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
    from datetime import datetime

    search = request.args.get('q', '').strip()
    tgl_str = request.args.get('tanggal', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = Penjualan.query
    if search:
        query = query.join(PenjualanDetail, Penjualan.id == PenjualanDetail.penjualan_id, isouter=True)\
                      .join(Produk, PenjualanDetail.produk_id == Produk.id, isouter=True)\
                      .filter(
                          db.or_(
                              Produk.nama_produk.ilike(f'%{search}%'),
                              db.cast(Penjualan.meja_id, db.String).ilike(f'%{search}%'),
                              db.cast(Penjualan.id, db.String).ilike(f'%{search}%')
                          )
                      ).distinct()

    if tgl_str:
        try:
            tgl = datetime.strptime(tgl_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Penjualan.tanggal) == tgl)
        except ValueError:
            tgl_str = ''

    # Menampilkan daftar penjualan dari yang terbaru
    pagination = query.order_by(Penjualan.tanggal.desc()).paginate(page=page, per_page=per_page, error_out=False)
    daftar_penjualan = pagination.items
    return render_template('penjualan/riwayat.html',
                           daftar_penjualan=daftar_penjualan,
                           pagination=pagination,
                           search=search,
                           tanggal=tgl_str)

@penjualan.route('/tambah', methods=['POST'])
@login_required
def proses_transaksi():
    if request.method == 'POST':
        # 1. Ambil data Header Penjualan
        meja_id = request.form.get('meja_id')
        customer_id = request.form.get('customer_id')
        tipe_pesanan = request.form.get('tipe_pesanan') # 'Makan di Tempat' atau 'Bungkus'
        total_bayar = int(request.form.get('total_bayar', 0))

        # --- VALIDASI: tipe pesanan wajib dipilih, dan meja wajib diisi kalau Dine In ---
        if tipe_pesanan not in ('Makan di Tempat', 'Take Away'):
            flash('Tipe pesanan wajib dipilih (Makan di Tempat / Take Away).', 'danger')
            return redirect(url_for('penjualan.index_kasir'))

        if tipe_pesanan == 'Makan di Tempat' and not meja_id:
            flash('Nomor meja wajib diisi untuk pesanan Makan di Tempat.', 'danger')
            return redirect(url_for('penjualan.index_kasir'))
        
        # --- LOGIKA STATUS DISISIPKAN DI SINI ---
        if tipe_pesanan == 'Makan di Tempat':
            # Jika Dine In, status awal masuk ke antrean pengerjaan
            status_awal = 'Dapur'
            uang_diterima = 0
            uang_kembalian = 0
            metode_bayar = 'Tunai'
        else:
            # Jika Take Away/Bungkus, diasumsikan langsung bayar di tempat
            metode_bayar = request.form.get('metode_bayar', 'Tunai')
            if metode_bayar == 'QRIS':
                # QRIS dianggap dibayar PAS sesuai total (gak ada kembalian tunai)
                uang_diterima = total_bayar
            else:
                try:
                    uang_diterima = int(request.form.get('bayar', 0) or 0)
                except ValueError:
                    flash('Jumlah uang yang diterima tidak valid.', 'danger')
                    return redirect(url_for('penjualan.index_kasir'))

            if uang_diterima < total_bayar:
                flash(f'Pembayaran belum cukup. Total tagihan Rp{total_bayar:,}, uang diterima baru Rp{uang_diterima:,}.'.replace(',', '.'), 'danger')
                return redirect(url_for('penjualan.index_kasir'))

            status_awal = 'Lunas'
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
                metode_bayar=metode_bayar,
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

            # 6. Catat otomatis ke Buku Kas kalau transaksi ini LANGSUNG lunas
            #    (Take Away yang dibayar di depan). Dine In belum dicatat di sini
            #    karena baru beneran lunas nanti pas "PROSES BAYAR" dari Tagihan.
            if status_awal == 'Lunas':
                kas_masuk = BukuKas(
                    user_id=current_user.id,
                    penjualan_id=baru.id,
                    jenis='masuk',
                    keterangan=f'Penjualan Take Away (Nota #{baru.id}) via {metode_bayar}',
                    jumlah=total_bayar,
                    metode_bayar=metode_bayar
                )
                db.session.add(kas_masuk)

            db.session.commit() 
            
            # Pesan Flash yang lebih dinamis
            if status_awal == 'Dapur':
                flash(f'Pesanan Meja {meja_id} berhasil dikirim ke Dapur & Bar!', 'success')
            else:
                flash(f'Transaksi berhasil! Kembalian: Rp {uang_kembalian:,}', 'success')

            if status_awal == 'Lunas':
                catat_log('PEMBAYARAN', f'Nota #{baru.id} (Take Away) lunas via {metode_bayar}. Total Rp{total_bayar:,}, bayar Rp{uang_diterima:,}.'.replace(',', '.'))

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
        meja_id_baru = request.form.get('meja_id')
        tipe_pesanan_baru = request.form.get('tipe_pesanan')

        # --- VALIDASI: sama seperti order baru ---
        if tipe_pesanan_baru not in ('Makan di Tempat', 'Take Away'):
            flash('Tipe pesanan wajib dipilih (Makan di Tempat / Take Away).', 'danger')
            return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

        if tipe_pesanan_baru == 'Makan di Tempat' and not meja_id_baru:
            flash('Nomor meja wajib diisi untuk pesanan Makan di Tempat.', 'danger')
            return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

        try:
            nota.meja_id = int(meja_id_baru) if meja_id_baru else None
        except ValueError:
            flash('Nomor meja harus berupa angka.', 'danger')
            return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

        nota.tipe_pesanan = tipe_pesanan_baru
           
        # --- DEBUG 2: Data yang Diterima dari Form ---
        produk_ids = request.form.getlist('produk_id[]')
        varians = request.form.getlist('varian[]')
        qtys = request.form.getlist('qty[]')
        
        print(f"[DEBUG POST] Diterima {len(produk_ids)} jenis produk dari keranjang.")
        print(f"[DEBUG POST] Data Diterima: IDs={produk_ids}, Varians={varians}, Qtys={qtys}")

        if not produk_ids:
            flash('Keranjang tidak boleh kosong. Tambahkan minimal 1 produk sebelum menyimpan.', 'danger')
            return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

        if not (len(produk_ids) == len(varians) == len(qtys)):
            flash('Data keranjang tidak lengkap/tidak sinkron. Silakan coba lagi.', 'danger')
            return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

        # --- Hitung qty LAMA per produk (sebelum diedit), untuk keperluan
        #     penyesuaian stok. Wajib diambil SEBELUM detail lama dihapus.
        detail_lama = PenjualanDetail.query.filter_by(penjualan_id=id).all()
        qty_lama_per_produk = {}
        for d in detail_lama:
            qty_lama_per_produk[d.produk_id] = qty_lama_per_produk.get(d.produk_id, 0) + d.qty

        # Harga per kombinasi (produk_id, varian) yang SUDAH ADA sebelumnya di nota ini.
        # Dipakai supaya item yang gak berubah tetap pakai harga yang beneran tercatat
        # dulu, bukan ke-reprice diam-diam kalau harga produknya udah berubah sejak
        # order ini dibuat. Item baru (kombinasi produk+varian yang belum pernah ada
        # di nota ini) tetap pakai harga produk TERKINI, sesuai harusnya.
        harga_lama_by_key = {(d.produk_id, d.varian): d.harga_satuan for d in detail_lama}

        # --- Validasi & hitung total dulu SEBELUM ubah apapun di database,
        #     biar kalau ada data yang gak valid, nota lama gak keburu rusak. ---
        item_baru_list = []
        total_baru = 0
        qty_baru_per_produk = {}
        try:
            for i in range(len(produk_ids)):
                p_id = int(produk_ids[i])
                p_qty = int(qtys[i])
                p_varian = varians[i]

                if p_qty <= 0:
                    flash(f'Jumlah item ke-{i+1} harus lebih dari 0.', 'danger')
                    return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

                produk_obj = Produk.query.get(p_id)
                if not produk_obj:
                    flash('Salah satu produk di keranjang sudah tidak tersedia. Hapus item itu dan coba lagi.', 'danger')
                    return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

                if (p_id, p_varian) in harga_lama_by_key:
                    # Item ini sudah ada sebelumnya (produk+varian sama) -> pakai harga lama
                    harga_item = harga_lama_by_key[(p_id, p_varian)]
                else:
                    # Item baru / varian baru -> pakai harga produk saat ini
                    harga_item = produk_obj.harga_jual
                    if p_varian == 'Mie Pansit' and ('Miso' in produk_obj.nama_produk or 'Bakso' in produk_obj.nama_produk):
                        harga_item += 1000

                subtotal = harga_item * p_qty
                total_baru += subtotal
                qty_baru_per_produk[p_id] = qty_baru_per_produk.get(p_id, 0) + p_qty

                print(f"   -> Item {i+1}: {produk_obj.nama_produk} | Varian: {p_varian} | Qty: {p_qty} | Harga: {harga_item} | Subtotal: {subtotal}")

                item_baru_list.append({'produk_id': p_id, 'qty': p_qty, 'harga': harga_item, 'varian': p_varian})
        except (ValueError, IndexError):
            flash('Data keranjang tidak valid. Silakan coba lagi.', 'danger')
            return redirect(url_for('penjualan.edit_nota', id=id, aksi=request.args.get('aksi')))

        # Baru sekarang aman untuk hapus data lama & masukin yang baru
        PenjualanDetail.query.filter_by(penjualan_id=id).delete()
        print(f"[DEBUG POST] Menghapus detail lama untuk nota #{id}")

        for item in item_baru_list:
            detail = PenjualanDetail(penjualan_id=id, produk_id=item['produk_id'], qty=item['qty'],
                                     harga_satuan=item['harga'], varian=item['varian'])
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
            metode_bayar = request.form.get('metode_bayar', 'Tunai')

            if metode_bayar == 'QRIS':
                # QRIS dianggap dibayar PAS sesuai total tagihan, gak ada kembalian tunai
                uang_diterima = total_baru
            else:
                try:
                    uang_diterima = int(request.form.get('bayar', 0) or 0)
                except ValueError:
                    flash('Jumlah uang yang diterima tidak valid.', 'danger')
                    return redirect(url_for('penjualan.edit_nota', id=id, aksi='bayar'))

            # PENTING: jangan sampai transaksi ditandai Lunas & tercatat ke Buku Kas
            # kalau uang yang diterima belum cukup (termasuk kalau kosong/0).
            if uang_diterima < total_baru:
                flash(f'Pembayaran belum cukup. Total tagihan Rp{total_baru:,}, uang diterima baru Rp{uang_diterima:,}.'.replace(',', '.'), 'danger')
                return redirect(url_for('penjualan.edit_nota', id=id, aksi='bayar'))

            nota.bayar = uang_diterima
            nota.kembalian = uang_diterima - total_baru
            nota.metode_bayar = metode_bayar
            nota.status = 'Lunas'
            print(f"[DEBUG POST] Pelunasan diproses. Metode: {metode_bayar}, Bayar: {uang_diterima}, Kembalian: {nota.kembalian}")

            # Catat otomatis ke Buku Kas sebagai kas masuk dari transaksi penjualan
            kas_masuk = BukuKas(
                user_id=current_user.id,
                penjualan_id=nota.id,
                jenis='masuk',
                keterangan=f'Penjualan Meja {nota.meja_id} (Nota #{nota.id}) via {metode_bayar}',
                jumlah=total_baru,
                metode_bayar=metode_bayar
            )
            db.session.add(kas_masuk)

        db.session.commit()
        print(f"[DEBUG POST] Sukses Update! Total Bayar Akhir: Rp {total_baru}")
        if aksi == 'bayar':
            catat_log('PEMBAYARAN', f'Nota #{id} (Meja {nota.meja_id}) lunas via {metode_bayar}. Total Rp{total_baru:,}, bayar Rp{uang_diterima:,}.'.replace(',', '.'))
        
        flash('Pembayaran berhasil diproses!' if aksi == 'bayar' else 'Nota berhasil diperbarui!', 'success')
        return redirect(url_for('penjualan.daftar_tagihan'))
        
    # Logika untuk tampilan (GET)
    produk_list = Produk.query.order_by(Produk.nama_produk).all()

    produk_per_kategori = {}
    for p in produk_list:
        produk_per_kategori.setdefault(p.kategori, []).append(p)
    
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
                           produk_per_kategori=produk_per_kategori,
                           mode_bayar=(request.args.get('aksi') == 'bayar'))

@penjualan.route('/hapus/<int:id>', methods=['POST'])
@login_required
@admin_required
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
        catat_log('HAPUS_NOTA', f'Menghapus Nota #{id}, stok dikembalikan.')
        
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
