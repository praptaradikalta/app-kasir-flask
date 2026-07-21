# routes/user_route.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from forms.user_form import UserForm
from extensions import db
from models import User # Gunakan satu sumber impor saja
from utils import admin_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login berhasil!', 'success')
            
            # Perbaikan: Gunakan namespace blueprint 'user.dashboard'
            # Dan arahkan ke next_page jika ada
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
        else:
            flash('Username atau password salah', 'danger')
    return render_template('login.html')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))

@user_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.all()
    return render_template('user/list.html', users=users)

@user_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def user_add():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username sudah dipakai, pilih username lain.', 'danger')
            return render_template('user/add.html', form=form)

        if not form.password.data:
            flash('Password wajib diisi untuk user baru.', 'danger')
            return render_template('user/add.html', form=form)

        user = User(
            username=form.username.data,
            password=form.password.data,
            role=form.role.data,
            nama_lengkap=form.nama_lengkap.data
        )
        db.session.add(user)
        db.session.commit()
        flash('User berhasil ditambahkan!', 'success')
        return redirect(url_for('user.user_list'))
    return render_template('user/add.html', form=form)

@user_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(id):
    user = User.query.get_or_404(id) # Gunakan get_or_404 agar lebih aman
    form = UserForm(obj=user)
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing and existing.id != user.id:
            flash('Username sudah dipakai user lain.', 'danger')
            return render_template('user/edit.html', form=form, user=user)

        user.username = form.username.data
        user.role = form.role.data
        user.nama_lengkap = form.nama_lengkap.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User berhasil diupdate!', 'success')
        return redirect(url_for('user.user_list'))
    return render_template('user/edit.html', form=form, user=user)

@user_bp.route('/users/delete/<int:id>')
@login_required
@admin_required
def user_delete(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Kamu tidak bisa menghapus akunmu sendiri.', 'danger')
        return redirect(url_for('user.user_list'))
    db.session.delete(user)
    db.session.commit()
    flash('User berhasil dihapus!', 'success')
    return redirect(url_for('user.user_list'))