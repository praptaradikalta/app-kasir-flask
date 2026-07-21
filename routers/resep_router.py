from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Produk, Resep, ResepDetail, BahanBaku, Racikan
from utils import admin_required

resep_bp = Blueprint('resep', __name__)

@resep_bp.route('/<int:produk_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def kelola_resep(produk_id):
    produk = Produk.query.get_or_404(produk_id)
    # Gunakan filter_by agar pencarian akurat
    resep = Resep.query.filter_by(produk_id=produk_id).first()
    bahan_baku = BahanBaku.query.order_by(BahanBaku.nama_bahan).all()
    semua_racikan = Racikan.query.order_by(Racikan.nama_racikan).all()

    if request.method == 'POST':
        try:
            porsi_hasil = int(request.form.get('porsi_hasil', 1))
        except (ValueError, TypeError):
            flash('Porsi hasil harus berupa angka.', 'error')
            return redirect(url_for('resep.kelola_resep', produk_id=produk_id))

        if porsi_hasil <= 0:
            flash('Porsi hasil harus lebih dari 0.', 'error')
            return redirect(url_for('resep.kelola_resep', produk_id=produk_id))
        
        if not resep:
            resep = Resep(produk_id=produk_id, porsi_hasil=porsi_hasil)
            db.session.add(resep)
        else:
            resep.porsi_hasil = porsi_hasil
            # Hapus rincian lama agar tidak duplikat saat disimpan ulang
            ResepDetail.query.filter_by(resep_id=resep.id).delete()

        db.session.flush() # Pastikan resep.id tersedia

        total_modal_batch = 0
        # Setiap baris dikirim sebagai "bahan:5" atau "racikan:3" -> biar 1 dropdown
        # bisa milih dari dua sumber (bahan mentah langsung ATAU racikan semi-jadi)
        sumber_list = request.form.getlist('sumber_id[]')
        qtys = request.form.getlist('qty_pakai[]')

        for sumber, qty in zip(sumber_list, qtys):
            if not sumber or not qty:
                continue
            try:
                tipe, sumber_id = sumber.split(':')
                sumber_id = int(sumber_id)
                qty_val = float(qty)
            except (ValueError, IndexError):
                continue
            if qty_val <= 0:
                continue

            if tipe == 'bahan':
                bahan = BahanBaku.query.get(sumber_id)
                if not bahan:
                    continue
                detail = ResepDetail(resep_id=resep.id, bahan_id=bahan.id, qty_pakai=qty_val)
                total_modal_batch += bahan.harga_beli_terakhir * qty_val
            elif tipe == 'racikan':
                racikan = Racikan.query.get(sumber_id)
                if not racikan:
                    continue
                detail = ResepDetail(resep_id=resep.id, racikan_id=racikan.id, qty_pakai=qty_val)
                total_modal_batch += racikan.harga_per_porsi * qty_val
            else:
                continue

            db.session.add(detail)

        # Update harga_beli di tabel Produk (Total Modal / Porsi Hasil)
        produk.harga_beli = int(total_modal_batch / porsi_hasil)
        
        try:
            db.session.commit()
            flash(f'Resep {produk.nama_produk} berhasil diperbarui!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan resep: {e}', 'error')
        
        return redirect(url_for('resep.kelola_resep', produk_id=produk.id))

    return render_template('resep/edit.html', produk=produk, resep=resep, bahan_baku=bahan_baku, semua_racikan=semua_racikan)
