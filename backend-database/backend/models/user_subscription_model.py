from models.lead_model import db
from datetime import datetime

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'

    user_id = db.Column(db.String(255), db.ForeignKey('users.user_id'), primary_key=True)
    credits_remaining = db.Column(db.Integer, nullable=False, default=10)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.plan_id'))
    tier_start_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Tambahkan relationship setelah import Plan
from models.plan_model import Plan
UserSubscription.plan = db.relationship('Plan', backref='user_subscriptions', lazy=True) 