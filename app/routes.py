from flask import render_template, flash, redirect, request, url_for, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from flask_http_response import success, result, error
from flask_wtf.csrf import generate_csrf
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, photos
from app.models import *
from app.utils import expand2square
from manage import db
from .forms import LoginForm, RegistrationForm, EditProfileForm, UploadImageForm, ChangePasswordForm
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
    """
    Shows all Tutors on the index page. 
    Data is a dictonary containing User and Tutor info, inside each there's a list containing
    an instance of the respective class
    """
    result = db.session.query(Users, Tutors).join(Tutors).all()
    
    data = {}
    data['user'] = []
    data['tutor'] = []
    rows = len(result)

    for i in range(len(result)):
        data['user'].append(result[i][0])
        data['tutor'].append(result[i][1])

    return render_template('index.html', title='Home Page', data=data, rows=rows)

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

@app.route('/profile/<int:tutor_id>', methods=['GET'])
def profile(tutor_id):
    """Only show Tutors, won't be displaying users profiles"""
    
    try:
        tutor = Tutors.query.get(tutor_id)
    except NoResultFound:
        flash("Tutor not registered", "danger")

    # get the user from tutor
    user = Users.query.get(tutor.user_id)
    
    if user is None or tutor is None:
        is_tutor = False
        flash('Tutor not registered', 'danger')
        return render_template('404.html')
    else:
        is_tutor = True

    is_owner = True if user == current_user else False
    is_following = True if user.is_following(tutor) else False
    
    return render_template('profile.html', user=user, tutor=tutor, is_owner=is_owner, 
        is_following=is_following, is_tutor=is_tutor)

@app.route('/following', methods=['GET'])
@login_required
def following():
    """
    Show all the Tutors the user is following (Join tables Tutors, Users and Followers)
    """
    id = current_user.id
    user = Users.query.get(current_user.id)

    # Joining tables Tutors, Users and Followers, filtering by Users.id
    result = db.session.query(Users, Tutors).join(Users, Tutors.followers).filter(Users.id==id).all()

    data = {}
    data['user'] = []
    data['tutor'] = []
    rows = len(result)

    for i in range(len(result)):
        data['user'].append(result[i][0])
        data['tutor'].append(result[i][1])

    return render_template('index.html', title='Following', data=data, rows=rows)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Edit profile page functionalities: include/change profile img, password, about me (initially)
    First I'll add just the users' functionalities, later I will also include Tutors
    """
    id = current_user.id
    user = Users.query.get(id)

    tutor = Tutors.query.filter_by(user_id=id).first()
    if tutor is None:
        return render_template('403.html')

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
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('profile', tutor_id=tutor.id))
    elif request.method == 'GET':
        profile_form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', user=user, profile_form=profile_form, image_form=image_form)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    id = current_user.id
    user = Users.query.get(id)
    image_form = UploadImageForm()
    logging.warning(image_form.errors)
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
            db.session.commit()
            flash('Your photo has been saved.', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', user=user, image_form=image_form)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = Users.query.get(current_user.id)
    password_form = ChangePasswordForm()
    if request.method == 'POST':
        if password_form.validate_on_submit():
            if user.check_password(password_form.current_password.data):
                user.set_password(password_form.new_password.data)
                db.session.commit()
                flash('Sucess! You have updated your password!')
            else:
                flash('Please review your password and try again')
        return redirect(url_for('settings'))
    return render_template('change_password.html', user=user, password_form=password_form)

@app.route('/display/<filename>')
@login_required
def display_image(filename):
	print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/follow_unfollow/<int:tutor_id>')
@login_required
def follow_unfollow(tutor_id):
    user = Users.query.get(current_user.id)
    try:
        tutor = Tutors.query.get(tutor_id)
    except NoResultFound:
        flash("Tutor not registered", "danger")

    is_following = user.is_following(tutor)

    user.unfollow(tutor) if is_following else user.follow(tutor)
    db.session.commit()
    return redirect(url_for('profile', tutor_id=tutor_id))


@app.route('/is_following/<int:user_id>/<int:tutor_id>')
def is_following(user_id, tutor_id):
    try:
        user = Users.query.get(user_id)
    except NoResultFound:
        return jsonify(error="User not found", code=404)
    try:
        tutor = Tutors.query.get(tutor_id)
    except NoResultFound:
        return jsonify(error="Tutor not found", code=404)
    
    is_following = user.is_following(tutor)
    return jsonify(is_following=is_following)