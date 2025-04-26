from flask import Flask
from models.lead_model import db
import input_form

app = input_form.app

with app.app_context():
    # Drop existing tables
    db.drop_all()
    print("Dropped all tables")
    
    # Create tables with new schema
    db.create_all()
    print("Created all tables with new schema")

print("Database tables recreated successfully!") 