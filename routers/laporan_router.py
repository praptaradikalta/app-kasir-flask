# laporan_router.py
from flask import Blueprint, render_template
laporan = Blueprint('laporan', __name__)

@laporan.route('/laporan')
def laporan_list():
    return render_template('laporan.html')