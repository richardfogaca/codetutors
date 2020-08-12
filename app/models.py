from datetime import datetime
from manage import db
from flask_sqlalchemy import SQLAlchemy


# Declaring the association table
tutor_category = db.Table('tutor_category',
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    profile_img = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    timestamp_joined = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Tutors(db.Model):
    __tablename__ = 'tutors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    price = db.Column(db.Float)

    # Connecting this field to the association table. 
    category = db.relationship("Categories", secondary=tutor_category)

    def __repr__(self):
        return '<Tutor id {}'.format(self.user_id) + ' , price {}>'.format(self.price)

class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    rating = db.Column(db.Integer, index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Review User: {}'.format(self.user_id) + ' Tutor: {}'.format(self.tutor_id) + ' Rating: {}'.format(self.rating)

class Categories(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    # Connecting this field to the association table. 
    tutor = db.relationship('Tutors', secondary=tutor_category)

    def __repr__(self):
        return '<Catego'