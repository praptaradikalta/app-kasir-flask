# forms/user_form.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Email

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Email', validators=[Optional(), Email(message='Format email tidak valid.')])
    password = PasswordField('Password')  # kosongin = gak ganti password
    role = SelectField('Role', choices=[('kasir','Kasir'),('admin','Admin'),('owner','Owner')])
    nama_lengkap = StringField('Nama Lengkap')
    submit = SubmitField('Simpan')