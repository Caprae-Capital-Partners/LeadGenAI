from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from controllers.auth_controller import AuthController
from flask_login import login_required, current_user, login_user, logout_user
from utils.decorators import role_required
from models.user_model import User, db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

auth_bp = Blueprint('auth', __name__)

# Get secret key from environment or use a default for development
SECRET_KEY = os.environ.get('SECRET_KEY')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, message = AuthController.login(username, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('main.index'))
        else:
            flash(message, 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'developer')
def signup():
    """Handle user registration - Only admin and developer can create accounts"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        company = request.form.get('company', '')  # Get company from form
        
        # Default role is 'user', but admin can change it
        role = request.form.get('role', 'user')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/signup.html')

        success, message = AuthController.register(username, email, password, role, company)
        
        if success:
            flash(message, 'success')
            # If admin creates a user, redirect to user management
            if current_user.is_admin():
                return redirect(url_for('auth.manage_users'))
            return redirect(url_for('main.index'))
        else:
            flash(message, 'danger')

    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    success, message = AuthController.logout()
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/manage_users')
@login_required
@role_required('admin', 'developer')
def manage_users():
    """Manage users - accessible to admins and developers"""
    users = User.query.all()
    return render_template('auth/manage_users.html', users=users)

@auth_bp.route('/update_user_role', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def update_user_role():
    """Update user role - only accessible to admins"""
    user_id = request.form.get('user_id')
    role = request.form.get('role')
    
    if not user_id or not role:
        flash('Missing required fields', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    # Validate role
    valid_roles = ['admin', 'developer', 'user']
    if role not in valid_roles:
        flash(f'Invalid role. Must be one of: {", ".join(valid_roles)}', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.manage_users'))
        
        user.role = role
        db.session.commit()
        flash(f'Role for {user.username} updated to {role}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating role: {str(e)}', 'danger')
    
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/delete_user')
@login_required
@role_required('admin', 'developer')
def delete_user():
    """Delete user - only accessible to admins"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        flash('User ID is required', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.manage_users'))
        
        # Prevent self-deletion
        if int(user_id) == current_user.user_id:
            flash('You cannot delete your own account', 'danger')
            return redirect(url_for('auth.manage_users'))
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} has been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/api/auth/login', methods=['POST'])
def login_api():
    """Login to get access token"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Log in the user with Flask-Login
    login_user(user)
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.user_id,
            "email": user.email,
            "name": user.username,
            "role": user.role
        }
    })

@auth_bp.route('/api/auth/register', methods=['POST'])
def register_api():
    """Register a new user"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    role = data.get('role', 'user')  # Default role is user
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400
    
    # Create new user
    new_user = User(
        email=email,
        password_hash=generate_password_hash(password),
        name=name,
        role=role
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        
        return jsonify({
            "message": "Registration successful",
            "user": {
                "id": new_user.user_id,
                "email": new_user.email,
                "name": new_user.username,
                "role": new_user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required
def get_user_info():
    """Get current user information"""
    return jsonify({
        "id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.username,
        "role": current_user.role
    })

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout_api():
    """Logout user"""
    logout_user()
    return jsonify({"message": "Logout successful"})

@auth_bp.route('/api/auth/users', methods=['GET'])
@login_required
@role_required('admin', 'developer')
def api_list_users():
    """API: List all users (admin/developer only)"""
    users = User.query.all()
    return jsonify({
        "users": [
            {
                "id": u.user_id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "company": getattr(u, 'company', None)
            } for u in users
        ]
    })

@auth_bp.route('/api/auth/user/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'developer')
def api_delete_user(user_id):
    """API: Delete user by id (admin/developer only, cannot delete self)"""
    if user_id == current_user.user_id:
        return jsonify({"error": "You cannot delete your own account"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User {user.username} has been deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/api/auth/user/<int:user_id>/role', methods=['PUT'])
@login_required
@role_required('admin', 'developer')
def api_update_user_role(user_id):
    """API: Update user role (admin/developer only)"""
    data = request.json
    role = data.get('role') if data else None
    valid_roles = ['admin', 'developer', 'user']
    if not role or role not in valid_roles:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        user.role = role
        db.session.commit()
        return jsonify({"message": f"Role for {user.username} updated to {role}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500 