from functools import wraps
from flask import flash, redirect, url_for, jsonify
from flask_login import current_user
import logging
# Assuming db is accessible from the models package, specifically where Lead model is defined
from models.lead_model import db # Import db
from models.user_subscription_model import UserSubscription # Import UserSubscription

def role_required(*roles):
    """
    Decorator to restrict access to specific roles.
    Usage: @role_required('admin') or @role_required('admin', 'developer')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'danger')
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                flash(f'Access denied. Required role: {", ".join(roles)}', 'danger')
                return redirect(url_for('main.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def credit_required(cost=1):
    """Decorator to check if the user has enough credits and deducts them on success."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'status': 'error', 'message': 'Authentication required.'}), 401

            user_id = current_user.get_id()
            user_subscription = UserSubscription.query.filter_by(user_id=user_id).first()

            # Ensure user has a subscription and enough credits
            if not user_subscription:
                 logging.error(f"User {user_id} attempting to access @credit_required route without a subscription.")
                 return jsonify({'status': 'error', 'message': 'User subscription not found.'}), 500

            if user_subscription.credits_remaining < cost:
                 return jsonify({'status': 'error', 'message': 'Insufficient credits.'}), 402

            # Execute the original function
            response = f(*args, **kwargs)

            # If the function executed successfully (didn't raise an exception), deduct credits
            # We might need more sophisticated checks here depending on the function's return value
            # or if exceptions are handled internally by the decorated function.
            # For now, assume success if no exception was raised.
            try:
                user_subscription.credits_remaining -= cost
                db.session.commit()
                logging.info(f"Successfully deducted {cost} credits for user {user_id}. Remaining credits: {user_subscription.credits_remaining}")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Failed to deduct credits for user {user_id}: {str(e)}")
                # Decide how to handle deduction failure - currently logs but doesn't stop response

            return response
        return decorated_function
    return decorator

def filter_lead_data_by_plan():
    """
    Decorator to filter and mask lead data based on the user's subscription plan.
    Assumes the decorated function returns a list of Lead model instances.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure user and subscription are available
            if not current_user.is_authenticated:
                 return jsonify({'status': 'error', 'message': 'Authentication required.'}), 401

            user_id = current_user.get_id()
            user_subscription = UserSubscription.query.filter_by(user_id=user_id).first()

            if not user_subscription:
                logging.error(f"filter_lead_data_by_plan decorator used for user {user_id} without a valid user subscription.")
                return jsonify({'status': 'error', 'message': 'User subscription not found.'}), 500 # Or handle as appropriate

            # Execute the original function to get leads (expected to return a list of Lead model instances)
            leads = f(*args, **kwargs)

            user_plan_name = user_subscription.plan_name

            processed_leads = []
            for lead in leads:
                # Define fields for different plans
                if user_plan_name == 'Free':
                    # Fields for Free plan (limited and masked contact info)
                    allowed_fields = [
                        'lead_id', 'company', 'industry', 'street', 'city', 'state',
                        'bbb_rating', 'phone', 'website', 'owner_email'
                    ]

                    # Mask sensitive data
                    masked_phone = '********' + (lead.phone[-4:] if lead.phone and len(lead.phone) > 4 else lead.phone or '')
                    # Mask email: show first char, then ***, then @domain if available
                    masked_email_parts = (lead.owner_email or '').split('@')
                    if len(masked_email_parts) > 1:
                        masked_email = f"{masked_email_parts[0][0] if masked_email_parts[0] else ''}***@{masked_email_parts[1]}"
                    else:
                        masked_email = f"{masked_email_parts[0][0] if masked_email_parts[0] else ''}***@"

                    processed_lead = {}
                    for field in allowed_fields:
                        if field == 'phone':
                            processed_lead[field] = masked_phone
                        elif field == 'owner_email':
                            processed_lead[field] = masked_email
                        elif hasattr(lead, field):
                             # Use getattr to get the value from the Lead object
                             processed_lead[field] = getattr(lead, field)
                        # Fields not present on the model will be skipped

                    processed_leads.append(processed_lead)

                else:
                    # Fields for other plans (use to_dict for full representation)
                    # If you need a specific set of columns for paid plans, define another list here
                    processed_leads.append(lead.to_dict()) # Assuming Lead model has a to_dict method

            return jsonify(processed_leads), 200
        return decorated_function
    return decorator