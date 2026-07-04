# penjualan_router.py
from flask import Blueprint, render_template
from extensions import db
from sqlalchemy import text # import text

penjualan = Blueprint('penjualan', __name__)

@penjualan.route('/')
def penjualan_list():
    data = db.session.execute(text("SELECT * FROM penjualan")).fetchall()
    return render_template('penjualan.html', penjualan=data)