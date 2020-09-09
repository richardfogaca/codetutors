from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_uploads import patch_request_class
from app.config import Config
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler, SMTPHandler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
import os, logging

csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login = LoginManager()
login.login_view = 'auth.login' # connecting the login view function to the login instance
bootstrap = Bootstrap()

def create_app(config_class=Config):
    app = Flask(__name__,
                static_folder='../static',
                template_folder='./templates')
    
    app.config.from_object(config_class)
    
    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    
    # app._static_folder = os.path.abspath("static/")
    app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(os.path.dirname(app.instance_path), 'static/uploads')

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    patch_request_class(app)  # set maximum file size, default is 16MB

    if not app.debug and not app.testing:
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

    return app

from app import models
