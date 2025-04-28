from flask import request, redirect, render_template, flash, url_for, jsonify
from models.lead_model import db, Lead
from sqlalchemy.exc import IntegrityError

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
        # Create lead with basic information
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
        
        # Handle dynamic fields if provided
        if form_data.getlist('dynamic_field_name[]') and form_data.getlist('dynamic_field_value[]'):
            field_names = form_data.getlist('dynamic_field_name[]')
            field_values = form_data.getlist('dynamic_field_value[]')
            
            for i in range(len(field_names)):
                if field_names[i] and field_values[i]:
                    # Set attribute if it exists on Lead model
                    field_name = field_names[i]
                    if hasattr(lead, field_name):
                        setattr(lead, field_name, field_values[i])
        
        try:
            db.session.add(lead)
            db.session.commit()
            return True, "Lead added successfully!"
        except IntegrityError as e:
            db.session.rollback()
            if "lead_email_key" in str(e):
                return False, f"Error: Email address '{lead.email}' is already in use. Please use a different email."
            elif "lead_phone_key" in str(e):
                return False, f"Error: Phone number '{lead.phone}' is already in use. Please use a different phone number."
            else:
                return False, f"Error adding lead: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error adding lead: {str(e)}"
    
    @staticmethod
    def update_lead(lead_id, form_data):
        """Update existing lead"""
        lead = Lead.query.get_or_404(lead_id)
        
        # Store original email and phone for comparison
        original_email = lead.email
        original_phone = lead.phone
        
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
        
        # Handle dynamic fields if provided
        if form_data.getlist('dynamic_field_name[]') and form_data.getlist('dynamic_field_value[]'):
            field_names = form_data.getlist('dynamic_field_name[]')
            field_values = form_data.getlist('dynamic_field_value[]')
            
            for i in range(len(field_names)):
                if field_names[i] and field_values[i]:
                    # Set attribute if it exists on Lead model
                    field_name = field_names[i]
                    if hasattr(lead, field_name):
                        setattr(lead, field_name, field_values[i])
        
        try:
            # Only commit if email or phone has changed
            if lead.email != original_email or lead.phone != original_phone:
                db.session.commit()
            else:
                # If no change to unique fields, this should be safe
                db.session.commit() 
            return True, "Lead updated successfully!"
        except IntegrityError as e:
            db.session.rollback()
            if "lead_email_key" in str(e):
                return False, f"Error: Email address '{lead.email}' is already used by another lead. Please use a different email."
            elif "lead_phone_key" in str(e):
                return False, f"Error: Phone number '{lead.phone}' is already used by another lead. Please use a different phone number."
            else:
                return False, f"Error updating lead: {str(e)}"
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