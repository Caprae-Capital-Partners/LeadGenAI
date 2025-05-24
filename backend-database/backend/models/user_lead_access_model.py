from sqlalchemy import Column, String, Enum, Boolean, ForeignKey, DateTime
from models.lead_model import db
import uuid
from datetime import datetime

class UserLeadAccess(db.Model):
    """User access to leads"""
    __tablename__ = 'user_lead_access'

    id = db.Column('uuid', String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id_leads_id = db.Column('user_id_leads_id', String(36), unique=True)
    user_id = db.Column('user_id', db.Integer, ForeignKey('users.user_id'), nullable=False)
    lead_id = db.Column('lead_id', String(100), ForeignKey('leads.lead_id'), nullable=False)
    access_type = db.Column('access_type', Enum('view', 'edit', 'admin', name='access_type_enum'), nullable=False)
    granted_by = db.Column('granted_by', db.Integer, ForeignKey('users.user_id'), nullable=True)
    granted_at = db.Column('granted_at', DateTime, default=datetime.utcnow)
    expires_at = db.Column('expires_at', DateTime, nullable=True)
    is_active = db.Column('is_active', Boolean, default=True)

    def __init__(self, user_id, lead_id, access_type, granted_by=None, expires_at=None):
        self.user_id = user_id
        self.lead_id = lead_id
        self.access_type = access_type
        self.granted_by = granted_by
        self.expires_at = expires_at
        self.user_id_leads_id = f"{user_id}_{lead_id}"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lead_id': self.lead_id,
            'access_type': self.access_type,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        } 