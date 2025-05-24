from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user_lead_access_model import UserLeadAccess
from models.user_lead_drafts_model import UserLeadDraft
from models.lead_model import Lead, db
from models.user_model import User
from controllers.audit_controller import AuditController
from utils.decorators import role_required
from datetime import datetime, timedelta

# Create blueprint
access_bp = Blueprint('access', __name__)

@access_bp.route('/api/lead-access', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def create_lead_access():
    """Create a new lead access - Admin and Developer only"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    user_id = data.get('user_id')
    lead_id = data.get('lead_id')
    access_type = data.get('access_type')
    
    if not user_id or not lead_id or not access_type:
        return jsonify({"error": "user_id, lead_id and access_type are required"}), 400
    
    # Validate access_type
    if access_type not in ['view', 'edit', 'admin']:
        return jsonify({"error": "Invalid access_type. Must be one of: view, edit, admin"}), 400
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if lead exists
    lead = Lead.query.filter_by(lead_id=lead_id, deleted=False).first()
    if not lead:
        return jsonify({"error": "Lead not found"}), 404
    
    # Set expiration if provided
    expires_at = None
    if 'expires_days' in data:
        expires_at = datetime.utcnow() + timedelta(days=data['expires_days'])
    
    try:
        # Create access
        access = AuditController.grant_lead_access(
            user_id=user_id,
            lead_id=lead_id,
            access_type=access_type,
            granted_by=str(current_user.user_id),
            expires_at=expires_at
        )
        
        if not access:
            return jsonify({"error": "Failed to create access"}), 500
        
        db.session.commit()
        return jsonify({"message": "Access granted successfully", "access": access.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@access_bp.route('/api/lead-access', methods=['GET'])
@login_required
def get_user_access():
    """Get all lead access for the current user"""
    try:
        # Get all active access for the current user
        access_list = UserLeadAccess.query.filter_by(user_id=str(current_user.user_id), is_active=True).all()
        
        # Format results
        results = []
        for access in access_list:
            lead = Lead.query.filter_by(lead_id=access.lead_id, deleted=False).first()
            if lead:
                result = access.to_dict()
                result['lead'] = {
                    'lead_id': lead.lead_id,
                    'company': lead.company
                }
                results.append(result)
        
        return jsonify({
            "total": len(results),
            "access_list": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@access_bp.route('/api/lead-access/<string:access_id>', methods=['PUT'])
@login_required
@role_required('admin', 'developer')
def update_lead_access(access_id):
    """Update a lead access - Admin and Developer only"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    access = UserLeadAccess.query.filter_by(id=access_id).first()
    if not access:
        return jsonify({"error": "Access not found"}), 404
    
    try:
        # Store old values for audit
        old_values = access.to_dict()
        
        # Update fields
        if 'access_type' in data:
            if data['access_type'] not in ['view', 'edit', 'admin']:
                return jsonify({"error": "Invalid access_type. Must be one of: view, edit, admin"}), 400
            access.access_type = data['access_type']
        
        if 'is_active' in data:
            access.is_active = bool(data['is_active'])
        
        if 'expires_days' in data:
            access.expires_at = datetime.utcnow() + timedelta(days=data['expires_days'])
        
        # Log the update
        AuditController.log_action(
            user_id=current_user.user_id,
            action_type='update',
            table_affected='user_lead_access',
            record_id=access.id,
            old_values=old_values,
            new_values=access.to_dict()
        )
        
        db.session.commit()
        return jsonify({"message": "Access updated successfully", "access": access.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@access_bp.route('/api/lead-access/<string:access_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'developer')
def delete_lead_access(access_id):
    """Delete a lead access - Admin and Developer only"""
    access = UserLeadAccess.query.filter_by(id=access_id).first()
    if not access:
        return jsonify({"error": "Access not found"}), 404
    
    try:
        # Store old values for audit
        old_values = access.to_dict()
        
        # Soft delete by setting inactive
        access.is_active = False
        
        # Log the deletion
        AuditController.log_action(
            user_id=current_user.user_id,
            action_type='delete',
            table_affected='user_lead_access',
            record_id=access.id,
            old_values=old_values,
            new_values=access.to_dict()
        )
        
        db.session.commit()
        return jsonify({"message": "Access revoked successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500 