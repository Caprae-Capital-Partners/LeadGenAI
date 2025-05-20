from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify, send_file
from controllers.lead_controller import LeadController
from controllers.upload_controller import UploadController
from controllers.export_controller import ExportController
from models.lead_model import db, Lead
from flask_login import login_required, current_user
from utils.decorators import role_required
import csv
from io import StringIO, BytesIO
import logging
import datetime
import pandas as pd
import io
from werkzeug.exceptions import NotFound
from sqlalchemy import or_, and_

# Create blueprint
lead_bp = Blueprint('lead', __name__)

@lead_bp.route('/')
@login_required
def index():
    """Redirect to view leads page"""
    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/form')
@login_required
def form():
    """Display form to add new lead"""
    return render_template('form.html')

@lead_bp.route('/submit', methods=['POST'])
# #@login_required
@role_required('admin', 'developer')
def submit():
    """Submit new lead - Admin and Developer only"""
    success, message = LeadController.create_lead(request.form)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/upload_page')
@login_required
def upload_page():
    """Display CSV upload page"""
    return render_template('upload.html')

@lead_bp.route('/upload', methods=['POST'])
# #@login_required
def upload_csv():
    """Handle CSV file upload"""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('lead.upload_page'))

    file = request.files['file']
    if file.filename == '':
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
        flash(f'Error during upload: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/view_leads')
@login_required
def view_leads():
    # Ambil parameter dari query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    company = request.args.get('company', '')
    status = request.args.get('status', '')

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
    )

@lead_bp.route('/edit/<int:lead_id>', methods=['GET', 'POST'])
#@login_required
@role_required('admin', 'developer')
def edit_lead(lead_id):
    """Edit lead - Admin and Developer only"""
    if request.method == 'POST':
        success, message = LeadController.update_lead(lead_id, request.form)

        if success:
            flash(message, 'success')
            return redirect(url_for('lead.view_leads'))
        else:
            flash(message, 'danger')

    lead = LeadController.get_lead_by_id(lead_id)
    return render_template('edit_lead.html', lead=lead)

