from app import create_app, db
from app.models import Users, Categories, Tutors, Reviews, Messages, Notifications
from sqlalchemy import func
from app.config import Config

config = Config()
app = create_app(config)

# When running the 'flask shell' command, it will automatically import everything below
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Users': Users, 'Categories': Categories, 
            'Tutors': Tutors, 'Reviews': Reviews, 'Messages': Messages,
            'Notifications': Notifications, 'func': func}