from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from models.user_model import User
from models.user_subscription_model import UserSubscription
from models.lead_model import db
from functools import wraps
from datetime import datetime, timedelta

user_management_bp = Blueprint('user_management', __name__)

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({"error": "Unauthorized access"}), 403
        return f(*args, **kwargs)
    return decorated_function

@user_management_bp.route('/admin/users')
@login_required
@super_admin_required
def user_management():
    """Render the user management page"""
    current_app.logger.info(f"Rendering user management page for user: {current_user.username}")
    return render_template('admin/user_management.html')

@user_management_bp.route('/api/admin/users')
@login_required
@super_admin_required
def get_users():
    """Get all users with their subscription information"""
    current_app.logger.info(f"Fetching all users and their subscription info by admin: {current_user.username}")
    users = User.query.all()
    user_list = []

    for user in users:
        subscription = UserSubscription.query.filter_by(user_id=user.user_id).first()
        user_data = {
            'id': str(user.user_id),
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'role': user.role,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'subscription': {
                'plan': subscription.plan_name if subscription else None,
                'status': 'active' if subscription and subscription.plan_expiration_timestamp and subscription.plan_expiration_timestamp > datetime.utcnow() else 'inactive',
                'credits': subscription.credits_remaining if subscription else 0,
                'expires_at': subscription.plan_expiration_timestamp.isoformat() if subscription and subscription.plan_expiration_timestamp else None
            } if subscription else None
        }
        user_list.append(user_data)
    current_app.logger.info(f"Total users fetched: {len(user_list)}")
    return jsonify(user_list)

@user_management_bp.route('/api/admin/users/<user_id>/subscription', methods=['PUT'])
@login_required
@super_admin_required
def update_subscription(user_id):
    """Update a user's subscription"""
    data = request.get_json()
    current_app.logger.info(f"Updating subscription for user_id: {user_id} by admin: {current_user.username}")
    user = User.query.get_or_404(user_id)

    subscription = UserSubscription.query.filter_by(user_id=user.user_id).first()
    if not subscription:
        current_app.logger.warning(f"No subscription found for user_id: {user_id}. Creating new subscription.")
        subscription = UserSubscription(user_id=user.user_id)
        db.session.add(subscription)

    if 'plan' in data:
        current_app.logger.info(f"Updating plan for user_id: {user_id} to {data['plan']}")
        subscription.plan_name = data['plan']
    if 'status' in data:
        current_app.logger.info(f"Updating status for user_id: {user_id} to {data['status']}")
        if data['status'] == 'active':
            subscription.plan_expiration_timestamp = datetime.utcnow() + timedelta(days=30)  # Default to 30 days
        else:
            subscription.plan_expiration_timestamp = datetime.utcnow()
    if 'credits' in data:
        current_app.logger.info(f"Updating credits for user_id: {user_id} to {data['credits']}")
        subscription.credits_remaining = data['credits']
    if 'expires_at' in data:
        current_app.logger.info(f"Updating expiration for user_id: {user_id} to {data['expires_at']}")
        subscription.plan_expiration_timestamp = datetime.fromisoformat(data['expires_at'])
    try:
        db.session.commit()
        current_app.logger.info(f"Subscription updated successfully for user_id: {user_id}")
        return jsonify({"message": "Subscription updated successfully"})
    except Exception as e:
        current_app.logger.error(f"Error updating subscription for user_id: {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to update subscription"}), 500

@user_management_bp.route('/api/admin/users/<user_id>/toggle-status', methods=['POST'])
@login_required
@super_admin_required
def toggle_user_status(user_id):
    """Toggle a user's active status"""
    current_app.logger.info(f"Toggling active status for user_id: {user_id} by admin: {current_user.username}")
    user = User.query.get_or_404(user_id)
    if str(user.user_id) == str(current_user.user_id):
        current_app.logger.warning(f"Admin {current_user.username} attempted to deactivate their own account!")
        return jsonify({"error": "Cannot deactivate your own account"}), 400

    user.is_active = not user.is_active
    try:
        db.session.commit()
        current_app.logger.info(f"User status updated successfully for user_id: {user_id}. New status: {user.is_active}")
        return jsonify({"message": "User status updated successfully", "is_active": user.is_active})
    except Exception as e:
        current_app.logger.error(f"Error toggling user status for user_id: {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to update user status"}), 500