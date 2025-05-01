import csv
from io import StringIO, BytesIO
import datetime
from models.lead_model import Lead

class ExportController:
    @staticmethod
    def export_leads_to_csv(lead_ids):
        """
        Export selected leads to CSV
        Args:
            lead_ids (list): List of lead IDs to export
        Returns:
            tuple: (BytesIO object, filename) or (None, None) if no leads found
        """
        if not lead_ids:
            return None, None

        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        
        # Write headers - using the field names from our model
        headers = ['ID', 'Company', 'First Name', 'Last Name', 'Email', 'Phone', 'Title',
                  'City', 'State', 'Website', 'LinkedIn URL', 'Industry', 'Revenue',
                  'Product/Service Category', 'Business Type', 'Employees Range',
                  'Year Founded', 'Owner LinkedIn', 'Owner Age', 'Score', 'Reasoning',
                  'Notes', 'Subject Line 1', 'Email Content 1', 'Subject Line 2',
                  'Email Content 2', 'LinkedIn Message 1', 'LinkedIn Message 2',
                  'Created At', 'Updated At']
        
        writer.writerow(headers)
        
        # Get leads from database
        leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
        
        if not leads:
            return None, None
        
        # Write data rows
        for lead in leads:
            row = [
                lead.id, lead.company, lead.first_name, lead.last_name,
                lead.email, lead.phone, lead.title, lead.city, lead.state,
                lead.website, lead.linkedin_url, lead.industry, lead.revenue,
                lead.product_service_category, lead.business_type, lead.employees_range,
                lead.year_founded, lead.owner_linkedin, lead.owner_age, lead.score,
                lead.reasoning, lead.additional_notes, lead.subject_line_1,
                lead.email_customization_1, lead.subject_line_2, lead.email_customization_2,
                lead.linkedin_customization_1, lead.linkedin_customization_2,
                lead.created_at, lead.updated_at
            ]
            writer.writerow(row)
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'exported_leads_{timestamp}.csv'
        
        # Convert to BytesIO
        output = BytesIO()
        output.write(si.getvalue().encode('utf-8-sig'))  # utf-8-sig for Excel compatibility
        output.seek(0)  # Move cursor to start
        
        return output, filename 