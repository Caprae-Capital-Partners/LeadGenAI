# routes/credit_routes.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from utils.decorators import credit_required
from controllers.subscription_controller import SubscriptionController
# Import your CreditController if you want to use it for more logic
# from controllers.credit_controller import CreditController

credit_bp = Blueprint('credit', __name__)

@credit_bp.route('/api/user/deduct_credit/<string:lead_id>', methods=['POST'])
@login_required
@credit_required(cost=1)
def deduct_credit_for_lead(lead_id):
    """
    Deduct 1 credit from the current user's account for a specific lead.
    Endpoint: POST /api/user/deduct_credit/<lead_id>
    Requires: User to be logged in and have at least 1 credit.
    Returns: JSON with status, message, and lead_id.
    """
    # You can add additional logic here if you want to use lead_id for something
    response = {
        "status": "success",
        "message": f"1 credit deducted successfully for lead {lead_id}.",
        "lead_id": lead_id
    }
    return jsonify(response), 200

@credit_bp.route('/api/user/subscription_info', methods=['GET'])
@login_required
def get_user_subscription_info():
    """
    Get the current user's subscription, plan, and user info.
    Endpoint: GET /api/user/subscription_info
    Returns: JSON with user, subscription, and plan details.
    """
    data, status = SubscriptionController.get_current_user_subscription_info(current_user)
    return jsonify(data), status