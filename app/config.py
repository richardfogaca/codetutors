import os

POSTGRES = {
    'user': 'richardfogaca',
    'pw': 'richard2906',
    'db': 'codetutors',
    'host': 'localhost',
    'port': '5432',
}

class Config(object):
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:\
        %(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4MB file max-limit.
    TEMPLATES_AUTO_RELOAD=True
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['rfncoding@gmail.com']
    TUTORS_PER_PAGE = 2
    REVIEWS_PER_PAGE = 1
    
    # from app import app
    # with app.app_context():
    #     UPLOADED_PHOTOS_DEST = os.path.join(os.path.dirname(app.instance_path), 'static/uploads')