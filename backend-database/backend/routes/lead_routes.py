from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify, send_file, current_app
from controllers.lead_controller import LeadController
from controllers.upload_controller import UploadController
from controllers.export_controller import ExportController
from models.user_subscription_model import UserSubscription
from models.lead_model import db, Lead
from flask_login import login_required, current_user
from utils.decorators import role_required, credit_required, filter_lead_data_by_plan
import csv
from io import StringIO, BytesIO
import logging
from datetime import datetime, timezone
import pandas as pd
import io
from werkzeug.exceptions import NotFound
from sqlalchemy import or_, and_
import requests
from models.user_model import User
from models.audit_log_model import LeadAuditLog
from models.edit_lead_drafts_model import EditLeadDraft
from models.user_lead_drafts_model import UserLeadDraft
import uuid
from sqlalchemy import Integer


# Create blueprint
lead_bp = Blueprint('lead', __name__)

@lead_bp.route('/')
@login_required
def index():
    """Redirect to view leads page"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: / by user_id={user_id}, username={username}')
    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/form')
@login_required
def form():
    """Display form to add new lead"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /form by user_id={user_id}, username={username}')
    return render_template('form.html')

@lead_bp.route('/submit', methods=['POST'])
# #@login_required
@role_required('admin', 'developer')
def submit():
    """Submit new lead - Admin and Developer only"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /submit by user_id={user_id}, username={username}')
    success, message = LeadController.create_lead(request.form)

    if success:
        current_app.logger.info(f'Lead created successfully: {message}')
        flash(message, 'success')
    else:
        current_app.logger.warning(f'Failed to create lead: {message}')
        flash(message, 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/upload_page')
@login_required
def upload_page():
    """Display CSV upload page"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /upload_page by user_id={user_id}, username={username}')
    return render_template('upload.html')

@lead_bp.route('/upload', methods=['POST'])
# #@login_required
def upload_csv():
    """Handle CSV file upload"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /upload by user_id={user_id}, username={username}')
    if 'file' not in request.files:
        current_app.logger.warning('No file part in upload request')
        flash('No file part', 'danger')
        return redirect(url_for('lead.upload_page'))

    file = request.files['file']
    if file.filename == '':
        current_app.logger.warning('No selected file in upload request')
        flash('No selected file', 'danger')
        return redirect(url_for('lead.upload_page'))

    name_col = request.form.get('name_column')
    email_col = request.form.get('email_column')
    phone_col = request.form.get('phone_column')
    first_name_col = request.form.get('first_name_column')
    last_name_col = request.form.get('last_name_column')

    # Collect dynamic field mappings
    dynamic_field_names = request.form.getlist('dynamic_field_name[]')
    dynamic_field_values = request.form.getlist('dynamic_field_value[]')
    dynamic_fields = {name: value for name, value in zip(dynamic_field_names, dynamic_field_values) if name and value}

    try:
        current_app.logger.info(f"[Lead] Starting CSV upload: {file.filename}")
        added, skipped_duplicates, skipped_empty_company, errors = UploadController.process_csv_file(
            file,
            name_col,
            email_col,
            phone_col,
            dynamic_fields,
            first_name_col=first_name_col,
            last_name_col=last_name_col
        )
        db.session.commit()
        current_app.logger.info(f"[Lead] Upload complete: Added={added}, Duplicates={skipped_duplicates}, Empty={skipped_empty_company}, Errors={errors}")

        # More informative success message
        message = 'Upload Complete! '
        if isinstance(added, tuple) and len(added) == 2:
            # If added is a tuple with new entries and updated entries
            new_entries, updated_entries = added
            message += f'Added: {new_entries}, Updated: {updated_entries}, '
        else:
            # Original format
            message += f'Added: {added}, '

        message += f'Skipped Duplicates: {skipped_duplicates}, '
        message += f'Skipped Empty Company: {skipped_empty_company}, '
        message += f'Errors: {errors}'

        # Add information to view log if there are errors or skips
        if errors > 0 or skipped_duplicates > 0 or skipped_empty_company > 0:
            message += ' (See upload_errors.log for details)'

        flash(message, 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Lead] Error during upload: {str(e)}")
        flash(f'Error during upload: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/view_leads')
@login_required
def view_leads():
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /view_leads by user_id={user_id}, username={username}')
    # Ambil parameter dari query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    company = request.args.get('company', '')
    status = request.args.get('status', '')
    location = request.args.get('location', '')
    role = request.args.get('role', '')
    industry = request.args.get('industry', '')

    # Query dengan filter dan pagination
    query = Lead.query.filter(Lead.deleted == False)
    if search:
        query = query.filter(
            db.or_(
                Lead.company.ilike(f'%{search}%'),
                Lead.owner_first_name.ilike(f'%{search}%'),
                Lead.owner_last_name.ilike(f'%{search}%'),
                Lead.owner_email.ilike(f'%{search}%')
            )
        )
    if company:
        query = query.filter(Lead.company.ilike(f'%{company}%'))
    if status:
        query = query.filter(Lead.status == status)
    if location:
        query = query.filter(
            (Lead.city.ilike(f'%{location}%')) | (Lead.state.ilike(f'%{location}%'))
        )
    if role:
        query = query.filter(Lead.owner_title.ilike(f'%{role}%'))
    if industry:
        query = query.filter(Lead.industry.ilike(f'%{industry}%'))

    # --- Advanced filter ---
    adv_filters = []
    idx = 0
    while True:
        field = request.args.get(f'adv_field_{idx}')
        operator = request.args.get(f'adv_operator_{idx}')
        value = request.args.get(f'adv_value_{idx}')
        logic = request.args.get(f'adv_logic_{idx}')
        if not field or not operator or not value:
            break
        adv_filters.append({'field': field, 'operator': operator, 'value': value, 'logic': logic})
        idx += 1
    adv_expressions = []
    for f in adv_filters:
        col = getattr(Lead, f['field'], None)
        if not col:
            continue
        val = f['value']
        op = f['operator']
        if op == 'equals':
            expr = col == val
        elif op == 'contains':
            expr = col.ilike(f'%{val}%')
        elif op == 'starts':
            expr = col.ilike(f'{val}%')
        elif op == 'ends':
            expr = col.ilike(f'%{val}')
        elif op == 'greater':
            expr = col > val
        elif op == 'less':
            expr = col < val
        else:
            expr = col == val
        adv_expressions.append((expr, f['logic']))
    if adv_expressions:
        expr = adv_expressions[0][0]
        for i in range(1, len(adv_expressions)):
            logic = adv_expressions[i][1]
            if logic == 'AND':
                expr = and_(expr, adv_expressions[i][0])
            else:
                expr = or_(expr, adv_expressions[i][0])
        query = query.filter(expr)
    # --- END advanced filter ---

    paginated = query.order_by(Lead.created_at.desc()).paginate(page=page, per_page=per_page)
    leads = paginated.items

    print(f"Page: {page}, Per Page: {per_page}, Leads: {[lead.lead_id for lead in leads]}")

    # Filter options (get from all data, not only current page)
    all_leads = LeadController.get_all_leads()
    locations = sorted(set(
        (lead.city.strip() + ', ' + lead.state.strip()).title() if lead.city and lead.state else (lead.city or lead.state or '').strip().title()
        for lead in all_leads if (lead.city or lead.state)
    ))
    roles = sorted(set(lead.owner_title for lead in all_leads if lead.owner_title))
    statuses = sorted(set(lead.status for lead in all_leads if lead.status))

    # Get additional filter options
    industries = sorted(set(lead.industry for lead in all_leads if lead.industry))
    business_types = sorted(set(lead.business_type for lead in all_leads if lead.business_type))
    employee_sizes = sorted(set(lead.employees for lead in all_leads if lead.employees))
    revenue_ranges = sorted(set(lead.revenue for lead in all_leads if lead.revenue))
    sources = sorted(set(lead.source for lead in all_leads if lead.source))

    return render_template('leads.html',
        leads=leads,
        locations=locations,
        roles=roles,
        statuses=statuses,
        industries=industries,
        business_types=business_types,
        employee_sizes=employee_sizes,
        revenue_ranges=revenue_ranges,
        sources=sources,
        page=page,
        per_page=per_page,
        total=paginated.total,
        pages=paginated.pages,
        search=search,
        company=company,
        status=status,
        location=location,
        role=role,
        industry=industry,
    )

@lead_bp.route('/edit/<string:lead_id>', methods=['GET', 'POST'])
#@login_required
@role_required('admin', 'developer')
def edit_lead(lead_id):
    """Edit lead - Admin and Developer only"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /edit/{lead_id} by user_id={user_id}, username={username}')
    if request.method == 'POST':
        success, message = LeadController.update_lead(lead_id, request.form)

        if success:
            current_app.logger.info(f'Lead updated successfully: {lead_id}')
            flash(message, 'success')
            return redirect(url_for('lead.view_leads'))
        else:
            current_app.logger.warning(f'Failed to update lead: {lead_id} - {message}')
            flash(message, 'danger')

    lead = LeadController.get_lead_by_id(lead_id)
    return render_template('edit_lead.html', lead=lead)

