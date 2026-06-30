# routes/user_route.py
from flask import Blueprint, render_template, redirect, url_for, flash
from models.user_model import User
from forms.user_form import UserForm
from extensions import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users')
def user_list():
    users = User.query.all()
    return render_template('user/list.html', users=users)

@user_bp.route('/users/add', methods=['GET', 'POST'])
def user_add():
    form = UserForm()
    if form.validate_on_submit():
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
def user_edit(id):
    user = User.query.get(id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        user.nama_lengkap = form.nama_lengkap.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User berhasil diupdate!', 'success')
        return redirect(url_for('user.user_list'))
    return render_template('user/edit.html', form=form)

@user_bp.route('/users/delete/<int:id>')
def user_delete(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    flash('User berhasil dihapus!', 'success')
    return redirect(url_for('user.user_list'))