from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from controllers.auth_controller import AuthController
from controllers.subscription_controller import SubscriptionController
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
        
        if "sandbox-api.capraeleadseekers.site" in request.host:
            return redirect("https://sandboxdev.saasquatchleads.com")
        elif "data.capraeleadseekers.site" in request.host:
            return redirect("https://app.saasquatchleads.com/")

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        success, message = AuthController.login(username, password)

        if success:
            flash(message, 'success')
         
            if "sandbox-api.capraeleadseekers.site" in request.host:
                return redirect("https://sandboxdev.saasquatchleads.com")
            elif "data.capraeleadseekers.site" in request.host:
                return redirect("https://app.saasquatchleads.com")
        else:
            flash(message, 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
# @login_required
# @role_required('admin', 'developer')
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
            # if current_user.is_admin():
            #     return redirect(url_for('auth.manage_users'))

            # Log in the newly created user
            user = User.query.filter_by(email=email).first()
            if user:
                login_user(user)

            # Redirect to choose plan page after successful signup
            return redirect(url_for('auth.choose_plan'))
        else:
            flash(message, 'danger')

    return render_template('auth/signup.html')


# @auth_bp.route('/logout')
# @login_required
# def logout():
#     """Handle user logout"""
#     success, message = AuthController.logout()

#     if success:
#         flash(message, 'success')
#     else:
#         flash(message, 'danger')

#     return redirect(url_for('auth.login'))

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
        if str(user_id) == str(current_user.user_id):
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

@auth_bp.route('/api/ping-auth', methods=["GET"])
@login_required
def ping_auth():
    return '', 204

@auth_bp.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


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
        "user": user.to_dict()
    })

@auth_bp.route('/api/auth/register', methods=['POST'])
def register_api():
    """Register a new user via API"""
    data = request.json

    if not data:
        return jsonify({"error": "No input data provided"}), 400

    email = data.get('email')
    password = data.get('password')
    username = data.get('username', '')
    role = data.get('role', 'user')  # Default role is user
    company = data.get('company', '') # Get company from JSON payload
    linkedin_url = data.get('linkedin_url', '') # Get linkedin_url from JSON payload

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Call the AuthController.register function
    success, message = AuthController.register(username, email, password, role, company, linkedin_url)

    if success:
        # Fetch the newly created user to log them in if needed for API flow
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user) # Log in the user with Flask-Login

        return jsonify({
            "message": "Registration successful",
            "user": user.to_dict() if user else None # Return user data if fetched
        }), 201

    else:
        # Registration failed, return the error message from the controller
        return jsonify({"error": message}), 400 # Use 400 for bad request/validation errors

