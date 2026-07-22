# laporan_router.py
from flask import Blueprint, render_template, request
from flask_login import login_required
from extensions import db
from models.penjualan import Penjualan
from models.penjualan_detail import PenjualanDetail
from models.produk_model import Produk
from sqlalchemy import func
from utils import admin_required
from datetime import datetime, date, timedelta

laporan = Blueprint('laporan', __name__)


def _hitung_rentang(preset, dari_str, sampai_str):
    """Tentukan rentang tanggal laporan berdasarkan preset yang dipilih."""
    today = date.today()

    if preset == 'minggu_ini':
        dari = today - timedelta(days=today.weekday())  # Senin minggu ini
        sampai = today
    elif preset == 'bulan_ini':
        dari = today.replace(day=1)
        sampai = today
    elif preset == 'custom':
        try:
            dari = datetime.strptime(dari_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            dari = today
        try:
            sampai = datetime.strptime(sampai_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            sampai = today
        if dari > sampai:
            dari, sampai = sampai, dari
    else:
        # default: hari_ini
        preset = 'hari_ini'
        dari = sampai = today

    return preset, dari, sampai


@laporan.route('/harian')
@login_required
@admin_required
def laporan_harian():
    preset = request.args.get('preset', 'hari_ini')
    preset, dari, sampai = _hitung_rentang(
        preset,
        request.args.get('dari'),
        request.args.get('sampai')
    )

    # --- Ringkasan Total Pendapatan & Transaksi ---
    # PENTING: hanya hitung transaksi yang sudah LUNAS. Order yang masih di
    # dapur/belum dibayar tidak dianggap sebagai pendapatan yang sudah masuk.
    ringkasan = db.session.query(
        func.sum(Penjualan.total_bayar).label('total_pendapatan'),
        func.count(Penjualan.id).label('total_transaksi')
    ).filter(
        func.date(Penjualan.tanggal).between(dari, sampai),
        Penjualan.status == 'Lunas'
    ).first()

    # --- Rincian Penjualan per Produk & Varian, sekaligus HPP & Laba Kotor ---
    # Catatan: HPP dihitung pakai harga_beli produk SAAT INI (bukan histori saat
    # transaksi terjadi), karena aplikasi belum menyimpan snapshot HPP per nota.
    rincian_raw = db.session.query(
        Produk.nama_produk,
        PenjualanDetail.varian,
        func.sum(PenjualanDetail.qty).label('total_qty'),
        func.sum(PenjualanDetail.qty * PenjualanDetail.harga_satuan).label('omzet'),
        Produk.harga_beli.label('hpp_satuan')
    ).join(PenjualanDetail, Produk.id == PenjualanDetail.produk_id)\
     .join(Penjualan, Penjualan.id == PenjualanDetail.penjualan_id)\
     .filter(
         func.date(Penjualan.tanggal).between(dari, sampai),
         Penjualan.status == 'Lunas'
     )\
     .group_by(Produk.nama_produk, PenjualanDetail.varian, Produk.harga_beli)\
     .order_by(func.sum(PenjualanDetail.qty * PenjualanDetail.harga_satuan).desc())\
     .all()

    rincian = []
    total_hpp = 0
    total_laba = 0
    for r in rincian_raw:
        hpp_total = r.total_qty * (r.hpp_satuan or 0)
        laba = r.omzet - hpp_total
        total_hpp += hpp_total
        total_laba += laba
        rincian.append({
            'nama_produk': r.nama_produk,
            'varian': r.varian,
            'total_qty': r.total_qty,
            'omzet': r.omzet,
            'hpp_total': hpp_total,
            'laba': laba,
        })

    # --- Rekap khusus semua varian Mie, per transaksi (bukan gabungan) ---
    # Beda dari tabel "Rincian Penjualan Menu" di atas yang digabung per menu+varian,
    # ini nampilin baris per transaksi lengkap tanggal & jam-nya, biar kelihatan
    # kapan tepatnya tiap varian mie itu laku (mis. buat lihat pola jam ramai).
    rekap_mie_raw = db.session.query(
        Penjualan.tanggal,
        Penjualan.id.label('nota_id'),
        Produk.nama_produk,
        PenjualanDetail.varian,
        PenjualanDetail.qty
    ).join(PenjualanDetail, Produk.id == PenjualanDetail.produk_id)\
     .join(Penjualan, Penjualan.id == PenjualanDetail.penjualan_id)\
     .filter(
         func.date(Penjualan.tanggal).between(dari, sampai),
         Penjualan.status == 'Lunas',
         Produk.nama_produk.ilike('%mie%')
     )\
     .order_by(Penjualan.tanggal.desc())\
     .all()

    rekap_mie = [{
        'tanggal': r.tanggal.strftime('%d %b %Y'),
        'waktu': r.tanggal.strftime('%H:%M'),
        'nota_id': r.nota_id,
        'nama_produk': r.nama_produk,
        'varian': r.varian,
        'qty': r.qty,
    } for r in rekap_mie_raw]

    return render_template('laporan/harian.html',
                           ringkasan=ringkasan,
                           rincian=rincian,
                           total_hpp=total_hpp,
                           total_laba=total_laba,
                           rekap_mie=rekap_mie,
                           preset=preset,
                           dari=dari.isoformat(),
                           sampai=sampai.isoformat())


@laporan.route('/stok-mutakhir')
@login_required
@admin_required
def stok_mutakhir():
    # Mengambil semua produk beserta jumlah stok terakhirnya
    daftar_stok = Produk.query.order_by(Produk.nama_produk).all()
    return render_template('laporan/stok_mutakhir.html', daftar_stok=daftar_stok)
