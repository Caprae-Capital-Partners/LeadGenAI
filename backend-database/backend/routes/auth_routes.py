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
        return redirect(url_for('main.index'))
        # return redirect("https://app.saasquatchleads.com/")

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        success, message = AuthController.login(username, password)

        if success:
            flash(message, 'success')
            # return redirect("https://app.saasquatchleads.com/")
            return redirect(url_for('main.index'))
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
        # Delete all user subscriptions before deleting user
        from models.user_subscription_model import UserSubscription
        UserSubscription.query.filter_by(user_id=user.user_id).delete()
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
    from models.user_subscription_model import UserSubscription

    user_sub = UserSubscription.query.filter_by(user_id=current_user.user_id).first()
    is_paused = getattr(user_sub, 'is_paused', False) if user_sub else False
    pause_end_date = user_sub.pause_end_date.isoformat() if user_sub and getattr(user_sub, 'pause_end_date', None) else None

    return jsonify({
        "id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.username,
        "role": current_user.role,
        "tier": current_user.tier,
        "is_paused": is_paused,
        "pause_end_date": pause_end_date
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
    """Render the plan selection page"""
    from models.plan_model import Plan
    from controllers.subscription_controller import SubscriptionController

    # Get all available plans
    plans = Plan.query.all()

    # Get current user subscription info
    subscription_info, status_code = SubscriptionController.get_current_user_subscription_info(current_user)

    if status_code == 200:
        current_plan = subscription_info.get('subscription', {}).get('plan_name', 'Free')
        current_credits = subscription_info.get('subscription', {}).get('credits_remaining', 0)
    else:
        current_plan = 'Free'
        current_credits = 0

    return render_template('auth/choose_plan.html',
                         plans=plans,
                         current_plan=current_plan,
                         current_credits=current_credits,
                         user_tier=current_user.tier)

@auth_bp.route('/pause_subscription')
@login_required
def pause_subscription_page():
    """Render the subscription pause page"""
    from controllers.subscription_controller import SubscriptionController

    # Get current user subscription info
    subscription_info, status_code = SubscriptionController.get_current_user_subscription_info(current_user)

    if status_code != 200:
        flash('No active subscription found.', 'info')
        return redirect(url_for('auth.choose_plan'))

    # Check if user is on free tier or already paused
    if current_user.tier == 'free':
        flash('You are on the free plan and cannot pause.', 'info')
        return redirect(url_for('auth.choose_plan'))

    if current_user.tier == 'pause':
        flash('Your subscription is already paused.', 'info')
        return redirect(url_for('auth.choose_plan'))

    return render_template('auth/pause_subscription.html',
                         subscription_info=subscription_info,
                         user_tier=current_user.tier)

@auth_bp.route('/create-pause-checkout-session', methods=['POST'])
@login_required
def create_pause_checkout_session():
    """Create a Stripe checkout session for pause subscription"""
    try:
        data = request.json or {}
        pause_duration = data.get('pause_duration')

        if not pause_duration:
            return jsonify({'error': 'pause_duration is required'}), 400

        response, status_code = SubscriptionController.create_pause_checkout_session(current_user, pause_duration)
        return jsonify(response), status_code

    except Exception as e:
        current_app.logger.error(f"Error creating pause checkout session: {str(e)}")
        return jsonify({'error': 'Failed to create pause checkout session'}), 500
def create_pause_checkout_session():
    """Create a Stripe checkout session for pause subscription"""
    if not request.json:
        return jsonify({'error': 'No data provided'}), 400

    pause_duration = request.json.get('pause_duration')
    if not pause_duration:
        return jsonify({'error': 'pause_duration is required'}), 400

    # Call the controller method
    response, status_code = SubscriptionController.create_pause_checkout_session(current_user, pause_duration)
    return jsonify(response), status_code

# @auth_bp.route('/upgrade_account')
# @login_required
# def upgrade_account():
#     return render_template('auth/upgrade_account.html')
@auth_bp.route('/cancel-subscription')
@login_required
def cancel_subscription():
    """Show cancellation form"""
    try:
        # Get current subscription info
        subscription_info, status_code = SubscriptionController.get_current_user_subscription_info(current_user)

        if status_code != 200:
            flash('Unable to retrieve subscription information.', 'error')
            return redirect(url_for('auth.choose_plan'))

        # Check if user can see this page (either active subscription or scheduled for cancellation)
        is_scheduled = subscription_info.get('subscription', {}).get('is_scheduled_for_cancellation', False)
        is_canceled = subscription_info.get('subscription', {}).get('is_canceled', False)

        # Only show this page if user has an active subscription or one scheduled for cancellation
        if current_user.tier == 'free' and not is_scheduled:
            flash('You are already on the free plan.', 'info')
            return redirect(url_for('auth.choose_plan'))

        return render_template('auth/cancel_subscription.html', subscription_info=subscription_info)
    except Exception as e:
        current_app.logger.error(f"Error showing cancellation form: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.choose_plan'))

# def cancel_subscription_page():
#     """Render the subscription cancellation page"""
#     from controllers.subscription_controller import SubscriptionController

#     # Get current user subscription info
#     subscription_info, status_code = SubscriptionController.get_current_user_subscription_info(current_user)

#     if status_code != 200:
#         flash('No active subscription found.', 'info')
#         return redirect(url_for('auth.choose_plan'))

#     # Check if user is already on free tier
#     if current_user.tier == 'free':
#         flash('You are already on the free plan.', 'info')
#         return redirect(url_for('auth.choose_plan'))

#     return render_template('auth/cancel_subscription.html',
#                          subscription_info=subscription_info,
#                          user_tier=current_user.tier)

@auth_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session"""
    # Call the controller method
    response, status_code = SubscriptionController.create_checkout_session(current_user)
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

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    success, message = AuthController.verify_email(token)
    current_app.logger.info(f"Email verification result: {success}, message: {message}")
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/send-verification')
@login_required
def send_verification():
    AuthController.send_verification_email(current_user)
    flash('Verification email sent!', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            AuthController.send_password_reset_email(user)
        flash('If your email is registered, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('password')
        success, message = AuthController.reset_password(token, new_password)
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)

# API: Send verification email (for logged-in user)
@auth_bp.route('/api/auth/send-verification', methods=['POST'])
@login_required
def api_send_verification():
    try:
        AuthController.send_verification_email(current_user)
        return jsonify({"message": "Verification email sent!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API: Verify email with token
@auth_bp.route('/api/auth/verify-email/<token>', methods=['POST'])
def api_verify_email(token):
    success, message = AuthController.verify_email(token)
    if success:
        return jsonify({"redirect_url": "https://sandbox-api.saasquatchleads.com/auth", "message": message}), 200
    else:
        return jsonify({"error": message}), 400

# API: Forgot password (request reset email)
@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required."}), 400
    user = User.query.filter_by(email=email).first()
    if user:
        AuthController.send_password_reset_email(user)
    # Always return success to avoid leaking user existence
    return jsonify({"message": "If your email is registered, a reset link has been sent."}), 200



# API: Reset password with token
@auth_bp.route('/api/auth/reset-password/<token>', methods=['POST'])
def api_reset_password(token):
    data = request.get_json()
    new_password = data.get('password')
    if not new_password:
        return jsonify({"error": "Password is required."}), 400
    success, message = AuthController.reset_password(token, new_password)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400

@auth_bp.route('/api/auth/check-student-email', methods=['POST'])
def check_student_email():
    """API endpoint to check if an email is a student email (school domain)"""
    from controllers.student_verification_controller import is_student_email
    data = request.json or {}
    email = data.get('email', '').lower()
    if not email:
        return jsonify({"error": "Email is required."}), 400
    is_student = is_student_email(email)
    return jsonify({"is_student_email": is_student}), 200

@auth_bp.route('/api/auth/user/<string:user_id>/cancel_subscription', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def api_cancel_user_subscription(user_id):
    """API: Cancel user subscription (admin/developer only)"""
    data = request.json or {}
    cancellation_type = data.get('cancellation_type', 'immediate') # Default to immediate
    feedback = data.get('feedback')
    comment = data.get('comment')

    if str(user_id) == str(current_user.user_id):
        return jsonify({"error": "You cannot cancel your own account via this admin route. Please use the user-facing cancellation route."}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Ensure the target user has a subscription to cancel
        from models.user_subscription_model import UserSubscription
        user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
        if not user_sub or user.tier == 'free':
            return jsonify({"error": f"User {user.username} does not have an active paid subscription to cancel."}), 400

        response, status_code = SubscriptionController.cancel_subscription(user, cancellation_type, feedback, comment)
        return jsonify(response), status_code
    except Exception as e:
        current_app.logger.error(f"Error canceling subscription for user {user_id} via API: {str(e)}")
        db.session.rollback() # Ensure rollback in case of error
        return jsonify({"error": f"Failed to cancel subscription: {str(e)}"}), 500

@auth_bp.route('/api/auth/user/<string:user_id>/reactivate_subscription', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def api_reactivate_user_subscription(user_id):
    """API: Reactivate user subscription (admin/developer only)"""

    if str(user_id) == str(current_user.user_id):
        return jsonify({"error": "You cannot reactivate your own account via this admin route."}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        response, status_code = SubscriptionController.reactivate_subscription(user)
        return jsonify(response), status_code
    except Exception as e:
        current_app.logger.error(f"Error reactivating subscription for user {user_id} via API: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Failed to reactivate subscription: {str(e)}"}), 500