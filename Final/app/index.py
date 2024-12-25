import hashlib
import json
import math
import random
from datetime import datetime
from app import app, dao, login, utils, db
from flask import render_template, request, redirect, url_for, jsonify, session, flash
from flask_login import login_user, logout_user, current_user, login_required
import cloudinary.uploader
from app.models import UserRole, Receipt

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['get', 'post'])
def user_signin():
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = utils.check_login(username=username, password=password)
        if user:
            login_user(user=user)

            if current_user.role == UserRole.ADMIN:
                return redirect('/admin')
            elif current_user.role == UserRole.RECEPTIONIST:
                return redirect(url_for('room_renting'))
            else:
                return redirect(url_for('home'))
        else:
            err_msg = 'Username or Password is incorrect!!!'

    return render_template('login_admin.html', err_msg=err_msg)

@app.route('/user-logout')
def user_signout():
    logout_user()
    return redirect(url_for('user_signin'))


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


if __name__ == "__main__":
    from app.admin import *
    app.run(debug=True)