from flask import request, redirect, render_template, flash, url_for, jsonify
from models.lead_model import db, Lead
from models.audit_logs_model import AuditLog
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import text

class LeadController:
    @staticmethod
    def get_all_leads():
        """Get all leads for view, with optional search and filters from request.args"""
        query = Lead.query.filter_by(deleted=False)
        args = request.args

        # Basic search across multiple fields
        search = args.get('search', '').strip()
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                db.or_(
                    db.func.lower(Lead.company).like(search_pattern),
                    db.func.lower(Lead.owner_first_name).like(search_pattern),
                    db.func.lower(Lead.owner_last_name).like(search_pattern),
                    db.func.lower(Lead.owner_email).like(search_pattern),
                    db.func.lower(Lead.phone).like(search_pattern),
                    db.func.lower(Lead.owner_title).like(search_pattern),
                    db.func.lower(Lead.city).like(search_pattern),
                    db.func.lower(Lead.state).like(search_pattern),
                    db.func.lower(Lead.website).like(search_pattern),
                    db.func.lower(Lead.company_linkedin).like(search_pattern),
                    db.func.lower(Lead.industry).like(search_pattern),
                    db.func.lower(Lead.product_category).like(search_pattern),
                    db.func.lower(Lead.business_type).like(search_pattern),
                    db.func.lower(Lead.status).like(search_pattern),
                )
            )

        # Individual filters
        if args.get('company'):
            query = query.filter(Lead.company == args.get('company'))
        if args.get('location'):
            location = args.get('location')
            if ',' in location:
                city, state = [x.strip() for x in location.split(',', 1)]
                query = query.filter(Lead.city == city, Lead.state == state)
            else:
                query = query.filter(db.or_(Lead.city == location, Lead.state == location))
        if args.get('role'):
            query = query.filter(Lead.owner_title == args.get('role'))
        if args.get('status'):
            query = query.filter(Lead.status == args.get('status'))
        if args.get('revenue'):
            try:
                revenue_val = float(args.get('revenue').replace('$','').replace('M','000000').replace('K','000'))
                query = query.filter(Lead.revenue >= revenue_val)
            except:
                pass

        return query.order_by(Lead.updated_at.desc()).all()

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
        """Update lead data"""
        try:
            lead = Lead.query.get(lead_id)
            if not lead:
                return False, "Lead not found"

            # Handle numeric fields - convert empty strings to None
            employees = form_data.get('employees')
            revenue = form_data.get('revenue')
            year_founded = form_data.get('year_founded')

            lead.employees = int(employees) if employees and employees.strip() else None
            lead.revenue = int(revenue) if revenue and revenue.strip() else None
            lead.year_founded = int(year_founded) if year_founded and year_founded.strip() else None

            # Update other fields
            lead.company = form_data.get('company')
            lead.website = form_data.get('website') or None
            lead.industry = form_data.get('industry') or None
            lead.product_category = form_data.get('product_category') or None
            lead.business_type = form_data.get('business_type') or None
            lead.bbb_rating = form_data.get('bbb_rating') or None
            lead.street = form_data.get('street') or None
            lead.city = form_data.get('city') or None
            lead.state = form_data.get('state') or None
            lead.company_phone = form_data.get('company_phone') or None
            lead.company_linkedin = form_data.get('company_linkedin') or None
            lead.owner_first_name = form_data.get('owner_first_name') or None
            lead.owner_last_name = form_data.get('owner_last_name') or None
            lead.owner_email = form_data.get('owner_email') or None
            lead.owner_title = form_data.get('owner_title') or None
            lead.owner_linkedin = form_data.get('owner_linkedin') or None
            lead.owner_phone_number = form_data.get('owner_phone_number') or None
            lead.source = form_data.get('source')
            lead.status = form_data.get('status', 'new')
            lead.updated_at = datetime.utcnow()

            db.session.commit()
            return True, "Lead updated successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating lead: {str(e)}"

    @staticmethod
    def delete_lead(lead_id, current_user=None):
        """Soft delete lead by ID"""
        lead = Lead.query.filter_by(lead_id=lead_id, deleted=False).first_or_404()

        try:
            # Store old values for audit log
            old_values = lead.to_dict()
            
            # Mark as deleted
            lead.deleted = True
            lead.deleted_at = datetime.utcnow()
            
            # Create audit log entry
            if current_user:
                AuditLog.log_change(
                    user_id=getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None) or str(current_user),
                    action_type='delete',
                    table_affected='leads',
                    record_id=str(lead_id),
                    old_values=old_values,
                    new_values={'deleted': True, 'deleted_at': lead.deleted_at.isoformat()},
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
            
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
            # Get all leads to be deleted
            leads = Lead.query.filter(
                Lead.lead_id.in_(lead_ids),
                Lead.deleted == False
            ).all()
            
            if not leads:
                return False, "No leads found with the specified IDs."
                
            now = datetime.utcnow()
            deleted_count = 0
            
            for lead in leads:
                old_values = lead.to_dict()
                lead.deleted = True
                lead.deleted_at = now
                deleted_count += 1
                
                if current_user:
                    AuditLog.log_change(
                        user_id=getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None) or str(current_user),
                        action_type='delete',
                        table_affected='leads',
                        record_id=str(lead.lead_id),
                        old_values=old_values,
                        new_values={'deleted': True, 'deleted_at': now.isoformat()},
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                
            db.session.commit()
            return True, f"{deleted_count} leads deleted successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting leads: {str(e)}"

    @staticmethod
    def restore_lead(lead_id, current_user=None):
        """Restore a soft-deleted lead"""
        lead = Lead.query.filter_by(lead_id=lead_id).first_or_404()

        try:
            # Store old values for audit log
            old_values = lead.to_dict()
            
            # Restore lead
            lead.deleted = False
            lead.deleted_at = None
            
            # Create audit log entry
            if current_user:
                AuditLog.log_change(
                    user_id=getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None) or str(current_user),
                    action_type='update',
                    table_affected='leads',
                    record_id=str(lead_id),
                    old_values=old_values,
                    new_values={'deleted': False, 'deleted_at': None},
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
            
            db.session.commit()
            return True, "Lead restored successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error restoring lead: {str(e)}"

    @staticmethod
    def restore_multiple_leads(lead_ids, current_user=None):
        """Restore multiple soft-deleted leads"""
        if not lead_ids:
            return False, "No leads selected for restoration."
            
        try:
            # Get all leads to be restored
            leads = Lead.query.filter(Lead.lead_id.in_(lead_ids)).all()
            
            if not leads:
                return False, "No leads found with the specified IDs."
                
            # Restore leads and create audit logs
            for lead in leads:
                old_values = lead.to_dict()
                lead.deleted = False
                lead.deleted_at = None
                
                if current_user:
                    AuditLog.log_change(
                        user_id=getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None) or str(current_user),
                        action_type='update',
                        table_affected='leads',
                        record_id=str(lead.lead_id),
                        old_values=old_values,
                        new_values={'deleted': False, 'deleted_at': None},
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                
            db.session.commit()
            return True, f"{len(leads)} leads restored successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error restoring leads: {str(e)}"

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