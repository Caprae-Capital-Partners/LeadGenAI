from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main landing page"""
    return render_template('index.html')

@main_bp.route('/docs/user')
@login_required
def user_docs():
    """Render the user documentation page"""
    return render_template('docs/user_docs.html')

@main_bp.route('/docs/admin')
@login_required
def admin_docs():
    """Render the admin documentation page - only accessible to admins and developers"""
    if current_user.role not in ['admin', 'developer']:
        return render_template('errors/403.html'), 403
    return render_template('docs/admin_docs.html') 