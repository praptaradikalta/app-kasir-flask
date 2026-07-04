# pengaturan_router.py
from flask import Blueprint, render_template
pengaturan = Blueprint('pengaturan', __name__)

@pengaturan.route('/')
def pengaturan_list():
    return render_template('pengaturan.html')