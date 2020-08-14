from app import app
from manage import db
from app.models import Users, Categories, Tutors, Reviews

# When running the 'flask shell' command, it will automatically import everything below
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Users': Users, 'Categories': Categories, 'Tutors': Tutors, 'Reviews': Reviews, 'app': app}