@lead_bp.route('/update_status/<string:lead_id>', methods=['POST'])
#@login_required
def update_status(lead_id):
    """Update lead status - All roles can update status"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /update_status/{lead_id} by user_id={user_id}, username={username}')
    try:
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
        new_status = request.form.get('status')
        if new_status:
            lead.status = new_status
            db.session.commit()
            current_app.logger.info(f'Lead status updated: {lead_id} to {new_status}')
            flash('Status updated successfully', 'success')
        else:
            current_app.logger.warning(f'No status provided for lead: {lead_id}')
            flash('No status provided', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating status for lead {lead_id}: {str(e)}')
        flash(f'Error updating status: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/leads/<string:lead_id>/delete', methods=['POST'])
#@login_required
@role_required('admin', 'developer', 'user')
def delete_lead(lead_id):
    """Soft delete lead - Admin and Developer only"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/{lead_id}/delete by user_id={user_id}, username={username}')
    try:
        success, message = LeadController.delete_lead(lead_id, current_user)
        if success:
            current_app.logger.info(f'Lead deleted: {lead_id}')
        else:
            current_app.logger.warning(f'Failed to delete lead: {lead_id} - {message}')
        return jsonify({'success': success, 'message': message})
    except NotFound:
        current_app.logger.error(f'Lead not found or already deleted: {lead_id}')
        return jsonify({'success': False, 'message': 'Lead not found or already deleted.'}), 404
    except Exception as e:
        import traceback
        current_app.logger.error(f'Error deleting lead {lead_id}: {str(e)}')
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@lead_bp.route('/leads/delete-multiple', methods=['POST'])
#@login_required
@role_required('admin', 'developer')
def delete_multiple_leads():
    """Soft delete multiple leads - Admin and Developer only"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/delete-multiple by user_id={user_id}, username={username}')
    try:
        lead_ids = request.json.get('lead_ids', [])
        if not lead_ids:
            current_app.logger.warning('No leads selected for deletion')
            return jsonify({'success': False, 'message': 'No leads selected'}), 400
        success, message = LeadController.delete_multiple_leads(lead_ids, current_user)
        if success:
            current_app.logger.info(f'Multiple leads deleted: {lead_ids}')
        else:
            current_app.logger.warning(f'Failed to delete multiple leads: {lead_ids} - {message}')
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        import traceback
        current_app.logger.error(f'Error deleting multiple leads: {str(e)}')
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@lead_bp.route('/api/leads', methods=['GET'])
#@login_required
def get_leads():
    """API endpoint to get all leads with pagination, search and filtering"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads [GET] by user_id={user_id}, username={username}')
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Get search and filter parameters
    search_term = request.args.get('search', '')
    company = request.args.get('company', '')
    status = request.args.get('status', '')
    source = request.args.get('source', '')
    industry = request.args.get('industry', '')
    location = request.args.get('location', '')

    # Build query with filters
    query = Lead.query.filter(Lead.deleted == False)

    if search_term:
        query = query.filter(
            db.or_(
                Lead.company.ilike(f'%{search_term}%'),
                Lead.owner_first_name.ilike(f'%{search_term}%'),
                Lead.owner_last_name.ilike(f'%{search_term}%'),
                Lead.owner_email.ilike(f'%{search_term}%')
            )
        )

    if company:
        query = query.filter(Lead.company.ilike(f'%{company}%'))

    if status:
        query = query.filter(Lead.status == status)

    if source:
        query = query.filter(Lead.source == source)

    if industry:
        query = query.filter(Lead.industry.ilike(f'%{industry}%'))

    if location:
        query = query.filter(
            (Lead.city.ilike(f'%{location}%')) | (Lead.state.ilike(f'%{location}%'))
        )

    # Execute paginated query
    paginated_leads = query.order_by(Lead.created_at.desc()).paginate(page=page, per_page=per_page)

    # Format results
    results = {
        "total": paginated_leads.total,
        "pages": paginated_leads.pages,
        "current_page": page,
        "per_page": per_page,
        "leads": [lead.to_dict() for lead in paginated_leads.items]
    }

    current_app.logger.info(f"[Lead] API get_leads returned {results['total']} leads.")
    return jsonify(results)

