from flask import render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import app, photos
from app.models import Users
from app.utils import expand2square
from manage import db
from .forms import LoginForm, RegistrationForm, ImageUploadForm
from PIL import Image
import logging, os, time, hashlib, pathlib


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home Page')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    logging.warning(form.errors)
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next') # next is the page the user tried to access before login
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Settings page functionalities: include/change profile img and password (initially)
    First I'll add just the users settings, later I will also include Tutors
    """
    id = current_user.get_id()
    form = ImageUploadForm()
    if form.validate_on_submit():
        for filename in request.files.getlist('profile'):
            # saving the profile image
            str_name = 'admin' + str(int(time.time()))
            name = hashlib.md5(str_name.encode("utf-8")).hexdigest()[:15]
            file_extension = pathlib.Path(filename.filename).suffix
            photos.save(filename, name=name + '.')

            # resizing the thumbnail
            file_url = photos.path(name) + file_extension
            image = Image.open(file_url)
            image = expand2square(image, (0, 0, 0)).resize((80, 80), Image.LANCZOS)
            image.save(file_url, quality=95)
            
        flash('Profile image uploaded successfully.')

    user = Users.query.get(id)
    return render_template('settings.html', user=user, form=form)

# @app.route('/manage')
# def manage_file():
#     files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])
#     return render_template('manage.html', files_list=files_list)


# @app.route('/open/<filename>')
# def open_file(filename):
#     file_url = photos.url(filename)
#     return render_template('browser.html', file_url=file_url)


# @app.route('/delete/<filename>')
# def delete_file(filename):
#     file_path = photos.path(filename)
#     os.remove(file_path)
#     return redirect(url_for('manage_file'))