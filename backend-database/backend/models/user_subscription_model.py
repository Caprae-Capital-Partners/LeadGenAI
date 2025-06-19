from models.lead_model import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), primary_key=True)
    credits_remaining = db.Column(db.Integer, nullable=False, default=10)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.plan_id'))
    plan_name = db.Column(db.String(100), nullable=True)
    payment_frequency = db.Column(db.String(30), default='monthly', nullable=False)
    tier_start_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    plan_expiration_timestamp = db.Column(db.DateTime, nullable=True)
    username = db.Column(db.String(100), nullable=True)
    is_paused = db.Column(db.Boolean, default=False, nullable=False)
    pause_end_date = db.Column(db.DateTime, nullable=True)
    original_plan_id = db.Column(db.Integer, nullable=True)
    original_plan_name = db.Column(db.String(100), nullable=True)
    is_canceled = db.Column(db.Boolean, default=False, nullable=False)
    canceled_at = db.Column(db.DateTime, nullable=True)
    is_call_outreach_cust = db.Column(db.Boolean, default=False, nullable=False)
    appointment_used = db.Column(db.Boolean, default=False, nullable=False)

    # Customer Portal Fields
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    billing_address_line1 = db.Column(db.String(255), nullable=True)
    billing_address_line2 = db.Column(db.String(255), nullable=True)
    billing_address_city = db.Column(db.String(255), nullable=True)
    billing_address_state = db.Column(db.String(255), nullable=True)
    billing_address_postal_code = db.Column(db.String(255), nullable=True)
    billing_address_country = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(255), nullable=True)
    payment_method_id = db.Column(db.String(255), nullable=True)
    payment_method_type = db.Column(db.String(100), nullable=True)
    payment_method_last4 = db.Column(db.String(4), nullable=True)
    payment_method_brand = db.Column(db.String(50), nullable=True)
    invoice_settings_default_payment_method = db.Column(db.String(255), nullable=True)
    preferred_locales = db.Column(db.String(255), nullable=True)
    currency = db.Column(db.String(3), nullable=True)
    subscription_status = db.Column(db.String(50), nullable=True)
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, default=False, nullable=False)
    invoice_email_enabled = db.Column(db.Boolean, default=True, nullable=False)
    customer_portal_last_updated = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'user_id': str(self.user_id),
            'credits_remaining': self.credits_remaining,
            'plan_id': self.plan_id,
            'plan_name': self.plan_name,
            'payment_frequency': self.payment_frequency,
            'tier_start_timestamp': self.tier_start_timestamp.isoformat() if self.tier_start_timestamp else None,
            'plan_expiration_timestamp': self.plan_expiration_timestamp.isoformat() if self.plan_expiration_timestamp else None,
            'is_paused': self.is_paused,
            'pause_end_date': self.pause_end_date.isoformat() if self.pause_end_date else None,
            'original_plan_id': self.original_plan_id,
            'original_plan_name': self.original_plan_name,
            # 'plan': self.plan.to_dict() if hasattr(self, 'plan') and self.plan else None,
            'username': self.username,
            'is_canceled': self.is_canceled,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'is_call_outreach_cust': self.is_call_outreach_cust,
            'appointment_used': self.appointment_used,
            'stripe_customer_id': self.stripe_customer_id,
            'billing_address_line1': self.billing_address_line1,
            'billing_address_line2': self.billing_address_line2,
            'billing_address_city': self.billing_address_city,
            'billing_address_state': self.billing_address_state,
            'billing_address_postal_code': self.billing_address_postal_code,
            'billing_address_country': self.billing_address_country,
            'phone_number': self.phone_number,
            'payment_method_id': self.payment_method_id,
            'payment_method_type': self.payment_method_type,
            'payment_method_last4': self.payment_method_last4,
            'payment_method_brand': self.payment_method_brand,
            'invoice_settings_default_payment_method': self.invoice_settings_default_payment_method,
            'preferred_locales': self.preferred_locales,
            'currency': self.currency,
            'subscription_status': self.subscription_status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'invoice_email_enabled': self.invoice_email_enabled,
            'customer_portal_last_updated': self.customer_portal_last_updated.isoformat() if self.customer_portal_last_updated else None
        
        }



# Tambahkan relationship setelah import Plan
from models.plan_model import Plan
UserSubscription.plan = db.relationship('Plan', backref='user_subscriptions', lazy=True)

#UserSubscription.to_dict = to_dict
def can_be_reactivated(self):
    """Check if subscription can be reactivated"""
    # Can be reactivated if scheduled for cancellation but not yet canceled
    is_scheduled_for_cancellation = (self.payment_frequency and 
                                   '_scheduled_cancel' in self.payment_frequency)
    return is_scheduled_for_cancellation and not self.is_canceled

UserSubscription.can_be_reactivated = can_be_reactivated