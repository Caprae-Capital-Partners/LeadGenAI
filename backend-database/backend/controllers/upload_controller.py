import pandas as pd
import io
import re
from datetime import datetime
from models.lead_model import db, Lead
from controllers.lead_controller import LeadController
import chardet
from flask import flash

class UploadController:
    # Add field mapping dictionary at the start of the class
    FIELD_MAPPING = {
        # Legacy field mappings
        'title': 'owner_title',
        'linkedin_url': 'company_linkedin',
        'product_service_category': 'product_category',
        'employees_range': 'employees',
        'associated_members': 'employees',
        'rev_source': 'source',
        'owner_age': None,
        'additional_notes': None,
        
        # Case-sensitive field mappings with spaces
        'Company': 'company',
        'City': 'city',
        'State': 'state',
        'First Name': 'owner_first_name',
        'Last Name': 'owner_last_name',
        'Email': 'owner_email',
        'Title': 'owner_title',
        'Website': 'website',
        'LinkedIn URL': 'company_linkedin',
        'Industry': 'industry',
        'Revenue': 'revenue',
        'Product/Service Category': 'product_category',
        'Business Type (B2B, B2B2C)': 'business_type',
        'Employees range': 'employees',
        'Year Founded': 'year_founded',
        "Owner's LinkedIn": 'owner_linkedin',
        'Associated Members': 'employees',
        'Phone': 'phone',
        'Company Phone': 'company_phone',
        'Owner Phone': 'owner_phone_number',
        'Street': 'street',
        'BBB Rating': 'bbb_rating',
        
        # Fields to ignore
        'Score': None,
        'Email customization #1': None,
        'Subject Line #1': None,
        'Email Customization #2': None,
        'Subject Line #2': None,
        'LinkedIn Customization #1': None,
        'LinkedIn Customization #2': None,
        'Reasoning for r//y/g': None,
    }

    @staticmethod
    def map_field_name(field_name):
        """Map a field name to its database column name"""
        # First try exact match
        if field_name in UploadController.FIELD_MAPPING:
            return UploadController.FIELD_MAPPING[field_name]
            
        # Try case-insensitive match
        field_name_lower = field_name.lower()
        for key, value in UploadController.FIELD_MAPPING.items():
            if key.lower() == field_name_lower:
                return value
                
        # If no match found, return None
        return None

    @staticmethod
    def log_error(filename, row_number, data, reason):
        log_file = "upload_errors.log"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {filename} Row {row_number}: ")
            
            if "Success" in reason:
                company = data.get('company', 'Unknown')
                f.write(f"SUCCESS - Company: '{company}' - {reason}\n")
            elif "Skipped" in reason:
                company = data.get('company', 'Unknown')
                f.write(f"SKIPPED - {reason}\n")
            elif "Error" in reason:
                company = data.get('company', 'Unknown')
                f.write(f"ERROR - Company: '{company}' - {reason}\n")
                f.write(f"       Data: {data}\n")
            else:
                f.write(f"{reason}\n")
                f.write(f"Data: {data}\n")

    @staticmethod
    def write_log_separator(filename):
        log_file = "upload_errors.log"
        with open(log_file, "a", encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"New Upload Session - File: {filename} at {timestamp}\n")

    @staticmethod
    def clean_email(email):
        if pd.isna(email):
            return None
        return str(email).strip().lower()

    @staticmethod
    def clean_phone(phone):
        if pd.isna(phone):
            return None
        return re.sub(r'\D', '', str(phone))
    
    @staticmethod
    def clean_website(website):
        if pd.isna(website):
            return None
        return str(website).strip().lower()

    @staticmethod
    def clean_company(company):
        if pd.isna(company):
            return None
        return str(company).strip()

    @staticmethod
    def is_valid_email(email):
        if not email or pd.isna(email):
            return False
        EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        return bool(EMAIL_REGEX.match(str(email).strip()))

    @staticmethod
    def is_valid_phone(phone):
        if not phone or pd.isna(phone):
            return False
        phone_str = re.sub(r'\D', '', str(phone))
        return phone_str.isdigit() and len(phone_str) >= 8
    
    @staticmethod
    def is_valid_website(website):
        if not website or pd.isna(website):
            return False
        return bool(website.strip())

    @staticmethod
    def is_valid_company(company):
        if not company or pd.isna(company):
            return False
        return bool(company.strip())

    @staticmethod
    def is_valid_row(name, email, phone):
        # Only validate company name, all other fields can be empty
        return True  # Remove validation since we want to allow empty fields

    @staticmethod
    def process_csv_file(file, name_col, email_col, phone_col, dynamic_fields=None, first_name_col=None, last_name_col=None):
        filename = file.filename
        UploadController.write_log_separator(filename)

        try:
            content = file.read()

            # Robust encoding detection and decoding
            if isinstance(content, bytes):
                detection = chardet.detect(content)
                detected_encoding = detection['encoding']
                encodings_to_try = [detected_encoding, 'utf-8', 'latin-1', 'windows-1252', 'ISO-8859-1']
                for encoding in encodings_to_try:
                    if not encoding:
                        continue
                    try:
                        content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise Exception("Could not decode the file with any common encoding")

            df = pd.read_csv(io.StringIO(content))
            df.columns = df.columns.str.strip()

            # Fill empty values with "-" for all columns
            df = df.fillna("-")

            # Only validate that the name column exists if provided
            if name_col and name_col not in df.columns:
                raise Exception(f"Missing required column: {name_col}")

            # Handle first_name and last_name columns if provided
            if first_name_col and first_name_col in df.columns:
                df['owner_first_name'] = df[first_name_col].apply(lambda x: str(x).strip() if str(x).strip() != "-" else "")
            else:
                df['owner_first_name'] = ""
                
            if last_name_col and last_name_col in df.columns:
                df['owner_last_name'] = df[last_name_col].apply(lambda x: str(x).strip() if str(x).strip() != "-" else "")
            else:
                df['owner_last_name'] = ""

            # Process name column if it exists
            if name_col and name_col in df.columns:
                df[name_col] = df[name_col].apply(lambda x: str(x).strip() if str(x).strip() != "-" else "")
                df['name'] = df[name_col]
                def split_name(name):
                    if not name or name == "-":
                        return "", ""
                    parts = name.strip().split()
                    if len(parts) == 0:
                        return "", ""
                    elif len(parts) == 1:
                        return parts[0], ""
                    else:
                        return parts[0], " ".join(parts[1:])
                df['owner_first_name'], df['owner_last_name'] = zip(*df['name'].map(split_name))
            else:
                if 'owner_first_name' not in df.columns:
                    df['owner_first_name'] = ""
                if 'owner_last_name' not in df.columns:
                    df['owner_last_name'] = ""
                df['name'] = ""

            # Always set name to first_name + last_name if name is empty
            df['name'] = df.apply(lambda row: row['name'] if row['name'] and row['name'] != "-" else f"{row.get('owner_first_name','')} {row.get('owner_last_name','')}".strip(), axis=1)

            # Process email and phone fields if they exist in the CSV
            df['owner_email'] = "" if email_col not in df.columns else df[email_col].apply(lambda x: UploadController.clean_email(x) if str(x).strip() != "-" else "")
            df['phone'] = "" if phone_col not in df.columns else df[phone_col].apply(lambda x: UploadController.clean_phone(x) if str(x).strip() != "-" else "")

            # Set company field - use name if company column doesn't exist
            # Normalize column names first
            df.columns = df.columns.str.lower()

            if 'company' not in df.columns:
                raise Exception("CSV file must contain a 'company' column.")
            else:
                df['company'] = df['company'].apply(lambda x: str(x).strip() if str(x).strip() != "-" else "")

            added_new = 0
            updated = 0
            skipped_duplicates = 0
            skipped_empty_company = 0
            errors = 0
            skipped_details = []

            for idx, row in df.iterrows():
                try:
                    # Get company value and skip if empty
                    company_value = str(row.get('company', '')).strip()
                    if not company_value:
                        skipped_empty_company += 1
                        error_message = f"Row {idx+2}: Empty company value, skipped."
                        skipped_details.append(error_message)
                        UploadController.log_error(filename, idx + 2, row.to_dict(), f"Skipped (empty company): Company value is empty")
                        continue  # Skip this row
                        
                    lead_data = {
                        'search_keyword': {},
                        'source': 'manual',
                        'company': company_value,
                        'status': 'new'
                    }

                    company_name = lead_data['company']
                    existing_lead = Lead.query.filter_by(company=company_name, deleted=False).first()
                    if existing_lead:
                        skipped_duplicates += 1
                        error_message = f"Row {idx+2}: Duplicate company '{company_name}' skipped."
                        skipped_details.append(error_message)
                        UploadController.log_error(filename, idx + 2, lead_data, f"Skipped (duplicate): Company '{company_name}' already exists in database")
                        continue

                    # Map and clean all fields from the CSV
                    for column in df.columns:
                        mapped_field = UploadController.map_field_name(column)
                        
                        # Skip fields that are mapped to None or already processed
                        if mapped_field is None or mapped_field in lead_data:
                            continue
                            
                        value = row[column]
                        if value != "-":  # Only process non-dash values
                            # Convert to string and clean
                            value = str(value).strip()
                            
                            # Special handling for specific fields
                            if mapped_field == 'employees':
                                try:
                                    if '-' in value:
                                        value = int(value.split('-')[0].strip())
                                    else:
                                        value = int(value)
                                except (ValueError, TypeError):
                                    value = None
                            elif mapped_field == 'revenue':
                                try:
                                    value = float(value.replace('$', '').replace('M', '000000').replace('K', '000'))
                                except (ValueError, TypeError):
                                    value = None
                            elif mapped_field == 'year_founded':
                                try:
                                    value = str(int(float(value)))
                                except (ValueError, TypeError):
                                    value = None
                            
                            # Only add non-empty values
                            if value not in (None, '', 'nan', 'NaN', 'None'):
                                lead_data[mapped_field] = value

                    # Remove any fields that are not in the Lead model
                    valid_fields = {
                        'search_keyword', 'source', 'company', 'status', 'city', 'state',
                        'owner_first_name', 'owner_last_name', 'owner_email', 'owner_title',
                        'website', 'company_linkedin', 'industry', 'revenue', 'product_category',
                        'business_type', 'employees', 'year_founded', 'owner_linkedin', 'phone',
                        'company_phone', 'owner_phone_number', 'street', 'bbb_rating'
                    }
                    
                    # Remove any fields that are not in valid_fields
                    lead_data = {k: v for k, v in lead_data.items() if k in valid_fields}
                    
                    # Add dynamic fields if provided
                    if dynamic_fields:
                        for db_field, csv_col in dynamic_fields.items():
                            if csv_col in df.columns and db_field in valid_fields:
                                value = row[csv_col]
                                if value != "-":
                                    lead_data[db_field] = str(value).strip()

                    # Try to add/update the lead
                    try:
                        # Clean and prepare the lead data
                        clean_lead_data = {}
                        for key, value in lead_data.items():
                            if value is not None and value != '' and value != "-":
                                if key == 'employees' and isinstance(value, str):
                                    try:
                                        clean_lead_data[key] = int(float(value))
                                    except (ValueError, TypeError):
                                        clean_lead_data[key] = None
                                elif key == 'revenue' and isinstance(value, str):
                                    try:
                                        value = value.replace('$', '').replace('M', '000000').replace('K', '000').replace('B', '000000000')
                                        clean_lead_data[key] = float(value)
                                    except (ValueError, TypeError):
                                        clean_lead_data[key] = None
                                elif key == 'year_founded' and isinstance(value, str):
                                    try:
                                        clean_lead_data[key] = str(int(float(value)))
                                    except (ValueError, TypeError):
                                        clean_lead_data[key] = None
                                elif key == 'search_keyword' and isinstance(value, dict):
                                    clean_lead_data[key] = value
                                else:
                                    clean_lead_data[key] = str(value).strip()

                        # Double check that we only have valid fields
                        clean_lead_data = {k: v for k, v in clean_lead_data.items() if k in valid_fields}

                        # Add/update the lead using the static method
                        try:
                            # Ensure we're passing a dictionary to add_or_update_lead_by_match
                            if not isinstance(clean_lead_data, dict):
                                raise ValueError("Lead data must be a dictionary")
                                
                            # Debugging to ensure the request is correct
                            print(f"Attempting to add/update lead: {clean_lead_data.get('company')}")
                            
                            result = LeadController.add_or_update_lead_by_match(clean_lead_data)
                            
                            # Handle the tuple return value
                            if isinstance(result, tuple) and len(result) == 2:
                                success, message = result
                                if success:
                                    if "updated successfully" in message:
                                        updated += 1
                                    elif "already up to date" in message:
                                        updated += 1  # Count as updated but wasn't changed
                                    else:
                                        added_new += 1
                                        
                                    # Verify lead actually exists in database
                                    verify_company = clean_lead_data.get('company')
                                    if verify_company:
                                        verify_lead = Lead.query.filter(
                                            db.func.lower(Lead.company) == db.func.lower(verify_company),
                                            Lead.deleted == False
                                        ).first()
                                        if verify_lead:
                                            if "updated successfully" in message:
                                                log_message = f"Success: {message} - Verified in DB with ID {verify_lead.lead_id}"
                                            elif "already up to date" in message:
                                                log_message = f"Success: {message} - No changes needed (ID {verify_lead.lead_id})"
                                            else:
                                                log_message = f"Success: {message} - Verified in DB with ID {verify_lead.lead_id}"
                                        else:
                                            log_message = f"Warning: {message} but not found in database verification check"
                                    else:
                                        log_message = f"Success: {message} - Unable to verify (no company name)"
                                    
                                    UploadController.log_error(filename, idx + 2, clean_lead_data, log_message)
                                else:
                                    # Check if it's a duplicate
                                    if "already exists" in message or "already in use" in message:
                                        skipped_duplicates += 1
                                        skipped_details.append(f"Row {idx+2}: {message}")
                                        UploadController.log_error(filename, idx + 2, clean_lead_data, f"Skipped (duplicate): {message}")
                                    else:
                                        errors += 1
                                        skipped_details.append(f"Row {idx+2}: {message}")
                                        UploadController.log_error(filename, idx + 2, clean_lead_data, f"Error: {message}")
                            else:
                                errors += 1
                                reason = f"Invalid return value from add_or_update_lead_by_match: {result}"
                                UploadController.log_error(filename, idx + 2, clean_lead_data, reason)
                                skipped_details.append(f"Row {idx+2}: {reason}")
                        except Exception as e:
                            errors += 1
                            reason = f"Error adding lead: {str(e)}"
                            UploadController.log_error(filename, idx + 2, clean_lead_data, reason)
                            skipped_details.append(f"Row {idx+2}: {reason}")
                            
                            # Try to print detailed error traceback
                            import traceback
                            print(f"Error traceback for row {idx+2}:")
                            traceback.print_exc()
                    except Exception as e:
                        errors += 1
                        reason = f"Error processing row: {str(e)}"
                        UploadController.log_error(filename, idx + 2, row.to_dict(), reason)
                        skipped_details.append(f"Row {idx+2}: {reason}")

                except Exception as e:
                    errors += 1
                    reason = f"Error processing row: {str(e)}"
                    UploadController.log_error(filename, idx + 2, row.to_dict(), reason)
                    skipped_details.append(f"Row {idx+2}: {reason}")

            return (added_new, updated), skipped_duplicates, skipped_empty_company, errors

        except pd.errors.EmptyDataError:
            UploadController.log_error(filename, 0, {}, "The CSV file is empty")
            raise Exception("The CSV file is empty")
        except pd.errors.ParserError:
            UploadController.log_error(filename, 0, {}, "Invalid CSV format")
            raise Exception("Invalid CSV format")
        except Exception as e:
            UploadController.log_error(filename, 0, {}, f"Error processing CSV: {str(e)}")
            raise Exception(f"Error processing CSV: {str(e)}")