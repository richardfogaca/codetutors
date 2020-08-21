from flask import render_template
from app import app
from manage import db

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def not_found_error(error):
    """
    The 500 error could be invoked after a database error, 
    to make sure any failed database sessions do not interfere with any database accesses triggered by the template, I issue a session rollback.
    """
    db.session.rollback()
    return render_template('500.html'), 500