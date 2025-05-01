from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify, send_file
from controllers.lead_controller import LeadController
from controllers.upload_controller import UploadController
from controllers.export_controller import ExportController
from controllers.dashboard_controller import DashboardController
from models.lead_model import db, Lead
from flask_login import login_required
import csv
from io import StringIO, BytesIO
import datetime

# Create blueprint
lead_bp = Blueprint('lead', __name__)

@lead_bp.route('/')
def index():
    """Display dashboard as home page"""
    stats = DashboardController.get_dashboard_stats()
    return render_template('dashboard.html', **stats)

@lead_bp.route('/form')
@login_required
def form():
    """Display form to add new lead"""
    return render_template('form.html')

@lead_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """Submit new lead"""
    success, message = LeadController.create_lead(request.form)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect('/')

@lead_bp.route('/upload_page')
@login_required
def upload_page():
    """Display CSV upload page"""
    return render_template('upload.html')

@lead_bp.route('/upload', methods=['POST'])
@login_required
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
        added, skipped_duplicates, errors = UploadController.process_csv_file(
            file,
            name_col,
            email_col,
            phone_col,
            dynamic_fields,
            first_name_col=first_name_col,
            last_name_col=last_name_col
        )
        db.session.commit()
        flash(f'Upload Complete! Added: {added}, Skipped: {skipped_duplicates}, Errors: {errors}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during upload: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/view_leads')
@login_required
def view_leads():
    """View all leads"""
    leads = LeadController.get_all_leads()
    
    # Get unique values for filters
    companies = sorted(set(lead.company for lead in leads if lead.company))
    locations = sorted(set(f"{lead.city}, {lead.state}" if lead.city and lead.state else (lead.city or lead.state) for lead in leads if (lead.city or lead.state)))
    roles = sorted(set(lead.title for lead in leads if lead.title))
    scores = sorted(set(lead.score for lead in leads if lead.score))
    
    # Get additional filter options
    industries = sorted(set(lead.industry for lead in leads if lead.industry))
    business_types = sorted(set(lead.business_type for lead in leads if lead.business_type))
    states = sorted(set(lead.state for lead in leads if lead.state))
    employee_sizes = sorted(set(lead.employees_range for lead in leads if lead.employees_range))
    revenue_ranges = sorted(set(lead.revenue for lead in leads if lead.revenue))
    
    return render_template('leads.html', 
                         leads=leads,
                         companies=companies,
                         locations=locations,
                         roles=roles,
                         scores=scores,
                         industries=industries,
                         business_types=business_types,
                         states=states,
                         employee_sizes=employee_sizes,
                         revenue_ranges=revenue_ranges)

@lead_bp.route('/edit/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def edit_lead(lead_id):
    """Edit lead"""
    if request.method == 'POST':
        success, message = LeadController.update_lead(lead_id, request.form)

        if success:
            flash(message, 'success')
            return redirect(url_for('lead.view_leads'))
        else:
            flash(message, 'danger')

    lead = LeadController.get_lead_by_id(lead_id)
    return render_template('edit_lead.html', lead=lead)

@lead_bp.route('/delete/<int:lead_id>')
@login_required
def delete_lead(lead_id):
    """Delete lead"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        db.session.delete(lead)
        db.session.commit()
        flash('Lead deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting lead: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    """API endpoint to get all leads"""
    leads = Lead.query.all()
    return jsonify([lead.to_dict() for lead in leads])

@lead_bp.route('/api/leads', methods=['POST'])
@login_required
def create_lead():
    """Create a new lead"""
    data = request.json
    lead = Lead(**data)
    
    try:
        db.session.add(lead)
        db.session.commit()
        return jsonify({"message": "Lead created successfully", "lead": lead.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/api/leads/<int:lead_id>', methods=['PUT'])
@login_required
def update_lead_api(lead_id):
    """Update a lead via API"""
    lead = Lead.query.get_or_404(lead_id)
    data = request.json
    
    try:
        for key, value in data.items():
            setattr(lead, key, value)
        db.session.commit()
        return jsonify({"message": "Lead updated successfully", "lead": lead.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/export_leads', methods=['POST'])
@login_required
def export_leads():
    """Export selected leads to CSV"""
    selected_leads = request.form.getlist('selected_leads[]')
    
    if not selected_leads:
        flash('Please select at least one lead to export', 'danger')
        return redirect(url_for('lead.view_leads'))
    
    try:
        csv_data = ExportController.export_leads_to_csv(selected_leads)
        
        # Create response
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            BytesIO(csv_data.encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'leads_export_{timestamp}.csv'
        )
    except Exception as e:
        flash(f'Error exporting leads: {str(e)}', 'danger')
        return redirect(url_for('lead.view_leads'))

@lead_bp.route('/dashboard')
@login_required
def dashboard():
    """Display dashboard"""
    stats = DashboardController.get_dashboard_stats()
    return render_template('dashboard.html', **stats)