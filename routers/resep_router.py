from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Produk, Resep, ResepDetail, BahanBaku

resep_bp = Blueprint('resep', __name__)

@resep_bp.route('/<int:produk_id>', methods=['GET', 'POST'])
@login_required
def kelola_resep(produk_id):
    produk = Produk.query.get_or_404(produk_id)
    # Gunakan filter_by agar pencarian akurat
    resep = Resep.query.filter_by(produk_id=produk_id).first()
    bahan_baku = BahanBaku.query.all()

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
        bahan_ids = request.form.getlist('bahan_id[]')
        qtys = request.form.getlist('qty_pakai[]')

        for b_id, qty in zip(bahan_ids, qtys):
            if b_id and qty:
                qty_val = float(qty)
                detail = ResepDetail(resep_id=resep.id, bahan_id=int(b_id), qty_pakai=qty_val)
                db.session.add(detail)
                
                # Ambil harga bahan untuk hitung HPP produk
                bahan = BahanBaku.query.get(b_id)
                total_modal_batch += (bahan.harga_beli_terakhir * qty_val)

        # Update harga_beli di tabel Produk (Total Modal / Porsi Hasil)
        produk.harga_beli = int(total_modal_batch / porsi_hasil)
        
        try:
            db.session.commit()
            flash(f'Resep {produk.nama_produk} berhasil diperbarui!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan resep: {e}', 'error')
        
        return redirect(url_for('resep.kelola_resep', produk_id=produk.id))

    return render_template('resep/edit.html', produk=produk, resep=resep, bahan_baku=bahan_baku)
