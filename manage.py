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

if __name__ == '__main__':
    manager.run()