# routers/shift_router.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Shift, BukuKas
from utils import catat_log
from datetime import datetime

shift_bp = Blueprint('shift', __name__)


def get_shift_aktif(user_id):
    return Shift.query.filter_by(user_id=user_id, status='aktif').first()


@shift_bp.route('/')
@login_required
def status():
    shift_aktif = get_shift_aktif(current_user.id)

    ringkasan = None
    if shift_aktif:
        ringkasan = hitung_ringkasan_kas(shift_aktif)

    riwayat_raw = Shift.query.filter_by(user_id=current_user.id, status='selesai')\
                              .order_by(Shift.waktu_mulai.desc()).limit(10).all()

    # Hitung ulang "perkiraan kas" & selisih buat tiap shift yang udah selesai,
    # dibatasi dari waktu_mulai SAMPAI waktu_selesai shift itu (bukan open-ended).
    # Sama kayak hitung_ringkasan_kas(): QRIS gak ikut dihitung ke kas fisik.
    riwayat = []
    for s in riwayat_raw:
        entri = BukuKas.query.filter(
            BukuKas.user_id == s.user_id,
            BukuKas.tanggal >= s.waktu_mulai,
            BukuKas.tanggal <= s.waktu_selesai
        ).all()
        total_masuk_tunai = sum(e.jumlah for e in entri if e.jenis == 'masuk' and (e.metode_bayar or 'Tunai') == 'Tunai')
        total_keluar = sum(e.jumlah for e in entri if e.jenis == 'keluar')
        perkiraan = s.modal_awal + total_masuk_tunai - total_keluar
        selisih = (s.modal_akhir or 0) - perkiraan
        riwayat.append({'shift': s, 'perkiraan_kas': perkiraan, 'selisih': selisih})

    return render_template('shift/status.html', shift_aktif=shift_aktif, ringkasan=ringkasan, riwayat=riwayat)


def hitung_ringkasan_kas(shift):
    """
    Modal awal + kas TUNAI masuk/keluar SEJAK shift ini mulai = perkiraan kas fisik
    yang harusnya ada di laci. Pembayaran QRIS SENGAJA gak ikut dihitung ke kas
    fisik, soalnya uangnya gak masuk laci -- masuknya ke rekening/e-wallet, bukan
    uang kertas yang bisa dihitung manual pas tutup shift.
    """
    entri = BukuKas.query.filter(
        BukuKas.user_id == shift.user_id,
        BukuKas.tanggal >= shift.waktu_mulai
    ).all()

    # Kas keluar (belanja bahan, dll) selalu dianggap tunai fisik, apapun kejadiannya
    # -- soalnya "keluar" itu kasir yang ngeluarin uang kertas dari laci.
    total_keluar = sum(e.jumlah for e in entri if e.jenis == 'keluar')

    # Kas masuk: cuma yang metode_bayar-nya Tunai yang beneran nambah fisik di laci.
    total_masuk_tunai = sum(e.jumlah for e in entri if e.jenis == 'masuk' and (e.metode_bayar or 'Tunai') == 'Tunai')
    total_masuk_qris = sum(e.jumlah for e in entri if e.jenis == 'masuk' and e.metode_bayar == 'QRIS')
    total_masuk = total_masuk_tunai + total_masuk_qris

    perkiraan_kas = shift.modal_awal + total_masuk_tunai - total_keluar

    return {
        'total_masuk': total_masuk,               # semua pemasukan (tunai + QRIS), buat info aja
        'total_masuk_tunai': total_masuk_tunai,
        'total_masuk_qris': total_masuk_qris,
        'total_keluar': total_keluar,
        'perkiraan_kas': perkiraan_kas,            # ini yang dipakai buat cocokin hitungan fisik laci
    }


@shift_bp.route('/buka', methods=['POST'])
@login_required
def buka_shift():
    if get_shift_aktif(current_user.id):
        flash('Kamu masih punya shift yang aktif. Tutup shift itu dulu sebelum buka yang baru.', 'danger')
        return redirect(url_for('shift.status'))

    try:
        modal_awal = int(request.form.get('modal_awal', 0) or 0)
    except ValueError:
        flash('Modal awal harus berupa angka.', 'danger')
        return redirect(url_for('shift.status'))

    if modal_awal < 0:
        flash('Modal awal tidak boleh negatif.', 'danger')
        return redirect(url_for('shift.status'))

    shift = Shift(user_id=current_user.id, modal_awal=modal_awal, status='aktif')
    db.session.add(shift)
    db.session.commit()

    catat_log('BUKA_SHIFT', f'User "{current_user.username}" buka shift dengan modal awal Rp{modal_awal:,}.'.replace(',', '.'))
    flash('Shift berhasil dibuka. Selamat bekerja!', 'success')
    return redirect(url_for('shift.status'))


@shift_bp.route('/tutup', methods=['POST'])
@login_required
def tutup_shift():
    shift = get_shift_aktif(current_user.id)
    if not shift:
        flash('Kamu tidak punya shift yang aktif.', 'danger')
        return redirect(url_for('shift.status'))

    try:
        modal_akhir = int(request.form.get('modal_akhir', 0) or 0)
    except ValueError:
        flash('Jumlah kas akhir harus berupa angka.', 'danger')
        return redirect(url_for('shift.status'))

    if modal_akhir < 0:
        flash('Jumlah kas akhir tidak boleh negatif.', 'danger')
        return redirect(url_for('shift.status'))

    ringkasan = hitung_ringkasan_kas(shift)
    selisih = modal_akhir - ringkasan['perkiraan_kas']

    shift.modal_akhir = modal_akhir
    shift.waktu_selesai = datetime.now()
    shift.status = 'selesai'
    shift.catatan = request.form.get('catatan', '').strip() or None
    db.session.commit()

    catat_log('TUTUP_SHIFT',
              f'User "{current_user.username}" tutup shift. Kas akhir Rp{modal_akhir:,}, '
              f'perkiraan Rp{ringkasan["perkiraan_kas"]:,}, selisih Rp{selisih:,}.'.replace(',', '.'))

    if selisih == 0:
        flash('Shift ditutup. Kas pas, sesuai perkiraan!', 'success')
    elif selisih > 0:
        flash(f'Shift ditutup. Kas LEBIH Rp{selisih:,} dari perkiraan.'.replace(',', '.'), 'warning')
    else:
        flash(f'Shift ditutup. Kas KURANG Rp{abs(selisih):,} dari perkiraan.'.replace(',', '.'), 'danger')

    return redirect(url_for('shift.status'))
