from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify
from controllers.lead_controller import LeadController
from controllers.upload_controller import UploadController
from models.lead_model import db

# Create blueprint
lead_bp = Blueprint('lead', __name__)

@lead_bp.route('/')
def form():
    """Display form to add new lead"""
    return render_template('form.html')

@lead_bp.route('/submit', methods=['POST'])
def submit():
    """Submit new lead"""
    success, message = LeadController.create_lead(request.form)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect('/')

@lead_bp.route('/upload_page')
def upload_page():
    """Display CSV upload page"""
    return render_template('upload.html')

@lead_bp.route('/upload', methods=['POST'])
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
            dynamic_fields
        )
        db.session.commit()
        flash(f'Upload Complete! Added: {added}, Skipped: {skipped_duplicates}, Errors: {errors}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during upload: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/view_leads')
def view_leads():
    """View all leads"""
    leads = LeadController.get_all_leads()
    return render_template('leads.html', leads=leads)

@lead_bp.route('/edit/<int:lead_id>', methods=['GET', 'POST'])
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
def delete_lead(lead_id):
    """Delete lead"""
    success, message = LeadController.delete_lead(lead_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/api/leads')
def get_leads():
    """API endpoint to get all leads"""
    return jsonify(LeadController.get_leads_json())