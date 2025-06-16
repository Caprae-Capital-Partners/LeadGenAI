from flask import Blueprint, request, jsonify, current_app, redirect, render_template, flash, url_for
from flask_login import login_required, current_user
import stripe
from models.user_model import User

customer_portal_bp = Blueprint('customer_portal', __name__)

@customer_portal_bp.route('/api/create-customer-portal-session', methods=['POST'])
@login_required
def create_customer_portal_session():
    """Create a Stripe customer portal session for the authenticated user"""
    try:
        current_app.logger.info(f"[Customer Portal] Creating portal session for user {current_user.user_id}")

        # Set Stripe API key
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Get return URL from request or use default
        data = request.json or {}
        return_url = data.get('return_url', 'https://app.saasquatchleads.com/subscription')

        # Find or create Stripe customer
        customer = None

        # Try to find existing customer by email
        try:
            customers = stripe.Customer.list(email=current_user.email, limit=5)
            if customers.data:
                customer = customers.data[0]
                current_app.logger.info(f"[Customer Portal] Found existing Stripe customer {customer.id}")
        except Exception as e:
            current_app.logger.warning(f"[Customer Portal] Error searching for customer: {str(e)}")

        # Create customer if not found
        if not customer:
            try:
                customer = stripe.Customer.create(
                    email=current_user.email,
                    name=current_user.username,
                    metadata={
                        'user_id': str(current_user.user_id)
                    }
                )
                current_app.logger.info(f"[Customer Portal] Created new Stripe customer {customer.id}")
            except Exception as e:
                current_app.logger.error(f"[Customer Portal] Error creating customer: {str(e)}")
                return jsonify({'error': 'Failed to create customer portal session'}), 500

        # Create portal session
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer.id,
                return_url=return_url,
            )

            current_app.logger.info(f"[Customer Portal] Created portal session {portal_session.id}")

            return jsonify({
                'url': portal_session.url,
                'session_id': portal_session.id
            }), 200

        except Exception as e:
            current_app.logger.error(f"[Customer Portal] Error creating portal session: {str(e)}")
            return jsonify({'error': 'Failed to create customer portal session'}), 500

    except Exception as e:
        current_app.logger.error(f"[Customer Portal] Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def redirect_to_stripe_portal():
    """Helper function to redirect to Stripe customer portal."""
    try:
        # Create portal session
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Find or create customer
        customer = None
        try:
            customers = stripe.Customer.list(email=current_user.email, limit=5)
            if customers.data:
                customer = customers.data[0]
        except Exception:
            pass

        if not customer:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.username,
                metadata={'user_id': str(current_user.user_id)}
            )

        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url='https://app.saasquatchleads.com/subscription',
        )

        # Redirect to portal
        return redirect(portal_session.url)

    except Exception as e:
        current_app.logger.error(f"[Customer Portal] Error in form handler: {str(e)}")
        flash('Error accessing customer portal.', 'error')
        return redirect(url_for('main.index'))


@customer_portal_bp.route('/customer_portal')
@login_required
def customer_portal():
    """Redirect directly to Stripe customer portal."""
    try:
        # Create Stripe customer portal session and redirect
        return redirect_to_stripe_portal()
    except Exception as e:
        flash(f'Error accessing customer portal: {str(e)}', 'error')
        return redirect(url_for('main.index'))