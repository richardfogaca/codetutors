from datetime import datetime
from time import time
from app import db
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from time import time
from sqlalchemy import func
import jwt, json

followers_table = db.Table('followers_table',
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

    # one to one relationship (uselist False)
    tutor = db.relationship('Tutors', backref='user', uselist=False)
    followed = db.relationship('Tutors', secondary=followers_table, lazy='dynamic',
        backref=db.backref('followers', lazy='dynamic'))
    reviews = db.relationship('Reviews', backref='user', uselist=True)
    
    messages_sent = db.relationship('Messages',
                                    foreign_keys='Messages.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Messages',
                                        foreign_keys='Messages.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    
    notifications = db.relationship('Notifications', backref='user',
                                    lazy='dynamic')

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
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def is_tutor(self):
        return True if self.tutor is not None else False

    def has_rated_tutor(self, tutor):
        result = db.session.query(Reviews)\
            .filter(Reviews.user_id==self.id, Reviews.tutor_id==tutor.id)\
            .first()
        return True if result is not None else False
    
    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Messages.query.filter_by(recipient=self).filter(
            Messages.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notifications(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
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
    about_me = db.Column(db.String(3000), nullable=True)
    price = db.Column(db.Float)
    telephone = db.Column(db.String(50), nullable=True)

    # Connecting this field to the association table. 
    categories = db.relationship('Categories', secondary="tutor_category", lazy='dynamic',
        backref=db.backref('tutors', lazy='dynamic'))
    reviews = db.relationship('Reviews', backref='tutor', uselist=True)

    def followers_total(self):
        return self.followers.count()
    

    def add_category(self, category):
        return self.category.append(category)

    def get_categories(self):
        """ Returns all categories of the respective Tutor
        """
        return db.session.query(Categories).join(Tutors.categories).filter(Tutors.user_id==self.user_id).all()

    def get_categories_id(self):
        # Will return a list containing just the IDs of the Categories the Tutor has assigned
        result = db.session.query(Categories.id).join(Tutors.categories).filter(Tutors.user_id==self.user_id).all()
        return [value for value, in result]
    
    def delete_categories(self):
        return db.session.query(Tutors.categories).filter(Tutors.user_id==self.user_id).delete()
    
    def count_ratings(self):
        """
        Returns the total of ratings of the Tutor
        """
        result = Reviews.query.filter(Reviews.tutor_id==self.id).all()
        
        return 0 if len(result) == 0 else db.session.query(func.count(Reviews.rating))\
                                            .group_by(Reviews.tutor_id)\
                                            .filter(Reviews.tutor_id==self.id)\
                                            .first()[0]

    def get_average_ratings(self):
        """
        Returns an average all ratings of the Tutor, rounded to 1 decimal place
        """
        result = Reviews.query.filter(Reviews.tutor_id==self.id).all()
        
        return 0 if len(result) == 0 else round(db.session.query(func.avg(Reviews.rating))\
                                            .group_by(Reviews.tutor_id)\
                                            .filter(Reviews.tutor_id==self.id)\
                                            .first()[0], 1)

    def __repr__(self):
        return '<Tutor id {}'.format(self.user_id) + ' , price {}>'.format(self.price)

class Reviews(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    
    # Create a relationship for these columns
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    
    title = db.Column(db.String(70), nullable=True)
    rating = db.Column(db.Integer, index=True)
    comment = db.Column(db.String(1500), nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Review User: {}'.format(self.user_id) + ' Tutor: {}'.format(self.tutor_id) + ' Rating: {}>'.format(self.rating)

class Categories(db.Model):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    
    # tutors = db.relationship('Tutors', secondary="tutor_category")

    @staticmethod
    def get_all():
        return db.session.query(Categories).all()

    def __repr__(self):
        return '<Category {}>'.format(self.name)

# Declaring the association table
tutor_category = db.Table('tutor_category',
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

class Messages(db.Model):
    __tablename__ = 'messages'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)
    
class Notifications(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))

from app import login

@login.user_loader
def load_user(id):
    return Users.query.get(int(id))
