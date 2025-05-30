from models.lead_model import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), primary_key=True)
    credits_remaining = db.Column(db.Integer, nullable=False, default=10)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.plan_id'))
    plan_name = db.Column(db.String(100), nullable=True)
    payment_frequency = db.Column(db.String(10), default='monthly', nullable=False)
    tier_start_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    plan_expiration_timestamp = db.Column(db.DateTime, nullable=True)
    username = db.Column(db.String(100), nullable=True)

# Tambahkan relationship setelah import Plan
from models.plan_model import Plan
UserSubscription.plan = db.relationship('Plan', backref='user_subscriptions', lazy=True)

def to_dict(self):
    return {
        'user_id': str(self.user_id),
        'credits_remaining': self.credits_remaining,
        'plan_id': self.plan_id,
        'plan_name': self.plan_name,
        'payment_frequency': self.payment_frequency,
        'tier_start_timestamp': self.tier_start_timestamp.isoformat() if self.tier_start_timestamp else None,
        'plan_expiration_timestamp': self.plan_expiration_timestamp.isoformat() if self.plan_expiration_timestamp else None,
        'plan': self.plan.to_dict() if hasattr(self, 'plan') and self.plan else None,
        'username': self.username
    }