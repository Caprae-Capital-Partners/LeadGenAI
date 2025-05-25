from flask import request, redirect, render_template, flash, url_for, jsonify
from models.lead_model import db, Lead
from models.audit_logs_model import AuditLog
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import text
from controllers.search_log_controller import SearchLogController
from flask_login import current_user
import time
import re
import logging

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
    def normalize_company_name(name):
        if not name:
            return ''
        return re.sub(r'[^a-zA-Z0-9 ]', '', name).strip().lower()

    @staticmethod
    def find_duplicate_lead(lead_data):
        """Find a duplicate lead using lead_id, composite key, company, or contact info."""
        Lead = globals()['Lead']  # for staticmethod context
        db = globals()['db']
        logging = globals()['logging']
        # 1. Check by lead_id
        if lead_data.get('lead_id'):
            lead = Lead.query.filter_by(lead_id=lead_data['lead_id']).first()
            if lead:
                return lead, 'lead_id'
        # 2. Composite key: normalized company + owner_email + phone
        company = LeadController.normalize_company_name(lead_data.get('company', ''))
        owner_email = str(lead_data.get('owner_email', '')).strip().lower()
        phone = str(lead_data.get('phone', '')).strip()
        if company and owner_email and phone:
            lead = Lead.query.filter(
                db.func.lower(db.func.replace(db.func.replace(db.func.replace(Lead.company, '-', ''), '.', ''), ',', '')) == company,
                db.func.lower(Lead.owner_email) == owner_email,
                Lead.phone == phone,
                Lead.deleted == False
            ).first()
            if lead:
                return lead, 'composite (company+email+phone)'
        # 3. Normalized company only
        if company:
            lead = Lead.query.filter(
                db.func.lower(db.func.replace(db.func.replace(db.func.replace(Lead.company, '-', ''), '.', ''), ',', '')) == company,
                Lead.deleted == False
            ).first()
            if lead:
                return lead, 'company only'
        # 4. owner_email or phone only
        query = Lead.query
        conditions = []
        if owner_email:
            conditions.append(Lead.owner_email == owner_email)
        if phone:
            conditions.append(Lead.phone == phone)
        if conditions:
            lead = query.filter(db.or_(*conditions)).first()
            if lead:
                return lead, 'email or phone only'
        return None, None

    @staticmethod
    def update_existing_lead(existing_lead, lead_data):
        logging = globals()['logging']
        updated = False
        updated_fields = []
        for key, value in lead_data.items():
            if hasattr(existing_lead, key):
                current_value = getattr(existing_lead, key)
                if value not in [None, '', 'N/A'] and current_value != value:
                    setattr(existing_lead, key, value)
                    updated = True
                    updated_fields.append(key)
                    logging.info(f"Updated field '{key}': '{current_value}' -> '{value}'")
            else:
                logging.warning(f"Skipping key '{key}': not in Lead model")
        return updated, updated_fields

    @staticmethod
    def create_new_lead(lead_data):
        Lead = globals()['Lead']
        db = globals()['db']
        logging = globals()['logging']
        clean_data = {k: v for k, v in lead_data.items() if v is not None and v != ""}
        lead = Lead(**clean_data)
        db.session.add(lead)
        db.session.commit()
        logging.info(f"Added new lead with ID: {lead.lead_id}")
        return lead

    @staticmethod
    def add_or_update_lead_by_match(lead_data):
        """Add a new lead or update existing lead by matching lead_id, company+email+phone, or email/phone only"""
        try:
            logging.info(f"Processing lead: {lead_data.get('company')}")
            existing_lead, match_type = LeadController.find_duplicate_lead(lead_data)
            if existing_lead:
                logging.info(f"Duplicate found by {match_type}")
                updated, updated_fields = LeadController.update_existing_lead(existing_lead, lead_data)
                try:
                    if updated:
                        db.session.commit()
                        msg = {
                            "status": "updated",
                            "message": f"Lead was found as a duplicate (matched by {match_type}) and has been updated.",
                            "updated_fields": updated_fields,
                            "match_type": match_type,
                            "lead_id": existing_lead.lead_id
                        }
                        logging.info(msg["message"])
                        return (True, msg)
                    else:
                        msg = {
                            "status": "no_change",
                            "message": f"Lead was found as a duplicate (matched by {match_type}) but no changes were needed.",
                            "match_type": match_type,
                            "lead_id": existing_lead.lead_id
                        }
                        logging.info(msg["message"])
                        return (True, msg)
                except Exception as e:
                    db.session.rollback()
                    msg = {
                        "status": "error",
                        "message": f"Error updating duplicate lead (matched by {match_type}): {str(e)}",
                        "match_type": match_type
                    }
                    logging.error(msg["message"])
                    return (False, msg)
            else:
                try:
                    lead = LeadController.create_new_lead(lead_data)
                    msg = {
                        "status": "created",
                        "message": "Lead was created successfully (no duplicate found).",
                        "lead_id": lead.lead_id
                    }
                    logging.info(msg["message"])
                    return (True, msg)
                except Exception as e:
                    db.session.rollback()
                    msg = {
                        "status": "error",
                        "message": f"Error creating new lead: {str(e)}"
                    }
                    logging.error(msg["message"])
                    return (False, msg)
        except IntegrityError as e:
            db.session.rollback()
            msg = {
                "status": "error",
                "message": f"IntegrityError while adding/updating lead: {str(e)}"
            }
            logging.error(msg["message"])
            return (False, msg)
        except Exception as e:
            db.session.rollback()
            msg = {
                "status": "error",
                "message": f"General exception while adding/updating lead: {str(e)}"
            }
            logging.error(msg["message"])
            return (False, msg)

    @staticmethod
    def search_leads_by_industry_location(industry=None, location=None):
        """Search leads by industry and location (for API), with search_logs caching"""
        # Temporarily commenting out caching logic to ensure function returns Lead instances for decorator
        # start_time = time.time()
        # # Normalize and hash the search
        # search_hash = SearchLogController.normalize_and_hash(industry, location)
        # # Check if log exists
        # log = SearchLogController.get_log_by_hash(search_hash)
        # if log and log.search_parameters:
        #     # Increment result_count and update timestamp
        #     log.result_count += 1
        #     log.searched_at = datetime.utcnow()
        #     db.session.commit()
        #     return log.search_parameters  # Already JSON serializable

        # If no log found or caching is off, search leads
        query = Lead.query.filter_by(deleted=False)
        if industry:
            query = query.filter(db.func.lower(Lead.industry) == industry.lower())

        if location:
            # Restore location filtering to search city, state, or street and exclude nulls/empty
            # Search in city, state, or street
            location_filter = db.or_(
                Lead.city.ilike(f"%{location}%"),
                Lead.state.ilike(f"%{location}%"),
                Lead.street.ilike(f"%{location}%") # Add street to the search
            )
            # Ensure at least one of city, state, or street is not null/empty
            not_null_or_empty = db.or_(
                Lead.city.isnot(None) & (Lead.city != ''),
                Lead.state.isnot(None) & (Lead.state != ''),
                Lead.street.isnot(None) & (Lead.street != '')
            )
            query = query.filter(location_filter, not_null_or_empty)

        leads = query.all()

        # Temporarily commenting out search logging
        # exec_time = int((time.time() - start_time) * 1000)
        # # Log the search
        # user_id = getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None)
        # if user_id:
        #     search_query = f"industry: {industry}, location: {location}"
        #     SearchLogController.log_search(
        #         user_id=user_id,
        #         search_query=search_query,
        #         search_hash=search_hash,
        #         search_parameters=[lead.to_dict() for lead in leads], # Log dictionary representation
        #         result_count=len(leads),
        #         execution_time_ms=exec_time
        #     )

        return leads # Return list of Lead model instances for the decorator

    @staticmethod
    def get_unique_industries():
        """Return a normalized, unique, sorted list of industries from the Lead table."""
        industries_query = db.session.query(Lead.industry).filter(
            Lead.industry.isnot(None),
            Lead.industry != '',
            Lead.deleted == False
        ).distinct().all()
        industries = [row[0] for row in industries_query]
        # Normalize: strip, remove empty, deduplicate, sort
        normalized = sorted(set(i.strip() for i in industries if i and i.strip()))
        return normalized