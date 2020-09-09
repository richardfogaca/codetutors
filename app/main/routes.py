from flask import render_template, flash, redirect, request, url_for, jsonify, current_app
from flask_login import current_user, login_required
from flask_http_response import success, result, error
from flask_wtf.csrf import generate_csrf
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename
from datetime import datetime
from app import db
from app.main.forms import MessageForm
from app.models import *
from app.utils import expand2square
from .forms import EditProfileForm, UploadImageForm, AddCategoryForm, AddReviewForm
from PIL import Image
from app.main import bp
import logging, os, time, hashlib, pathlib

from os import path


# this decorator function is executed before any other  view function
@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/')
@bp.route('/index')
def index():
    """
    Shows all Tutors on the index page. 
    """
    page = request.args.get('page', 1, type=int)
    result = db.session.query(Users)\
        .join(Tutors)\
        .paginate(page, current_app.config['TUTORS_PER_PAGE'], False)
    next_url = url_for('main.index', page=result.next_num) if result.has_next else None
    prev_url = url_for('main.index', page=result.prev_num) if result.has_prev else None

    return render_template('index.html', title='CodeTutors - Home', result=result.items, 
                        next_url=next_url, prev_url=prev_url)

@bp.route('/profile/<int:tutor_id>', methods=['GET'])
def profile(tutor_id):
    """Only show Tutors, won't be displaying users profiles"""
    try:
        tutor = Tutors.query.get(tutor_id)
    except NoResultFound:
        flash("Tutor not registered", "danger")
    
    user = Users.query.get(tutor.user_id)
    if user is None:
        flash('Tutor not registered', 'danger')
        return render_template('errors/404.html')
    
    page = request.args.get('page', 1, type=int)
    result = Reviews.query.filter(Reviews.tutor_id==tutor_id)\
        .paginate(page, current_app.config['REVIEWS_PER_PAGE'], False)
    
    next_url = url_for('main.profile', tutor_id=tutor_id ,page=result.next_num) if result.has_next else None
    prev_url = url_for('main.profile', tutor_id=tutor_id ,page=result.prev_num) if result.has_prev else None
    
    is_owner = True if user == current_user else False
    is_following = True if user.is_following(tutor) else False
    title = tutor.user.first_name + ' ' + tutor.user.last_name + ' - CodeTutors'
    
    return render_template('profile.html', title=title ,user=user, tutor=tutor, is_owner=is_owner, 
                        is_following=is_following, result=result.items, 
                        next_url=next_url, prev_url=prev_url)

@bp.route('/following/<int:user_id>', methods=['GET'])
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
        .paginate(page, current_app.config['TUTORS_PER_PAGE'], False)
    
    next_url = url_for('main.index', page=result.next_num) if result.has_next else None
    prev_url = url_for('main.index', page=result.prev_num) if result.has_prev else None

    return render_template('index.html', title='CodeTutors - Following', result=result.items,
                        next_url=next_url, prev_url=prev_url)

@bp.route('/followers/<int:tutor_id>', methods=['GET'])
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
        .paginate(page, current_app.config['TUTORS_PER_PAGE'], False)
    
    next_url = url_for('main.index', page=result.next_num) \
        if result.has_next else None
    prev_url = url_for('main.index', page=result.prev_num) \
        if result.has_prev else None

    return render_template('index.html', title='CodeTutors - Followers', result=result.items,
                        next_url=next_url, prev_url=prev_url)

@bp.route('/edit_profile', methods=['GET', 'POST'])
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
            current_app.photos.save(filename, name=name + '.')

            # resizing the thumbnail image
            file_url = current_app.photos.path(name) + file_extension
            image = Image.open(file_url)
            image = expand2square(image, (0, 0, 0)).resize((150, 150), Image.LANCZOS)
            image.save(file_url, quality=95)

            # saving the filename into users.profile_img
            user.profile_img = name + file_extension
        if profile_form.validate_on_submit() and profile_form.save.data and profile_form.about_me.data:
            current_user.about_me = profile_form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('main.profile', tutor_id=tutor.id))
    elif request.method == 'GET':
        profile_form.about_me.data = tutor.about_me
    return render_template('edit_profile.html', title='CodeTutors - Edit profile',
                           user=user, profile_form=profile_form, image_form=image_form)

