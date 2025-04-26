# TODO:
# include all the fields mention by Patrik
# creating web for field mapping
# handling error if new user don't have each and every column data
#

from flask import Flask, request, render_template
import pandas as pd
import io
import re
import os
from datetime import datetime

app = Flask(__name__)

# simulated database (need to remove)
leads_db = []

# Paths
LOG_FILE = "upload_errors.log"
LEADS_OUTPUT_FILE = "leads_output.csv"

# Helper: Clean and Normalize Email
def clean_email(email):
    if pd.isna(email):
        return None
    return str(email).strip().lower()

# Helper: Clean and Normalize Phone
def clean_phone(phone):
    if pd.isna(phone):
        return None
    return re.sub(r'\D', '', str(phone))  # keep only numbers

# Helper: Validate Required Fields
def is_valid_row(name, email, phone):
    return all([name, email, phone])

# Helper: Check Duplicates (by email or phone)
def is_duplicate(email, phone):
    for lead in leads_db:
        if lead['email'] == email or lead['phone'] == phone:
            return True
    return False

# Helper: Log Errors to File (append mode)
def log_error(filename, row_number, name, email, phone, reason):
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {filename} Row {row_number}: {reason} ==> {name},{email},{phone}\n")

# Helper: Write Separator Between Upload Logs
def write_log_separator():
    with open(LOG_FILE, "a") as f:
        f.write("="*30 + "\n")

# Route: Home Page
@app.route("/", methods=["GET"])
def home():
    return render_template("upload.html")

# Route: Upload and Process CSV
@app.route("/upload", methods=["POST"])
def upload_csv():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']

    if file.filename == '':
        return "No selected file"

    filename = file.filename

    # Get user field mappings
    name_col = request.form.get('name_column')
    email_col = request.form.get('email_column')
    phone_col = request.form.get('phone_column')

    # Read CSV into DataFrame
    try:
        content = file.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(content))
    except Exception as e:
        return f"Failed to read CSV: {str(e)}"

    # Check columns exist
    for col in [name_col, email_col, phone_col]:
        if col not in df.columns:
            return f"Error: Column '{col}' not found in CSV."

    # Normalize fields and cleaning phone and email fields
    df['name'] = df[name_col].fillna("").astype(str).str.strip()
    df['email'] = df[email_col].apply(clean_email)
    df['phone'] = df[phone_col].apply(clean_phone)

    # Additional optional fields (safe fallback)
    df['company'] = df.get('Company', "").fillna("").astype(str).str.strip()
    df['city'] = df.get('City', "").fillna("").astype(str).str.strip()
    df['state'] = df.get('State', "").fillna("").astype(str).str.strip()
    df['first_name'] = df.get('First Name', "").fillna("").astype(str).str.strip()
    df['last_name'] = df.get('Last Name', "").fillna("").astype(str).str.strip()

    added = 0
    skipped_duplicates = 0
    errors = 0

    # Separator before new file log
    write_log_separator()

    # Process each lead
    for idx, row in df.iterrows():
        name = row['name']
        email = row['email']
        phone = row['phone']

        # checking the empty
        if not is_valid_row(name, email, phone):
            errors += 1
            log_error(filename, idx+2, name or "_", email or "_", phone or "_", "Missing required field (name, email, or phone)")
            continue

        if is_duplicate(email, phone):
            skipped_duplicates += 1
            continue

        # Add to leads database
        # add the data for database in here
        leads_db.append({
            "name": name,
            "email": email,
            "phone": phone,
            "company": row['company'],
            "city": row['city'],
            "state": row['state'],
            "first_name": row['first_name'],
            "last_name": row['last_name']
        })
        added += 1

    # After upload, save updated leads_db to CSV
    # Need to remove
    leads_df = pd.DataFrame(leads_db)
    leads_df.to_csv(LEADS_OUTPUT_FILE, index=False)


    # need to convert this result into the notification to the user
    result = f"""
    Upload Complete!<br>
    Leads Added: {added}<br>
    Duplicates Skipped: {skipped_duplicates}<br>
    Errors Logged: {errors}<br><br>
    <a href="/">Go Back</a><br>
    """
    return result

if __name__ == "__main__":
    app.run(debug=True)
