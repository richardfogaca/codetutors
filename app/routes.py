from flask import render_template, flash, redirect, request, url_for, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from flask_http_response import success, result, error
from flask_wtf.csrf import generate_csrf
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, photos
from app.email import send_password_reset_email
from app.models import *
from app.utils import expand2square
from manage import db
from .forms import LoginForm, RegistrationForm, EditProfileForm, UploadImageForm, ChangePasswordForm, ResetPasswordRequestForm, ResetPasswordForm, AddCategoryForm, AddReviewForm
from PIL import Image
import logging, os, time, hashlib, pathlib

from os import path


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
    """
    page = request.args.get('page', 1, type=int)
    result = db.session.query(Users)\
        .join(Tutors)\
        .paginate(page, app.config['TUTORS_PER_PAGE'], False)
    next_url = url_for('index', page=result.next_num) if result.has_next else None
    prev_url = url_for('index', page=result.prev_num) if result.has_prev else None

    return render_template('index.html', title='CodeTutors - Home', result=result.items, 
                        next_url=next_url, prev_url=prev_url)

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
    return render_template('login.html', title='CodeTutors - Sign In', form=form)

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
    return render_template('register.html', title='CodeTutors - Register', form=form)

@app.route('/profile/<int:tutor_id>', methods=['GET'])
def profile(tutor_id):
    """Only show Tutors, won't be displaying users profiles"""
    try:
        tutor = Tutors.query.get(tutor_id)
    except NoResultFound:
        flash("Tutor not registered", "danger")
    
    user = Users.query.get(tutor.user_id)
    if user is None:
        flash('Tutor not registered', 'danger')
        return render_template('404.html')
    
    page = request.args.get('page', 1, type=int)
    result = Reviews.query.filter(Reviews.tutor_id==tutor_id)\
        .paginate(page, app.config['REVIEWS_PER_PAGE'], False)
    
    next_url = url_for('profile', tutor_id=tutor_id ,page=result.next_num) if result.has_next else None
    prev_url = url_for('profile', tutor_id=tutor_id ,page=result.prev_num) if result.has_prev else None
    
    is_owner = True if user == current_user else False
    is_following = True if user.is_following(tutor) else False
    title = tutor.user.first_name + ' ' + tutor.user.last_name + ' - CodeTutors'
    
    return render_template('profile.html', title=title ,user=user, tutor=tutor, is_owner=is_owner, 
                        is_following=is_following, result=result.items, 
                        next_url=next_url, prev_url=prev_url)

@app.route('/following/<int:user_id>', methods=['GET'])
@login_required
def following(user_id):
    """
    Show all the Tutors the user is following
    """
    user = Users.query.get(user_id)
    page = request.args.get('page', 1, type=int)
    result = db.session.query(Users)\
        .join(Tutors, Tutors.user_id==Users.id ,full=True)\
        .join(followers_table, Tutors.id == followers_table.c.followed_id)\
        .filter(user_id==followers_table.c.follower_id)\
        .paginate(page, app.config['TUTORS_PER_PAGE'], False)
    
    next_url = url_for('index', page=result.next_num) if result.has_next else None
    prev_url = url_for('index', page=result.prev_num) if result.has_prev else None

    return render_template('index.html', title='CodeTutors - Following', result=result.items,
                        next_url=next_url, prev_url=prev_url)

@app.route('/followers/<int:tutor_id>', methods=['GET'])
@login_required
def followers(tutor_id):
    """
    Show all the followers of a Tutor
    """
    try:
        tutor = Tutors.query.get(tutor_id)
    except:
        flash('Tutor not registered', 'danger')
        return render_template('404.html')
    
    page = request.args.get('page', 1, type=int)

    result = db.session.query(Users)\
        .join(followers_table, followers_table.c.follower_id == Users.id)\
        .filter(followers_table.c.followed_id == tutor.user_id)\
        .paginate(page, app.config['TUTORS_PER_PAGE'], False)
    
    next_url = url_for('index', page=result.next_num) \
        if result.has_next else None
    prev_url = url_for('index', page=result.prev_num) \
        if result.has_prev else None

    return render_template('index.html', title='CodeTutors - Followers', result=result.items,
                        next_url=next_url, prev_url=prev_url)

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
        if profile_form.validate_on_submit() and profile_form.save.data and profile_form.about_me.data:
            current_user.about_me = profile_form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('profile', tutor_id=tutor.id))
    elif request.method == 'GET':
        profile_form.about_me.data = tutor.about_me
    return render_template('edit_profile.html', title='CodeTutors - Edit profile',
                           user=user, profile_form=profile_form, image_form=image_form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    id = current_user.id
    user = Users.query.get(id)
    is_tutor = True if Tutors.query.filter_by(user_id=id).first() is not None else False
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
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', title='CodeTutors - Dashboard',
                        user=user, image_form=image_form, is_tutor=is_tutor)


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
        return redirect(url_for('dashboard'))
    return render_template('change_password.html', title='CodeTutors - Reset Password' ,user=user, password_form=password_form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='CodeTutors - Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = Users.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='CodeTutors - Reset Password', form=form)

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

@app.route('/get_rating/<int:tutor_id>')
def get_rating(tutor_id):
    try:
        tutor = Tutors.query.get(tutor_id)
    except NoResultFound:
        return jsonify(error="Tutor not found", code=404)
    pass

@app.route('/assign_category', methods=['GET', 'POST'])
@login_required
def assign_category():
    user = Users.query.get(current_user.id)
    tutor = Tutors.query.filter_by(user_id=user.id).first()

    form = AddCategoryForm()
    form.category.choices = [(c.id, c.name) for c in Categories.query.order_by('name')]
    if request.method == 'POST' and form.validate_on_submit():
        categories = Categories.get_all()
        # looping through the choices, we check the choice ID against what was passed in the form
        for choice in categories:
            # when there's a match, append the object
            if choice.id in form.category.data:
                tutor.category.append(choice)
        db.session.commit()
        flash('You have saved your categories')
        return redirect('index')
    return render_template('assign_category.html', title='CodeTutors - Assign Categories', form=form)

@app.route('/category/<int:category_id>')
@login_required
def category(category_id):
    """
    List all Tutors related to that specific Category
    """
    page = request.args.get('page', 1, type=int)
    result = db.session.query(Users)\
        .join(Tutors)\
        .join(tutor_category, tutor_category.c.tutor_id == Tutors.id)\
        .join(Categories, Categories.id == tutor_category.c.category_id)\
        .filter(Categories.id==category_id)\
        .paginate(page, app.config['TUTORS_PER_PAGE'], False)
    next_url = url_for('index', page=result.next_num) if result.has_next else None
    prev_url = url_for('index', page=result.prev_num) if result.has_prev else None
    
    category_name = Categories.query.get(category_id).name
    title = 'CodeTutors [' + category_name + ']' 
    
    return render_template('index.html', title=title, result=result.items, 
                        next_url=next_url, prev_url=prev_url)
    
@app.route('/add_review/<int:tutor_id>', methods=['GET', 'POST'])
@login_required
def add_review(tutor_id):
    user = Users.query.get(current_user.id)
    tutor = Tutors.query.get(tutor_id)
    form = AddReviewForm()
    has_rated = user.has_rated_tutor(tutor)
    review = db.session.query(Reviews).filter(Reviews.user==user, Reviews.tutor==tutor).first()

    if request.method == 'GET' and has_rated:
        form.title.data = review.title
        form.rating.data = review.rating
        form.comment.data = review.comment
        
    elif request.method == 'POST' and form.validate_on_submit():
        if user.id == tutor.user_id:
            flash('You can\'t review yourself', 'danger')
            redirect(url_for('index'))
        title = form.title.data
        rating = form.rating.data
        comment = form.comment.data
        if rating < 1 or rating > 5:
            flash("Your rating must be from 1 to 5")
            return redirect(url_for('add_review'))
        comment = form.comment.data
        if review is None:
            review = Reviews(title=title, rating=rating, comment=comment, user=user, tutor=tutor)
            db.session.add(review)
            db.session.commit()
            flash('Your review has been submited', 'success')
        else:
            review.title = title
            review.rating = rating
            review.comment = comment
            db.session.commit()
            flash('Your review has been edited', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_review.html', title="CodeTutors - Review your Tutor" ,form=form, tutor=tutor)

@app.route('/my_reviews')
@login_required
def my_reviews():
    user = Users.query.get(current_user.id)
    page = request.args.get('page', 1, type=int)
    result = Reviews.query.filter(Reviews.user==user).paginate(page, app.config['REVIEWS_PER_PAGE'], False)
    next_url = url_for('my_reviews', page=result.next_num) if result.has_next else None
    prev_url = url_for('my_reviews', page=result.prev_num) if result.has_prev else None
    
    return render_template('my_reviews.html', title="CodeTutors - My Reviews" ,result=result.items, next_url=next_url, prev_url=prev_url)
