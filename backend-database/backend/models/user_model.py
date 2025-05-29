from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models.lead_model import db
from datetime import datetime
import hashlib
import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user', nullable=False)
    tier = db.Column(db.String(50), default='free', nullable=False)
    company = db.Column(db.String(100))  # New field for company
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    linkedin_url = db.Column(db.String(255), nullable=True)

    def get_id(self):
        """Return user_id as the identifier for Flask-Login"""
        return str(self.user_id)

    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def is_developer(self):
        """Check if user is developer"""
        return self.role == 'developer'

    def is_staff(self):
        """Check if user is admin or developer"""
        return self.role in ['admin', 'developer']

    def __repr__(self):
        return f'<User {self.username}>'

    @classmethod
    def generate_user_id(cls, email, password):
        """
        Generate a unique user_id based on email and password.
        Uses SHA-256 hash of combined email and password.
        """
        combined = f"{email or ''}{password or ''}"
        hash_object = hashlib.sha256(combined.encode())
        return hash_object.hexdigest()[:32]

    def __init__(self, **kwargs):
        # Generate user_id if not provided
        if 'user_id' not in kwargs:
            kwargs['user_id'] = self.generate_user_id(
                email=kwargs.get('email'),
                password=kwargs.get('password')
            )
        super().__init__(**kwargs)


    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "tier": self.tier,
            "company": self.company,
            "linkedin_url": self.linkedin_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }