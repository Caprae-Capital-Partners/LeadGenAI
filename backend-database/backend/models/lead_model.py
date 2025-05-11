from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'leads'
    
    # Primary key
    lead_id = db.Column(db.Integer, primary_key=True)
    
    # Base data
    search_keyword = db.Column(JSONB, nullable=False)  # Base64-encoded JSON string
    draft_data = db.Column(JSONB, nullable=True)  # Draft user data
    
    # Company Information
    company = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    product_category = db.Column(db.String(100), nullable=True)  # Previously product_service_category
    business_type = db.Column(db.String(100), nullable=True)
    employees = db.Column(db.Integer, nullable=True)  # Previously employees_range
    revenue = db.Column(db.Float, nullable=True)
    year_founded = db.Column(db.String(20), nullable=True)
    bbb_rating = db.Column(db.String(10), nullable=True)
    
    # Location Information
    street = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    
    # Company Contact
    company_phone = db.Column(db.String(20), nullable=True)  # New field
    company_linkedin = db.Column(db.String(255), nullable=True)  # Previously linkedin_url
    
    # Owner/Contact Information
    owner_first_name = db.Column(db.String(50), nullable=True)  # Previously first_name
    owner_last_name = db.Column(db.String(50), nullable=True)  # Previously last_name
    owner_title = db.Column(db.String(100), nullable=True)  # Previously title
    owner_linkedin = db.Column(db.String(255), nullable=True)
    owner_phone_number = db.Column(db.String(20), nullable=True)  # New field
    owner_email = db.Column(db.String(120), nullable=True)  # Previously email
    phone = db.Column(db.String(20), nullable=True)  # Changed from Integer to String
    
    # Source information
    source = db.Column(db.String(50), nullable=False)  # Growjo / Apollo / both
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='new', nullable=False)
    
    def __repr__(self):
        return f'<Lead {self.lead_id}: {self.company}>'
    
    # Helper method to convert to dictionary
    def to_dict(self):
        """Convert Lead object to dictionary for API response"""
        return {
            'lead_id': self.lead_id,
            'search_keyword': self.search_keyword,
            'draft_data': self.draft_data,
            'company': self.company,
            'website': self.website,
            'industry': self.industry,
            'product_category': self.product_category,
            'business_type': self.business_type,
            'employees': self.employees,
            'revenue': self.revenue,
            'year_founded': self.year_founded,
            'bbb_rating': self.bbb_rating,
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'company_phone': self.company_phone,
            'company_linkedin': self.company_linkedin,
            'owner_first_name': self.owner_first_name,
            'owner_last_name': self.owner_last_name,
            'owner_title': self.owner_title,
            'owner_linkedin': self.owner_linkedin,
            'owner_phone_number': self.owner_phone_number,
            'owner_email': self.owner_email,
            'phone': self.phone,
            'source': self.source,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted': self.deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        } 