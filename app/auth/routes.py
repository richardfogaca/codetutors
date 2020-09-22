from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app.auth.forms import LoginForm, UserRegistrationForm, ResetPasswordForm, ChangePasswordForm, ResetPasswordRequestForm, TutorRegistrationForm
from app.models import Users, Tutors, Categories
from app import db
from werkzeug.urls import url_parse
from app.auth.email import send_password_reset_email

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next') # next is the page the user tried to access before login
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.home')
        return redirect(next_page)
    return render_template('auth/login.html', title='CodeTutors - Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        user = Users(first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='CodeTutors - Register', form=form)

@bp.route('/register_tutor', methods=['GET', 'POST'])
@login_required
def register_tutor():
    # Validate if tutor is already registered
    user = Users.query.get(current_user.id)

    if user.is_tutor():
        return redirect(url_for('main.profile', tutor_id=user.tutor.id))
    form = TutorRegistrationForm()
    form.category.choices = [(c.id, c.name) for c in Categories.query.order_by('name')]
    
    categories = Categories.get_all()
    categories_total = len(categories)
    
    if form.validate_on_submit():
        about_me = form.about_me.data
        price = form.price.data
        telephone = form.telephone.data
        tutor = Tutors(user_id=current_user.id, about_me=about_me, telephone=telephone, price=price)
        user.tutor = tutor
        db.session.add(tutor)
        db.session.commit()
        
        # looping through the choices, we check the choice ID against what was passed in the form
        for choice in categories:
            # when there's a match, append the object
            if choice.id in form.category.data:
                tutor.categories.append(choice)
        db.session.commit()
        flash('Congratulations, you are now a registered tutor!', 'success')
        return redirect(url_for('main.profile', tutor_id=tutor.id))
    return render_template('auth/register_tutor.html', title='CodeTutors - Tutor Registration', 
                           form=form, categories_total=categories_total)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = Users.query.get(current_user.id)
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if user.check_password(form.current_password.data):
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Sucess! You have updated your password!', 'success')
        else:
            flash('Please review your password and try again', 'warning')
        return redirect(url_for('main.dashboard'))
    return render_template('auth/change_password.html', title='CodeTutors - Reset Password' ,user=user, form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='CodeTutors - Reset Password', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = Users.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', title='CodeTutors - Reset Password', form=form)