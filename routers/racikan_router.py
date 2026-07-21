# routers/racikan_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Racikan, RacikanDetail, BahanBaku, ResepDetail
from utils import admin_required, catat_log

racikan_bp = Blueprint('racikan', __name__)


@racikan_bp.route('/')
@login_required
@admin_required
def list_racikan():
    semua = Racikan.query.order_by(Racikan.nama_racikan).all()
    return render_template('racikan/list.html', semua_racikan=semua)


@racikan_bp.route('/tambah', methods=['POST'])
@login_required
@admin_required
def tambah_racikan():
    nama = request.form.get('nama_racikan', '').strip()
    satuan = request.form.get('satuan_hasil', 'porsi').strip() or 'porsi'

    if not nama:
        flash('Nama racikan wajib diisi.', 'danger')
        return redirect(url_for('racikan.list_racikan'))

    if Racikan.query.filter_by(nama_racikan=nama).first():
        flash(f'Racikan "{nama}" sudah ada.', 'danger')
        return redirect(url_for('racikan.list_racikan'))

    racikan = Racikan(nama_racikan=nama, satuan_hasil=satuan, porsi_hasil=1, harga_per_porsi=0)
    db.session.add(racikan)
    db.session.commit()

    catat_log('TAMBAH_RACIKAN', f'Menambahkan racikan "{nama}".')
    flash(f'Racikan "{nama}" berhasil ditambahkan. Sekarang atur resepnya.', 'success')
    return redirect(url_for('racikan.kelola_resep_racikan', racikan_id=racikan.id))


@racikan_bp.route('/hapus/<int:id>')
@login_required
@admin_required
def hapus_racikan(id):
    racikan = Racikan.query.get_or_404(id)

    # Jangan sampai racikan yang lagi dipakai di resep produk ke-hapus,
    # nanti resep produk itu jadi rusak referensinya.
    dipakai_di = ResepDetail.query.filter_by(racikan_id=id).count()
    if dipakai_di > 0:
        flash(f'Racikan "{racikan.nama_racikan}" masih dipakai di {dipakai_di} resep produk. Hapus dari resep itu dulu.', 'danger')
        return redirect(url_for('racikan.list_racikan'))

    nama = racikan.nama_racikan
    db.session.delete(racikan)
    db.session.commit()
    catat_log('HAPUS_RACIKAN', f'Menghapus racikan "{nama}".')
    flash(f'Racikan "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('racikan.list_racikan'))


@racikan_bp.route('/resep/<int:racikan_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def kelola_resep_racikan(racikan_id):
    racikan = Racikan.query.get_or_404(racikan_id)

    if request.method == 'POST':
        try:
            porsi_hasil = int(request.form.get('porsi_hasil', 1))
        except (ValueError, TypeError):
            flash('Porsi hasil harus berupa angka.', 'danger')
            return redirect(url_for('racikan.kelola_resep_racikan', racikan_id=racikan_id))

        if porsi_hasil <= 0:
            flash('Porsi hasil harus lebih dari 0.', 'danger')
            return redirect(url_for('racikan.kelola_resep_racikan', racikan_id=racikan_id))

        satuan_hasil = request.form.get('satuan_hasil', racikan.satuan_hasil).strip() or racikan.satuan_hasil
        racikan.porsi_hasil = porsi_hasil
        racikan.satuan_hasil = satuan_hasil

        # Hapus detail lama, buat ulang dari form
        RacikanDetail.query.filter_by(racikan_id=racikan.id).delete()

        bahan_ids = request.form.getlist('bahan_id[]')
        qtys = request.form.getlist('qty_pakai[]')

        for i in range(len(bahan_ids)):
            if not bahan_ids[i]:
                continue
            try:
                qty = float(qtys[i])
            except (ValueError, IndexError):
                continue
            if qty <= 0:
                continue
            detail = RacikanDetail(racikan_id=racikan.id, bahan_id=int(bahan_ids[i]), qty_pakai=qty)
            db.session.add(detail)

        db.session.commit()

        # Hitung ulang HPP racikan ini, lalu sebarkan ke semua Produk yang memakainya
        racikan.update_hpp()
        for rd in ResepDetail.query.filter_by(racikan_id=racikan.id).all():
            if rd.resep.produk:
                rd.resep.produk.update_hpp()

        catat_log('EDIT_RESEP_RACIKAN', f'Mengubah resep racikan "{racikan.nama_racikan}". HPP baru: Rp{racikan.harga_per_porsi:,}.'.replace(',', '.'))
        flash(f'Resep & HPP racikan "{racikan.nama_racikan}" berhasil diperbarui!', 'success')
        return redirect(url_for('racikan.kelola_resep_racikan', racikan_id=racikan_id))

    semua_bahan = BahanBaku.query.order_by(BahanBaku.nama_bahan).all()
    return render_template('racikan/edit.html', racikan=racikan, semua_bahan=semua_bahan)
