import pandas as pd
from io import BytesIO
import datetime
from models.lead_model import Lead
import openpyxl  # Required for Excel export

class ExportController:
    @staticmethod
    def export_leads_to_file(lead_ids, file_format='csv'):
        """
        Export selected leads to CSV or Excel
        Args:
            lead_ids (list): List of lead IDs to export
            file_format (str): Format to export ('csv' or 'excel')
        Returns:
            tuple: (BytesIO object, filename, mimetype) or (None, None, None) if no leads found
        """
        if not lead_ids:
            return None, None, None

        # Get leads from database
        leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
        
        if not leads:
            return None, None, None

        # Convert leads to list of dictionaries
        data = []
        for lead in leads:
            lead_dict = {
                'Company': lead.company,
                'First Name': lead.first_name,
                'Last Name': lead.last_name,
                'Email': lead.email,
                'Phone': lead.phone,
                'Title': lead.title,
                'City': lead.city,
                'State': lead.state,
                'Website': lead.website,
                'LinkedIn URL': lead.linkedin_url,
                'Industry': lead.industry,
                'Revenue': lead.revenue,
                'Product/Service Category': lead.product_service_category,
                'Business Type': lead.business_type,
                'Employees Range': lead.employees_range,
                'Year Founded': lead.year_founded,
                'Owner LinkedIn': lead.owner_linkedin,
                'Owner Age': lead.owner_age,
                'Score': lead.score,
                'Reasoning': lead.reasoning,
                'Notes': lead.additional_notes,
                'Subject Line 1': lead.subject_line_1,
                'Email Content 1': lead.email_customization_1,
                'Subject Line 2': lead.subject_line_2,
                'Email Content 2': lead.email_customization_2,
                'LinkedIn Message 1': lead.linkedin_customization_1,
                'LinkedIn Message 2': lead.linkedin_customization_2,
                'Created At': lead.created_at,
                'Updated At': lead.updated_at
            }
            data.append(lead_dict)

        # Create DataFrame
        df = pd.DataFrame(data)

        # Create BytesIO object
        output = BytesIO()
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if file_format.lower() == 'excel':
            # Export to Excel
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Leads')
            filename = f'exported_leads_{timestamp}.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            # Export to CSV
            df.to_csv(output, index=False, encoding='utf-8-sig')
            filename = f'exported_leads_{timestamp}.csv'
            mimetype = 'text/csv'

        output.seek(0)
        return output, filename, mimetype 