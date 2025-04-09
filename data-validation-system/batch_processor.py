# batch_processor.py
import os
import pandas as pd
import json
import logging
import time
from datetime import datetime
from validator import ChatGPTValidator
from prompt_templates import PromptTemplates

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='batch_processor.log'
)
logger = logging.getLogger('batch_processor')

class BatchProcessor:
    """
    Process CSV files in batches for validation with ChatGPT
    """
    
    def __init__(self, validator, batch_mode='single', batch_size=5):
        """
        Initialize the batch processor
        
        Args:
            validator: ChatGPTValidator instance
            batch_mode: 'single' (one data point per request) or 'batch' (multiple points per request)
            batch_size: Number of rows to process in one batch (save interval)
        """
        self.validator = validator
        self.batch_mode = batch_mode
        self.batch_size = batch_size
    
    def process_file(self, input_file, output_file):
        """
        Process a CSV file and validate its data
        
        Args:
            input_file: Input CSV file path
            output_file: Output CSV file path
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Read the input CSV
            logger.info(f"Reading input file: {input_file}")
            df = pd.read_csv(input_file)
            logger.info(f"Read {len(df)} rows from {input_file}")
            
            # Check if output file already exists - we can resume
            if os.path.exists(output_file):
                logger.info(f"Output file exists: {output_file}")
                output_df = pd.read_csv(output_file)
                
                # Find which rows have already been processed
                processed_indices = []
                for i, row in output_df.iterrows():
                    business_name = row.get('Business Name', row.get('Company', ''))
                    if business_name:
                        matching_indices = df[
                            (df['Business Name'] == business_name) | 
                            (df['Company'] == business_name)
                        ].index.tolist()
                        processed_indices.extend(matching_indices)
                
                processed_indices = list(set(processed_indices))
                logger.info(f"Found {len(processed_indices)} rows already processed")
                
                # Filter remaining rows
                remaining_df = df.drop(processed_indices)
                
                # If all rows processed, exit
                if len(remaining_df) == 0:
                    logger.info("All rows already processed, nothing to do")
                    return output_file
                
                # Start with existing results
                results = output_df.to_dict('records')
                df_to_process = remaining_df
            else:
                results = []
                df_to_process = df
            
            logger.info(f"Processing {len(df_to_process)} rows")
            
            # Process in batches
            for start_idx in range(0, len(df_to_process), self.batch_size):
                end_idx = min(start_idx + self.batch_size, len(df_to_process))
                batch_df = df_to_process.iloc[start_idx:end_idx]
                
                logger.info(f"Processing batch {start_idx//self.batch_size + 1}: rows {start_idx} to {end_idx-1}")
                
                batch_results = self._process_batch(batch_df)
                results.extend(batch_results)
                
                # Save intermediate results
                pd.DataFrame(results).to_csv(output_file, index=False)
                logger.info(f"Saved intermediate results to {output_file} ({len(results)} rows)")
            
            # Final save
            final_df = pd.DataFrame(results)
            final_df.to_csv(output_file, index=False)
            logger.info(f"Processing complete. Saved {len(final_df)} rows to {output_file}")
            
            return output_file
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise
    
    def _process_batch(self, batch_df):
        """
        Process a batch of rows
        
        Args:
            batch_df: DataFrame with rows to process
            
        Returns:
            List of dictionaries with processed data
        """
        results = []
        
        for _, row in batch_df.iterrows():
            row_dict = row.to_dict()
            company_name = row_dict.get('Business Name', row_dict.get('Company', 'Unknown'))
            logger.info(f"Processing company: {company_name}")
            
            try:
                # Combine all company info
                company_info = row_dict.copy()
                
                # Process based on batch mode
                if self.batch_mode == 'batch':
                    # Batch mode - validate multiple data points at once
                    result_dict = self._process_company_batch_mode(company_info)
                else:
                    # Single mode - validate each data point separately
                    result_dict = self._process_company_single_mode(company_info)
                
                # Add to results
                results.append(result_dict)
                
            except Exception as e:
                logger.error(f"Error processing company {company_name}: {e}")
                # Add error info to results
                error_dict = row_dict.copy()
                error_dict['validation_error'] = str(e)
                results.append(error_dict)
        
        return results
    
    def _process_company_single_mode(self, company_info):
        """
        Process a single company by validating each data point separately
        
        Args:
            company_info: Dictionary with company data
            
        Returns:
            Dictionary with validation results
        """
        result_dict = company_info.copy()
        company_name = company_info.get('Business Name', company_info.get('Company', 'Unknown'))
        
        # Check and validate revenue if available
        if 'estimated_revenue' in company_info and company_info['estimated_revenue'] != 'Not found':
            logger.info(f"Validating revenue for {company_name}")
            revenue_prompt = PromptTemplates.revenue_validation_prompt(company_info, company_info)
            revenue_validation = self.validator.validate_data_point(revenue_prompt)
            
            # Add validation results to result dictionary
            result_dict['revenue_confidence'] = revenue_validation.get('confidence', 0)
            result_dict['revenue_explanation'] = revenue_validation.get('explanation', '')
            result_dict['revenue_flags'] = json.dumps(revenue_validation.get('flags', []))
        
        # Check and validate employee count if available
        if 'Company Size' in company_info and company_info['Company Size'] != 'Not found':
            logger.info(f"Validating employee count for {company_name}")
            employee_prompt = PromptTemplates.employee_count_validation_prompt(company_info)
            employee_validation = self.validator.validate_data_point(employee_prompt)
            
            # Add validation results to result dictionary
            result_dict['employee_count_confidence'] = employee_validation.get('confidence', 0)
            result_dict['employee_count_explanation'] = employee_validation.get('explanation', '')
            result_dict['employee_count_flags'] = json.dumps(employee_validation.get('flags', []))
        
        # Check and validate decision makers if available
        for i in range(1, 4):  # Up to 3 decision makers
            name_key = f'Decision Maker {i} Name'
            if name_key in company_info and company_info[name_key] != 'Not found':
                logger.info(f"Validating decision maker {i} for {company_name}")
                
                # Extract decision maker info
                decision_maker = {
                    'name': company_info.get(f'Decision Maker {i} Name', ''),
                    'title': company_info.get(f'Decision Maker {i} Title', ''),
                    'source': company_info.get(f'Decision Maker {i} Source', '')
                }
                
                # Only validate if we have both name and title
                if decision_maker['name'] and decision_maker['title']:
                    dm_prompt = PromptTemplates.decision_maker_validation_prompt(company_info, decision_maker)
                    dm_validation = self.validator.validate_data_point(dm_prompt)
                    
                    # Add validation results to result dictionary
                    result_dict[f'decision_maker_{i}_confidence'] = dm_validation.get('confidence', 0)
                    result_dict[f'decision_maker_{i}_explanation'] = dm_validation.get('explanation', '')
                    result_dict[f'decision_maker_{i}_flags'] = json.dumps(dm_validation.get('flags', []))
        
        return result_dict
    
    def _process_company_batch_mode(self, company_info):
        """
        Process a single company by validating multiple data points in one request
        
        Args:
            company_info: Dictionary with company data
            
        Returns:
            Dictionary with validation results
        """
        result_dict = company_info.copy()
        company_name = company_info.get('Business Name', company_info.get('Company', 'Unknown'))
        
        # Prepare data points to validate
        data_points = {}
        
        # Add revenue if available
        if 'estimated_revenue' in company_info and company_info['estimated_revenue'] != 'Not found':
            data_points['revenue'] = {
                'value': company_info['estimated_revenue'],
                'source': company_info.get('source', 'Unknown')
            }
        
        # Add employee count if available
        if 'Company Size' in company_info and company_info['Company Size'] != 'Not found':
            data_points['employee_count'] = {
                'value': company_info['Company Size'],
                'source': 'LinkedIn'
            }
        
        # Add decision makers if available
        for i in range(1, 4):  # Up to 3 decision makers
            name_key = f'Decision Maker {i} Name'
            title_key = f'Decision Maker {i} Title'
            if name_key in company_info and company_info[name_key] != 'Not found' and \
               title_key in company_info and company_info[title_key] != 'Not found':
                data_points[f'decision_maker_{i}'] = {
                    'value': f"{company_info[name_key]} - {company_info[title_key]}",
                    'source': company_info.get(f'Decision Maker {i} Source', 'Unknown')
                }
        
        # If we have data points to validate
        if data_points:
            logger.info(f"Validating {len(data_points)} data points for {company_name}")
            batch_prompt = PromptTemplates.batch_validation_prompt(company_info, data_points)
            batch_validation = self.validator.validate_data_point(batch_prompt)
            
            # Check if we got valid results
            if 'data_points' in batch_validation:
                data_point_results = batch_validation['data_points']
                
                # Process each data point result
                for point_name, validation in data_point_results.items():
                    if point_name == 'revenue':
                        result_dict['revenue_confidence'] = validation.get('confidence', 0)
                        result_dict['revenue_explanation'] = validation.get('explanation', '')
                        result_dict['revenue_flags'] = json.dumps(validation.get('flags', []))
                    elif point_name == 'employee_count':
                        result_dict['employee_count_confidence'] = validation.get('confidence', 0)
                        result_dict['employee_count_explanation'] = validation.get('explanation', '')
                        result_dict['employee_count_flags'] = json.dumps(validation.get('flags', []))
                    elif point_name.startswith('decision_maker_'):
                        dm_num = point_name.split('_')[-1]
                        result_dict[f'decision_maker_{dm_num}_confidence'] = validation.get('confidence', 0)
                        result_dict[f'decision_maker_{dm_num}_explanation'] = validation.get('explanation', '')
                        result_dict[f'decision_maker_{dm_num}_flags'] = json.dumps(validation.get('flags', []))
            else:
                # Something went wrong with batch validation, add error info
                logger.warning(f"Batch validation failed for {company_name}: {batch_validation.get('error', 'Unknown error')}")
                result_dict['validation_error'] = batch_validation.get('error', 'Unknown error')
        
        return result_dict