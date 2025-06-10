from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from models.user_model import User
from models.user_subscription_model import UserSubscription
from models.lead_model import db
from functools import wraps
from utils.decorators import role_required
from datetime import datetime, timedelta

user_management_bp = Blueprint('user_management', __name__)


@user_management_bp.route('/admin/users')
@login_required

def user_management():
    """Render the user management page"""
    return render_template('admin/user_management.html')

@user_management_bp.route('/api/admin/users')
@login_required
def get_users():
    """Get all users with their subscription information"""
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
    
    return jsonify(user_list)

@user_management_bp.route('/api/admin/users/<user_id>/subscription', methods=['PUT'])
@login_required
def update_subscription(user_id):
    """Update a user's subscription"""
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    
    subscription = UserSubscription.query.filter_by(user_id=user.user_id).first()
    if not subscription:
        subscription = UserSubscription(user_id=user.user_id)
        db.session.add(subscription)
    
    if 'plan' in data:
        subscription.plan_name = data['plan']
    if 'status' in data:
        if data['status'] == 'active':
            subscription.plan_expiration_timestamp = datetime.utcnow() + timedelta(days=30)  # Default to 30 days
        else:
            subscription.plan_expiration_timestamp = datetime.utcnow()
    if 'credits' in data:
        subscription.credits_remaining = data['credits']
    if 'expires_at' in data:
        subscription.plan_expiration_timestamp = datetime.fromisoformat(data['expires_at'])
    
    db.session.commit()
    return jsonify({"message": "Subscription updated successfully"})

@user_management_bp.route('/api/admin/users/<user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle a user's active status"""
    user = User.query.get_or_404(user_id)
    if str(user.user_id) == str(current_user.user_id):
        return jsonify({"error": "Cannot deactivate your own account"}), 400
        
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"message": "User status updated successfully", "is_active": user.is_active}) 