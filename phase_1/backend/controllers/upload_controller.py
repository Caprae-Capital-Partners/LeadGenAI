import pandas as pd
import io
import re
import chardet
from datetime import datetime
from models.lead_model import db, Lead

class UploadController:
    @staticmethod
    def log_error(filename, row_number, data, reason):
        log_file = "upload_errors.log"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {filename} Row {row_number}: {reason} ")
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
    def is_valid_row(name, email, phone):
        # Make all fields optional as requested
        return True

    @staticmethod
    def detect_encoding(content):
        # Use chardet to detect encoding
        result = chardet.detect(content)
        encoding = result['encoding']
        confidence = result['confidence']
        
        # If confidence is low, fall back to reliable encodings
        if confidence < 0.7:
            # Try these encodings in order
            for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']:
                try:
                    content.decode(enc)
                    return enc
                except UnicodeDecodeError:
                    continue
                
        return encoding or 'latin-1'  # Fallback to latin-1 which can handle any byte value

    @staticmethod
    def process_csv_file(file, name_col=None, email_col=None, phone_col=None, dynamic_fields=None):
        filename = file.filename
        UploadController.write_log_separator(filename)

        try:
            content = file.read()
            
            # Detect encoding
            encoding = UploadController.detect_encoding(content)
            
            # Try multiple encodings if the detected one fails
            for enc in [encoding, 'latin-1', 'windows-1252', 'utf-8-sig', 'iso-8859-1']:
                try:
                    decoded_content = content.decode(enc)
                    df = pd.read_csv(io.StringIO(decoded_content))
                    break
                except (UnicodeDecodeError, pd.errors.ParserError):
                    if enc == 'iso-8859-1':  # Last resort encoding
                        # If all encodings fail, try reading directly as bytes with a more permissive parser
                        df = pd.read_csv(io.BytesIO(content), encoding='latin-1', on_bad_lines='skip', 
                                        encoding_errors='replace')
                    continue
            
            df.columns = df.columns.str.strip()
            
            # Handle optional fields (as requested by user)
            if name_col and name_col in df.columns:
                df['full_name'] = df[name_col].astype(str).fillna("").str.strip()
                # Split name if available
                def split_name(name):
                    parts = name.strip().split()
                    if len(parts) == 0:
                        return "", ""
                    elif len(parts) == 1:
                        return parts[0], ""
                    else:
                        return parts[0], " ".join(parts[1:])
                df['first_name'], df['last_name'] = zip(*df['full_name'].map(split_name))
            else:
                df['full_name'] = ""
                df['first_name'] = ""
                df['last_name'] = ""
                
            if email_col and email_col in df.columns:
                df['email'] = df[email_col].apply(UploadController.clean_email)
            else:
                df['email'] = None
                
            if phone_col and phone_col in df.columns:
                df['phone'] = df[phone_col].apply(UploadController.clean_phone)
            else:
                df['phone'] = None

            added = 0
            skipped_duplicates = 0
            errors = 0

            for idx, row in df.iterrows():
                name = row.get('full_name', '')
                email = row.get('email', None)
                phone = row.get('phone', None)
                first_name = row.get('first_name', '')
                last_name = row.get('last_name', '')

                # Check for duplicates only if email or phone is provided
                existing_lead = None
                if email or phone:
                    query = []
                    if email:
                        query.append(Lead.email == email)
                    if phone:
                        query.append(Lead.phone == phone)
                    
                    if query:
                        existing_lead = Lead.query.filter(db.or_(*query)).first()

                if existing_lead:
                    skipped_duplicates += 1
                    UploadController.log_error(
                        filename,
                        idx + 2,
                        {
                            'name': name,
                            'email': email,
                            'phone': phone
                        },
                        "Duplicate entry found"
                    )
                    continue

                try:
                    lead_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'full_name': name,
                        'email': email,
                        'phone': phone
                    }
                    
                    # Add dynamic fields
                    if dynamic_fields:
                        for db_field, csv_col in dynamic_fields.items():
                            if csv_col in df.columns:
                                lead_data[db_field] = row[csv_col]
                    
                    lead = Lead(**lead_data)
                    db.session.add(lead)
                    added += 1
                except Exception as e:
                    errors += 1
                    UploadController.log_error(
                        filename,
                        idx + 2,
                        {
                            'name': name,
                            'email': email,
                            'phone': phone
                        },
                        f"Database error: {str(e)}"
                    )
                    continue

            return added, skipped_duplicates, errors

        except pd.errors.EmptyDataError:
            UploadController.log_error(filename, 0, {}, "The CSV file is empty")
            raise Exception("The CSV file is empty")
        except pd.errors.ParserError as e:
            UploadController.log_error(filename, 0, {}, f"Invalid CSV format: {str(e)}")
            raise Exception(f"Invalid CSV format: {str(e)}")
        except Exception as e:
            UploadController.log_error(filename, 0, {}, f"Error processing CSV: {str(e)}")
            raise Exception(f"Error processing CSV: {str(e)}")