from flask import Flask
import sys
import os
from decimal import Decimal
import json

# Add parent directory to path to run script independently
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.plan_model import Plan
from models.lead_model import db  # Assuming db instance is accessible from lead_model

# Define the plan data based on screenshots
plans_data = [
    {
        "plan_name": "Free",
        "description": "Basic access with limited leads and features",
        "monthly_price": Decimal('0.00'),
        "annual_price": Decimal('0.00'),
        "monthly_lead_quota": 8, # 100 leads/year / 12 months approx
        "cost_per_lead": Decimal('0.000'),
        "has_ai_features": False,
        "initial_credits": 8, # Assuming initial credits = monthly quota
        "credit_reset_frequency": "monthly",
        "features_json": json.dumps(["Phase 1 Scraper", "No contact details"])
    },
    {
        "plan_name": "Bronze",
        "description": "Expanded access with more leads and basic features",
        "monthly_price": Decimal('19.00'),
        "annual_price": Decimal('199.00'),
        "monthly_lead_quota": 50, # 600 leads/year / 12 months
        "cost_per_lead": Decimal('0.333'),
        "has_ai_features": False,
        "initial_credits": 50, # Assuming initial credits = monthly quota
        "credit_reset_frequency": "monthly",
        "features_json": json.dumps(["Basic Filters", "CSV Export"])
    },
    {
        "plan_name": "Silver",
        "description": "More leads and advanced contact features",
        "monthly_price": Decimal('49.00'),
        "annual_price": Decimal('499.00'),
        "monthly_lead_quota": 125, # 1500 leads/year / 12 months
        "cost_per_lead": Decimal('0.333'),
        "has_ai_features": False,
        "initial_credits": 125, # Assuming initial credits = monthly quota
        "credit_reset_frequency": "monthly",
        "features_json": json.dumps(["Phone Numbers", "Advanced Features"])
    },
    {
        "plan_name": "Gold",
        "description": "High volume leads and AI features",
        "monthly_price": Decimal('99.00'),
        "annual_price": Decimal('999.00'),
        "monthly_lead_quota": 292, # 3500 leads/year / 12 months approx
        "cost_per_lead": Decimal('0.285'),
        "has_ai_features": True,
        "initial_credits": 292, # Assuming initial credits = monthly quota
        "credit_reset_frequency": "monthly",
        "features_json": json.dumps(["Email Writing AI", "Priority"])
    },
     {
        "plan_name": "Platinum",
        "description": "Unlimited leads and custom workflows",
        "monthly_price": Decimal('199.00'),
        "annual_price": Decimal('1999.00'),
        "monthly_lead_quota": None, # Unlimited leads
        "cost_per_lead": None, # Cost per lead is not applicable for unlimited
        "has_ai_features": True,
        "initial_credits": None, # Unlimited credits (set to None)
        "credit_reset_frequency": "monthly", # Still reset frequency for consistency, even if quota is None
        "features_json": json.dumps(["Custom workflows", "Priority support"])
    },
    {
        "plan_name": "Enterprise",
        "description": "Custom pricing and features for large organizations",
        "monthly_price": None, # Custom pricing
        "annual_price": None, # Custom pricing
        "monthly_lead_quota": None, # Custom leads
        "cost_per_lead": None, # Custom cost
        "has_ai_features": True, # Assuming AI features for Enterprise as per image footnote
        "initial_credits": None, # Custom credits (set to None)
        "credit_reset_frequency": "custom",
        "features_json": json.dumps(["Custom Features"])
    }
]

def seed_plans():
    """Seeds the plans table with initial data."""
    app = create_app()
    with app.app_context():
        print("Seeding plans table...")
        for plan_data in plans_data:
            # Check if plan already exists to avoid duplicates
            existing_plan = Plan.query.filter_by(plan_name=plan_data['plan_name']).first()
            if existing_plan:
                print(f"Plan '{plan_data['plan_name']}' already exists. Skipping.")
                continue

            try:
                # Convert features_json string back to Python object for model instantiation if necessary,
                # although SQLAlchemy's JSON type often handles strings directly if the DB supports it.
                # Let's keep it as string as it's already dumped.
                plan = Plan(**plan_data)
                db.session.add(plan)
                db.session.commit()
                print(f"Added plan: {plan_data['plan_name']}")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding plan {plan_data['plan_name']}: {str(e)}")

        print("Plans seeding complete.")

if __name__ == '__main__':
    seed_plans()