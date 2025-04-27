from flask import Flask, render_template, request, redirect, jsonify, flash, url_for
from models.lead_model import db, Lead

import os

app = Flask(__name__)
# Using PostgreSQL as database with local user for testing
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ZqxqhrXPZGiULnFToDzVjItstlSBLgIo@tramway.proxy.rlwy.net:22825/railway'
#postgresql://postgres:ZqxqhrXPZGiULnFToDzVjItstlSBLgIo@tramway.proxy.rlwy.net:22825/railway
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'

db.init_app(app)

# Flask 2.0+ uses this instead of before_first_request
with app.app_context():
    db.create_all()

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Create a new lead with available fields from form
    lead = Lead(
        # Basic contact info
        first_name=request.form.get('first_name', ''),
        last_name=request.form.get('last_name', ''),
        email=request.form.get('email', ''),
        phone=request.form.get('phone', ''),
        title=request.form.get('title', ''),
        
        # Company info
        company=request.form.get('company', ''),
        city=request.form.get('city', ''),
        state=request.form.get('state', ''),
        website=request.form.get('website', ''),
        industry=request.form.get('industry', ''),
        business_type=request.form.get('business_type', ''),
        
        # Other fields that might be in the form
        additional_notes=request.form.get('notes', '')
    )
    
    db.session.add(lead)
    db.session.commit()
    flash('Lead added successfully!', 'success')
    return redirect('/')

@app.route('/view_leads')
def view_leads():
    leads = Lead.query.all()
    return render_template('leads.html', leads=leads)

@app.route('/edit/<int:lead_id>', methods=['GET', 'POST'])
def edit_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    
    if request.method == 'POST':
        # Update lead info with form data
        lead.first_name = request.form.get('first_name', '')
        lead.last_name = request.form.get('last_name', '')
        lead.email = request.form.get('email', '')
        lead.phone = request.form.get('phone', '')
        lead.company = request.form.get('company', '')
        lead.industry = request.form.get('industry', '')
        lead.city = request.form.get('city', '')
        lead.state = request.form.get('state', '')
        lead.website = request.form.get('website', '')
        lead.business_type = request.form.get('business_type', '')
        
        try:
            db.session.commit()
            flash('Lead updated successfully!', 'success')
            return redirect(url_for('view_leads'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating lead: {str(e)}', 'danger')
    
    return render_template('edit_lead.html', lead=lead)

@app.route('/delete/<int:lead_id>')
def delete_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    
    try:
        db.session.delete(lead)
        db.session.commit()
        flash('Lead deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting lead: {str(e)}', 'danger')
    
    return redirect(url_for('view_leads'))

@app.route('/api/leads')
def get_leads():
    leads = Lead.query.all()
    return jsonify([lead.to_dict() for lead in leads])

if __name__ == '__main__':
    app.run(debug=True) 