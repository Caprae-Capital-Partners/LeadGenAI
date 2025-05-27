from models.audit_logs_model import AuditLog
from models.search_logs_model import SearchLog
from models.user_lead_access_model import UserLeadAccess
from models.edit_lead_drafts_model import EditLeadDraft
from models.user_lead_drafts_model import UserLeadDraft
from models.lead_model import db
from flask import request

class AuditController:
    """Controller for managing audits and logs"""
    
    @staticmethod
    def log_action(user_id, action_type, table_affected, record_id, old_values=None, new_values=None):
        """Log an action to the audit logs"""
        try:
            # Get IP and user agent
            ip_address = request.remote_addr if request and hasattr(request, 'remote_addr') else None
            user_agent = request.user_agent.string if request and hasattr(request, 'user_agent') else None
            
            # Create audit log
            log = AuditLog(
                user_id=user_id,
                action_type=action_type,
                table_affected=table_affected,
                record_id=record_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(log)
            return log
        except Exception as e:
            print(f"Error logging action: {e}")
            return None
    
    @staticmethod
    def grant_lead_access(user_id, lead_id, access_type, granted_by, expires_at=None):
        """Grant a user access to a lead"""
        try:
            # Create new access
            access = UserLeadAccess(
                user_id=user_id,
                lead_id=lead_id,
                access_type=access_type,
                granted_by=granted_by,
                expires_at=expires_at
            )
            
            db.session.add(access)
            
            # Log the change
            AuditController.log_action(
                user_id=granted_by,
                action_type='create',
                table_affected='user_lead_access',
                record_id=access.id,
                new_values=access.to_dict()
            )
            
            return access
        except Exception as e:
            db.session.rollback()
            print(f"Error granting lead access: {e}")
            return None 