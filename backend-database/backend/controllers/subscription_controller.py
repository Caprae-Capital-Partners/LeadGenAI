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
                payment_method_types=['card'],
                metadata={
                    'plan_type': plan_type,
                    'user_id': str(user.user_id)
                }
            )
            current_app.logger.info(f"[Subscription] Stripe session created successfully for user {user.user_id}, plan {plan_type}")
            # Database updates will happen in webhook after successful payment verification
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
                        # Get subscription ID from the session
                        subscription_id = session.get('subscription')
                        customer_id = session.get('customer')
                        
                        current_app.logger.info(f"[Webhook] Processing checkout completion - subscription_id: {subscription_id}, customer_id: {customer_id}")
                        
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
                                user_sub.stripe_subscription_id = subscription_id
                                user_sub.stripe_customer_id = customer_id
                                user_sub.cancel_at_period_end = False
                                current_app.logger.info(f"[Webhook] UserSubscription for user {user.user_id} updated to plan {plan_type} with subscription_id {subscription_id}.")
                            else:
                                new_sub = UserSubscription(
                                    user_id=user.user_id,
                                    plan_id=plan.plan_id,
                                    plan_name=plan.plan_name,
                                    credits_remaining=plan.initial_credits if plan.initial_credits is not None else 0,
                                    payment_frequency=plan.credit_reset_frequency if plan.credit_reset_frequency else 'monthly',
                                    tier_start_timestamp=now,
                                    plan_expiration_timestamp=expiration,
                                    username=user.username,
                                    stripe_subscription_id=subscription_id,
                                    stripe_customer_id=customer_id,
                                    cancel_at_period_end=False
                                )
                                db.session.add(new_sub)
                                current_app.logger.info(f"[Webhook] Created new UserSubscription for user {user.user_id} with plan {plan_type} and subscription_id {subscription_id}.")
                            db.session.commit()
                            current_app.logger.info(f"[Webhook] User {user.user_id} tier updated to {user.tier} with subscription_id {subscription_id} stored in db.")
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

            elif event['type'] == 'customer.subscription.created':
                subscription = event['data']['object']
                SubscriptionController._handle_subscription_created(subscription)

            elif event['type'] == 'customer.subscription.updated':
                subscription = event['data']['object']
                SubscriptionController._handle_subscription_updated(subscription)

            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                SubscriptionController._handle_subscription_canceled(subscription)

            elif event['type'] == 'setup_intent.succeeded':
                setup_intent = event['data']['object']
                SubscriptionController.handle_payment_method_update(setup_intent)

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

    @staticmethod
    def _handle_subscription_created(subscription):
        """
        Handle new subscription creation - ensure stripe_subscription_id is stored
        """
        try:
            customer_id = subscription.get('customer')
            subscription_id = subscription.get('id')
            
            current_app.logger.info(f"[Webhook] New subscription created {subscription_id} for customer {customer_id}")
            
            # Find user by customer ID
            from models.user_subscription_model import UserSubscription
            
            user_sub = UserSubscription.query.filter_by(stripe_customer_id=customer_id).first()
            if user_sub and not user_sub.stripe_subscription_id:
                user_sub.stripe_subscription_id = subscription_id
                db.session.commit()
                current_app.logger.info(f"[Webhook] Updated UserSubscription with stripe_subscription_id {subscription_id} for user {user_sub.user_id}")
            else:
                current_app.logger.warning(f"[Webhook] UserSubscription not found or already has subscription_id for customer {customer_id}")
                
        except Exception as e:
            current_app.logger.error(f"[Webhook] Error handling subscription creation: {str(e)}")

    @staticmethod
    def _handle_subscription_updated(subscription):
        """
        Handle subscription updates, particularly when cancel_at_period_end is set or pause_collection changes
        """
        try:
            customer_id = subscription.get('customer')
            cancel_at_period_end = subscription.get('cancel_at_period_end', False)
            subscription_id = subscription.get('id')
            pause_collection = subscription.get('pause_collection')
            
            current_app.logger.info(f"[Webhook] Subscription updated for customer {customer_id}, cancel_at_period_end: {cancel_at_period_end}, pause_collection: {pause_collection}")
            
            # Find user by subscription ID
            from models.user_subscription_model import UserSubscription
            
            user_sub = UserSubscription.query.filter_by(stripe_subscription_id=subscription_id).first()
            if user_sub:
                user_sub.cancel_at_period_end = cancel_at_period_end
                
                # Handle pause collection updates
                if pause_collection and pause_collection.get('behavior'):
                    user_sub.is_paused = True
                    user_sub.pause_behavior = pause_collection.get('behavior')
                    user_sub.pause_resumes_at = pause_collection.get('resumes_at')
                    current_app.logger.info(f"[Webhook] Subscription {subscription_id} paused with behavior {pause_collection.get('behavior')} for user {user_sub.user_id}")
                else:
                    user_sub.is_paused = False
                    user_sub.pause_behavior = None
                    user_sub.pause_resumes_at = None
                    current_app.logger.info(f"[Webhook] Subscription {subscription_id} unpaused for user {user_sub.user_id}")
                
                db.session.commit()
                
                if cancel_at_period_end:
                    current_app.logger.info(f"[Webhook] Subscription {subscription_id} scheduled for cancellation at period end for user {user_sub.user_id}")
                else:
                    current_app.logger.info(f"[Webhook] Subscription {subscription_id} cancellation was stopped for user {user_sub.user_id}")
            else:
                current_app.logger.warning(f"[Webhook] UserSubscription not found for updated subscription {subscription_id}")
                
        except Exception as e:
            current_app.logger.error(f"[Webhook] Error handling subscription update: {str(e)}")

    @staticmethod
    def _handle_subscription_canceled(subscription):
        """
        Handle subscription cancellation - reset user to free tier
        """
        try:
            customer_id = subscription.get('customer')
            subscription_id = subscription.get('id')
            
            current_app.logger.info(f"[Webhook] Subscription {subscription_id} canceled for customer {customer_id}")
            
            # Find user by subscription ID
            from models.user_subscription_model import UserSubscription
            from models.user_model import User
            
            user_sub = UserSubscription.query.filter_by(stripe_subscription_id=subscription_id).first()
            if user_sub:
                user = User.query.get(user_sub.user_id)
                if user:
                    user.tier = 'free'
                    user_sub.credits_remaining = 0
                    user_sub.plan_name = 'free'
                    user_sub.cancel_at_period_end = False
                    db.session.commit()
                    current_app.logger.info(f"[Webhook] Reset user {user.user_id} to free tier due to subscription cancellation")
                else:
                    current_app.logger.warning(f"[Webhook] User not found for subscription {subscription_id}")
            else:
                current_app.logger.warning(f"[Webhook] UserSubscription not found for canceled subscription {subscription_id}")
            
        except Exception as e:
            current_app.logger.error(f"[Webhook] Error handling subscription cancellation: {str(e)}")

    @staticmethod
    def pause_subscription(user, subscription_id=None, behavior='void', resumes_at=None):
        """
        Pause user's subscription with specified behavior
        """
        try:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            
            if not subscription_id:
                # Get subscription ID from user's subscription record
                from models.user_subscription_model import UserSubscription
                user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
                if user_sub and user_sub.stripe_subscription_id:
                    subscription_id = user_sub.stripe_subscription_id
                else:
                    current_app.logger.error(f"[Subscription] No subscription_id found for user {user.user_id}")
                    return {'error': 'No active subscription found'}, 404
            
            # Prepare pause collection parameters
            pause_collection = {'behavior': behavior}
            if resumes_at:
                pause_collection['resumes_at'] = resumes_at
            
            # Pause the subscription
            subscription = stripe.Subscription.modify(
                subscription_id,
                pause_collection=pause_collection
            )
            
            # Update local database
            from models.user_subscription_model import UserSubscription
            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
            if user_sub:
                user_sub.is_paused = True
                user_sub.pause_behavior = behavior
                user_sub.pause_resumes_at = resumes_at
                db.session.commit()
            
            current_app.logger.info(f"[Subscription] Paused subscription {subscription_id} with behavior {behavior}")
            return {
                'message': f'Subscription paused successfully with {behavior} behavior',
                'is_paused': True,
                'pause_behavior': behavior,
                'resumes_at': resumes_at
            }, 200
                
        except stripe.error.InvalidRequestError as e:
            current_app.logger.error(f"[Subscription] Invalid subscription pause request: {str(e)}")
            return {'error': 'Invalid subscription or already paused'}, 400
        except Exception as e:
            current_app.logger.error(f"[Subscription] Error pausing subscription: {str(e)}")
            return {'error': 'Error pausing subscription'}, 500

    @staticmethod
    def resume_subscription(user, subscription_id=None):
        """
        Resume user's paused subscription
        """
        try:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            
            if not subscription_id:
                # Get subscription ID from user's subscription record
                from models.user_subscription_model import UserSubscription
                user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
                if user_sub and user_sub.stripe_subscription_id:
                    subscription_id = user_sub.stripe_subscription_id
                else:
                    current_app.logger.error(f"[Subscription] No subscription_id found for user {user.user_id}")
                    return {'error': 'No active subscription found'}, 404
            
            # Resume the subscription by unsetting pause_collection
            subscription = stripe.Subscription.modify(
                subscription_id,
                pause_collection=''
            )
            
            # Update local database
            from models.user_subscription_model import UserSubscription
            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
            if user_sub:
                user_sub.is_paused = False
                user_sub.pause_behavior = None
                user_sub.pause_resumes_at = None
                db.session.commit()
            
            current_app.logger.info(f"[Subscription] Resumed subscription {subscription_id}")
            return {
                'message': 'Subscription resumed successfully',
                'is_paused': False
            }, 200
                
        except stripe.error.InvalidRequestError as e:
            current_app.logger.error(f"[Subscription] Invalid subscription resume request: {str(e)}")
            return {'error': 'Invalid subscription or not paused'}, 400
        except Exception as e:
            current_app.logger.error(f"[Subscription] Error resuming subscription: {str(e)}")
            return {'error': 'Error resuming subscription'}, 500

    @staticmethod
    def create_update_payment_session(user):
        """
        Create a Checkout session in setup mode to update payment method
        """
        try:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            
            # Get user's subscription info
            from models.user_subscription_model import UserSubscription
            user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
            
            if not user_sub or not user_sub.stripe_customer_id:
                current_app.logger.error(f"[Subscription] No customer ID found for user {user.user_id}")
                return {'error': 'No active subscription found'}, 404
            
            success_url = url_for('auth.update_payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
            cancel_url = url_for('auth.update_payment_cancel', _external=True)
            
            # Create setup mode checkout session
            checkout_session = stripe.checkout.Session.create(
                mode='setup',
                customer=user_sub.stripe_customer_id,
                payment_method_types=['card'],
                success_url=success_url,
                cancel_url=cancel_url,
                setup_intent_data={
                    'metadata': {
                        'subscription_id': user_sub.stripe_subscription_id,
                        'user_id': str(user.user_id),
                        'customer_id': user_sub.stripe_customer_id
                    }
                }
            )
            
            current_app.logger.info(f"[Subscription] Setup session created for user {user.user_id}")
            return {'sessionId': checkout_session.id}, 200
            
        except Exception as e:
            current_app.logger.error(f"[Subscription] Error creating update payment session: {str(e)}")
            return {'error': 'Error creating payment update session'}, 500

    @staticmethod
    def handle_payment_method_update(setup_intent):
        """
        Handle payment method update after successful setup
        """
        try:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            
            metadata = setup_intent.get('metadata', {})
            customer_id = metadata.get('customer_id')
            subscription_id = metadata.get('subscription_id')
            user_id = metadata.get('user_id')
            payment_method_id = setup_intent.get('payment_method')
            
            if not all([customer_id, subscription_id, payment_method_id]):
                current_app.logger.error(f"[Subscription] Missing required data in setup intent metadata")
                return
            
            # Update the subscription's default payment method
            stripe.Subscription.modify(
                subscription_id,
                default_payment_method=payment_method_id
            )
            
            # Also update customer's default payment method for future invoices
            stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            current_app.logger.info(f"[Subscription] Updated payment method for user {user_id}, subscription {subscription_id}")
            
        except Exception as e:
            current_app.logger.error(f"[Subscription] Error updating payment method: {str(e)}")

    @staticmethod
    def cancel_subscription(user, subscription_id=None, cancel_at_period_end=True):
        """
        Cancel user's subscription either immediately or at period end
        """
        try:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            
            if not subscription_id:
                # Get subscription ID from user's subscription record
                from models.user_subscription_model import UserSubscription
                user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
                if user_sub and user_sub.stripe_subscription_id:
                    subscription_id = user_sub.stripe_subscription_id
                else:
                    current_app.logger.error(f"[Subscription] No subscription_id found for user {user.user_id}")
                    return {'error': 'No active subscription found'}, 404
            
            if cancel_at_period_end:
                # Schedule cancellation at period end
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                current_app.logger.info(f"[Subscription] Scheduled cancellation for subscription {subscription_id} at period end")
                return {
                    'message': 'Subscription will be canceled at the end of the current billing period',
                    'cancel_at_period_end': True,
                    'current_period_end': subscription.current_period_end
                }, 200
            else:
                # Cancel immediately
                subscription = stripe.Subscription.cancel(subscription_id)
                # Update user tier immediately
                user.tier = 'free'
                user_sub = UserSubscription.query.filter_by(user_id=user.user_id).first()
                if user_sub:
                    user_sub.credits_remaining = 0
                    user_sub.plan_name = 'free'
                db.session.commit()
                current_app.logger.info(f"[Subscription] Immediately canceled subscription {subscription_id}")
                return {
                    'message': 'Subscription canceled immediately',
                    'canceled_at': subscription.canceled_at
                }, 200
                
        except stripe.error.InvalidRequestError as e:
            current_app.logger.error(f"[Subscription] Invalid subscription cancellation request: {str(e)}")
            return {'error': 'Invalid subscription or already canceled'}, 400
        except Exception as e:
            current_app.logger.error(f"[Subscription] Error canceling subscription: {str(e)}")
            return {'error': 'Error canceling subscription'}, 500