@auth_bp.route('/api/auth/user', methods=['GET'])
@login_required
def get_user_info():
    """Get current user information"""
    return jsonify({
        "id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.username,
        "role": current_user.role,
        "tier" : current_user.tier,
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

@auth_bp.route('/api/auth/user/<string:user_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'developer')
def api_delete_user(user_id):
    """API: Delete user by id (admin/developer only, cannot delete self)"""
    if str(user_id) == str(current_user.user_id):
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

@auth_bp.route('/api/auth/user/<string:user_id>/role', methods=['PUT'])
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

@auth_bp.route('/choose_plan')
@login_required
def choose_plan():
    """Display the plan selection page after signup"""
    return render_template('auth/choose_plan.html')

@auth_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session"""
    # Call the controller method
    response, status_code = SubscriptionController.create_checkout_session(current_user)
    return jsonify(response), status_code

@auth_bp.route('/payment/success')
@login_required
def payment_success():
    return redirect("https://app.saasquatchleads.com")

@auth_bp.route('/payment/cancel')
@login_required
def payment_cancel():
    return redirect("https://app.saasquatchleads.com/subscription")

@auth_bp.route('/subscription')
@login_required
def subscription_page():
    """Subscription management page"""
    from models.user_subscription_model import UserSubscription
    user_sub = UserSubscription.query.filter_by(user_id=str(current_user.user_id)).first()
    return render_template('auth/manage_subscriptions.html', 
                         user_subscription=user_sub, 
                         current_tier=getattr(current_user, 'tier', 'free'))

@auth_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Main Stripe webhook endpoint"""
    from controllers.subscription_controller import SubscriptionController
    payload = request.get_data()
    sig_header = request.headers.get('stripe-signature')
    response, status_code = SubscriptionController.handle_stripe_webhook(payload, sig_header)
    return jsonify(response), status_code

@auth_bp.route('/manage_subscriptions')
@login_required
@role_required('admin')
def manage_subscriptions():
    """Manage user subscriptions - Admin only"""
    users = User.query.all()
    return render_template('auth/manage_subscriptions.html', users=users)

# @auth_bp.route('/update_subscription', methods=['POST'])
# @login_required
# @role_required('admin')
# def update_subscription():
#     """Update user subscription tier - Admin only"""
#     user_id = request.form.get('user_id')
#     subscription_tier = request.form.get('subscription_tier')

#     try:
#         user = User.query.get(user_id)
#         if user:
#             user.subscription_tier = subscription_tier
#             db.session.commit()
#             flash(f'Subscription updated for {user.username} to {subscription_tier}', 'success')
#         else:
#             flash('User not found', 'danger')
#     except Exception as e:
#         db.session.rollback()
#         flash(f'Error updating subscription: {str(e)}', 'danger')

#     return redirect(url_for('auth.manage_subscriptions'))

def handle_successful_payment(session):
    try:
        user_id = session.get('client_reference_id')
        if not user_id:
            print("No user_id found in session")
            return

        user = User.query.get(user_id)
        if not user:
            print(f"User {user_id} not found")
            return

        # Get line items and extract price ID
        line_items = stripe.checkout.Session.list_line_items(session.id)
        if not line_items or not line_items.data:
            print("No line items found")
            return

        price_id = line_items.data[0].price.id

        # Map price_id to subscription tier
        price_to_tier = {
            current_app.config['STRIPE_PRICES']['gold']: 'gold',
            current_app.config['STRIPE_PRICES']['silver']: 'silver',
            current_app.config['STRIPE_PRICES']['bronze']: 'bronze'
        }

        new_tier = price_to_tier.get(price_id)
        if not new_tier:
            print(f"Invalid price_id: {price_id}")
            return

        user.subscription_tier = new_tier
        db.session.commit()
        print(f"Successfully updated user {user_id} to tier {new_tier}")

    except Exception as e:
        print(f"Error handling payment: {str(e)}")
        db.session.rollback()

@auth_bp.route('/api/auth/update_user', methods=['POST'])
@login_required
def update_user_info():
    """Update current user's username, email, and/or password"""
    data = request.json or {}
    user = current_user
    updated = False
    errors = []
    updated_fields = []

    if 'username' in data:
        user.username = data['username']
        updated = True
        updated_fields.append('username')
    if 'email' in data:
        user.email = data['email']
        updated = True
        updated_fields.append('email')
    if 'password' in data:
        try:
            user.set_password(data['password'])
            updated = True
            updated_fields.append('password')
        except Exception as e:
            errors.append(f"Password update failed: {str(e)}")
    if 'company' in data:
        user.company = data['company']
        updated = True
        updated_fields.append('company')
    if 'linkedin_url' in data:
        user.linkedin_url = data['linkedin_url']
        updated = True
        updated_fields.append('linkedin_url')

    if updated:
        try:
            try:
                current_app.logger.info(f"[User Update] User {user.user_id} attempting to update fields: {updated_fields}")
            except Exception as log_e:
                print(f"[User Update] Logging failed: {log_e}")
            db.session.commit()
            try:
                current_app.logger.info(f"[User Update] User {user.user_id} updated fields: {updated_fields} successfully.")
            except Exception as log_e:
                print(f"[User Update] Logging failed: {log_e}")
            return jsonify({
                "message": "User info updated successfully",
                "user": user.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            try:
                current_app.logger.error(f"[User Update] Failed to update user {user.user_id}: {str(e)}")
            except Exception as log_e:
                print(f"[User Update] Logging failed: {log_e}")
            return jsonify({"error": f"Failed to update user: {str(e)}"}), 500
    else:
        try:
            current_app.logger.warning(f"[User Update] No valid fields to update for user {user.user_id}. Errors: {errors}")
        except Exception as log_e:
            print(f"[User Update] Logging failed: {log_e}")
        return jsonify({"error": "No valid fields to update", "details": errors}), 400

@auth_bp.route('/api/auth/payment_cancel')
@login_required
def api_payment_cancel():
    """Handle payment cancellation via API"""
    response, status_code = SubscriptionController.payment_cancel_handler(current_user)
    return jsonify(response), status_code


@auth_bp.route('/api/auth/update_payment_success')
@login_required
def update_payment_success():
    """Handle successful payment method update"""
    session_id = request.args.get('session_id')
    current_app.logger.info(f"[Payment Update] Success for user {current_user.user_id}, session: {session_id}")

    return jsonify({
        'message': "Payment method updated successfully!",
        'redirect_url': "https://app.saasquatchleads.com/subscription",
        'session_id': session_id
    }), 200

@auth_bp.route('/api/auth/update_payment_cancel')
@login_required
def update_payment_cancel():
    """Handle cancelled payment method update"""
    current_app.logger.info(f"[Payment Update] Cancelled for user {current_user.user_id}")

    return jsonify({
        'message': "Payment method update was cancelled.",
        'redirect_url': "https://app.saasquatchleads.com/subscription"
    }), 200