@lead_bp.route('/api/leads', methods=['POST'])
#@login_required
@role_required('admin', 'developer')
def create_lead():
    """Create a new lead via API - Admin and Developer only"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads [POST] by user_id={user_id}, username={username}')
    data = request.json

    company = data.get('company')
    owner_email = data.get('owner_email')

    if not company:
        current_app.logger.warning("[Lead] Attempted to create lead with missing company field")
        return jsonify({"error": "Company field is required"}), 400

    # Make case-insensitive search
    query = Lead.query.filter(
        db.func.lower(Lead.company) == db.func.lower(company),
        Lead.deleted == False
    )

    if owner_email:
        query = query.filter_by(owner_email=owner_email)
    existing_lead = query.first()
    if existing_lead:
        current_app.logger.info(f"[Lead] Duplicate lead found for company: {company}, skipping creation.")
        return jsonify({
            "message": "Lead already exists, skipping creation.",
            "lead": existing_lead.to_dict(),
            "skipped": True
        }), 200

    lead = Lead(**data)
    try:
        db.session.add(lead)
        db.session.commit()
        current_app.logger.info(f"[Lead] Lead created successfully: {lead.lead_id}")
        # Verify lead was actually created
        verify_lead = Lead.query.filter_by(lead_id=lead.lead_id).first()
        if not verify_lead:
            db.session.rollback()
            return jsonify({"error": "Failed to create lead - verification check failed"}), 500

        return jsonify({
            "message": "Lead created successfully",
            "lead": lead.to_dict(),
            "skipped": False
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Lead] Error creating lead: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/api/leads/<string:lead_id>', methods=['PUT'])
#@login_required
@role_required('admin', 'developer')
def update_lead_api(lead_id):
    """Update a lead via API - Admin and Developer only"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/{lead_id} [PUT] by user_id={user_id}, username={username}')
    lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
    data = request.json

    try:
        for key, value in data.items():
            setattr(lead, key, value)
        db.session.commit()
        current_app.logger.info(f"[Lead] Lead updated via API: {lead_id}")
        if request.is_json:
            return jsonify({'success': True, 'message': 'Lead updated successfully'})
        else:
            flash('Lead updated successfully', 'success')
            return redirect(url_for('lead.view_leads'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Lead] Error updating lead via API {lead_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/api/leads/<string:lead_id>/status', methods=['PUT'])
#@login_required
def update_status_api(lead_id):
    """Update a lead's status via API - All roles can update status"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/{lead_id}/status [PUT] by user_id={user_id}, username={username}')
    lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
    data = request.json

    if 'status' not in data:
        current_app.logger.warning(f"[Lead] Status field missing in update_status_api for lead {lead_id}")
        return jsonify({"error": "Status field is required"}), 400

    try:
        lead.status = data['status']
        db.session.commit()
        current_app.logger.info(f"[Lead] Status updated via API: {lead_id} to {data['status']}")
        return jsonify({"message": "Status updated successfully", "lead": lead.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Lead] Error updating status via API {lead_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/export_leads', methods=['POST'])
#@login_required
def export_leads():
    """Export selected leads to CSV or Excel - All roles can export"""
    selected_leads = request.form.getlist('selected_leads[]')
    file_format = request.form.get('file_format', 'csv', 'excel')
    export_type = request.form.get('export_type', 'selected')
    print('DEBUG EXPORT file_format:', file_format)

    # Get filter parameters if exporting filtered data
    filter_params = None
    if export_type == 'filtered':
        filter_params = {
            'company': request.form.get('company', ''),
            'location': request.form.get('location', ''),
            'role': request.form.get('role', ''),
            'status': request.form.get('status', ''),
            'revenue': request.form.get('revenue', ''),
            'search': request.form.get('search', '')
        }
        # Remove empty filters
        filter_params = {k: v for k, v in filter_params.items() if v}

    # Check if we're exporting selected leads and if any are selected
    if export_type == 'selected' and not selected_leads:
        flash('Please select at least one lead to export', 'danger')
        return redirect(url_for('lead.view_leads'))

    try:
        # Pass either lead_ids or filter_params based on export type
        if export_type == 'selected':
            output, filename, mimetype = ExportController.export_leads_to_file(selected_leads, file_format)
        else:  # filtered
            output, filename, mimetype = ExportController.export_leads_to_file(None, file_format, filter_params)

        if output is None:
            flash('No leads found to export', 'danger')
            return redirect(url_for('lead.view_leads'))

        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error exporting leads: {str(e)}', 'danger')
        return redirect(url_for('lead.view_leads'))

def parse_revenue_value(revenue_str):
    """
    Parse revenue values in format like $5M, 50M, $1.5M, 5000000, etc.
    Returns float value in millions, or None if parsing fails.
    """
    if not revenue_str or str(revenue_str).strip() == '-':
        return None
    s = str(revenue_str).replace('$', '').replace(',', '').strip()
    try:
        if s.lower().endswith('m'):
            return float(s[:-1])
        elif s.lower().endswith('k'):
            return float(s[:-1]) / 1000
        else:
            val = float(s)
            # If value is very large, assume it's in units (e.g. 5000000 = 5M)
            if val > 100000:
                return val / 1_000_000
            return val
    except Exception:
        return None

@lead_bp.route('/api/upload_leads', methods=['POST'])
@login_required
def api_upload_leads():
    """API endpoint to upload multiple leads"""
    try:
        user_id = getattr(current_user, 'user_id', None)
        username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
        current_app.logger.info(f'Route hit: /api/upload_leads by user_id={user_id}, username={username}')
        data = request.get_json()
        if not data or not isinstance(data, list) or len(data) == 0:
            current_app.logger.warning(f"[Upload] Invalid data format. Data: {data}")
            return jsonify({"status": "error", "message": "Invalid data format. Expected a list of leads"}), 400
        required_fields = ['company', 'website', 'owner_linkedin']
        valid_leads = []
        invalid_indices = []
        error_details = []
        for i, lead in enumerate(data):
            if 'email' in lead and 'owner_email' not in lead:
                lead['owner_email'] = lead.pop('email')
            if all(field in lead for field in required_fields):
                # Clean revenue field if present
                if 'revenue' in lead:
                    try:
                        parsed_revenue = parse_revenue_value(lead['revenue'])
                        if parsed_revenue is not None:
                            lead['revenue'] = parsed_revenue
                        else:
                            lead['revenue'] = None
                    except Exception as e:
                        error_details.append(f"Row {i}: Error parsing revenue '{lead['revenue']}': {str(e)}")
                        lead['revenue'] = None
                # Clean fields if present
                if 'owner_email' in lead:
                    lead['owner_email'] = UploadController.clean_email(lead.get('owner_email', ''))
                else:
                    lead['owner_email'] = ''

                if 'phone' in lead:
                    lead['phone'] = UploadController.clean_phone(lead.get('phone', ''))
                else:
                    lead['phone'] = ''

                if 'website' in lead:
                    lead['website'] = UploadController.clean_website(lead.get('website', ''))
                else:
                    lead['website'] = ''
                lead['company'] = UploadController.clean_company(lead['company'])
                if UploadController.is_valid_company(lead['company']):
                    if 'search_keyword' not in lead:
                        lead['search_keyword'] = {}
                    if hasattr(Lead, 'truncate_fields'):
                        lead = Lead.truncate_fields(lead)
                    valid_leads.append(lead)
                else:
                    invalid_indices.append(i)
            else:
                invalid_indices.append(i)
        current_app.logger.info(f"[Upload] Valid leads: {len(valid_leads)}, Invalid leads: {len(invalid_indices)}")
        added_new = 0
        updated = 0
        no_change = 0
        skipped = 0
        errors = 0
        detailed_results = []
        valid_columns = set(c.name for c in Lead.__table__.columns)  # <-- Add this line
        for i, lead_data in enumerate(valid_leads):
            try:
                filtered_lead_data = {k: v for k, v in lead_data.items() if k in valid_columns}
                success, result = LeadController.add_or_update_lead_by_match(filtered_lead_data)
                # Add original index for easier frontend mapping
                result['original_index'] = invalid_indices.index(i) if i in invalid_indices else i
                detailed_results.append(result)
                status = result.get('status', '')
                if status == "created":
                    added_new += 1
                elif status == "updated":
                    updated += 1
                elif status == "no_change":
                    no_change += 1
                elif status == "error":
                    errors += 1
                    error_details.append(result.get('message', f'Unknown error for lead at index {i}'))
                else:
                     # This might catch unexpected statuses from controller, count as skipped
                    skipped += 1
                    error_details.append(f'Skipped lead at index {i} due to unexpected controller status: {status}')
            except Exception as e:
                errors += 1
                error_details.append(f"Exception saving lead at index {i}: {str(e)}")
        current_app.logger.info(f"[Upload] Added: {added_new}, Updated: {updated}, No Change: {no_change}, Skipped: {skipped}, Errors: {errors}")
        # Determine overall status
        overall_status = "success"
        if errors > 0 or len(invalid_indices) > 0:
            overall_status = "warning"
        if added_new == 0 and updated == 0 and no_change == 0:
             # If no leads were successfully processed (added/updated/no_change)
            overall_status = "error"

        return jsonify({
            "status": overall_status,
            "message": f"Upload Complete. Added: {added_new}, Updated: {updated}, No Change: {no_change}, Skipped (Controller): {skipped}, Invalid (Initial Check): {len(invalid_indices)}, Errors: {errors}",
            "stats": {
                "added_new": added_new,
                "updated": updated,
                "no_change": no_change,
                "skipped_controller": skipped, # Skipped by controller logic
                "invalid_initial_check": len(invalid_indices), # Skipped by initial validation
                "errors": errors,
                "invalid_indices": invalid_indices, # Indices from original payload that failed initial check
                "error_details": error_details,
                "detailed_results": detailed_results # Results for leads that passed initial check
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Upload] Error during upload: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error during upload: {str(e)}"
        }), 500

@lead_bp.route('/api/leads/<string:lead_id>', methods=['DELETE'])
#@login_required
@role_required('admin', 'developer')
def delete_lead_api(lead_id):
    """Soft delete a lead via API - Admin and Developer only"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/{lead_id} [DELETE] by user_id={user_id}, username={username}')
    try:
        # Use the controller method which implements soft delete
        success, message = LeadController.delete_lead(lead_id, current_user=current_user)
        if success:
            current_app.logger.info(f"[Lead] Lead deleted via API: {lead_id}")
            return jsonify({"message": "Lead successfully deleted"})
        else:
            current_app.logger.warning(f"[Lead] Failed to delete lead via API: {lead_id} - {message}")
            return jsonify({"error": message}), 400
    except Exception as e:
        current_app.logger.error(f"[Lead] Error deleting lead via API {lead_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/leads/<string:lead_id>', methods=['GET'])
#@login_required
def get_lead_by_id(lead_id):
    """Get detail of a single lead by ID"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/{lead_id} [GET] by user_id={user_id}, username={username}')
    try:
        lead = Lead.query.filter_by(lead_id=lead_id, deleted=False).first_or_404()
        return jsonify(lead.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# Sources Management Endpoints
@lead_bp.route('/api/sources', methods=['GET'])
#@login_required
def get_sources():
    """Get all available lead sources"""
    try:
        # Query all distinct sources from the leads table
        sources = db.session.query(Lead.source).filter(
            Lead.source.isnot(None),
            Lead.source != ''
        ).distinct().all()

        # Extract the source strings from the query result
        source_list = [source[0] for source in sources]

        return jsonify({
            "total": len(source_list),
            "sources": sorted(source_list)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/sources', methods=['POST'])
#@login_required
@role_required('admin', 'developer')
def add_source():
    """Add a new source - Admin and Developer only"""
    try:
        data = request.json

        if not data or 'name' not in data:
            return jsonify({"error": "Source name is required"}), 400

        source_name = data['name'].strip()

        if not source_name:
            return jsonify({"error": "Source name cannot be empty"}), 400

        # Check if source already exists
        existing_sources = db.session.query(Lead.source).filter(
            Lead.source == source_name
        ).first()

        if existing_sources:
            return jsonify({"error": "Source already exists"}), 400

        # Create a dummy lead with just the source to add it to the system
        # This is a simple way to add a source without creating a separate table
        # In a production system, you might want a dedicated sources table
        dummy_lead = Lead(
            company="Source Definition",
            source=source_name,
            status="Source Definition"
        )

        db.session.add(dummy_lead)
        db.session.commit()

        return jsonify({
            "message": "Source added successfully",
            "source": source_name
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Stats Endpoints
@lead_bp.route('/api/stats/summary', methods=['GET'])
#@login_required
def get_stats_summary():
    """Get lead count summary statistics"""
    try:
        # Get time range parameters (defaults to last 30 days)
        days = request.args.get('days', 30, type=int)
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)

        # Get leads count by date
        date_query = db.session.query(
            db.func.date(Lead.created_at).label('date'),
            db.func.count(Lead.lead_id).label('count')
        ).filter(
            Lead.created_at >= start_date,
            Lead.deleted == False
        ).group_by(
            db.func.date(Lead.created_at)
        ).all()

        # Get leads count by source
        source_query = db.session.query(
            Lead.source,
            db.func.count(Lead.lead_id).label('count')
        ).filter(
            Lead.deleted == False,
            Lead.source.isnot(None),
            Lead.source != ''
        ).group_by(
            Lead.source
        ).all()

        # Get leads count by status
        status_query = db.session.query(
            Lead.status,
            db.func.count(Lead.lead_id).label('count')
        ).filter(
            Lead.deleted == False,
            Lead.status.isnot(None),
            Lead.status != ''
        ).group_by(
            Lead.status
        ).all()

        # Format results
        date_stats = {str(date): count for date, count in date_query}
        source_stats = {source: count for source, count in source_query}
        status_stats = {status: count for status, count in status_query}

        # Get total lead count
        total_leads = db.session.query(Lead).filter(Lead.deleted == False).count()

        return jsonify({
            "total_leads": total_leads,
            "by_date": date_stats,
            "by_source": source_stats,
            "by_status": status_stats
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/stats/top-sources', methods=['GET'])
#@login_required
def get_top_sources():
    """Get top performing lead sources"""
    try:
        # Get time range parameters (defaults to all time)
        days = request.args.get('days', None, type=int)
        limit = request.args.get('limit', 5, type=int)

        # Build query
        query = db.session.query(
            Lead.source,
            db.func.count(Lead.lead_id).label('count')
        ).filter(
            Lead.deleted == False,
            Lead.source.isnot(None),
            Lead.source != ''
        )

        # Add date filter if specified
        if days:
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            query = query.filter(Lead.created_at >= start_date)

        # Complete query with group by and order
        results = query.group_by(
            Lead.source
        ).order_by(
            db.func.count(Lead.lead_id).desc()
        ).limit(limit).all()

        # Format results
        top_sources = [
            {"source": source, "count": count}
            for source, count in results
        ]

        return jsonify({
            "top_sources": top_sources
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/leads/<string:lead_id>/restore', methods=['POST'])
#@login_required
def restore_lead(lead_id):
    """Restore a soft-deleted lead"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/{lead_id}/restore by user_id={user_id}, username={username}')
    success, message = LeadController.restore_lead(lead_id, current_user)
    return jsonify({'success': success, 'message': message})

@lead_bp.route('/leads/restore-multiple', methods=['POST'])
#@login_required
def restore_multiple_leads():
    """Restore multiple soft-deleted leads"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/restore-multiple by user_id={user_id}, username={username}')
    lead_ids = request.json.get('lead_ids', [])
    success, message = LeadController.restore_multiple_leads(lead_ids, current_user)
    return jsonify({'success': success, 'message': message})

@lead_bp.route('/leads/deleted', methods=['GET'])
# #@login_required
def view_deleted_leads():
    """View all soft-deleted leads"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/deleted by user_id={user_id}, username={username}')
    leads = Lead.query.filter_by(deleted=True).order_by(Lead.deleted_at.desc()).all()
    return render_template('deleted_leads.html', leads=leads)

@lead_bp.route('/leads/<string:lead_id>/permanent-delete', methods=['POST'])
# #@login_required
@role_required('admin', 'developer')
def permanent_delete_lead(lead_id):
    """Permanently delete a lead from the database (hard delete)"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/{lead_id}/permanent-delete by user_id={user_id}, username={username}')
    try:
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
        db.session.delete(lead)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lead permanently deleted.'})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Error permanently deleting lead: {str(e)}'}), 500


@lead_bp.route('/api/user/deduct_credit', methods=['POST'])
@login_required
@credit_required(cost=1)
def api_deduct_credit():
    """API endpoint to deduct 1 credit from the current user's account."""
    # If we reach this point, the credit_required decorator has already
    # checked the subscription, credits, and successfully deducted 1 credit.
    # So, we just need to return a success response.
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/user/deduct_credit by user_id={user_id}, username={username}')
    return jsonify({
        "status": "success",
        "message": "1 credit deducted successfully.",
    }), 200


@lead_bp.route('/api/lead_scrape', methods=['POST'])
@login_required
def api_search_leads():
    data = request.get_json()
    # logging.debug(f"[IN] /api/search_leads data: {data}")
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/lead_scrape by user_id={user_id}, username={username}')
    industry = data.get("industry", "")
    location = data.get("location", "")
    results = LeadController.search_leads_by_industry_location(industry, location, current_user)
    # logging.debug(f"[OUT] /api/search_leads results: {results}")
    return jsonify(results)

@lead_bp.route('/api/lead_scrape_old', methods=['POST'])
@login_required # Ensure user is logged in
# @credit_required(cost=1)
@filter_lead_data_by_plan()
def api_search_leads_old():
    data = request.get_json()
    # logging.debug(f"[IN] /api/search_leads data: {data}")
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/lead_scrape_old by user_id={user_id}, username={username}')
    industry = data.get("industry", "")
    location = data.get("location", "")
    results = LeadController.search_leads_by_industry_location_old(industry, location)
    # logging.debug(f"[OUT] /api/search_leads results: {results}")
    return results



@lead_bp.route('/api/industries', methods=['GET'])
@login_required
def get_industries():
    """Get all unique industries (normalized) for selection in frontend"""
    try:
        user_id = getattr(current_user, 'user_id', None)
        username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
        current_app.logger.info(f'Route hit: /api/industires by user_id={user_id}, username={username}')

        # Use controller logic if available, else query directly
        industries = LeadController.get_unique_industries() if hasattr(LeadController, 'get_unique_industries') else None
        if industries is None:
            # Fallback: query directly
            industries_query = db.session.query(Lead.industry).filter(
                Lead.industry.isnot(None),
                Lead.industry != '',
                Lead.deleted == False
            ).distinct().all()
            industries = [row[0] for row in industries_query]
        # Normalize: strip, lower, remove duplicates, sort
        normalized = sorted(set(i.strip() for i in industries if i and i.strip()))
        current_app.logger.info('Search industries successfully')
        return jsonify({
            "total": len(normalized),
            "industries": normalized
        })
    except Exception as e:
        current_app.logger.info('Search industries failed')
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/leads/batch', methods=['PUT'])
def batch_update_leads():
    """Batch update multiple leads via API"""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Request body must be a list of lead objects"}), 400

    success_count = 0
    skipped_count = 0
    failed = []
    details = []

    for item in data:
        lead_id = item.get('lead_id')
        if not lead_id:
            failed.append({"lead_id": None, "error": "Missing lead_id"})
            continue
        lead = Lead.query.filter_by(lead_id=lead_id).first()
        if not lead:
            failed.append({"lead_id": lead_id, "error": "Lead not found"})
            continue

        changed = False
        unchanged_fields = []
        changed_fields = []
        try:
            for key, value in item.items():
                if key != 'lead_id' and hasattr(lead, key):
                    current_value = getattr(lead, key)
                    if current_value != value:
                        setattr(lead, key, value)
                        changed = True
                        changed_fields.append(key)
                    else:
                        unchanged_fields.append(key)
            if changed:
                db.session.commit()
                success_count += 1
                details.append({
                    "lead_id": lead_id,
                    "status": "updated",
                    "changed_fields": changed_fields
                })
            else:
                skipped_count += 1
                details.append({
                    "lead_id": lead_id,
                    "status": "skipped",
                    "unchanged_fields": unchanged_fields
                })
        except Exception as e:
            db.session.rollback()
            failed.append({"lead_id": lead_id, "error": str(e)})

    return jsonify({
        "updated": success_count,
        "skipped": skipped_count,
        "failed": failed,
        "details": details,
        "message": f"Batch update complete. Updated: {success_count}, Skipped (no change): {skipped_count}, Failed: {len(failed)}"
    })

@lead_bp.route('/api/leads/delete-multiple', methods=['POST'])
@login_required
def api_delete_multiple_leads():
    """API endpoint: Soft delete (mark as deleted) multiple leads at once."""
    try:
        # support two formats: array of object, or direct object
        data = request.get_json()
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'lead_ids' in data[0]:
            lead_ids = data[0]['lead_ids']
        elif isinstance(data, dict) and 'lead_ids' in data:
            lead_ids = data['lead_ids']
        else:
            return jsonify({"status": "error", "message": "Invalid request body. Must be array of object with 'lead_ids' or object with 'lead_ids'."}), 400
        if not lead_ids or not isinstance(lead_ids, list):
            return jsonify({"status": "error", "message": "No lead_ids provided."}), 400
        # use the same controller

        user_id = getattr(current_user, 'user_id', None)
        username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
        current_app.logger.info(f'Route hit: /api/leads/delete-multiple by user_id={user_id}, username={username}')
        success, message = LeadController.delete_multiple_leads(lead_ids, current_user)
        if success:
            return jsonify({"status": "success", "message": message or f"{len(lead_ids)} leads deleted successfully"})
        else:
            return jsonify({"status": "error", "message": message or "Failed to delete leads"}), 400
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@lead_bp.route('/api/leads/enrich-multiple', methods=['POST'])
@login_required
def enrich_multiple_leads():
    data = request.get_json()
    leads = data.get('leads', [])
    if not leads or not isinstance(leads, list):
        return jsonify({"error": "No leads provided"}), 400

    results = []
    for lead_data in leads:
        lead_id = lead_data.get('lead_id')
        user_id = lead_data.get('user_id')
        if not lead_id:
            results.append({"error": "Missing lead_id", "lead_data": lead_data})
            continue
        # Update only null/empty fields using add_or_update_lead_by_match
        success, message = LeadController.add_or_update_lead_by_match(lead_data)
        results.append({
            "lead_id": lead_id,
            "user_id": user_id,
            "success": success,
            "message": message
        })

    return jsonify({"results": results})

@lead_bp.route('/api/leads/summary', methods=['GET'])
@login_required
def leads_summary():
    total = Lead.query.filter_by(deleted=False).count()
    status_counts = db.session.query(Lead.status, db.func.count(Lead.lead_id)).filter_by(deleted=False).group_by(Lead.status).all()
    return jsonify({
        "total": total,
        "status_counts": {status: count for status, count in status_counts}
    })

@lead_bp.route('/leads/edited', methods=['GET'])
@login_required
def view_edited_leads():
    """View all edited leads (pending drafts)"""
    from models.user_model import User
    from models.edit_lead_drafts_model import EditLeadDraft
    from models.lead_model import Lead
    # Only show drafts that are not deleted and in draft/review phase
    drafts = EditLeadDraft.query.filter_by(is_deleted=False).filter(EditLeadDraft.phase.in_(['draft', 'review'])).order_by(EditLeadDraft.updated_at.desc()).all()
    rows = []
    for draft in drafts:
        original = Lead.query.filter_by(lead_id=draft.lead_id).first()
        edit_user = User.query.get(draft.user_id) if draft.user_id else None
        rows.append({'original': original, 'edit': draft, 'edit_user': edit_user})
    return render_template('edited_leads.html', leads=rows)

@lead_bp.route('/leads/<string:lead_id>/edit', methods=['POST'])
@login_required
@role_required('admin', 'developer', 'user')
def edit_lead_api(lead_id):
    """Edit lead - Admin, Developer, User. Save to EditLeadDraft, not to Lead."""
    from datetime import datetime
    from models.edit_lead_drafts_model import EditLeadDraft
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/{lead_id}/edit by user_id={user_id}, username={username}')
    lead = Lead.query.filter_by(lead_id=lead_id, deleted=False).first_or_404()
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    try:
        user_id = (
            getattr(current_user, 'id', None) or
            getattr(current_user, 'user_id', None) or
            data.get('user_id')
        )
        if not user_id:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'message': 'Missing user_id'}), 400
            else:
                flash('Missing user_id', 'danger')
                return redirect(url_for('lead.view_leads'))
        try:
            user_id = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'message': 'Invalid user_id format'}), 400
            else:
                flash('Invalid user_id format', 'danger')
                return redirect(url_for('lead.view_leads'))
        data = dict(data)
        if 'revenue' in data and data['revenue']:
            revenue_str = str(data['revenue']).replace(',', '.')
            try:
                data['revenue'] = float(revenue_str)
            except ValueError:
                data['revenue'] = None
        draft = EditLeadDraft.query.filter_by(lead_id=lead_id, user_id=user_id, is_deleted=False).first()
        if not draft:
            draft = EditLeadDraft(
                lead_id=lead_id,
                user_id=user_id,
                draft_data=data,
                phase='draft'
            )
            draft.updated_at = datetime.now(timezone.utc)
            db.session.add(draft)
        else:
            draft.draft_data = data
            draft.updated_at = datetime.now(timezone.utc)
            draft.phase = 'draft'
        db.session.commit()
        current_app.logger.info(f"[Lead] Draft saved successfully: {lead_id}")
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({'success': True, 'message': 'Draft saved successfully'})
        else:
            flash('Draft saved successfully', 'success')
            return redirect(url_for('lead.view_leads'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Lead] Error saving draft: {str(e)}")
        import traceback
        print(traceback.format_exc())
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'message': str(e)}), 500
        else:
            flash(f'Error saving draft: {str(e)}', 'danger')
            return redirect(url_for('lead.view_leads'))

