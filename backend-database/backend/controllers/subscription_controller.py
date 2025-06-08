import stripe
from flask import request, jsonify, current_app, url_for
from models.user_model import User, db
from sqlalchemy import func
from dateutil.relativedelta import relativedelta
from datetime import datetime


class SubscriptionController:

    @staticmethod
    def create_checkout_session(user):
        try:
            current_app.logger.info(f"[Subscription] Incoming create_checkout_session request. User: {getattr(user, 'user_id', None)}, is_authenticated: {getattr(user, 'is_authenticated', None)}")
            current_app.logger.info(f"[Subscription] Request data: {request.data}")
            current_app.logger.info(f"[Subscription] Request json: {request.json}")
            plan_type = request.json.get('plan_type')
            current_app.logger.info(f"[Subscription] Extracted plan_type: {plan_type}")
            price_id = current_app.config['STRIPE_PRICES'].get(plan_type)
            if not price_id:
                current_app.logger.error(f"[Subscription] Invalid plan_type provided: {plan_type}. Check STRIPE_PRICES config.")
                return {'error': f'Invalid plan type provided: {plan_type}. Check STRIPE_PRICES config.'}, 400

            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            success_url = url_for('auth.payment_success', _external=True)
            cancel_url = url_for('auth.payment_cancel', _external=True)

            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(user.user_id),
                payment_method_types=['card']
            )
            current_app.logger.info(f"[Subscription] Stripe session created successfully for user {user.user_id}, plan {plan_type}")
            current_app.logger.info(f"commented code for the db updates starts ")
            current_app.logger.info(f"===================== NO WEBHOOK FUNCTION IS WORKING, DOING CHANGES IN DB WITHOUT PAYMNET =====================")
            # --- DB update logic moved to webhook. The following is intentionally commented out ---
            # Always update or create UserSubscription for the selected plan
            user.tier = plan_type
            from models.user_subscription_model import UserSubscription
            from models.plan_model import Plan
            now = datetime.utcnow()
            plan = Plan.query.filter(func.lower(Plan.plan_name) == plan_type.lower()).first()
            if plan:
                expiration = None
                if plan.credit_reset_frequency == 'monthly':
                    expiration = now + relativedelta(months=1)
                elif plan.credit_reset_frequency == 'annual':
                    expiration = now + relativedelta(years=1)
                # Upsert logic: update if exists, else create
                user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
                if user_sub:
                    user_sub.plan_id = plan.plan_id
                    user_sub.plan_name = plan.plan_name
                    user_sub.credits_remaining = plan.initial_credits if plan.initial_credits is not None else 0
                    user_sub.payment_frequency = plan.credit_reset_frequency if plan.credit_reset_frequency else 'monthly'
                    user_sub.tier_start_timestamp = now
                    user_sub.plan_expiration_timestamp = expiration
                    user_sub.username = user.username
                    current_app.logger.info(f"[Subscription] UserSubscription for user {user.user_id} updated to plan {plan_type}.")
                else:
                    new_sub = UserSubscription(
                        user_id=user.user_id,
                        plan_id=plan.plan_id,
                        plan_name=plan.plan_name,
                        credits_remaining=plan.initial_credits if plan.initial_credits is not None else 0,
                        payment_frequency=plan.credit_reset_frequency if plan.credit_reset_frequency else 'monthly',
                        tier_start_timestamp=now,
                        plan_expiration_timestamp=expiration,
                        username=user.username
                    )
                    db.session.add(new_sub)
                    current_app.logger.info(f"[Subscription] Created new UserSubscription for user {user.user_id} with plan {plan_type}.")
            else:
                current_app.logger.error(f"[Subscription] Plan {plan_type} not found when updating/creating UserSubscription for user {user.user_id}.")
            db.session.commit()
            current_app.logger.info(f"[Subscription] User {user.user_id} tier updated to {user.tier} In db.")
            # --- End of commented block ---
            return {'sessionId': checkout_session.id}, 200
        except Exception as e:
            import traceback
            current_app.logger.error(f"[Subscription] Error creating checkout session: {e}\n{traceback.format_exc()}")
            return {'error': 'Error creating checkout session. Please try again later.'}, 500

    @staticmethod
    def handle_stripe_webhook(payload, sig_header):
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            current_app.logger.info(f"Webhook received: {event['type']}")

            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                user_id = session.get('client_reference_id')
                plan_type = None
                # Try to get plan_type from session metadata or line items
                # If you set plan_type in metadata during checkout, use that
                if 'metadata' in session and session['metadata'].get('plan_type'):
                    plan_type = session['metadata']['plan_type']
                else:
                    # Fallback: get price_id from line items and map to plan_type
                    line_items = stripe.checkout.Session.list_line_items(session['id'])
                    if line_items and line_items.data:
                        price_id = line_items.data[0].price.id
                        # Map price_id to plan_type using config
                        for k, v in current_app.config['STRIPE_PRICES'].items():
                            if v == price_id:
                                plan_type = k
                                break
                current_app.logger.info(f"Payment successful for user {user_id}, plan_type: {plan_type}")
                # Only proceed if we have both user_id and plan_type
                if user_id and plan_type:
                    from models.user_model import User
                    user = User.query.get(int(user_id))
                    if user:
                        user.tier = plan_type
                        # Upsert UserSubscription as in create_checkout_session
                        from models.user_subscription_model import UserSubscription
                        from models.plan_model import Plan
                        from sqlalchemy import func
                        from dateutil.relativedelta import relativedelta
                        from datetime import datetime
                        now = datetime.utcnow()
                        plan = Plan.query.filter(func.lower(Plan.plan_name) == plan_type.lower()).first()
                        if plan:
                            expiration = None
                            if plan.credit_reset_frequency == 'monthly':
                                expiration = now + relativedelta(months=1)
                            elif plan.credit_reset_frequency == 'annual':
                                expiration = now + relativedelta(years=1)
                            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
                            if user_sub:
                                user_sub.plan_id = plan.plan_id
                                user_sub.plan_name = plan.plan_name
                                user_sub.credits_remaining = plan.initial_credits if plan.initial_credits is not None else 0
                                user_sub.payment_frequency = plan.credit_reset_frequency if plan.credit_reset_frequency else 'monthly'
                                user_sub.tier_start_timestamp = now
                                user_sub.plan_expiration_timestamp = expiration
                                user_sub.username = user.username
                                current_app.logger.info(f"[Webhook] UserSubscription for user {user.user_id} updated to plan {plan_type}.")
                            else:
                                new_sub = UserSubscription(
                                    user_id=user.user_id,
                                    plan_id=plan.plan_id,
                                    plan_name=plan.plan_name,
                                    credits_remaining=plan.initial_credits if plan.initial_credits is not None else 0,
                                    payment_frequency=plan.credit_reset_frequency if plan.credit_reset_frequency else 'monthly',
                                    tier_start_timestamp=now,
                                    plan_expiration_timestamp=expiration,
                                    username=user.username
                                )
                                db.session.add(new_sub)
                                current_app.logger.info(f"[Webhook] Created new UserSubscription for user {user.user_id} with plan {plan_type}.")
                            db.session.commit()
                            current_app.logger.info(f"[Webhook] User {user.user_id} tier updated to {user.tier} In db.")
                        else:
                            current_app.logger.error(f"[Webhook] Plan {plan_type} not found when updating/creating UserSubscription for user {user.user_id}.")
                    else:
                        current_app.logger.warning(f"[Webhook] User {user_id} not found for successful payment.")
                else:
                    current_app.logger.warning(f"[Webhook] Missing user_id or plan_type in session for successful payment.")

            elif event['type'] == 'checkout.session.async_payment_failed':
                session = event['data']['object']
                user_id = session.get('client_reference_id')
                if user_id:
                    from models.user_model import User
                    user = User.query.get(int(user_id))
                    if user:
                        user.tier = 'free'
                        db.session.commit()
                        current_app.logger.info(f"Reset user {user_id} to free tier due to payment failure")

            # Add other Stripe event types as needed (e.g., invoice.payment_failed for recurring payments)

        except ValueError as e:
            current_app.logger.error(f"Webhook error: Invalid payload - {str(e)}")
            return {'error': 'Invalid payload'}, 400
        except stripe.error.SignatureVerificationError as e:
            current_app.logger.error(f"Webhook error: Invalid signature - {str(e)}")
            return {'error': 'Invalid signature'}, 400
        except Exception as e:
            current_app.logger.error(f"Webhook error: {str(e)}")
            return {'error': str(e)}, 400

        return {'status': 'success'}, 200

    @staticmethod
    def _handle_successful_payment(session):
        try:
            user_id = session.get('client_reference_id')
            if not user_id:
                current_app.logger.warning("No user_id found in session")
                return

            user = User.query.get(int(user_id))
            if not user:
                current_app.logger.warning(f"User {user_id} not found")
                return

            # Get line items and extract price ID
            line_items = stripe.checkout.Session.list_line_items(session.id)
            if not line_items or not line_items.data:
                current_app.logger.warning("No line items found for session")
                return

            price_id = line_items.data[0].price.id

            # Map price_id to subscription tier, including the new Platinum tier
            price_to_tier = {
                current_app.config['STRIPE_PRICES']['gold']: 'gold',
                current_app.config['STRIPE_PRICES']['silver']: 'silver',
                current_app.config['STRIPE_PRICES']['bronze']: 'bronze',
                current_app.config['STRIPE_PRICES']['platinum']: 'platinum' # Added Platinum tier
            }

            new_tier = price_to_tier.get(price_id)
            print(f" this is the new ties from handle succesfull {new_tier}")
            if not new_tier:
                current_app.logger.warning(f"Invalid price_id: {price_id}")
                return

            # Update the user's tier instead of subscription_tier
            user.tier = new_tier
            db.session.commit()
            print(f"Successfully updated user {user_id} to tier {new_tier}")

        except Exception as e:
            print(f" changes is commited ")
            current_app.logger.error(f"Error handling successful payment for session {session.id}: {str(e)}")
            db.session.rollback()


    @staticmethod
    def get_current_user_subscription_info(user):
        """
        Returns a dictionary with the current user's subscription, plan, and user info (selected fields only).
        """
        from models.user_subscription_model import UserSubscription
        from models.plan_model import Plan
        from models.user_model import User

        user_id = user.get_id()
        user_obj = User.query.filter_by(user_id=user_id).first()
        if not user_obj:
            return {'error': 'User not found'}, 404

        user_sub = UserSubscription.query.filter_by(user_id=user_id).first()
        if not user_sub:
            return {'error': 'User subscription not found'}, 404

        plan = None
        if user_sub.plan_id:
            plan = Plan.query.filter_by(plan_id=user_sub.plan_id).first()

        # Only include selected fields
        user_data = {
            'user_id': str(user_obj.user_id),
            'email': user_obj.email
        }
        subscription_data = {
            'credits_remaining': user_sub.credits_remaining,
            'payment_frequency': user_sub.payment_frequency,
            'plan_name': user_sub.plan_name,
            'tier_start_timestamp': user_sub.tier_start_timestamp.isoformat() if user_sub.tier_start_timestamp else None,
            'plan_expiration_timestamp': user_sub.plan_expiration_timestamp.isoformat() if user_sub.plan_expiration_timestamp else None,
            'username': user_sub.username
        }
        plan_data = None
        if plan:
            plan_data = {
                'cost_per_lead': float(plan.cost_per_lead) if plan.cost_per_lead is not None else None,
                'features_json': plan.features_json,
                'credit_reset_frequency': plan.credit_reset_frequency,
                'initial_credits': plan.initial_credits
            }

        return {
            'user': user_data,
            'subscription': subscription_data,
            'plan': plan_data
        }, 200

    @staticmethod
    def payment_success_handler(user):
        """
        Handle payment success logic and return a JSON response with a redirect URL.
        """
        # You can add any additional logic here if needed (e.g., logging, updating user, etc.)
        return {
            'message': 'Your subscription has been activated successfully!',
            'redirect_url': 'https://app.saasquatchleads.com/'
        }, 200

    @staticmethod
    def payment_cancel_handler(user):
        """
        Handle payment cancel logic and return a JSON response with a redirect URL.
        """
        # You can add any additional logic here if needed (e.g., logging, updating user, etc.)
        return {
            'message': 'Payment cancelled. You can choose a plan when you are ready.',
            'redirect_url': 'https://app.saasquatchleads.com/subscription'
        }, 200