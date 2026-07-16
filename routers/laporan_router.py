# laporan_router.py
from flask import Blueprint, render_template, request
from flask_login import login_required
from extensions import db
from models.penjualan import Penjualan
from models.penjualan_detail import PenjualanDetail
from models.produk_model import Produk
from sqlalchemy import func
from datetime import datetime, date

laporan = Blueprint('laporan', __name__)

@laporan.route('/harian')
@login_required
def laporan_harian():
    # 1. Ambil Tanggal Hari Ini (Default)
    tanggal_str = request.args.get('tanggal', date.today().isoformat())
    target_date = datetime.strptime(tanggal_str, '%Y-%m-%d').date()

    # 2. Ringkasan Total Pendapatan & Transaksi
    ringkasan = db.session.query(
        func.sum(Penjualan.total_bayar).label('total_pendapatan'),
        func.count(Penjualan.id).label('total_transaksi')
    ).filter(func.date(Penjualan.tanggal) == target_date).first()

    # 3. Rincian Penjualan per Produk & Varian (Penting untuk Evaluasi) [Riwayat]
    rincian_menu = db.session.query(
        Produk.nama_produk,
        PenjualanDetail.varian,
        func.sum(PenjualanDetail.qty).label('total_qty'),
        func.sum(PenjualanDetail.qty * PenjualanDetail.harga_satuan).label('subtotal')
    ).join(PenjualanDetail, Produk.id == PenjualanDetail.produk_id)\
     .join(Penjualan, Penjualan.id == PenjualanDetail.penjualan_id)\
     .filter(func.date(Penjualan.tanggal) == target_date)\
     .group_by(Produk.nama_produk, PenjualanDetail.varian)\
     .all()

    return render_template('laporan/harian.html', 
                           ringkasan=ringkasan, 
                           rincian=rincian_menu, 
                           tanggal=tanggal_str)