from flask import Flask
import sys
import os

# Add parent directory to path to run script independently
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.lead_model import db

def recreate_database():
    """Drop all tables and recreate them"""
    with app.app_context():
        # Drop existing tables
        db.drop_all()
        print("Dropped all tables")
        
        # Create tables with new schema
        db.create_all()
        print("Created all tables with new schema")
    
    print("Database tables recreated successfully!")

if __name__ == "__main__":
    recreate_database() 