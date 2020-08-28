from datetime import datetime
from app import login
from manage import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from time import time
import jwt


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('tutors.id'))
)

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=True, nullable=False)
    last_name = db.Column(db.String(64), index=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    profile_img = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    timestamp_joined = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(140), default=datetime.utcnow)

    # the many-to-many in this table is accessible via user.followed
    # In Tutors via tutor.followers
    followed = db.relationship('Tutors', secondary=followers, lazy='dynamic',
        backref=db.backref('followers', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon'.format(
        digest)
    
    def follow(self, tutor):
        if not self.is_following(tutor):
            self.followed.append(tutor)

    def unfollow(self, tutor):
        if self.is_following(tutor):
            self.followed.remove(tutor)

    def is_following(self, tutor):
        if tutor.id is None:
            return False
        return self.followed.filter_by(id=tutor.id).first() is not None

    def following_total(self):
        return self.followed.count()

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Users.query.get(id)

    def __repr__(self):
        return '<User {} {}>'.format(self.first_name, self.last_name)

class Tutors(db.Model):
    __tablename__ = 'tutors'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    about_me = db.Column(db.String(140), nullable=True)
    price = db.Column(db.Float)
    telephone = db.Column(db.String(50), nullable=True)

    # Connecting this field to the association table. 
    category = db.relationship("Categories", secondary="tutor_category")

    def followers_total(self):
        return self.followers.count()
    
    def add_category(self, category):
        return self.category.append(category)

    def __repr__(self):
        return '<Tutor id {}'.format(self.user_id) + ' , price {}>'.format(self.price)

class Reviews(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    rating = db.Column(db.Integer, index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Review User: {}'.format(self.user_id) + ' Tutor: {}'.format(self.tutor_id) + ' Rating: {}>'.format(self.rating)

class Categories(db.Model):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    # Connecting this field to the association table. 
    tutor = db.relationship('Tutors', secondary="tutor_category")

    def __repr__(self):
        return '<Category {}>'.format(self.name)

# Declaring the association table
tutor_category = db.Table('tutor_category',
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

@login.user_loader
def load_user(id):
    return Users.query.get(int(id))

from app import app