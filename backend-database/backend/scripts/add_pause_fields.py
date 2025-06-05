
"""
Database migration script to add pause-related fields to user_subscriptions table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.lead_model import db
from sqlalchemy import text

def add_pause_fields():
    """Add pause-related fields to user_subscriptions table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                AND column_name IN ('is_paused', 'pause_behavior', 'pause_resumes_at')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Add missing columns
            if 'is_paused' not in existing_columns:
                db.session.execute(text("""
                    ALTER TABLE user_subscriptions 
                    ADD COLUMN is_paused BOOLEAN DEFAULT FALSE
                """))
                print("✅ Added is_paused column")
            
            if 'pause_behavior' not in existing_columns:
                db.session.execute(text("""
                    ALTER TABLE user_subscriptions 
                    ADD COLUMN pause_behavior VARCHAR(50)
                """))
                print("✅ Added pause_behavior column")
            
            if 'pause_resumes_at' not in existing_columns:
                db.session.execute(text("""
                    ALTER TABLE user_subscriptions 
                    ADD COLUMN pause_resumes_at INTEGER
                """))
                print("✅ Added pause_resumes_at column")
            
            db.session.commit()
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    add_pause_fields()
