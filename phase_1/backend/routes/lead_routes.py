from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify
from controllers.lead_controller import LeadController

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