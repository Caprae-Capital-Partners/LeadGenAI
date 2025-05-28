from models.user_model import User, db
from flask_login import login_user, logout_user
from models.plan_model import Plan
from models.user_subscription_model import UserSubscription
from datetime import datetime, timedelta
import logging

class AuthController:
    @staticmethod
    def register(username, email, password, role='user', company=''):
        """Register a new user"""
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return False, "Username already exists"

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return False, "Email already registered"

        # Validate role
        valid_roles = ['admin', 'developer', 'user']
        if role not in valid_roles:
            return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"

        try:
            # Create new user
            user = User(username=username, email=email, role=role, company=company)
            user.set_password(password)

            # Add to database (commit early to get user_id if autoincremented, or ensure user exists for FK)
            # Note: This might need adjustment based on how user_id is generated (if it's UUID, may not need early commit)
            db.session.add(user)
            db.session.flush() # Use flush to make user_id available without committing

            # Assign default 'free' tier in User model (for quick access)
            user.tier = 'free'

            # Fetch the 'Free' plan
            free_plan = Plan.query.filter_by(plan_name='Free').first()
            logging.info(f"free plan {free_plan}")
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
                    plan_expiration_timestamp=tier_expiration # Set the calculated expiration timestamp
                )
                db.session.add(user_subscription)
            else:
                logging.warning("'Free' plan not found in database. Cannot create initial user subscription.")
                # Decide how to handle this - maybe raise an error or create user without subscription?
                # For now, user is created without subscription, which might cause issues later.

            # Commit both user and subscription (if created) in a single transaction
            db.session.commit()

            return True, "Registration successful"
        except Exception as e:
            db.session.rollback()
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