@lead_bp.route('/leads/<string:lead_id>/apply', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def apply_edited_lead(lead_id):
    """Apply changes: finalize the edit, salin data dari draft ke Lead, hapus draft."""
    from models.edit_lead_drafts_model import EditLeadDraft
    from models.lead_model import Lead
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /leads/{lead_id}/apply by user_id={user_id}, username={username}')
    draft = EditLeadDraft.query.filter_by(lead_id=lead_id, is_deleted=False).first()
    lead = Lead.query.filter_by(lead_id=lead_id).first()
    if not draft or not lead:
        return jsonify({'success': False, 'message': 'Draft or lead not found.'}), 404
    try:
        for key, value in draft.draft_data.items():
            if hasattr(lead, key) and key not in ['lead_id', 'created_at', 'deleted', 'deleted_at']:
                col_type = type(getattr(lead, key))
                if value == '' and col_type in [int, float, type(None)]:
                    setattr(lead, key, None)
                else:
                    setattr(lead, key, value)
        db.session.delete(draft)
        db.session.commit()
        current_app.logger.info(f"[Lead] Changes applied and lead finalized: {lead_id}")
        return jsonify({'success': True, 'message': 'Changes applied and lead finalized.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Lead] Error applying changes: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@lead_bp.route('/api/draft/delete', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def delete_draft_api():
    """Permanently delete a draft by lead_id (API)."""
    from models.edit_lead_drafts_model import EditLeadDraft
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/draft/delete by user_id={user_id}, username={username}')
    data = request.get_json() or {}
    lead_id = data.get('lead_id')
    print('DEBUG: lead_id param:', lead_id)
    draft = EditLeadDraft.query.filter_by(lead_id=lead_id).first()
    print('DEBUG: draft found:', draft)
    if not draft:
        return jsonify({'success': False, 'message': 'Draft not found.'}), 404
    try:
        db.session.delete(draft)
        db.session.commit()
        print('DEBUG: draft permanently deleted')
        current_app.logger.info(f"[Lead] Draft permanently deleted: {lead_id}")
        return jsonify({'success': True, 'message': 'Draft permanently deleted.'})
    except Exception as e:
        db.session.rollback()
        print('DEBUG: error:', e)
        current_app.logger.error(f"[Lead] Error deleting draft: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@lead_bp.route('/api/leads/multiple', methods=['GET'])
# @login_required
def get_leads_by_multiple_ids():
    """Get details of multiple leads by comma-separated IDs in query param 'lead_ids'"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/multiple by user_id={user_id}, username={username}')
    lead_ids_param = request.args.get('lead_ids', '')
    if not lead_ids_param:
        return jsonify({"error": "No lead_ids provided"}), 400
    lead_ids = [lid.strip() for lid in lead_ids_param.split(',') if lid.strip()]
    if not lead_ids:
        return jsonify({"error": "No valid lead_ids provided"}), 400
    leads = Lead.query.filter(Lead.lead_id.in_(lead_ids), Lead.deleted == False).all()
    results = [lead.to_dict() for lead in leads]
    return jsonify({"results": results})
#Drafts API
@lead_bp.route('/api/leads/search-results', methods=['POST'])
@login_required
def save_search_results():
    """Save search results with search criteria as drafts"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"error": "Request body must be a list of leads with search criteria"}), 400

        # Extract search criteria from the first lead (they should all have the same criteria)
        search_criteria = data[0].get('search_criteria', {}) if data else {}
        industry = search_criteria.get('industry', '')
        location = search_criteria.get('location', '')
        timestamp = search_criteria.get('timestamp')

        # Generate a unique search session ID for this batch of drafts
        search_session_id = str(uuid.uuid4())

        # Create a draft for each lead
        drafts = []
        skipped = []
        for idx, lead_data in enumerate(data):
            lead_id = lead_data.get('lead_id')
            if not lead_id:
                continue

            # Check if draft already exists for this lead and user
            existing_draft = UserLeadDraft.query.filter_by(
                user_id=current_user.user_id,
                lead_id=lead_id,
                is_deleted=False
            ).first()

            if existing_draft:
                skipped.append({
                    'lead_id': lead_id,
                    'reason': 'Draft already exists',
                    'existing_draft_id': existing_draft.draft_id
                })
                continue

            # Add search criteria to draft data
            draft_data = {
                **lead_data,
                'search_criteria': {
                    'industry': industry,
                    'location': location,
                    'timestamp': timestamp,
                    'source': 'enhancement_page',
                    'search_session_id': search_session_id,
                    'search_index': idx
                }
            }

            # Create draft with explicit draft_id
            draft = UserLeadDraft(
                user_id=current_user.user_id,
                lead_id=lead_id,
                draft_data=draft_data,
                change_summary=f"Search result for industry: {industry}, location: {location}",
                phase='draft',
                status='pending'
            )
            # Ensure draft_id is set (though it should be auto-generated by the model)
            if not draft.draft_id:
                draft.draft_id = str(uuid.uuid4())

            db.session.add(draft)
            drafts.append(draft)

        # Save all drafts
        db.session.commit()

        current_app.logger.info(f"[Lead] Saved {len(drafts)} search results as drafts, skipped {len(skipped)} existing drafts")
        return jsonify({
            "message": f"Saved {len(drafts)} search results as drafts, skipped {len(skipped)} existing drafts",
            "search_session_id": search_session_id,
            "search_criteria": {
                "industry": industry,
                "location": location,
                "timestamp": timestamp
            },
            "drafts": [{
                **draft.to_dict(),
                'search_index': draft.draft_data.get('search_criteria', {}).get('search_index')
            } for draft in drafts],
            "skipped": skipped
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Lead] Error saving search results: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/leads/search-session/<string:search_session_id>', methods=['GET'])
@login_required
def get_search_session_drafts(search_session_id):
    """Get all drafts from a specific search session"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/search-session/{search_session_id} by user_id={user_id}, username={username}')
    drafts = UserLeadDraft.query.filter(
        UserLeadDraft.user_id == current_user.user_id,
        UserLeadDraft.is_deleted == False,
        UserLeadDraft.draft_data['search_criteria']['search_session_id'].astext == search_session_id
    ).order_by(
        UserLeadDraft.draft_data['search_criteria']['search_index'].astext.cast(Integer)
    ).all()

    if not drafts:
        return jsonify({
            "message": "No drafts found for this search session",
            "search_session_id": search_session_id,
            "drafts": []
        }), 200

    # Extract search criteria from first draft
    first_draft = drafts[0]
    search_criteria = first_draft.draft_data.get('search_criteria', {})

    return jsonify({
        "message": f"Found {len(drafts)} drafts for this search session",
        "search_session_id": search_session_id,
        "search_criteria": {
            "industry": search_criteria.get('industry'),
            "location": search_criteria.get('location'),
            "timestamp": search_criteria.get('timestamp')
        },
        "drafts": [draft.to_dict() for draft in drafts]
    })

# Drafts API
@lead_bp.route('/api/leads/search-drafts', methods=['GET'])
@login_required
def get_search_drafts():
    """Get drafts by search criteria (industry and/or location)"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/search-drafts by user_id={user_id}, username={username}')
    industry = request.args.get('industry')
    location = request.args.get('location')

    if not industry and not location:
        return jsonify({"error": "At least one of industry or location must be provided"}), 400

    query = UserLeadDraft.query.filter(
        UserLeadDraft.user_id == current_user.user_id,
        UserLeadDraft.is_deleted == False
    )

    if industry:
        query = query.filter(
            UserLeadDraft.draft_data['search_criteria']['industry'].astext == industry
        )
    if location:
        query = query.filter(
            UserLeadDraft.draft_data['search_criteria']['location'].astext == location
        )

    # Group by search_session_id to get unique search sessions
    drafts = query.order_by(UserLeadDraft.created_at.desc()).all()

    # Group drafts by search_session_id
    sessions = {}
    for draft in drafts:
        session_id = draft.draft_data.get('search_criteria', {}).get('search_session_id')
        if session_id:
            if session_id not in sessions:
                sessions[session_id] = {
                    "search_session_id": session_id,
                    "search_criteria": {
                        "industry": draft.draft_data['search_criteria'].get('industry'),
                        "location": draft.draft_data['search_criteria'].get('location'),
                        "timestamp": draft.draft_data['search_criteria'].get('timestamp')
                    },
                    "drafts": [],
                    "created_at": draft.created_at.isoformat()
                }
            sessions[session_id]["drafts"].append(draft.to_dict())

    # Convert to list and sort by created_at
    sessions_list = list(sessions.values())
    sessions_list.sort(key=lambda x: x["created_at"], reverse=True)

    return jsonify({
        "message": f"Found {len(sessions_list)} search sessions",
        "sessions": sessions_list
    })

@lead_bp.route('/api/leads/recent-searches', methods=['GET'])
@login_required
def get_recent_search_sessions():
    """Get recent search sessions with their drafts"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/recent-searches by user_id={user_id}, username={username}')
    limit = request.args.get('limit', 5, type=int)

    # Get unique search sessions ordered by most recent
    drafts = UserLeadDraft.query.filter(
        UserLeadDraft.user_id == current_user.user_id,
        UserLeadDraft.is_deleted == False
    ).order_by(
        UserLeadDraft.created_at.desc()
    ).all()

    # Group by search_session_id
    sessions = {}
    for draft in drafts:
        session_id = draft.draft_data.get('search_criteria', {}).get('search_session_id')
        if session_id and session_id not in sessions:
            sessions[session_id] = {
                "search_session_id": session_id,
                "search_criteria": {
                    "industry": draft.draft_data['search_criteria'].get('industry'),
                    "location": draft.draft_data['search_criteria'].get('location'),
                    "timestamp": draft.draft_data['search_criteria'].get('timestamp')
                },
                "drafts": [],
                "created_at": draft.created_at.isoformat()
            }
            # Only add drafts if we haven't reached the limit
            if len(sessions) <= limit:
                sessions[session_id]["drafts"].append(draft.to_dict())

    # Convert to list and sort by created_at
    sessions_list = list(sessions.values())
    sessions_list.sort(key=lambda x: x["created_at"], reverse=True)
    sessions_list = sessions_list[:limit]

    return jsonify({
        "message": f"Found {len(sessions_list)} recent search sessions",
        "sessions": sessions_list
    })

@lead_bp.route('/api/leads/drafts', methods=['GET'])
@login_required
def get_user_drafts():
    """Get all drafts for the current user"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/drafts by user_id={user_id}, username={username}')
    drafts = UserLeadDraft.query.filter_by(user_id=current_user.user_id, is_deleted=False).all()
    return jsonify([d.to_dict() for d in drafts])

@lead_bp.route('/api/leads/drafts/<string:draft_id>', methods=['GET'])
@login_required
def get_draft(draft_id):
    """Get a specific draft by ID"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/drafts/{draft_id} by user_id={user_id}, username={username}')
    draft = UserLeadDraft.query.filter_by(draft_id=draft_id, is_deleted=False).first()
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
    return jsonify(draft.to_dict())

def deep_merge_dict(original, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            original[key] = deep_merge_dict(original.get(key, {}), value)
        else:
            original[key] = value
    return original

@lead_bp.route('/api/leads/drafts/<string:draft_id>', methods=['PUT'])
@login_required
def update_draft(draft_id):
    """Update a specific draft"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/drafts/{draft_id} by user_id={user_id}, username={username}')
    draft = UserLeadDraft.query.filter_by(draft_id=draft_id, is_deleted=False).first()
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
    data = request.json
    if 'draft_data' in data:
        existing_data = draft.draft_data or {}
        new_data = data['draft_data']

        merged = deep_merge_dict(existing_data, new_data)
        draft.draft_data = dict(merged)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(draft, "draft_data")

    if 'change_summary' in data:
        draft.change_summary = data['change_summary']
    draft.updated_at = datetime.now(timezone.utc)
    draft.increment_version()
    db.session.commit()
    return jsonify(draft.to_dict())

@lead_bp.route('/api/leads/drafts/<string:draft_id>', methods=['DELETE'])
@login_required
def delete_draft(draft_id):
    """Soft delete a draft"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/drafts/{draft_id} by user_id={user_id}, username={username}')
    draft = UserLeadDraft.query.filter_by(draft_id=draft_id, is_deleted=False).first()
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
    draft.is_deleted = True
    db.session.commit()
    return jsonify({"message": "Draft deleted"})

@lead_bp.route('/api/leads/drafts', methods=['POST'])
@login_required
def create_draft():
    """Create a new draft"""
    from models.lead_model import Lead
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /api/leads/drafts by user_id={user_id}, username={username}')
    data = request.json
    lead_id = data.get('lead_id')
    draft_data = data.get('draft_data')

    # If lead_id is not provided, try to find it in the leads table using company (and optionally other fields)
    if not lead_id:
        draft_data = data.get('draft_data', {})
        company = data.get('company') or draft_data.get('company')
        street = data.get('street') or draft_data.get('street')
        city = data.get('city') or draft_data.get('city')
        state = data.get('state') or draft_data.get('state')
        company_phone = data.get('company_phone') or draft_data.get('company_phone')
        website = data.get('website') or draft_data.get('website')
        if not company:
            current_app.logger.warning(f"[Draft] Cannot find or generate lead_id: company is missing. Data: {data}")
            return jsonify({"error": "company is required to find or generate lead_id"}), 400
        # Try to find the lead in the leads table (match on company, street, city, state, company_phone, website)
        lead = Lead.query.filter_by(
            company=company,
            # street=street,
            # city=city,
            # state=state,
            # company_phone=company_phone,
            # website=website
        ).first()
        if lead:
            lead_id = lead.lead_id
            current_app.logger.info(f"[Draft] Found existing lead_id: {lead_id} for company='{company}'")
        # else:
        #     lead_id = Lead.generate_lead_id(
        #         company=company,
        #         street=street,
        #         city=city,
        #         state=state,
        #         company_phone=company_phone,
        #         website=website
        #     )
        #     current_app.logger.info(f"[Draft] No existing lead found, generated lead_id: {lead_id} using company='{company}', street='{street}', city='{city}', state='{state}', company_phone='{company_phone}', website='{website}'")
    else:
        current_app.logger.info(f"[Draft] lead_id provided in request: {lead_id}")

    if not lead_id or not draft_data:
        current_app.logger.warning(f"[Draft] Missing lead_id or draft_data. lead_id: {lead_id}, draft_data: {draft_data}")
        return jsonify({"error": "lead_id and draft_data are required (or enough data to generate lead_id)"}), 400

    current_app.logger.info(f"[Draft] Creating draft with lead_id: {lead_id} for user_id: {current_user.user_id}")
    try:
        draft = UserLeadDraft(
            user_id=current_user.user_id,
            lead_id=lead_id,
            draft_data=draft_data,
            change_summary=data.get('change_summary')
        )
        db.session.add(draft)
        db.session.commit()
        current_app.logger.info(f"[Draft] Draft created successfully for lead_id: {lead_id}")
        return jsonify(draft.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Draft] Error creating draft for lead_id: {lead_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/drafts')
@login_required
def view_drafts():
    """Render the drafts view template"""
    user_id = getattr(current_user, 'user_id', None)
    username = getattr(current_user, 'username', getattr(current_user, 'email', 'anonymous'))
    current_app.logger.info(f'Route hit: /drafts by user_id={user_id}, username={username}')
    return render_template('leads/view_drafts.html')