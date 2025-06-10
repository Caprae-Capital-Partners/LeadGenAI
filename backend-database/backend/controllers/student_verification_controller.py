import re
from flask import current_app
from models.user_model import User, db

# List of student/school domains
STUDENT_DOMAINS = [
    ".edu",
    ".ac.in",
    ".ac.uk",
    ".edu.in",
]

def is_student_email(email):
    """
    Check if the email belongs to a student domain.
    """
    email = email.lower()
    for domain in STUDENT_DOMAINS:
        if email.endswith(domain):
            current_app.logger.info(f"{email} is a student email.")
            return True
    return False

def set_user_as_student(user):
    """
    Set the user's role to 'student' if not already set.
    """
    if user.role != 'student':
        current_app.logger.info(f"Setting user {user.email} role to 'student' after domain and email verification.")
        user.role = 'student'
        db.session.commit()
        return True
    return False