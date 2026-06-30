# penjualan_router.py
from flask import Blueprint, render_template
penjualan = Blueprint('penjualan', __name__)

@penjualan.route('/penjualan')
def penjualan_list():
    return render_template('penjualan.html')