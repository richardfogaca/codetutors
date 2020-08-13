from flask import Flask
from app.config import Config
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
login = LoginManager(app)
login.login_view = 'login' # connecting the login view function to the login instance

if __name__ == '__main__':
    app.run()

from app import routes
