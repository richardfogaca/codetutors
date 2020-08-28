from flask import Flask
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)

migrate = Migrate(app, db)
migrate.init_app(app,db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
db.init_app(app)


# def create_app():
#     app = Flask(__name__)
#     app.config['DEBUG'] = True
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:\
#     %(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     db = SQLAlchemy(app)
#     db.init_app(app)
#     return app

if __name__ == '__main__':
    manager.run()