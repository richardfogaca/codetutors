from flask import render_template
from app import db
from app.errors import bp

@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def not_found_error(error):
    """
    The 500 error could be invoked after a database error, 
    to make sure any failed database sessions do not interfere with any database accesses triggered by the template, I issue a session rollback.
    """
    db.session.rollback()
    return render_template('errors/500.html'), 500