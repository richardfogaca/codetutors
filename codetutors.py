from app import create_app, db
from app.models import Users, Categories, Tutors, Reviews

app = create_app()

# When running the 'flask shell' command, it will automatically import everything below
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Users': Users, 'Categories': Categories, 'Tutors': Tutors, 'Reviews': Reviews}