import stripe
from flask import request, jsonify, current_app, url_for
from models.user_model import User, db
from models.user_subscription_model import UserSubscription
from sqlalchemy import func
from dateutil.relativedelta import relativedelta
from datetime import datetime
from utils.email_utils import send_outreach_confirmation_email


class SubscriptionController:

    @staticmethod
    def create_checkout_session(user):
        try:
            current_app.logger.info(f"[Subscription] Incoming create_checkout_session request. User: {getattr(user, 'user_id', None)}, is_authenticated: {getattr(user, 'is_authenticated', None)}")

            # Validate request data
            if not request.json:
                current_app.logger.error("[Subscription] No JSON data provided")
                return {'error': 'No data provided'}, 400

            plan_type = request.json.get('plan_type')
            current_app.logger.info(f"[Subscription] Extracted plan_type: {plan_type}")

            if not plan_type:
                current_app.logger.error("[Subscription] No plan_type provided")
                return {'error': 'plan_type is required'}, 400

            price_id = current_app.config['STRIPE_PRICES'].get(plan_type)
            if not price_id:
                current_app.logger.error(f"[Subscription] Invalid plan_type provided: {plan_type}. Available plans: {list(current_app.config['STRIPE_PRICES'].keys())}")
                return {'error': f'Invalid plan type provided: {plan_type}. Available plans: {list(current_app.config["STRIPE_PRICES"].keys())}'}, 400

            # Validate Stripe configuration
            if not current_app.config.get('STRIPE_SECRET_KEY'):
                current_app.logger.error("[Subscription] STRIPE_SECRET_KEY not configured")
                return {'error': 'Payment system not configured'}, 500

            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            success_url = "https://app.saasquatchleads.com"
            cancel_url = "https://app.saasquatchleads.com/subscription"

            # Determine the Stripe mode based on plan_type
            if plan_type == 'call_outreach':
                stripe_mode = 'payment'  # For one-time payments
            else:
                stripe_mode = 'subscription' # For recurring subscriptions

            # Initialize parameters for checkout session
            checkout_session_params = {
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': stripe_mode,
                'success_url': success_url,
                'cancel_url': cancel_url,
                'client_reference_id': str(user.user_id),
                'payment_method_types': [
                    'card',
                    'link',
                ],
                'metadata': {
                    'plan_type': plan_type,
                    'user_id': str(user.user_id)
                }
            }

            # Add subscription_data only if in subscription mode
            if stripe_mode == 'subscription':
                checkout_session_params['subscription_data'] = {
                    'metadata': {
                        'plan_type': plan_type,
                        'user_id': str(user.user_id)
                    }
                }

            checkout_session = stripe.checkout.Session.create(
                **checkout_session_params
            )
            current_app.logger.info(f"[Subscription] Stripe session created successfully for user {user.user_id}, plan {plan_type}")
            current_app.logger.info(f"commented code for the db updates starts ")
            current_app.logger.info(f"===================== WEBHOOK FUNCTION IS WORKING, WAITING FOR WEBHOOK TO UPDATE DB =====================")
            # --- DB update logic moved to webhook. The following is intentionally commented out ---
            # Always update or create UserSubscription for the selected plan
            # user.tier = plan_type
            # from models.user_subscription_model import UserSubscription
            # from models.plan_model import Plan
            # now = datetime.utcnow()
            # plan = Plan.query.filter(func.lower(Plan.plan_name) == plan_type.lower()).first()
            # if plan:
            #     expiration = None
            #     if plan.credit_reset_frequency == 'monthly':
            #         expiration = now + relativedelta(months=1)
            #     elif plan.credit_reset_frequency == 'annual':
            #         expiration = now + relativedelta(years=1)
            #     # Upsert logic: update if exists, else create
            #     user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
            #     if user_sub:
            #         user_sub.plan_id = plan.plan_id
            #         user_sub.plan_name = plan.plan_name
            #         user_sub.credits_remaining = plan.initial_credits if plan.initial_credits is not None else 0
            #         user_sub.payment_frequency = plan.credit_reset_frequency if plan.credit_reset_frequency else 'monthly'
            #         user_sub.tier_start_timestamp = now
            #         user_sub.plan_expiration_timestamp = expiration
            #         user_sub.username = user.username
            #         current_app.logger.info(f"[Subscription] UserSubscription for user {user.user_id} updated to plan {plan_type}.")
            #     else:
            #         new_sub = UserSubscription(
            #             user_id=user.user_id,
            #             plan_id=plan.plan_id,
            #             plan_name=plan.plan_name,
            #             credits_remaining=plan.initial_credits if plan.initial_credits is not None else 0,
            #             payment_frequency=plan.credit_reset_frequency if plan.credit_reset_frequency else 'monthly',
            #             tier_start_timestamp=now,
            #             plan_expiration_timestamp=expiration,
            #             username=user.username
            #         )
            #         db.session.add(new_sub)
            #         current_app.logger.info(f"[Subscription] Created new UserSubscription for user {user.user_id} with plan {plan_type}.")
            # else:
            #     current_app.logger.error(f"[Subscription] Plan {plan_type} not found when updating/creating UserSubscription for user {user.user_id}.")
            # db.session.commit()
            # current_app.logger.info(f"[Subscription] User {user.user_id} tier updated to {user.tier} In db.")
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

                current_app.logger.info(f"[Webhook] Processing checkout.session.completed for user_id: {user_id}")

                # Try to get plan_type from session metadata first (more reliable)
                if 'metadata' in session and session['metadata'].get('plan_type'):
                    plan_type = session['metadata']['plan_type']
                    current_app.logger.info(f"[Webhook] Got plan_type from metadata: {plan_type}")

                # Fallback: get from subscription metadata if session metadata doesn't exist
                if not plan_type and 'subscription' in session:
                    try:
                        subscription = stripe.Subscription.retrieve(session['subscription'])
                        if subscription.metadata and subscription.metadata.get('plan_type'):
                            plan_type = subscription.metadata['plan_type']
                            current_app.logger.info(f"[Webhook] Got plan_type from subscription metadata: {plan_type}")
                    except Exception as e:
                        current_app.logger.warning(f"[Webhook] Could not retrieve subscription metadata: {str(e)}")

                # Final fallback: get price_id from line items and map to plan_type
                if not plan_type:
                    try:
                        line_items = stripe.checkout.Session.list_line_items(session['id'])
                        if line_items and line_items.data:
                            price_id = line_items.data[0].price.id
                            # Map price_id to plan_type using config
                            for k, v in current_app.config['STRIPE_PRICES'].items():
                                if v == price_id:
                                    plan_type = k
                                    break
                            current_app.logger.info(f"[Webhook] Got plan_type from line items: {plan_type}")
                    except Exception as e:
                        current_app.logger.error(f"[Webhook] Error retrieving line items: {str(e)}")

                # Log payment method used
                if session.get('payment_intent'):
                    # One-time payment
                    payment_intent = stripe.PaymentIntent.retrieve(session['payment_intent'])
                    payment_method_type = payment_intent.payment_method_types[0] if payment_intent.payment_method_types else 'unknown'
                    current_app.logger.info(f"[Webhook] Payment completed using: {payment_method_type}")
                elif session.get('subscription'):
                    # Subscription: get the latest invoice
                    subscription = stripe.Subscription.retrieve(session['subscription'])
                    latest_invoice_id = subscription.get('latest_invoice')
                    if latest_invoice_id:
                        invoice = stripe.Invoice.retrieve(latest_invoice_id)
                        payment_intent_id = invoice.get('payment_intent')
                        if payment_intent_id:
                            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                            payment_method_type = payment_intent.payment_method_types[0] if payment_intent.payment_method_types else 'unknown'
                            current_app.logger.info(f"[Webhook] Subscription payment completed using: {payment_method_type}")
                        else:
                            current_app.logger.info("[Webhook] No payment_intent found on invoice; cannot log payment method type.")
                    else:
                        current_app.logger.info("[Webhook] No latest_invoice found on subscription; cannot log payment method type.")
                else:
                    current_app.logger.info("[Webhook] No payment_intent or subscription found in session; skipping payment method logging.")

                # Check if this is an outreach service payment
                if session.get('metadata') and session['metadata'].get('service_type') == 'phone_call_outreach':
                    current_app.logger.info(f"-------------[Webhook] Processing outreach payment for user_id: {user_id} DOING NOTHING")
                    # from controllers.outreach_controller import OutreachController
                    # if OutreachController.handle_outreach_payment_success(session):
                    #     current_app.logger.info(f"[Webhook] Successfully processed outreach payment for user {user_id}")
                    # else:
                    #     current_app.logger.error(f"[Webhook] Failed to process outreach payment for user {user_id}")
                # Check if this is a pause subscription payment
                elif session.get('metadata') and session['metadata'].get('is_pause_subscription') == 'true':
                    current_app.logger.info(f"[Webhook] Processing pause subscription payment for user_id: {user_id}")
                    if SubscriptionController.handle_pause_subscription_success(session['metadata'], user_id):
                        current_app.logger.info(f"[Webhook] Successfully processed pause subscription for user {user_id}")
                    else:
                        current_app.logger.error(f"[Webhook] Failed to process pause subscription for user {user_id}")
                # Only proceed if we have both user_id and plan_type for subscription payments
                elif user_id and plan_type:
                    # Handle 'call_outreach' plan specifically
                    if plan_type == 'call_outreach':
                        from models.user_subscription_model import UserSubscription
                        user_sub = UserSubscription.query.filter_by(user_id=user_id).first()
                        if user_sub:
                            user_sub.is_call_outreach_cust = True
                            db.session.commit()
                            current_app.logger.info(f"[Webhook] User {user_id} subscribed to 'Pro Call Outreach'. is_call_outreach_cust set to True.")
                            # Send confirmation email
                            if user:
                                send_outreach_confirmation_email(user.email, user.username)
                                current_app.logger.info(f"[Webhook] Sent outreach confirmation email to user {user.username}.")
                            else:
                                current_app.logger.warning(f"[Webhook] User object not available for outreach confirmation email,{user.username} despite user_id being present.")
                        else:
                            current_app.logger.warning(f"[Webhook] UserSubscription not found for user {user_id} when processing 'call_outreach' payment.")
                        return jsonify({'status': 'success'}), 200 # Exit after handling call_outreach

                    from models.user_model import User
                    user = User.query.get(user_id)
                    if user:
                        # Check if this is a pause subscription
                        if plan_type.startswith('pause_'):
                            # Handle pause subscription
                            if SubscriptionController.handle_pause_subscription_success(session['metadata'], user_id):
                                current_app.logger.info(f"[Webhook] Successfully processed pause subscription for user {user_id}")
                            else:
                                current_app.logger.error(f"[Webhook] Failed to process pause subscription for user {user_id}")
                        else:
                            # Handle regular subscription
                            user.tier = plan_type
                        # Upsert UserSubscription as in create_checkout_session
                        from models.user_subscription_model import UserSubscription
                        from models.plan_model import Plan
                        from sqlalchemy import func
                        from dateutil.relativedelta import relativedelta
                        from datetime import datetime
                        now = datetime.utcnow()
                        # Map plan_type to correct plan name in database
                        plan_name_mapping = {
                            'bronze_annual': 'Bronze_Annual',
                            'silver_annual': 'Silver_Annual',
                            'gold_annual': 'Gold_Annual',
                            'platinum_annual': 'Platinum_Annual',
                            'bronze': 'Bronze',
                            'silver': 'Silver',
                            'gold': 'Gold',
                            'platinum': 'Platinum',
                            'student_monthly': 'Student Monthly',
                            'student_semester': 'Student Semester',
                            'student_annual': 'Student Annual',
                            'call_outreach': 'Pro Call Outreach',
                        }
                        mapped_plan_name = plan_name_mapping.get(plan_type, plan_type)
                        plan = Plan.query.filter(func.lower(Plan.plan_name) == mapped_plan_name.lower()).first()
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
                current_app.logger.warning(f"[Webhook] Async payment failed for user {user_id}")
                if user_id:
                    from models.user_model import User
                    user = User.query.get(user_id)
                    if user:
                        user.tier = 'free'
                        db.session.commit()
                        current_app.logger.info(f"Reset user {user_id} to free tier due to payment failure")

            elif event['type'] == 'invoice.payment_failed':
                # Handle recurring payment failures
                invoice = event['data']['object']
                subscription_id = invoice.get('subscription')
                customer_id = invoice.get('customer')
                current_app.logger.warning(f"[Webhook] Invoice payment failed for subscription {subscription_id}")

                if customer_id:
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                        user = User.query.filter_by(email=customer.email).first()
                        if user:
                            current_app.logger.info(f"[Webhook] Recurring payment failed for user {user.user_id}")
                            # You can implement retry logic or downgrade logic here
                            # For now, we'll just log it
                    except Exception as e:
                        current_app.logger.error(f"Error processing payment failure: {str(e)}")

            elif event['type'] == 'payment_method.attached':
                # Log when customers add new payment methods
                payment_method = event['data']['object']
                customer_id = payment_method.get('customer')
                payment_method_type = payment_method.get('type')
                current_app.logger.info(f"[Webhook] New payment method ({payment_method_type}) attached to customer {customer_id}")

            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                customer_id = subscription.get('customer')
                if customer_id:
                    try:
                        from models.user_subscription_model import UserSubscription
                        from models.user_model import User
                        customer = stripe.Customer.retrieve(customer_id)
                        user = User.query.filter_by(email=customer.email).first()
                        if user:
                            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()

                            # Check if this was a scheduled cancellation
                            is_scheduled_cancel = (user_sub and
                                                 user_sub.payment_frequency and
                                                 '_scheduled_cancel' in user_sub.payment_frequency)

                            if is_scheduled_cancel:
                                current_app.logger.info(f"Processing scheduled cancellation for user {user.user_id} - subscription period has ended")
                            else:
                                current_app.logger.info(f"Processing immediate cancellation for user {user.user_id}")

                            # Now actually cancel and move to free tier
                            SubscriptionController._handle_local_cancellation(user, user_sub)
                            current_app.logger.info(f"Processed subscription cancellation for user {user.user_id}")
                    except Exception as e:
                        current_app.logger.error(f"Error processing subscription.deleted webhook: {str(e)}")

            elif event['type'] == 'customer.subscription.updated':
                subscription = event['data']['object']
                customer_id = subscription.get('customer')

                if customer_id:
                    try:
                        from models.user_subscription_model import UserSubscription
                        from models.user_model import User
                        customer = stripe.Customer.retrieve(customer_id)
                        user = User.query.filter_by(email=customer.email).first()

                        if user:
                            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()

                            # Handle cancel_at_period_end updates
                            if subscription.get('cancel_at_period_end'):
                                current_app.logger.info(f"Webhook: Subscription {subscription['id']} scheduled for cancellation at period end for user {user.user_id}")
                                current_app.logger.info(f"Webhook: cancel_at_period_end timestamp: {subscription.get('cancel_at')}")

                                # Mark the subscription as scheduled for cancellation
                                if user_sub and user_sub.payment_frequency and '_scheduled_cancel' not in user_sub.payment_frequency:
                                    user_sub.payment_frequency = f"{user_sub.payment_frequency}_scheduled_cancel"
                                    db.session.commit()
                                    current_app.logger.info(f"Webhook: Marked subscription as scheduled for cancellation for user {user.user_id}")

                            # Handle reactivation (when cancel_at_period_end is removed)
                            elif not subscription.get('cancel_at_period_end') and user_sub and user_sub.payment_frequency and '_scheduled_cancel' in user_sub.payment_frequency:
                                # Remove the scheduled cancellation marker
                                user_sub.payment_frequency = user_sub.payment_frequency.replace('_scheduled_cancel', '')
                                db.session.commit()
                                current_app.logger.info(f"Webhook: Removed scheduled cancellation for user {user.user_id} - subscription reactivated")

                    except Exception as e:
                        current_app.logger.error(f"Error processing subscription.updated webhook: {str(e)}")

            elif event['type'] == 'payment_intent.succeeded':
                # Handle one-time payments like outreach service
                payment_intent = event['data']['object']
                if payment_intent.get('metadata') and payment_intent['metadata'].get('service_type') == 'phone_call_outreach':
                    current_app.logger.info(f"[Outreach] Payment intent succeeded for outreach service")
                    # This will be handled by checkout.session.completed for outreach
                    pass

            # Add other Stripe event types as needed (e.g., invoice.payment_failed for recurring payments)

        except ValueError as e:
            current_app.logger.error(f"Webhook error: Invalid payload - {str(e)}")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            current_app.logger.error(f"Webhook error: Invalid signature - {str(e)}")
            return jsonify({'error': 'Invalid signature'}), 400
        except Exception as e:
            import traceback
            current_app.logger.error(f"Webhook error: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Internal server error'}), 500

        return jsonify({'status': 'success'}), 200

    @staticmethod
    def _handle_successful_payment(session):
        try:
            user_id = session.get('client_reference_id')
            if not user_id:
                current_app.logger.warning("No user_id found in session")
                return

            user = User.query.get(user_id)
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
                current_app.config['STRIPE_PRICES']['platinum']: 'platinum', # Added Platinum tier
                current_app.config['STRIPE_PRICES']['bronze_annual']: 'bronze_annual',
                current_app.config['STRIPE_PRICES']['silver_annual']: 'silver_annual',
                current_app.config['STRIPE_PRICES']['gold_annual']: 'gold_annual',
                current_app.config['STRIPE_PRICES']['platinum_annual']: 'platinum_annual',
            }

            new_tier = price_to_tier.get(price_id)
            print(f" this is the new ties from handle succesfull {new_tier}")
            if not new_tier:
                current_app.logger.warning(f"Invalid price_id: {price_id}")
                return

            # Update the user's tier instead of subscription_tier
            user.tier = new_tier
            db.session.commit()
            current_app.logger.info(f"Successfully updated user {user_id} to tier {new_tier}")

        except Exception as e:
            current_app.logger.info(f" changes not commited error ")
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

        # Check if subscription is scheduled for cancellation
        is_scheduled_for_cancellation = (user_sub.payment_frequency and
                                       '_scheduled_cancel' in user_sub.payment_frequency)

        # Clean payment frequency for display
        display_payment_frequency = user_sub.payment_frequency
        if is_scheduled_for_cancellation:
            display_payment_frequency = user_sub.payment_frequency.replace('_scheduled_cancel', '')

        # Only include selected fields
        user_data = {
            'user_id': str(user_obj.user_id),
            'email': user_obj.email,
            'username': user_obj.username,
        }
        subscription_data = {
            'credits_remaining': user_sub.credits_remaining,
            'payment_frequency': display_payment_frequency,
            'plan_name': user_sub.plan_name,
            'tier_start_timestamp': user_sub.tier_start_timestamp.isoformat() if user_sub.tier_start_timestamp else None,
            'plan_expiration_timestamp': user_sub.plan_expiration_timestamp.isoformat() if user_sub.plan_expiration_timestamp else None,
            'is_scheduled_for_cancellation': is_scheduled_for_cancellation,
            'is_paused': getattr(user_sub, 'is_paused', False),
            'pause_end_date': user_sub.pause_end_date.isoformat() if getattr(user_sub, 'pause_end_date', None) else None,
            'original_plan_name': getattr(user_sub, 'original_plan_name', None),
            'is_cancelled': getattr(user_sub, 'is_cancelled', False),
            'is_call_outreach_cust': getattr(user_sub, 'is_call_outreach_cust', False),
            'is_pause': getattr(user_sub, 'is_pause', False),
            'pause_end_date': getattr(user_sub, 'pause_end_date', None),

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
    def is_subscription_scheduled_for_cancellation(user):
        """
        Check if user's subscription is scheduled for cancellation
        """
        from models.user_subscription_model import UserSubscription

        user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
        if not user_sub:
            return False

        return (user_sub.payment_frequency and
                '_scheduled_cancel' in user_sub.payment_frequency)

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

    @staticmethod
    def cancel_subscription(user, cancellation_type='immediate', feedback=None, comment=None):
        """
        Cancel user subscription - either immediate or at period end
        """
        try:
            current_app.logger.info(f"cancel_subscription called for user {user.user_id} with type {cancellation_type}")
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

            # Get user subscription info
            from models.user_subscription_model import UserSubscription
            from models.plan_model import Plan

            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
            if not user_sub:
                current_app.logger.info("No user_sub found, returning error response.")
                return {'error': 'No active subscription found'}, 404

            # Check if user is on free tier - if so, there's nothing to cancel
            if user.tier == 'free':
                current_app.logger.info(f"User {user.user_id} is already on free tier")
                return {'message': 'You are already on the free plan.'}, 200

            # Try multiple approaches to find Stripe customer and subscription
            customer = None
            subscription = None

            # Approach 1: Find customer by email
            try:
                customers = stripe.Customer.list(email=user.email, limit=5)
                if customers.data:
                    customer = customers.data[0]
                    current_app.logger.info(f"Found Stripe customer {customer.id} for email {user.email}")
            except Exception as e:
                current_app.logger.warning(f"Error searching customer by email: {str(e)}")

            # Approach 2: If no customer found, search all customers (less efficient but thorough)
            if not customer:
                try:
                    # Search through recent customers to find one that might match
                    all_customers = stripe.Customer.list(limit=100)
                    for cust in all_customers.data:
                        if cust.email == user.email:
                            customer = cust
                            current_app.logger.info(f"Found customer {customer.id} in broader search")
                            break
                except Exception as e:
                    current_app.logger.warning(f"Error in broader customer search: {str(e)}")

            # If we found a customer, look for active subscriptions
            if customer:
                try:
                    subscriptions = stripe.Subscription.list(
                        customer=customer.id,
                        status='active',
                        limit=10
                    )
                    if subscriptions.data:
                        subscription = subscriptions.data[0]
                        current_app.logger.info(f"Found active subscription {subscription.id}")
                    else:
                        # Check for subscriptions that are past_due or incomplete
                        all_subs = stripe.Subscription.list(
                            customer=customer.id,
                            limit=10
                        )
                        for sub in all_subs.data:
                            if sub.status in ['active', 'past_due', 'incomplete']:
                                subscription = sub
                                current_app.logger.info(f"Found subscription {subscription.id} with status {sub.status}")
                                break
                except Exception as e:
                    current_app.logger.warning(f"Error searching subscriptions: {str(e)}")

            # If we have a subscription, proceed with Stripe cancellation
            if subscription:
                try:
                    current_app.logger.info(f"Found subscription {subscription.id}. Proceeding with cancellation type: {cancellation_type}")

                    if cancellation_type == 'immediate':
                        # Cancel immediately
                        current_app.logger.info("Attempting immediate cancellation in Stripe.")
                        canceled_subscription = stripe.Subscription.cancel(
                            subscription.id,
                            prorate=True,
                            invoice_now=False
                        )
                        current_app.logger.info(f"Subscription {subscription.id} canceled immediately in Stripe.")
                        return SubscriptionController._handle_local_cancellation(user, user_sub)

                    elif cancellation_type == 'period_end':
                        # Cancel at period end - DO NOT cancel immediately, just schedule it
                        current_app.logger.info("Attempting period_end cancellation in Stripe.")
                        updated_subscription = stripe.Subscription.modify(
                            subscription.id,
                            cancel_at_period_end=True,
                            cancellation_details={
                                'comment': comment or '',
                                'feedback': feedback or 'other'
                            }
                        )

                        import datetime
                        current_app.logger.info(f"Stripe subscription updated successfully: cancel_at_period_end={updated_subscription.cancel_at_period_end}")

                        if updated_subscription.current_period_end:
                            cancel_date = datetime.datetime.fromtimestamp(updated_subscription.current_period_end)
                            current_app.logger.info(f"Scheduled cancellation at period end for subscription {subscription.id} for user {user.user_id}")

                            # Mark subscription as scheduled for cancellation in local database
                            # BUT DO NOT change user tier or plan - keep current access until period end
                            if '_scheduled_cancel' not in user_sub.payment_frequency:
                                user_sub.payment_frequency = f"{user_sub.payment_frequency}_scheduled_cancel"
                                db.session.commit()
                                current_app.logger.info(f"Updated payment_frequency to mark scheduled cancellation for user {user.user_id}.")

                            return {
                                'message': f'Subscription will be canceled at the end of your current billing period ({cancel_date.strftime("%B %d, %Y")}). You will retain access to your current plan until then.',
                                'cancel_at': updated_subscription.current_period_end,
                                'cancel_date': cancel_date.strftime("%B %d, %Y"),
                                'status': 'scheduled_for_cancellation'
                            }, 200
                        else:
                            # If no period end available, just mark as scheduled locally
                            if '_scheduled_cancel' not in user_sub.payment_frequency:
                                user_sub.payment_frequency = f"{user_sub.payment_frequency}_scheduled_cancel"
                                db.session.commit()

                            return {
                                'message': 'Subscription has been scheduled for cancellation at the end of your billing period.',
                                'status': 'scheduled_for_cancellation'
                            }, 200

                except stripe.error.StripeError as e:
                    current_app.logger.error(f"Stripe error during cancellation: {str(e)}")
                    # Fallback to local cancellation
                    return SubscriptionController._handle_local_cancellation(user, user_sub)

            # If no Stripe subscription found, handle locally
            current_app.logger.info(f"No Stripe subscription found for user {user.user_id}, handling locally")
            if cancellation_type == 'period_end':
                # For period end cancellation without Stripe subscription, just mark as scheduled
                if '_scheduled_cancel' not in user_sub.payment_frequency:
                    user_sub.payment_frequency = f"{user_sub.payment_frequency}_scheduled_cancel"
                    db.session.commit()

                return {
                    'message': 'Subscription has been scheduled for cancellation at the end of your billing period.',
                    'status': 'scheduled_for_cancellation'
                }, 200
            else:
                # For immediate cancellation, proceed with local cancellation
                return SubscriptionController._handle_local_cancellation(user, user_sub)

        except Exception as e:
            current_app.logger.error(f"Error canceling subscription for user {user.user_id}: {str(e)}")
            if cancellation_type == 'period_end':
                # For period end cancellation, don't immediately cancel on error
                if user_sub and '_scheduled_cancel' not in user_sub.payment_frequency:
                    user_sub.payment_frequency = f"{user_sub.payment_frequency}_scheduled_cancel"
                    db.session.commit()

                return {
                    'message': 'Subscription has been scheduled for cancellation at the end of your billing period.',
                    'status': 'scheduled_for_cancellation'
                }, 200
            else:
                # For immediate cancellation, proceed with local cancellation
                return SubscriptionController._handle_local_cancellation(user, user_sub)

    @staticmethod
    def _handle_local_cancellation(user, user_sub):
        """
        Handle cancellation in local database only
        """
        try:
            current_app.logger.info(f"_handle_local_cancellation called for user {user.user_id}")
            from models.plan_model import Plan
            from datetime import datetime

            # Reset user to free tier
            user.tier = 'free'

            # Update subscription to free plan
            free_plan = Plan.query.filter(func.lower(Plan.plan_name) == 'free').first()
            if free_plan:
                user_sub.plan_id = free_plan.plan_id
                user_sub.plan_name = free_plan.plan_name
                user_sub.credits_remaining = free_plan.initial_credits if free_plan.initial_credits is not None else 5
                # Clean up any scheduled cancellation marker
                user_sub.payment_frequency = 'monthly'
                user_sub.tier_start_timestamp = datetime.utcnow()
                user_sub.plan_expiration_timestamp = None
            else:
                # If no free plan exists, set basic defaults
                user_sub.plan_id = None
                user_sub.plan_name = 'Free'
                user_sub.credits_remaining = 5
                # Clean up any scheduled cancellation marker
                user_sub.payment_frequency = 'monthly'
                user_sub.tier_start_timestamp = datetime.utcnow()
                user_sub.plan_expiration_timestamp = None

            # Set cancellation fields
            user_sub.is_canceled = True
            user_sub.canceled_at = datetime.utcnow()
            current_app.logger.info(f"Set is_canceled=True and canceled_at for user {user.user_id} in user_subscriptions.")

            db.session.commit()
            current_app.logger.info(f"Successfully canceled subscription locally for user {user.user_id}")
            current_app.logger.info("Returning success response from _handle_local_cancellation.")
            return {
                'message': 'Subscription canceled successfully. You have been moved to the free plan.',
                'new_tier': 'free',
                'credits_remaining': user_sub.credits_remaining
            }, 200

        except Exception as e:
            current_app.logger.error(f"Error in local cancellation for user {user.user_id}: {str(e)}")
            current_app.logger.info("Returning error response from _handle_local_cancellation.")
            db.session.rollback()
            return {'error': 'Error processing cancellation'}, 500

    @staticmethod
    def create_pause_checkout_session(user, pause_duration):
        """
        Create a Stripe checkout session for pause subscription
        """
        try:
            current_app.logger.info(f"[Pause Subscription] Creating pause checkout for user {user.user_id}, duration: {pause_duration}")

            # Validate pause duration
            valid_durations = ['pause_one_month', 'pause_two_month', 'pause_three_month']
            if pause_duration not in valid_durations:
                return {'error': f'Invalid pause duration. Valid options: {valid_durations}'}, 400

            # Get price ID from config - make sure these are configured in your app
            price_id = current_app.config['STRIPE_PRICES'].get(pause_duration)
            if not price_id:
                current_app.logger.error(f"Price ID not found for {pause_duration} in STRIPE_PRICES config")
                return {'error': f'Price configuration not found for {pause_duration}'}, 400

            # Validate Stripe configuration
            if not current_app.config.get('STRIPE_SECRET_KEY'):
                return {'error': 'Payment system not configured'}, 500

            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            success_url = "https://app.saasquatchleads.com/payment-success"  # Changed to absolute URL
            cancel_url = "https://app.saasquatchleads.com/payment-cancel"    # Changed to absolute URL

            # Get current subscription info
            from models.user_subscription_model import UserSubscription
            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()

            # Prepare metadata
            metadata = {
                'pause_duration': pause_duration,
                'user_id': str(user.user_id),
                'is_pause_subscription': 'true'
            }

            if user_sub:
                metadata.update({
                    'original_plan_id': str(user_sub.plan_id) if user_sub.plan_id else '',
                    'original_plan_name': user_sub.plan_name if user_sub.plan_name else '',
                    'original_tier': user.tier
                })

            # Create the checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',  # Changed to 'payment' for one-time charges
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(user.user_id),
                metadata=metadata
            )

            current_app.logger.info(f"[Pause Subscription] Stripe session created successfully for user {user.user_id}")
            return {'sessionId': checkout_session.id}, 200

        except Exception as e:
            import traceback
            current_app.logger.error(f"[Pause Subscription] Error creating checkout session: {e}\n{traceback.format_exc()}")
            return {'error': 'Error creating pause checkout session. Please try again later.'}, 500
    @staticmethod
    def handle_pause_subscription_success(session_metadata, user_id):
        """
        Handle successful pause subscription payment
        """
        try:
            from models.user_subscription_model import UserSubscription
            from models.plan_model import Plan
            from datetime import datetime, timedelta
            from sqlalchemy import func

            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f"[Pause] User {user_id} not found")
                return False

            user_sub = UserSubscription.query.filter_by(user_id=user_id).first()
            if not user_sub:
                current_app.logger.error(f"[Pause] UserSubscription not found for user {user_id}")
                return False

            pause_duration = session_metadata.get('pause_duration')
            original_plan_id = session_metadata.get('original_plan_id')
            original_plan_name = session_metadata.get('original_plan_name')
            original_tier = session_metadata.get('original_tier')

            current_app.logger.info(f"[Pause] Processing pause for user {user_id}, duration: {pause_duration}")

            # Calculate pause end date
            duration_mapping = {
                'pause_one_month': 1,
                'pause_two_month': 2,
                'pause_three_month': 3
            }

            months = duration_mapping.get(pause_duration, 1)
            pause_end_date = datetime.utcnow() + timedelta(days=30 * months)

            # Store original subscription info before changing
            if not user_sub.original_plan_id:  # Only store if not already set
                user_sub.original_plan_id = user_sub.plan_id
                user_sub.original_plan_name = user_sub.plan_name

            # Set pause status
            user_sub.is_paused = True
            user_sub.pause_end_date = pause_end_date
            user_sub.credits_remaining = 0  # Set credits to 0 during pause

            # Update plan to pause plan or create pause entry
            pause_plan = Plan.query.filter(func.lower(Plan.plan_name) == 'pause').first()
            if pause_plan:
                user_sub.plan_id = pause_plan.plan_id
                user_sub.plan_name = pause_plan.plan_name
                current_app.logger.info(f"[Pause] Found existing pause plan, setting plan_id to {pause_plan.plan_id}")
            else:
                # Set plan to pause without referencing a specific plan_id
                user_sub.plan_name = 'Pause'
                current_app.logger.info(f"[Pause] No pause plan found in database, setting plan_name to 'Pause'")

            # Set user tier to pause
            user.tier = 'pause'

            db.session.commit()
            current_app.logger.info(f"[Pause] Successfully paused subscription for user {user_id} until {pause_end_date}")
            current_app.logger.info(f"[Pause] User tier set to: {user.tier}, plan_name: {user_sub.plan_name}, is_paused: {user_sub.is_paused}")
            return True

        except Exception as e:
            import traceback
            current_app.logger.error(f"[Pause] Error handling pause subscription success: {str(e)}\n{traceback.format_exc()}")
            db.session.rollback()
            return False

    @staticmethod
    def check_and_restore_paused_subscriptions():
        """
        Check for expired pause subscriptions and restore them
        This should be called periodically (e.g., daily cron job)
        """
        try:
            from models.user_subscription_model import UserSubscription
            from models.plan_model import Plan
            from datetime import datetime

            # Find all paused subscriptions that should be restored
            expired_pauses = UserSubscription.query.filter(
                UserSubscription.is_paused == True,
                UserSubscription.pause_end_date <= datetime.utcnow()
            ).all()
            for user_sub in expired_pauses:
                try:
                    user = User.query.get(user_sub.user_id)
                    if not user:
                        continue
                    # Restore original subscription
                    if user_sub.original_plan_id:
                        original_plan = Plan.query.get(user_sub.original_plan_id)
                        if original_plan:
                            user_sub.plan_id = original_plan.plan_id
                            user_sub.plan_name = original_plan.plan_name
                            user_sub.credits_remaining = original_plan.initial_credits or 0

                            # Map plan name back to tier
                            tier_mapping = {
                                'bronze': 'bronze',
                                'silver': 'silver',
                                'gold': 'gold',
                                'platinum': 'platinum',
                                'bronze_annual': 'bronze_annual',
                                'silver_annual': 'silver_annual',
                                'gold_annual': 'gold_annual',
                                'platinum_annual': 'platinum_annual'
                            }
                            user.tier = tier_mapping.get(original_plan.plan_name.lower(), 'free')
                    else:
                        # Fallback to free tier
                        free_plan = Plan.query.filter(func.lower(Plan.plan_name) == 'free').first()
                        if free_plan:
                            user_sub.plan_id = free_plan.plan_id
                            user_sub.plan_name = free_plan.plan_name
                            user_sub.credits_remaining = free_plan.initial_credits or 10
                        user.tier = 'free'

                    # Clear pause status
                    user_sub.is_paused = False
                    user_sub.pause_end_date = None
                    user_sub.original_plan_id = None
                    user_sub.original_plan_name = None

                    current_app.logger.info(f"[Pause] Restored subscription for user {user_sub.user_id}")

                except Exception as e:
                    current_app.logger.error(f"[Pause] Error restoring subscription for user {user_sub.user_id}: {str(e)}")
                    continue

            db.session.commit()
            current_app.logger.info(f"[Pause] Processed {len(expired_pauses)} expired pause subscriptions")

        except Exception as e:
            current_app.logger.error(f"[Pause] Error checking expired pause subscriptions: {str(e)}")
            db.session.rollback()