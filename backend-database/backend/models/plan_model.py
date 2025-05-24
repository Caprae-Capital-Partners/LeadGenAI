from models.lead_model import db
from datetime import datetime

class Plan(db.Model):
    __tablename__ = 'plans'

    plan_id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    monthly_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    initial_credits = db.Column(db.Integer, nullable=False, default=10)
    credit_reset_frequency = db.Column(db.String(50))
    features_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 