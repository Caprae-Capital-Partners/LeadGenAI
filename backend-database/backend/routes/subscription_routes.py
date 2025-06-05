from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models.user_subscription_model import UserSubscription
from models.lead_model import db
from controllers.subscription_controller import SubscriptionController
import logging

subscription_bp = Blueprint('subscription', __name__)

# @subscription_bp.route('/api/subscription/decrement_credits', methods=['POST'])
# # @login_required
# def decrement_credits():
#     """
#     Decrease credits_remaining for the currently logged in user.
#     Body: { "amount": 1 }
#     """
#     data = request.json or {}
#     amount = int(data.get('amount', 1))
#     if amount < 1:
#         return jsonify({"error": "Amount must be >= 1"}), 400

#     user_sub = UserSubscription.query.filter_by(user_id=str(current_user.user_id)).first()
#     if not user_sub:
#         return jsonify({"error": "User subscription not found"}), 404

#     if user_sub.credits_remaining < amount:
#         return jsonify({"error": "Not enough credits"}), 400

#     user_sub.credits_remaining -= amount
#     db.session.commit()
#     return jsonify({
#         "message": f"Credits decreased by {amount}",
#         "credits_remaining": user_sub.credits_remaining
#     })


@subscription_bp.route('/api/subscription/credits', methods=['GET'])
@login_required
def get_credits():
    user_sub = UserSubscription.query.filter_by(
        user_id=str(current_user.user_id)).first()
    if not user_sub:
        return jsonify({"credits_remaining": 0})
    return jsonify({"credits_remaining": user_sub.credits_remaining})


@subscription_bp.route('/api/subscription/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user's subscription"""
    data = request.json or {}
    cancel_at_period_end = data.get('cancel_at_period_end', True)
    subscription_id = data.get(
        'subscription_id')  # You'll need to store this in your DB

    response, status_code = SubscriptionController.cancel_subscription(
        current_user,
        subscription_id=subscription_id,
        cancel_at_period_end=cancel_at_period_end)
    return jsonify(response), status_code


@subscription_bp.route('/api/subscription/pause', methods=['POST'])
@login_required
def pause_subscription():
    """Pause user's subscription"""
    data = request.json or {}
    behavior = data.get('behavior', 'void')  # Default to void behavior
    resumes_at = data.get('resumes_at')  # Optional resume timestamp
    subscription_id = data.get('subscription_id')

    # Validate behavior
    valid_behaviors = ['void', 'keep_as_draft', 'mark_uncollectible']
    if behavior not in valid_behaviors:
        return jsonify({'error': f'Invalid behavior. Must be one of: {", ".join(valid_behaviors)}'}), 400

    response, status_code = SubscriptionController.pause_subscription(
        current_user,
        subscription_id=subscription_id,
        behavior=behavior,
        resumes_at=resumes_at
    )
    return jsonify(response), status_code


@subscription_bp.route('/api/subscription/resume', methods=['POST'])
@login_required
def resume_subscription():
    """Resume user's paused subscription"""
    data = request.json or {}
    subscription_id = data.get('subscription_id')

    response, status_code = SubscriptionController.resume_subscription(
        current_user,
        subscription_id=subscription_id
    )
    return jsonify(response), status_code


@subscription_bp.route('/api/subscription/update-payment-method', methods=['POST'])
@login_required
def update_payment_method():
    """Create a checkout session to update payment method"""
    response, status_code = SubscriptionController.create_update_payment_session(current_user)
    return jsonify(response), status_code


@subscription_bp.route('/api/subscription/reactivate', methods=['POST'])
@login_required
def reactivate_subscription():
    """Stop a pending cancellation"""
    try:
        data = request.json or {}
        subscription_id = data.get('subscription_id')

        if not subscription_id:
            return jsonify({'error': 'subscription_id is required'}), 400

        import stripe
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Stop the pending cancellation
        subscription = stripe.Subscription.modify(subscription_id,
                                                  cancel_at_period_end=False)

        current_app.logger.info(
            f"[Subscription] Reactivated subscription {subscription_id} for user {current_user.user_id}"
        )

        return jsonify({
            'message': 'Subscription reactivated successfully',
            'cancel_at_period_end': False
        }), 200

    except stripe.error.InvalidRequestError as e:
        current_app.logger.error(
            f"[Subscription] Invalid reactivation request: {str(e)}")
        return jsonify({'error':
                        'Invalid subscription or cannot reactivate'}), 400
    except Exception as e:
        current_app.logger.error(
            f"[Subscription] Error reactivating subscription: {str(e)}")
        return jsonify({'error': 'Error reactivating subscription'}), 500


@subscription_bp.route('/webhook', methods=['POST'])
def subscription_webhook():
    """Handle Stripe webhook events for subscriptions"""
    current_app.logger.info(
        f"[Webhook] webhook received at /subscription/webhook")
    payload = request.get_data()
    sig_header = request.headers.get('stripe-signature')
    # Log the webhook receipt
    current_app.logger.info(
        f"[Webhook] Stripe webhook received at /subscription/webhook. Headers: {dict(request.headers)}"
    )
    current_app.logger.info(f"[Webhook] Payload snippet: {payload[:200]}")
    response, status_code = SubscriptionController.handle_stripe_webhook(
        payload, sig_header)
    return jsonify(response), status_code


'''@subscription_bp.route('/webhook', methods=['POST'])
def main_webhook():
    """Handle Stripe webhook events - main webhook endpoint"""
    current_app.logger.info(f"[Webhook] webhook received at /webhook")
    payload = request.get_data()
    sig_header = request.headers.get('stripe-signature')
    response, status_code = SubscriptionController.handle_stripe_webhook(
        payload, sig_header)
    return jsonify(response), status_code'''


@subscription_bp.route('/', methods=['GET'])
@login_required
def subscription_page():
    """Display subscription management page"""
    from models.user_subscription_model import UserSubscription
    user_sub = UserSubscription.query.filter_by(
        user_id=str(current_user.user_id)).first()
    return jsonify({
        'current_tier': getattr(current_user, 'tier', 'free'),
        'subscription': {
            'credits_remaining':
            user_sub.credits_remaining if user_sub else 0,
            'plan_name':
            user_sub.plan_name if user_sub else 'free',
            'cancel_at_period_end':
            getattr(user_sub, 'cancel_at_period_end', False),
            'is_paused':
            getattr(user_sub, 'is_paused', False),
            'pause_behavior':
            getattr(user_sub, 'pause_behavior', None),
            'pause_resumes_at':
            getattr(user_sub, 'pause_resumes_at', None),
            'stripe_subscription_id':
            getattr(user_sub, 'stripe_subscription_id', None)
        }
    })


@subscription_bp.route('/manage', methods=['GET'])
@login_required
def manage_subscription():
    """Get current subscription info for management"""
    response, status_code = SubscriptionController.get_current_user_subscription_info(
        current_user)
    return jsonify(response), status_code
