from flask import render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, photos
from app.models import Users
from app.utils import expand2square
from manage import db
from .forms import LoginForm, RegistrationForm, EditProfileForm, UploadImageForm
from PIL import Image
import logging, os, time, hashlib, pathlib


# this decorator function is executed before any other  view function
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

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

@app.route('/profile/<int:id>', methods=['GET'])
def profile(id):
    user = Users.query.get(id)
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Edit profile page functionalities: include/change profile img, password, about me (initially)
    First I'll add just the users' functionalities, later I will also include Tutors
    """
    id = current_user.get_id()
    user = Users.query.get(id)
    profile_form = EditProfileForm()
    image_form = UploadImageForm()
    if request.method == 'POST':
        if image_form.validate_on_submit():
            # saving the profile image
            filename = image_form.profile_img.data
            str_name = 'admin' + str(int(time.time()))
            name = hashlib.md5(str_name.encode("utf-8")).hexdigest()[:15]
            file_extension = pathlib.Path(filename.filename).suffix
            photos.save(filename, name=name + '.')

            # resizing the thumbnail image
            file_url = photos.path(name) + file_extension
            image = Image.open(file_url)
            image = expand2square(image, (0, 0, 0)).resize((150, 150), Image.LANCZOS)
            image.save(file_url, quality=95)

            # saving the filename into users.profile_img
            user.profile_img = name + file_extension
        if profile_form.validate_on_submit() and profile_form.save.data:
            current_user.about_me = profile_form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('profile', id=id))
    elif request.method == 'GET':
        profile_form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', user=user, profile_form=profile_form, image_form=image_form)

@app.route('/display/<filename>')
def display_image(filename):
	print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)


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