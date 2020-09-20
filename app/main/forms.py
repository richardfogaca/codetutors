from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectMultipleField, widgets, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app.models import Users
from flask_uploads import UploadSet, IMAGES

photos = UploadSet('photos', IMAGES)

class UploadImageForm(FlaskForm):
    profile_img = FileField('Profile Image', validators=[FileRequired(), FileAllowed(photos, 'Images only!')])
    upload = SubmitField('Upload')

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
    
class EditProfileForm(FlaskForm):
    about_me = TextAreaField('About me', validators=[DataRequired(), Length(min=0, max=3000)])
    category = MultiCheckboxField('Programming Languages', coerce=int)
    save = SubmitField('Save')

class AddReviewForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=70)])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[Optional(), Length(min=1, max=1500)])
    submit = SubmitField('Submit')
    
class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField('Submit')