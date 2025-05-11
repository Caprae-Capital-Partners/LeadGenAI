from flask import request, redirect, render_template, flash, url_for, jsonify
from models.lead_model import db, Lead
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import text

class LeadController:
    @staticmethod
    def get_all_leads():
        """Get all leads for view"""
        # return Lead.query.filter_by(deleted=False).order_by(Lead.updated_at.desc()).all()
        return Lead.query.order_by(Lead.updated_at.desc()).all()

    @staticmethod
    def get_lead_by_id(lead_id):
        """Get lead by ID"""
        # return Lead.query.filter_by(id=lead_id, deleted=False).first_or_404()
        return Lead.query.filter_by(lead_id=lead_id).first_or_404()

    @staticmethod
    def get_leads_by_ids(lead_ids):
        """Get multiple leads by their IDs"""
        # return Lead.query.filter(Lead.id.in_(lead_ids), Lead.deleted==False).all()
        return Lead.query.filter(Lead.lead_id.in_(lead_ids)).all()

    @staticmethod
    def create_lead(form_data):
        """Create new lead from form data"""
        # Create lead with basic information
        lead = Lead(
            # Base data
            search_keyword=form_data.get('search_keyword', {}),
            
            # Company info
            company=form_data.get('company', ''),
            website=form_data.get('website', ''),
            industry=form_data.get('industry', ''),
            product_category=form_data.get('product_category', ''),
            business_type=form_data.get('business_type', ''),
            employees=form_data.get('employees', None),
            revenue=form_data.get('revenue', None),
            year_founded=form_data.get('year_founded', ''),
            bbb_rating=form_data.get('bbb_rating', ''),
            
            # Location
            street=form_data.get('street', ''),
            city=form_data.get('city', ''),
            state=form_data.get('state', ''),
            
            # Company contact
            company_phone=form_data.get('company_phone', ''),
            company_linkedin=form_data.get('company_linkedin', ''),
            
            # Owner/contact info
            owner_first_name=form_data.get('owner_first_name', ''),
            owner_last_name=form_data.get('owner_last_name', ''),
            owner_title=form_data.get('owner_title', ''),
            owner_linkedin=form_data.get('owner_linkedin', ''),
            owner_phone_number=form_data.get('owner_phone_number', ''),
            owner_email=form_data.get('owner_email', ''),
            phone=form_data.get('phone', ''),
            
            # Source
            source=form_data.get('source', 'manual')
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
            if "lead_owner_email_key" in str(e):
                return False, f"Error: Email address '{lead.owner_email}' is already in use. Please use a different email."
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
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()
        
        # Store original email and phone for comparison
        original_email = lead.owner_email
        original_phone = lead.phone
        
        # Base data
        if 'search_keyword' in form_data:
            lead.search_keyword = form_data.get('search_keyword')
        if 'draft_data' in form_data:
            lead.draft_data = form_data.get('draft_data')
            
        # Company information
        lead.company = form_data.get('company', lead.company)
        lead.website = form_data.get('website', lead.website)
        lead.industry = form_data.get('industry', lead.industry)
        lead.product_category = form_data.get('product_category', lead.product_category)
        lead.business_type = form_data.get('business_type', lead.business_type)
        lead.employees = form_data.get('employees', lead.employees)
        lead.revenue = form_data.get('revenue', lead.revenue)
        lead.year_founded = form_data.get('year_founded', lead.year_founded)
        lead.bbb_rating = form_data.get('bbb_rating', lead.bbb_rating)
        
        # Location
        lead.street = form_data.get('street', lead.street)
        lead.city = form_data.get('city', lead.city)
        lead.state = form_data.get('state', lead.state)
        
        # Company contact
        lead.company_phone = form_data.get('company_phone', lead.company_phone)
        lead.company_linkedin = form_data.get('company_linkedin', lead.company_linkedin)
        
        # Owner/contact info
        lead.owner_first_name = form_data.get('owner_first_name', lead.owner_first_name)
        lead.owner_last_name = form_data.get('owner_last_name', lead.owner_last_name)
        lead.owner_title = form_data.get('owner_title', lead.owner_title)
        lead.owner_linkedin = form_data.get('owner_linkedin', lead.owner_linkedin)
        lead.owner_phone_number = form_data.get('owner_phone_number', lead.owner_phone_number)
        lead.owner_email = form_data.get('owner_email', lead.owner_email)
        lead.phone = form_data.get('phone', lead.phone)
        
        # Source
        lead.source = form_data.get('source', lead.source)
        
        # Status
        lead.status = form_data.get('status', lead.status)
        
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
            if lead.owner_email != original_email or lead.phone != original_phone:
                db.session.commit()
            else:
                # If no change to unique fields, this should be safe
                db.session.commit() 
            return True, "Lead updated successfully!"
        except IntegrityError as e:
            db.session.rollback()
            if "lead_owner_email_key" in str(e):
                return False, f"Error: Email address '{lead.owner_email}' is already used by another lead. Please use a different email."
            elif "lead_phone_key" in str(e):
                return False, f"Error: Phone number '{lead.phone}' is already used by another lead. Please use a different phone number."
            else:
                return False, f"Error updating lead: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating lead: {str(e)}"

    @staticmethod
    def delete_lead(lead_id, current_user=None):
        """Soft delete lead by ID"""
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()

        try:
            # Set current user for audit log if provided
            if current_user:
                user_name = current_user.username if hasattr(current_user, 'username') else str(current_user)
                db.session.execute(text("SELECT set_app_user(:username)"), {'username': user_name})
                
            # Instead of deleting, mark as deleted
            lead.deleted = True
            lead.deleted_at = datetime.utcnow()
            db.session.commit()
            return True, "Lead deleted successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting lead: {str(e)}"

    @staticmethod
    def delete_multiple_leads(lead_ids, current_user=None):
        """Soft delete multiple leads by their IDs"""
        if not lead_ids:
            return False, "No leads selected for deletion."
            
        try:
            # Set current user for audit log if provided
            if current_user:
                user_name = current_user.username if hasattr(current_user, 'username') else str(current_user)
                db.session.execute(text("SELECT set_app_user(:username)"), {'username': user_name})
                
            # Get all leads to be deleted
            leads = Lead.query.filter(Lead.lead_id.in_(lead_ids)).all()
            
            if not leads:
                return False, "No leads found with the specified IDs."
                
            # Mark all leads as deleted
            now = datetime.utcnow()
            for lead in leads:
                lead.deleted = True
                lead.deleted_at = now
                
            db.session.commit()
            return True, f"{len(leads)} leads deleted successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting leads: {str(e)}"

    @staticmethod
    def get_leads_json():
        """Get all leads as JSON for API"""
        leads = Lead.query.filter_by(deleted=False).all()
        return [lead.to_dict() for lead in leads]

    @staticmethod
    def add_or_update_lead_by_match(lead_data):
        """Add a new lead or update existing lead by matching email or phone"""
        try:
            # Only check for duplicates if email or phone is not empty
            query = Lead.query
            conditions = []
            
            # Clean and validate the data
            if lead_data.get('owner_email'):
                lead_data['owner_email'] = str(lead_data['owner_email']).strip().lower()
                conditions.append(Lead.owner_email == lead_data['owner_email'])
            if lead_data.get('phone'):
                lead_data['phone'] = str(lead_data['phone']).strip()
                conditions.append(Lead.phone == lead_data['phone'])
                
            if conditions:
                existing_lead = query.filter(db.or_(*conditions)).first()
            else:
                existing_lead = None

            if existing_lead:
                # Update existing lead with new data
                for key, value in lead_data.items():
                    if hasattr(existing_lead, key) and value is not None:
                        setattr(existing_lead, key, value)
                db.session.commit()
                return (True, "Lead updated successfully")
            else:
                # Create new lead
                # Remove any None values to avoid SQLAlchemy errors
                clean_data = {k: v for k, v in lead_data.items() if v is not None}
                try:
                    lead = Lead(**clean_data)
                    db.session.add(lead)
                    db.session.commit()
                    return (True, "Lead added successfully")
                except Exception as e:
                    db.session.rollback()
                    return (False, f"Error creating lead: {str(e)}")
        except IntegrityError as e:
            db.session.rollback()
            if "lead_owner_email_key" in str(e):
                return (False, f"Email address '{lead_data.get('owner_email')}' is already in use")
            elif "lead_phone_key" in str(e):
                return (False, f"Phone number '{lead_data.get('phone')}' is already in use")
            else:
                return (False, "Duplicate data detected")
        except Exception as e:
            db.session.rollback()
            return (False, f"Error adding/updating lead: {str(e)}")