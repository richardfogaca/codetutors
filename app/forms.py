from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import Categories
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectMultipleField, widgets, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional, NumberRange
from app.models import Users
from app import photos

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me', default='checked')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    first_name = StringField('First name', validators=[DataRequired()])
    last_name = StringField('Last name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign In')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class UploadImageForm(FlaskForm):
    profile_img = FileField('Profile Image', validators=[FileRequired(), FileAllowed(photos, 'Images only!')])
    upload = SubmitField('Upload')
    
class EditProfileForm(FlaskForm):
    about_me = TextAreaField('About me', validators=[Length(min=0, max=3000)])
    save = SubmitField('Save')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired()])
    new_password_2 = PasswordField('Repeat new password', validators=[DataRequired(), EqualTo('new_password')])
    save = SubmitField('Save')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class AddCategoryForm(FlaskForm):
    category = MultiCheckboxField('Programming Languages', coerce=int)
    save = SubmitField('Save')

class AddReviewForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=70)])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=1, max=1500)])
    submit = SubmitField('Submit')