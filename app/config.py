import os

POSTGRES = {
    'user': 'richard',
    'pw': 'richard2906',
    'db': 'codetutors',
    'host': 'localhost',
    'port': '5432',
}

class Config(object):
    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:\
        %(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'