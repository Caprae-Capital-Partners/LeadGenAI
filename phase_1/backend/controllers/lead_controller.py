from flask import request, redirect, render_template, flash, url_for, jsonify
from models.lead_model import db, Lead

class LeadController:
    @staticmethod
    def get_all_leads():
        """Get all leads for view"""
        return Lead.query.all()
    
    @staticmethod
    def get_lead_by_id(lead_id):
        """Get lead by ID"""
        return Lead.query.get_or_404(lead_id)
    
    @staticmethod
    def create_lead(form_data):
        """Create new lead from form data"""
        lead = Lead(
            # Basic contact info
            first_name=form_data.get('first_name', ''),
            last_name=form_data.get('last_name', ''),
            email=form_data.get('email', ''),
            phone=form_data.get('phone', ''),
            title=form_data.get('title', ''),
            
            # Company info
            company=form_data.get('company', ''),
            city=form_data.get('city', ''),
            state=form_data.get('state', ''),
            website=form_data.get('website', ''),
            industry=form_data.get('industry', ''),
            business_type=form_data.get('business_type', ''),
            
            # Other fields
            additional_notes=form_data.get('notes', '')
        )
        
        try:
            db.session.add(lead)
            db.session.commit()
            return True, "Lead added successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error adding lead: {str(e)}"
    
    @staticmethod
    def update_lead(lead_id, form_data):
        """Update existing lead"""
        lead = Lead.query.get_or_404(lead_id)
        
        lead.first_name = form_data.get('first_name', '')
        lead.last_name = form_data.get('last_name', '')
        lead.email = form_data.get('email', '')
        lead.phone = form_data.get('phone', '')
        lead.company = form_data.get('company', '')
        lead.industry = form_data.get('industry', '')
        lead.city = form_data.get('city', '')
        lead.state = form_data.get('state', '')
        lead.website = form_data.get('website', '')
        lead.business_type = form_data.get('business_type', '')
        
        try:
            db.session.commit()
            return True, "Lead updated successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating lead: {str(e)}"
    
    @staticmethod
    def delete_lead(lead_id):
        """Delete lead by ID"""
        lead = Lead.query.get_or_404(lead_id)
        
        try:
            db.session.delete(lead)
            db.session.commit()
            return True, "Lead deleted successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting lead: {str(e)}"
    
    @staticmethod
    def get_leads_json():
        """Get all leads as JSON for API"""
        leads = Lead.query.all()
        return [lead.to_dict() for lead in leads] 