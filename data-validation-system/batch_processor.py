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
            
        Returns:
            Path to the output file
        """
        try:
            # Check if input file exists
            if not os.path.exists(input_file):
                error_msg = f"Input file not found: {input_file}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"Created output directory: {output_dir}")
            
            # Read the input CSV with more robust error handling
            logger.info(f"Reading input file: {input_file}")
            try:
                # First attempt with standard parsing
                df = pd.read_csv(input_file)
            except pd.errors.ParserError as e:
                # If that fails, try with more options to handle problematic files
                logger.warning(f"CSV parsing error: {e}, trying with engine='python' and error_bad_lines=False")
                df = pd.read_csv(
                    input_file, 
                    engine='python',
                    on_bad_lines='skip',  # Skip bad lines instead of raising an error
                    escapechar='\\',      # Handle escaped characters
                    quoting=0  # Be flexible with quotes
                )
                logger.info(f"Successfully read file with alternative parser")
            
            # Basic validation of CSV content
            if len(df) == 0:
                logger.warning(f"Warning: Input file {input_file} has no rows")
                
            # Ensure required columns exist
            required_columns = ['Business Name', 'Company']
            if not any(col in df.columns for col in required_columns):
                error_msg = f"Input file must contain at least one of these columns: {required_columns}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            logger.info(f"Read {len(df)} rows from {input_file}")
            
            # Fill NaN values with empty strings for better processing
            # This prevents issues when accessing dictionary values
            for col in df.columns:
                df[col] = df[col].fillna('')
            
            # Check if output file already exists - we can resume
            if os.path.exists(output_file):
                logger.info(f"Output file exists: {output_file}")
                try:
                    output_df = pd.read_csv(output_file)
                    
                    # Find which rows have already been processed
                    processed_indices = []
                    for i, row in output_df.iterrows():
                        business_name = row.get('Business Name', '')
                        company_name = row.get('Company', '')
                        
                        # Use business name or company name to match rows
                        if business_name:
                            matching_indices = df[df['Business Name'] == business_name].index.tolist()
                            processed_indices.extend(matching_indices)
                        elif company_name:
                            matching_indices = df[df['Company'] == company_name].index.tolist()
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
                except Exception as e:
                    logger.error(f"Error reading existing output file: {e}")
                    logger.info("Starting fresh with all rows")
                    results = []
                    df_to_process = df
            else:
                results = []
                df_to_process = df
            
            logger.info(f"Processing {len(df_to_process)} rows")
            
            # Process in batches
            for start_idx in range(0, len(df_to_process), self.batch_size):
                end_idx = min(start_idx + self.batch_size, len(df_to_process))
                batch_df = df_to_process.iloc[start_idx:end_idx]
                
                batch_num = start_idx//self.batch_size + 1
                total_batches = (len(df_to_process) + self.batch_size - 1) // self.batch_size
                logger.info(f"Processing batch {batch_num}/{total_batches}: rows {start_idx} to {end_idx-1}")
                
                batch_results = self._process_batch(batch_df)
                results.extend(batch_results)
                
                # Save intermediate results
                try:
                    pd.DataFrame(results).to_csv(output_file, index=False)
                    logger.info(f"Saved intermediate results to {output_file} ({len(results)} rows)")
                except Exception as e:
                    logger.error(f"Error saving intermediate results: {e}")
                    # Try to save to a backup file
                    backup_file = f"{output_file}.backup.{int(time.time())}.csv"
                    try:
                        pd.DataFrame(results).to_csv(backup_file, index=False)
                        logger.info(f"Saved backup to {backup_file}")
                    except:
                        logger.error(f"Failed to save backup file")
            
            # Final save
            try:
                final_df = pd.DataFrame(results)
                final_df.to_csv(output_file, index=False)
                logger.info(f"Processing complete. Saved {len(final_df)} rows to {output_file}")
            except Exception as e:
                logger.error(f"Error saving final results: {e}")
                # Last attempt - save to a timestamped file
                final_backup = f"{output_file}.final.{int(time.time())}.csv"
                pd.DataFrame(results).to_csv(final_backup, index=False)
                logger.info(f"Saved final results to backup file: {final_backup}")
            
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
        
        for idx, row in batch_df.iterrows():
            # Convert row to dictionary with empty string for NaN values
            row_dict = {k: ('' if pd.isna(v) else v) for k, v in row.to_dict().items()}
            
            # Determine company name from available fields
            company_name = row_dict.get('Business Name', '') or row_dict.get('Company', 'Unknown')
            logger.info(f"Processing company: {company_name} (row {idx})")
            
            try:
                # Add a retry mechanism for validation
                max_retries = 2
                for retry in range(max_retries + 1):
                    try:
                        # Process based on batch mode
                        if self.batch_mode == 'batch':
                            # Batch mode - validate multiple data points at once
                            result_dict = self._process_company_batch_mode(row_dict)
                        else:
                            # Single mode - validate each data point separately
                            result_dict = self._process_company_single_mode(row_dict)
                        
                        # Successfully processed, break the retry loop
                        break
                    except Exception as retry_error:
                        if retry < max_retries:
                            logger.warning(f"Retry {retry+1}/{max_retries} for {company_name}: {retry_error}")
                            time.sleep(5)  # Wait before retrying
                        else:
                            # Max retries reached, re-raise the exception
                            raise
                
                # Add to results
                results.append(result_dict)
                
            except Exception as e:
                logger.error(f"Error processing company {company_name}: {e}")
                # Add error info to results
                error_dict = row_dict.copy()
                error_dict['validation_error'] = str(e)
                results.append(error_dict)
                
                # Add a short delay after an error to allow system recovery
                time.sleep(3)
        
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
        company_name = company_info.get('Business Name', '') or company_info.get('Company', 'Unknown')
        
        # Check and validate revenue if available
        if 'estimated_revenue' in company_info and company_info['estimated_revenue']:
            logger.info(f"Validating revenue for {company_name}")
            try:
                revenue_prompt = PromptTemplates.revenue_validation_prompt(company_info, company_info)
                revenue_validation = self.validator.validate_data_point(revenue_prompt)
                
                # Add validation results to result dictionary
                result_dict['revenue_confidence'] = revenue_validation.get('confidence', 0)
                result_dict['revenue_explanation'] = revenue_validation.get('explanation', '')
                result_dict['revenue_flags'] = json.dumps(revenue_validation.get('flags', []))
                logger.info(f"Revenue validation complete for {company_name} with confidence {revenue_validation.get('confidence', 0)}")
            except Exception as e:
                logger.error(f"Error validating revenue for {company_name}: {e}")
                result_dict['revenue_validation_error'] = str(e)
        
        # Check and validate employee count if available
        if 'Company Size' in company_info and company_info['Company Size']:
            logger.info(f"Validating employee count for {company_name}")
            try:
                employee_prompt = PromptTemplates.employee_count_validation_prompt(company_info)
                employee_validation = self.validator.validate_data_point(employee_prompt)
                
                # Add validation results to result dictionary
                result_dict['employee_count_confidence'] = employee_validation.get('confidence', 0)
                result_dict['employee_count_explanation'] = employee_validation.get('explanation', '')
                result_dict['employee_count_flags'] = json.dumps(employee_validation.get('flags', []))
                logger.info(f"Employee count validation complete for {company_name} with confidence {employee_validation.get('confidence', 0)}")
            except Exception as e:
                logger.error(f"Error validating employee count for {company_name}: {e}")
                result_dict['employee_count_validation_error'] = str(e)
        
        # Check and validate decision makers if available
        for i in range(1, 4):  # Up to 3 decision makers
            name_key = f'Decision Maker {i} Name'
            title_key = f'Decision Maker {i} Title'
            
            if name_key in company_info and company_info[name_key] and title_key in company_info and company_info[title_key]:
                logger.info(f"Validating decision maker {i} for {company_name}")
                
                try:
                    # Extract decision maker info
                    decision_maker = {
                        'name': company_info.get(f'Decision Maker {i} Name', ''),
                        'title': company_info.get(f'Decision Maker {i} Title', ''),
                        'source': company_info.get(f'Decision Maker {i} Source', '')
                    }
                    
                    dm_prompt = PromptTemplates.decision_maker_validation_prompt(company_info, decision_maker)
                    dm_validation = self.validator.validate_data_point(dm_prompt)
                    
                    # Add validation results to result dictionary
                    result_dict[f'decision_maker_{i}_confidence'] = dm_validation.get('confidence', 0)
                    result_dict[f'decision_maker_{i}_explanation'] = dm_validation.get('explanation', '')
                    result_dict[f'decision_maker_{i}_flags'] = json.dumps(dm_validation.get('flags', []))
                    logger.info(f"Decision maker {i} validation complete for {company_name} with confidence {dm_validation.get('confidence', 0)}")
                except Exception as e:
                    logger.error(f"Error validating decision maker {i} for {company_name}: {e}")
                    result_dict[f'decision_maker_{i}_validation_error'] = str(e)
        
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
        company_name = company_info.get('Business Name', '') or company_info.get('Company', 'Unknown')
        
        # Prepare data points to validate
        data_points = {}
        
        # Add revenue if available
        if 'estimated_revenue' in company_info and company_info['estimated_revenue']:
            data_points['revenue'] = {
                'value': company_info['estimated_revenue'],
                'source': company_info.get('source', 'Unknown')
            }
        
        # Add employee count if available
        if 'Company Size' in company_info and company_info['Company Size']:
            data_points['employee_count'] = {
                'value': company_info['Company Size'],
                'source': 'LinkedIn'
            }
        
        # Add decision makers if available
        for i in range(1, 4):  # Up to 3 decision makers
            name_key = f'Decision Maker {i} Name'
            title_key = f'Decision Maker {i} Title'
            
            if (name_key in company_info and company_info[name_key] and 
                title_key in company_info and company_info[title_key]):
                data_points[f'decision_maker_{i}'] = {
                    'value': f"{company_info[name_key]} - {company_info[title_key]}",
                    'source': company_info.get(f'Decision Maker {i} Source', 'Unknown')
                }
        
        # If we have data points to validate
        if data_points:
            logger.info(f"Validating {len(data_points)} data points in batch mode for {company_name}")
            try:
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
                    
                    logger.info(f"Batch validation complete for {company_name} with {len(data_point_results)} validated data points")
                else:
                    # Something went wrong with batch validation, add error info
                    error_msg = batch_validation.get('error', 'Unknown error in batch validation')
                    logger.warning(f"Batch validation failed for {company_name}: {error_msg}")
                    result_dict['validation_error'] = error_msg
                    
                    # Add raw response for debugging
                    if 'raw_response' in batch_validation:
                        result_dict['validation_raw_response'] = batch_validation['raw_response']
            except Exception as e:
                logger.error(f"Error in batch validation for {company_name}: {e}")
                result_dict['validation_error'] = str(e)
        else:
            logger.info(f"No data points to validate for {company_name}")
        
        return result_dict