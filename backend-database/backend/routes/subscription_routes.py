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
    user_sub = UserSubscription.query.filter_by(user_id=str(current_user.user_id)).first()
    if not user_sub:
        return jsonify({"credits_remaining": 0})
    return jsonify({"credits_remaining": user_sub.credits_remaining})

@subscription_bp.route('/webhook', methods=['POST'])
def subscription_webhook():
    """Handle Stripe webhook events for subscriptions"""
    current_app.logger.info(f"[Webhook] webhook recived.+++")
    payload = request.get_data()
    sig_header = request.headers.get('stripe-signature')
    # Log the webhook receipt
    current_app.logger.info("[Webhook] Stripe webhook received. Processing event in handler.")
    response, status_code = SubscriptionController.handle_stripe_webhook(payload, sig_header)
    return jsonify(response), status_code