@bp.route('/dashboard', methods=['GET', 'POST'])
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
            current_app.photos.save(filename, name=name + '.')

            # resizing the thumbnail image
            file_url = current_app.photos.path(name) + file_extension
            image = Image.open(file_url)
            image = expand2square(image, (0, 0, 0)).resize((150, 150), Image.LANCZOS)
            image.save(file_url, quality=95)

            # saving the filename into users.profile_img
            user.profile_img = name + file_extension
            db.session.commit()
            flash('Your photo has been saved.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('dashboard.html', title='CodeTutors - Dashboard',
                        user=user, image_form=image_form, is_tutor=is_tutor)

@bp.route('/display/<filename>')
@login_required
def display_image(filename):
	print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)

@bp.route('/follow_unfollow/<int:tutor_id>')
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
    return redirect(url_for('main.profile', tutor_id=tutor_id))

@bp.route('/is_following/<int:user_id>/<int:tutor_id>')
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

@bp.route('/get_rating/<int:tutor_id>')
def get_rating(tutor_id):
    try:
        tutor = Tutors.query.get(tutor_id)
    except NoResultFound:
        return jsonify(error="Tutor not found", code=404)
    pass

@bp.route('/assign_category', methods=['GET', 'POST'])
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

@bp.route('/category/<int:category_id>')
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
        .paginate(page, current_app.config['TUTORS_PER_PAGE'], False)
    next_url = url_for('main.index', page=result.next_num) if result.has_next else None
    prev_url = url_for('main.index', page=result.prev_num) if result.has_prev else None
    
    category_name = Categories.query.get(category_id).name
    title = 'CodeTutors [' + category_name + ']' 
    
    return render_template('index.html', title=title, result=result.items, 
                        next_url=next_url, prev_url=prev_url)
    
@bp.route('/add_review/<int:tutor_id>', methods=['GET', 'POST'])
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
            redirect(url_for('main.index'))
        title = form.title.data
        rating = form.rating.data
        comment = form.comment.data
        if rating < 1 or rating > 5:
            flash("Your rating must be from 1 to 5")
            return redirect(url_for('main.add_review'))
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
        return redirect(url_for('main.index'))
    
    return render_template('add_review.html', title="CodeTutors - Review your Tutor" ,form=form, tutor=tutor)

@bp.route('/my_reviews')
@login_required
def my_reviews():
    user = Users.query.get(current_user.id)
    page = request.args.get('page', 1, type=int)
    result = Reviews.query.filter(Reviews.user==user).paginate(page, current_app.config['REVIEWS_PER_PAGE'], False)
    next_url = url_for('main.my_reviews', page=result.next_num) if result.has_next else None
    prev_url = url_for('main.my_reviews', page=result.prev_num) if result.has_prev else None
    
    return render_template('my_reviews.html', title="CodeTutors - My Reviews" ,result=result.items, next_url=next_url, prev_url=prev_url)

@bp.route('/send_message/<int:user_id>', methods=['GET', 'POST'])
@login_required
def send_message(user_id):
    user = Users.query.filter_by(id=user_id).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Messages(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.messages'))
    return render_template('send_message.html', title='CodeTutors - Send Message',
                           form=form, recipient=user.first_name)
    
@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Messages.timestamp.desc()).paginate(
            page, current_app.config['MESSAGES_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', title='CodeTutors - Messages', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/notifications')
@login_required
def notifications():
    """
    Giving the option to only request notifications since a given time.
        The since option can be included in the query string of the request URL,
        with the unix timestamp of the starting time, as a floating point number.
        Only notifications that occurred after this time will be returned if this argument is included
    """ 
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notifications.timestamp > since).order_by(Notifications.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])