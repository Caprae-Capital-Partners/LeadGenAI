from flask import Flask
import sys
import os

# Add parent directory to path to run script independently
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.user_model import User, db

def create_dev_user():
    """Create a development user"""
    with app.app_context():
        # Check if dev user already exists
        dev_user = User.query.filter_by(username='dev').first()
        if dev_user:
            print("Development user already exists!")
            return

        # Create new dev user
        dev_user = User(
            username='dev',
            email='dev@example.com'
        )
        dev_user.set_password('dev123')  # Set a simple password for development
        
        # Add to database
        db.session.add(dev_user)
        db.session.commit()
        print("Development user created successfully!")
        print("Username: dev")
        print("Password: dev123")

if __name__ == '__main__':
    create_dev_user() 