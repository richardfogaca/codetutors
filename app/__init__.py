from flask import Flask
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from flask_login import LoginManager
import os

app = Flask(__name__)
csrf = CSRFProtect(app)
app._static_folder = os.path.abspath("static/")
app.config.from_object(Config)
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(os.path.dirname(app.instance_path), 'static/uploads')

login = LoginManager(app)
login.login_view = 'login' # connecting the login view function to the login instance

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB

if __name__ == '__main__':
    app.run()

from app import routes



