from models.user_model import User, db
from flask_login import login_user, logout_user
from models.plan_model import Plan
from models.user_subscription_model import UserSubscription
from datetime import datetime, timedelta
from utils.token_utils import generate_token, confirm_token
from utils.email_utils import send_email
from flask import url_for, render_template, current_app, redirect, request
# from controllers.student_verification_controller import is_student_email, set_user_as_student


class AuthController:
    @staticmethod
    def register(username, email, password, role='user', company='', linkedin_url=''):
        """Register a new user"""
        current_app.logger.info(f"Attempting to register user: username={username}, email={email}, role={role}")
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            current_app.logger.warning(f"Registration failed: Username '{username}' already exists.")
            return False, "Username already exists"

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            current_app.logger.warning(f"Registration failed: Email '{email}' already registered.")
            return False, "Email already registered"

        # Validate role
        valid_roles = ['admin', 'developer', 'user']
        if role not in valid_roles:
            current_app.logger.warning(f"Registration failed: Invalid role '{role}'.")
            return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"

        try:
            # Create new user
            user = User(username=username, email=email, role=role, company=company, linkedin_url=linkedin_url)
            user.set_password(password)

            # Add to database (commit early to get user_id if autoincremented, or ensure user exists for FK)
            # Note: This might need adjustment based on how user_id is generated (if it's UUID, may not need early commit)
            db.session.add(user)
            db.session.flush() # Use flush to make user_id available without committing

            # Assign default 'free' tier in User model (for quick access)
            user.tier = 'free'

            # Fetch the 'Free' plan
            free_plan = Plan.query.filter_by(plan_name='Free').first()
            current_app.logger.info(f"Fetched free plan: {free_plan}")
            if free_plan:
                # Calculate expiration date (30 days from start timestamp)
                tier_start = datetime.utcnow()
                tier_expiration = tier_start + timedelta(days=30)

                # Create a new UserSubscription entry for the user, setting all relevant columns
                user_subscription = UserSubscription(
                    user_id=user.user_id, # Use the newly created user's ID
                    plan_id=free_plan.plan_id,
                    plan_name=free_plan.plan_name, # Set plan_name
                    payment_frequency=free_plan.credit_reset_frequency if free_plan.credit_reset_frequency else 'monthly', # Use credit_reset_frequency from Plan
                    credits_remaining=free_plan.initial_credits if free_plan.initial_credits is not None else 0,
                    tier_start_timestamp=tier_start, # Set the start timestamp
                    plan_expiration_timestamp=tier_expiration, # Set the calculated expiration timestamp
                    username=user.username
                )
                db.session.add(user_subscription)
            else:
                current_app.logger.warning("'Free' plan not found in database. Cannot create initial user subscription.")
                # Decide how to handle this - maybe raise an error or create user without subscription?
                # For now, user is created without subscription, which might cause issues later.

            # Commit both user and subscription (if created) in a single transaction
            db.session.commit()
            current_app.logger.info(f"User '{username}' registered successfully. Sending verification email...")
            AuthController.send_verification_email(user)

            return True, "Registration successful"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration failed for user '{username}': {str(e)}")
            return False, f"Registration failed: {str(e)}"

    @staticmethod
    def login(username, password):
        """Login a user"""
        try:
            # Find user by username
            user = User.query.filter_by(username=username).first()
            # Check if user exists and password is correct
            if user and user.check_password(password):
                login_user(user)
                return True, "Login successful"
            return False, "Invalid username or password"
        except Exception as e:
            return False, f"Login failed: {str(e)}"

    @staticmethod
    def logout():
        """Logout current user"""
        try:
            logout_user()
            return True, "Logout successful"
        except Exception as e:
            return False, f"Logout failed: {str(e)}"

    @staticmethod
    def send_verification_email(user):
        try:
            token = generate_token(user.email, salt='email-verify')
            user.email_verification_sent_at = datetime.utcnow()
            db.session.commit()
            # Use frontend URL for verification
            if "sandbox-api.capraeleadseekers.site" in request.host:
                verify_url = f"https://sandboxdev.saasquatchleads.com/verify-email/{token}"
            elif "data.capraeleadseekers.site" in request.host:
                verify_url = f"https://app.saasquatchleads.com/verify-email/{token}"
            else:
                verify_url = f"https://app.saasquatchleads.com/verify-email/{token}"
            html = render_template('emails/verify_email.html', verify_url=verify_url, user=user, now=datetime.utcnow)
            send_email('Verify Your Email', [user.email], html)
            current_app.logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email to {user.email}: {str(e)}")

    @staticmethod
    def verify_email(token):
        try:
            email = confirm_token(token, salt='email-verify')
            if not email:
                current_app.logger.warning("Email verification failed: Invalid or expired token.")
                return False, "Invalid or expired token."
            user = User.query.filter_by(email=email).first()
            if not user:
                current_app.logger.warning(f"Email verification failed: No user found for email {email}.")
                return False, "Invalid user."
            if user.is_email_verified:
                current_app.logger.info(f"Email already verified for user {user.email}.")
                return False, "Email already verified."
            if user.email_verification_sent_at and datetime.utcnow() > user.email_verification_sent_at + timedelta(hours=1):
                current_app.logger.warning(f"Verification link expired for user {user.email}.")
                return False, "Verification link expired."
            user.is_email_verified = True
            db.session.commit()
            current_app.logger.info(f"Email verified for user {user.email}.")

            # Student domain check and role update (added, do not change existing logic)
            # if is_student_email(user.email):
            #     set_user_as_student(user)

            # return True, "Success, Email verified!"
        except Exception as e:
            current_app.logger.error(f"Error during email verification: {str(e)}")
            return False, f"Verification failed: {str(e)}"

    @staticmethod
    def send_password_reset_email(user):
        try:
            token = generate_token(user.email, salt='password-reset')
            user.password_reset_sent_at = datetime.utcnow()
            db.session.commit()
            # Use frontend URL for reset
            if "sandbox-api.capraeleadseekers.site" in request.host:
                reset_url = f"https://sandboxdev.saasquatchleads.com/reset-password/{token}"
            elif "data.capraeleadseekers.site" in request.host:
                reset_url = f"https://app.saasquatchleads.com/reset-password/{token}"
            else:
                reset_url = f"https://app.saasquatchleads.com/reset-password/{token}"
            html = render_template('emails/reset_password.html', reset_url=reset_url, user=user, now=datetime.utcnow)
            send_email('Reset Your Password', [user.email], html)
            current_app.logger.info(f"Password reset email sent to {user.email} at {datetime.utcnow()}, username: {user.username}")
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")

    @staticmethod
    def reset_password(token, new_password):
        try:
            email = confirm_token(token, salt='password-reset')
            if not email:
                current_app.logger.warning("Password reset failed: Invalid or expired token.")
                return False, "Invalid or expired token."
            user = User.query.filter_by(email=email).first()
            if not user:
                current_app.logger.warning(f"Password reset failed: No user found for email {email}.")
                return False, "User not found."
            if user.password_reset_sent_at and datetime.utcnow() > user.password_reset_sent_at + timedelta(hours=1):
                current_app.logger.warning(f"Password reset link expired for user {user.email}.")
                return False, "Reset link expired."
            user.set_password(new_password)
            db.session.commit()
            current_app.logger.info(f"Password reset successful for user {user.email}.")
            return True, "Password reset successful."
        except Exception as e:
            current_app.logger.error(f"Error during password reset: {str(e)}")
            return False, f"Password reset failed: {str(e)}"