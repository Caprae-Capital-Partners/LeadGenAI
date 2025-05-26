import stripe
from flask import request, jsonify, current_app, url_for
from models.user_model import User, db
import logging


class SubscriptionController:

    @staticmethod
    def create_checkout_session(user):
        try:
            plan_type = request.json.get('plan_type')
            price_id = current_app.config['STRIPE_PRICES'].get(plan_type)
        
            logging.info(f"this is -----plan tpye {plan_type}")

            if not price_id:
                # Return a more specific error for debugging
                return {'error': f'Invalid plan type provided: {plan_type}. Check STRIPE_PRICES config.'}, 400

            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

            # Use url_for to generate correct success and cancel URLs
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
                client_reference_id=str(user.user_id), # Use user.user_id for consistency
                payment_method_types=['card']
            )
            logging.info(f"this is -----after the succes session crete {plan_type}")
            user.tier = plan_type
            db.session.commit()
            logging.info(f"payment succes current{user.user_id} tier is  {user.tier}")
            return {'sessionId': checkout_session.id}, 200
        except Exception as e:
            # Log the error for server-side debugging
            logging.error(f"Error creating checkout session: {e}")
            return {'error': 'Error creating checkout session. Please try again later.'}, 500

    @staticmethod
    def handle_stripe_webhook(payload, sig_header):
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            logging.info(f"Webhook received: {event['type']}")

            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                user_id = session.get('client_reference_id')
                logging.info(f"Payment successful for user {user_id}")
                SubscriptionController._handle_successful_payment(session)

            elif event['type'] == 'checkout.session.async_payment_failed':
                session = event['data']['object']
                user_id = session.get('client_reference_id')
                if user_id:
                    user = User.query.get(int(user_id))
                    if user:
                        user.tier = 'free'
                        logging.info(f" if payment failed the tire si is {user.tier}")
                        db.session.commit()
                        logging.info(f"Reset user {user_id} to free tier due to payment failure")

            # Add other Stripe event types as needed (e.g., invoice.payment_failed for recurring payments)

        except ValueError as e:
            logging.error(f"Webhook error: Invalid payload - {str(e)}")
            return {'error': 'Invalid payload'}, 400
        except stripe.error.SignatureVerificationError as e:
            logging.error(f"Webhook error: Invalid signature - {str(e)}")
            return {'error': 'Invalid signature'}, 400
        except Exception as e:
            logging.error(f"Webhook error: {str(e)}")
            return {'error': str(e)}, 400

        return {'status': 'success'}, 200

    @staticmethod
    def _handle_successful_payment(session):
        try:
            user_id = session.get('client_reference_id')
            if not user_id:
                logging.warning("No user_id found in session")
                return

            user = User.query.get(int(user_id))
            if not user:
                logging.warning(f"User {user_id} not found")
                return

            # Get line items and extract price ID
            line_items = stripe.checkout.Session.list_line_items(session.id)
            if not line_items or not line_items.data:
                logging.warning("No line items found for session")
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
            logging.info(f" this is the new ties from handle succesfull {new_tier}")
            if not new_tier:
                logging.warning(f"Invalid price_id: {price_id}")
                return

            # Update the user's tier instead of subscription_tier
            user.tier = new_tier
            db.session.commit()
            logging.info(f"Successfully updated user {user_id} to tier {new_tier}")

        except Exception as e:
            logging.error(f" changes is commited ")
            logging.error(f"Error handling successful payment for session {session.id}: {str(e)}")
            db.session.rollback()