@lead_bp.route('/update_status/<int:lead_id>', methods=['POST'])
#@login_required
def update_status(lead_id):
    """Update lead status - All roles can update status"""
    try:
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
        new_status = request.form.get('status')
        if new_status:
            lead.status = new_status
            db.session.commit()
            flash('Status updated successfully', 'success')
        else:
            flash('No status provided', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/leads/<int:lead_id>/delete', methods=['POST'])
#@login_required
@role_required('admin', 'developer')
def delete_lead(lead_id):
    """Soft delete lead - Admin and Developer only"""
    try:
        success, message = LeadController.delete_lead(lead_id, current_user)
        return jsonify({'success': success, 'message': message})
    except NotFound:
        return jsonify({'success': False, 'message': 'Lead not found or already deleted.'}), 404
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@lead_bp.route('/leads/delete-multiple', methods=['POST'])
#@login_required
@role_required('admin', 'developer')
def delete_multiple_leads():
    """Soft delete multiple leads - Admin and Developer only"""
    try:
        lead_ids = request.json.get('lead_ids', [])
        if not lead_ids:
            return jsonify({'success': False, 'message': 'No leads selected'}), 400
        success, message = LeadController.delete_multiple_leads(lead_ids, current_user)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@lead_bp.route('/api/leads', methods=['GET'])
#@login_required
def get_leads():
    """API endpoint to get all leads with pagination, search and filtering"""
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

    return jsonify(results)

@lead_bp.route('/api/leads', methods=['POST'])
#@login_required
@role_required('admin', 'developer')
def create_lead():
    """Create a new lead via API - Admin and Developer only"""
    data = request.json

    company = data.get('company')
    owner_email = data.get('owner_email')

    if not company:
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
        return jsonify({
            "message": "Lead already exists, skipping creation.",
            "lead": existing_lead.to_dict(),
            "skipped": True
        }), 200

    lead = Lead(**data)
    try:
        db.session.add(lead)
        db.session.commit()

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
        # Log the error for debugging
        print(f"API create_lead error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/api/leads/<int:lead_id>', methods=['PUT'])
#@login_required
@role_required('admin', 'developer')
def update_lead_api(lead_id):
    """Update a lead via API - Admin and Developer only"""
    lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
    data = request.json

    try:
        for key, value in data.items():
            setattr(lead, key, value)
        db.session.commit()
        return jsonify({"message": "Lead updated successfully", "lead": lead.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/api/leads/<int:lead_id>/status', methods=['PUT'])
#@login_required
def update_status_api(lead_id):
    """Update a lead's status via API - All roles can update status"""
    lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
    data = request.json

    if 'status' not in data:
        return jsonify({"error": "Status field is required"}), 400

    try:
        lead.status = data['status']
        db.session.commit()
        return jsonify({"message": "Status updated successfully", "lead": lead.to_dict()})
    except Exception as e:
        db.session.rollback()
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

@lead_bp.route('/api/upload_leads', methods=['POST'])
# #@login_required
def api_upload_leads():
    """API endpoint to upload multiple leads"""
    try:
        data = request.get_json()

        if not data or not isinstance(data, list) or len(data) == 0:
            return jsonify({"status": "error", "message": "Invalid data format. Expected a list of leads"}), 400

        # Initial validation - only require company field
        required_fields = ['company', 'website', 'owner_linkedin']
        valid_leads = []
        invalid_indices = []

        # Pre-validate all leads at once
        for i, lead in enumerate(data):
            # Check if data uses old 'email' field format and convert to owner_email
            if 'email' in lead and 'owner_email' not in lead:
                lead['owner_email'] = lead.pop('email')

            if all(field in lead for field in required_fields):
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

                # Company validation only
                if UploadController.is_valid_company(lead['company']):
                    # Set default values for required fields
                    if 'search_keyword' not in lead:
                        lead['search_keyword'] = {}  # Empty JSON object as default

                    # Truncate fields to match database limitations
                    if hasattr(Lead, 'truncate_fields'):
                        lead = Lead.truncate_fields(lead)
                    valid_leads.append(lead)
                else:
                    invalid_indices.append(i)
            else:
                invalid_indices.append(i)

        # Process all valid leads using add_or_update_lead_by_match
        added_new = 0
        updated = 0
        skipped = 0
        errors = 0

        for lead_data in valid_leads:
            try:
                success, message = LeadController.add_or_update_lead_by_match(lead_data)
                if success:
                    if "updated successfully" in message:
                        updated += 1
                    elif "already up to date" in message:
                        updated += 1  # Count as updated but wasn't changed
                    else:
                        added_new += 1
                else:
                    if "already in use" in message or "already exists" in message:
                        skipped += 1
                    else:
                        errors += 1
            except Exception as e:
                errors += 1
                print(f"Error processing lead: {str(e)}")

        return jsonify({
            "status": "success",
            "message": f"Upload Complete! Added: {added_new}, Updated: {updated}, Skipped: {skipped}, Errors: {errors}",
            "stats": {
                "added_new": added_new,
                "updated": updated,
                "skipped_duplicates": skipped,
                "errors": errors,
                "invalid_indices": invalid_indices[:10] if invalid_indices else []
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Error during upload: {str(e)}"
        }), 500

@lead_bp.route('/api/leads/<int:lead_id>', methods=['DELETE'])
#@login_required
@role_required('admin', 'developer')
def delete_lead_api(lead_id):
    """Soft delete a lead via API - Admin and Developer only"""
    try:
        # Use the controller method which implements soft delete
        success, message = LeadController.delete_lead(lead_id, current_user=current_user)
        if success:
            return jsonify({"message": "Lead successfully deleted"})
        else:
            return jsonify({"error": message}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/leads/<int:lead_id>', methods=['GET'])
#@login_required
def get_lead_by_id(lead_id):
    """Get detail of a single lead by ID"""
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

@lead_bp.route('/leads/<lead_id>/restore', methods=['POST'])
#@login_required
def restore_lead(lead_id):
    """Restore a soft-deleted lead"""
    success, message = LeadController.restore_lead(lead_id, current_user)
    return jsonify({'success': success, 'message': message})

@lead_bp.route('/leads/restore-multiple', methods=['POST'])
#@login_required
def restore_multiple_leads():
    """Restore multiple soft-deleted leads"""
    lead_ids = request.json.get('lead_ids', [])
    success, message = LeadController.restore_multiple_leads(lead_ids, current_user)
    return jsonify({'success': success, 'message': message})

@lead_bp.route('/leads/deleted', methods=['GET'])
# #@login_required
def view_deleted_leads():
    """View all soft-deleted leads"""
    leads = Lead.query.filter_by(deleted=True).order_by(Lead.deleted_at.desc()).all()
    return render_template('deleted_leads.html', leads=leads)

@lead_bp.route('/leads/<int:lead_id>/permanent-delete', methods=['POST'])
# #@login_required
@role_required('admin', 'developer')
def permanent_delete_lead(lead_id):
    """Permanently delete a lead from the database (hard delete)"""
    try:
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
        db.session.delete(lead)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lead permanently deleted.'})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Error permanently deleting lead: {str(e)}'}), 500


@lead_bp.route('/api/lead_scrape', methods=['POST'])
def api_search_leads():
    data = request.get_json()
    # logging.debug(f"[IN] /api/search_leads data: {data}")
    industry = data.get("industry", "")
    location = data.get("location", "")
    results = LeadController.search_leads_by_industry_location(industry, location)
    # logging.debug(f"[OUT] /api/search_leads results: {results}")
    return jsonify(results)

@lead_bp.route('/api/industries', methods=['GET'])
# #@login_required
def get_industries():
    """Get all unique industries (normalized) for selection in frontend"""
    try:
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
        return jsonify({
            "total": len(normalized),
            "industries": normalized
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/leads/enrichment-status', methods=['GET'])
#@login_required
def get_leads_enrichment_status():
    """Get enrichment status for leads"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Build base query
        query = Lead.query.filter(Lead.deleted == False)

        # Get leads with their enrichment status
        leads = query.paginate(page=page, per_page=per_page)

        # Check enrichment status for each lead
        enriched_leads = []
        for lead in leads.items:
            lead_dict = lead.to_dict()

            # Check required fields
            required_fields = {
                'owner_email': bool(lead.owner_email),
                'owner_phone_number': bool(lead.owner_phone_number),
                'website': bool(lead.website),
                'owner_linkedin': bool(lead.owner_linkedin)
            }

            # Calculate enrichment status
            missing_fields = [field for field, has_value in required_fields.items() if not has_value]
            is_fully_enriched = len(missing_fields) == 0

            # Add enrichment info to lead data
            lead_dict.update({
                'enrichment_status': {
                    'is_fully_enriched': is_fully_enriched,
                    'missing_fields': missing_fields,
                    'last_enriched_at': lead.updated_at.isoformat() if lead.updated_at else None,
                    'needs_enrichment': not is_fully_enriched
                }
            })

            enriched_leads.append(lead_dict)

        return jsonify({
            "total": leads.total,
            "pages": leads.pages,
            "current_page": page,
            "per_page": per_page,
            "leads": enriched_leads
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/leads/<int:lead_id>/enrich', methods=['POST'])
# #@login_required
def enrich_lead(lead_id):
    """Enrich a single lead's data"""
    try:
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()

        # Check if lead needs enrichment
        required_fields = {
            'owner_email': bool(lead.owner_email),
            'owner_phone_number': bool(lead.owner_phone_number),
            'website': bool(lead.website),
            'owner_linkedin': bool(lead.owner_linkedin)
        }

        missing_fields = [field for field, has_value in required_fields.items() if not has_value]

        if not missing_fields:
            return jsonify({
                "message": "Lead already fully enriched",
                "lead": lead.to_dict()
            })

        # TODO: Implement enrichment logic here
        # This would be where you call your scraping service

        # Update lead with new data
        lead.updated_at = datetime.datetime.now()
        db.session.commit()

        return jsonify({
            "message": "Lead enriched successfully",
            "lead": lead.to_dict(),
            "enriched_fields": missing_fields
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@lead_bp.route('/api/leads/check-missing', methods=['POST'])
# #@login_required
def check_missing_fields():
    """
    Check which required fields are missing for a batch of leads.
    Request body: { "lead_ids": [1, 2, 3, ...] }
    Response: {
      "results": [
        {"lead_id": 1, "missing_fields": ["owner_email", ...], "status": "ok"},
        {"lead_id": 2, "missing_fields": [], "status": "ok"},
        {"lead_id": 3, "missing_fields": null, "status": "not_found"}
      ]
    }
    """
    lead_ids = request.json.get('lead_ids', [])
    required_fields = ['owner_email', 'owner_phone_number', 'website', 'owner_linkedin']
    results = []
    for lead_id in lead_ids:
        lead = Lead.query.get(lead_id)
        if not lead:
            results.append({
                "lead_id": lead_id,
                "missing_fields": None,
                "status": "not_found"
            })
            continue
        missing = [field for field in required_fields if not getattr(lead, field)]
        results.append({
            "lead_id": lead_id,
            "missing_fields": missing,
            "status": "ok"
        })
    return jsonify({"results": results})


@lead_bp.route('/enrichment-test')
# @login_required
def enrichment_test_page():
    return render_template('enrichment_test.html')

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

        success, message = LeadController.delete_multiple_leads(lead_ids, current_user)
        if success:
            return jsonify({"status": "success", "message": message or f"{len(lead_ids)} leads deleted successfully"})
        else:
            return jsonify({"status": "error", "message": message or "Failed to delete leads"}), 400
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500