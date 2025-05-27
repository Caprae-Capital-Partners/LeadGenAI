from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user_lead_drafts_model import UserLeadDraft
from models.lead_model import Lead, db
from controllers.audit_controller import AuditController
from utils.decorators import role_required
from datetime import datetime, timedelta
from uuid import UUID

# Create blueprint
drafts_bp = Blueprint('drafts', __name__)

@drafts_bp.route('/lead-drafts', methods=['GET'])
@login_required
def get_user_drafts():
    drafts = UserLeadDraft.query.filter_by(user_id=current_user.user_id, is_deleted=False).all()
    return jsonify([d.to_dict() for d in drafts])

@drafts_bp.route('/lead-drafts/<string:draft_id>', methods=['GET'])
@login_required
def get_draft(draft_id):
    draft = UserLeadDraft.query.filter_by(draft_id=draft_id, is_deleted=False).first()
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
    return jsonify(draft.to_dict())

@drafts_bp.route('/lead-drafts/<string:draft_id>', methods=['PUT'])
@login_required
def update_draft(draft_id):
    draft = UserLeadDraft.query.filter_by(draft_id=draft_id, is_deleted=False).first()
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
    data = request.json
    if 'draft_data' in data:
        draft.draft_data = data['draft_data']
    if 'change_summary' in data:
        draft.change_summary = data['change_summary']
    draft.updated_at = datetime.utcnow()
    draft.increment_version()
    db.session.commit()
    return jsonify(draft.to_dict())

@drafts_bp.route('/lead-drafts/<string:draft_id>', methods=['DELETE'])
@login_required
def delete_draft(draft_id):
    draft = UserLeadDraft.query.filter_by(draft_id=draft_id, is_deleted=False).first()
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
    draft.is_deleted = True
    db.session.commit()
    return jsonify({"message": "Draft deleted"})

@drafts_bp.route('/lead-drafts', methods=['POST'])
@login_required
def create_draft():
    data = request.json
    lead_id = data.get('lead_id')
    draft_data = data.get('draft_data')
    if not lead_id or not draft_data:
        return jsonify({"error": "lead_id and draft_data are required"}), 400
    draft = UserLeadDraft(
        user_id=current_user.user_id,
        lead_id=lead_id,
        draft_data=draft_data,
        change_summary=data.get('change_summary')
    )
    db.session.add(draft)
    db.session.commit()
    return jsonify(draft.to_dict()), 201

@drafts_bp.route('/lead-drafts/search', methods=['POST'])
@login_required
def save_search_draft():
    data = request.json
    draft_data = data.get('draft_data')
    if not draft_data:
        return jsonify({"error": "draft_data is required"}), 400
    draft = UserLeadDraft.query.filter_by(user_id=current_user.user_id, lead_id='search', is_deleted=False).first()
    if draft:
        draft.draft_data = draft_data
        draft.updated_at = datetime.utcnow()
    else:
        draft = UserLeadDraft(
            user_id=current_user.user_id,
            lead_id='search',
            draft_data=draft_data,
            change_summary=data.get('change_summary', 'Search draft')
        )
        db.session.add(draft)
    db.session.commit()
    return jsonify(draft.to_dict())

@drafts_bp.route('/lead-drafts/search', methods=['GET'])
@login_required
def get_search_draft():
    draft = UserLeadDraft.query.filter_by(user_id=current_user.user_id, lead_id='search', is_deleted=False).first()
    if not draft:
        return jsonify({"message": "No search draft found", "draft": None}), 200
    return jsonify({"message": "Search draft found", "draft": draft.to_dict()}), 200 