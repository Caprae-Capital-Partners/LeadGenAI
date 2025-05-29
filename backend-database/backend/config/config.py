import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base config class"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

        # Use os.getenv for reading environment variables
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

    # Read individual price IDs and reconstruct the dictionary
    STRIPE_PRICES = {
        'bronze': os.getenv('STRIPE_PRICE_BRONZE'),
        'silver': os.getenv('STRIPE_PRICE_SILVER'),
        'gold': os.getenv('STRIPE_PRICE_GOLD'),
        'platinum': os.getenv('STRIPE_PRICE_PLATINUM'),
        'bronze_annual': os.getenv('STRIPE_PRICE_BRONZE_ANNUAL')

    }

    # You might want to add checks to ensure these keys are loaded
    if not all([STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET] + list(STRIPE_PRICES.values())):
         print("Warning: Stripe environment variables not fully loaded!")

    # Ensure webhook events list remains
    STRIPE_WEBHOOK_EVENTS = [
        'checkout.session.completed', 'customer.subscription.created',
        'customer.subscription.updated', 'customer.subscription.deleted',
        'invoice.payment_succeeded', 'invoice.payment_failed'
    ]

class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True

class ProductionConfig(Config):
    """Production config"""
    DEBUG = False

# Use development config by default
config = DevelopmentConfig