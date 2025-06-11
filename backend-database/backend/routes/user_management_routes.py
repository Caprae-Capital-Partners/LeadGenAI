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
    return render_template('admin/user_management.html')

@user_management_bp.route('/api/admin/users')
@login_required
@super_admin_required
def get_users():
    """Get all users with their subscription information"""
    current_app.logger.info(f"Fetching all users and their subscription info by admin: {current_user.username}")
    users = User.query.all()
    users = users[:30]
    user_list = []
    for idx, user in enumerate(users, start=1):
        try:
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
        except Exception as e:
            current_app.logger.error(f"Error processing user {user.user_id}, {user.username} , {getattr(user, 'username', 'unknown')}: {str(e)}")
            continue
    current_app.logger.info(f"Total users processed: {len(user_list)}")
    return jsonify({
        'count': len(user_list),
        'users': user_list
    })

@user_management_bp.route('/api/admin/users_simple')
@login_required
# @super_admin_required
def get_users_simple():
    """Get all users with their subscription information (simple version, matching original keys) in batches of 200"""
    from models.user_model import User
    from models.user_subscription_model import UserSubscription
    from datetime import datetime

    batch_size = 200
    offset = 0
    user_list = []
    try:
        while True:
            users = User.query.offset(offset).limit(batch_size).all()
            if not users:
                break
            for idx, user in enumerate(users, start=offset+1):
                try:
                    current_app.logger.info(f"Processed user {idx}: {user.username}")
                    subscription = UserSubscription.query.filter_by(user_id=user.user_id).first()
                    user_data = {
                        'id': str(user.user_id),
                        'username': user.username or "",
                        'email': user.email or "",
                        'is_active': bool(user.is_active),
                        'role': user.role or "user",
                        'created_at': user.created_at.isoformat() if user.created_at else None,
                        'subscription': {
                            'plan': subscription.plan_name if subscription else None,
                            'status': 'active' if subscription and subscription.plan_expiration_timestamp and subscription.plan_expiration_timestamp > datetime.utcnow() else 'inactive',
                            'credits': subscription.credits_remaining if subscription else 0,
                            'expires_at': subscription.plan_expiration_timestamp.isoformat() if subscription and subscription.plan_expiration_timestamp else None
                        } if subscription else {
                            'plan': None,
                            'status': 'inactive',
                            'credits': 0,
                            'expires_at': None
                        }
                    }
                    user_list.append(user_data)
                    current_app.logger.info(f"Processed user {idx}: {user.username}")
                except Exception as e:
                    current_app.logger.error(f"Error processing user {getattr(user, 'user_id', 'unknown')}, {getattr(user, 'username', 'unknown')}: {str(e)}")
                    continue
            offset += batch_size
    except Exception as e:
        current_app.logger.error(f"Error fetching users or subscriptions: {str(e)}")
        return jsonify({'error': 'Failed to fetch users'}), 500

    current_app.logger.info(f"Total users processed: {len(user_list)}")
    return jsonify({
        'count': len(user_list),
        'users': user_list
    })

@user_management_bp.route('/api/admin/users/<user_id>/subscription', methods=['PUT'])
@login_required
@super_admin_required
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
@super_admin_required
def toggle_user_status(user_id):
    """Toggle a user's active status"""
    user = User.query.get_or_404(user_id)
    if str(user.user_id) == str(current_user.user_id):
        return jsonify({"error": "Cannot deactivate your own account"}), 400

    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"message": "User status updated successfully", "is_active": user.is_active})