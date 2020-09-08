from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler, SMTPHandler
import os, logging

app = Flask(__name__)
csrf = CSRFProtect(app)
app._static_folder = os.path.abspath("static/")
app.config.from_object(Config)
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(os.path.dirname(app.instance_path), 'static/uploads')
mail = Mail(app)
bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login' # connecting the login view function to the login instance

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB

if not app.debug:
    # Email configuration
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='CodeTutors Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/codetutors.log', maxBytes=10240,
                                    backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Codetutors startup')

from app.models import Categories
def clever_function():
    return Categories.get_all()
app.jinja_env.globals.update(clever_function=clever_function)

if __name__ == '__main__':
    app.run()

from app import routes, models, errors
