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
    
    def process_file(self, input_file: str, output_file: str) -> str:
        """Process a file in batches"""
        try:
            # Read input file
            df = pd.read_csv(input_file)
            
            # Check for required columns
            required_columns = ['Business Name', 'LinkedIn Link', 'Company Size']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Input file is missing required columns: {', '.join(missing_columns)}")
            
            # Initialize results list
            results = []
            
            # Process in batches
            for i in range(0, len(df), self.batch_size):
                batch = df.iloc[i:i + self.batch_size]
                batch_results = self.process_batch(batch)
                results.extend(batch_results)
                
                # Save progress after each batch
                pd.DataFrame(results).to_csv(output_file, index=False)
                print(f"Processed batch {i//self.batch_size + 1}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error processing file {input_file}: {e}")
            raise
    
    def process_batch(self, batch_df):
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
                    except Exception as e:
                        if retry == max_retries:
                            logger.error(f"Failed to process company {company_name} after {max_retries} retries: {e}")
                            result_dict = {
                                'error': str(e),
                                'confidence': 0.0,
                                'explanation': f'Error during validation: {str(e)}',
                                'flags': ['Validation error']
                            }
                        else:
                            logger.warning(f"Retry {retry + 1} for company {company_name}: {e}")
                            time.sleep(2)  # Wait before retrying
                
                # Add original data to result
                result_dict.update(row_dict)
                results.append(result_dict)
                
            except Exception as e:
                logger.error(f"Error processing company {company_name}: {e}")
                result_dict = {
                    'error': str(e),
                    'confidence': 0.0,
                    'explanation': f'Error during processing: {str(e)}',
                    'flags': ['Processing error']
                }
                result_dict.update(row_dict)
                results.append(result_dict)
        
        return results
    
    def _process_company_single_mode(self, company_info):
        """Process a single company's data points one at a time"""
        results = []
        
        # Extract company name
        company_name = company_info.get('Business Name', company_info.get('Company', ''))
        if not company_name:
            logger.warning("Skipping row with no company name")
            return results
        
        # Process each data point
        data_points = {
            'CEO': {
                'name': company_info.get('CEO Name', ''),
                'title': company_info.get('CEO Title', ''),
                'source': company_info.get('CEO Source', 'LinkedIn')
            },
            'Contact': {
                'email': company_info.get('Email', ''),
                'phone': company_info.get('Phone', ''),
                'source': company_info.get('Contact Source', 'LinkedIn')
            }
        }
        
        for point_name, point_data in data_points.items():
            try:
                if point_name == 'CEO':
                    prompt = self.prompt_templates.ceo_validation_prompt(company_info, point_data)
                elif point_name == 'Contact':
                    prompt = self.prompt_templates.contact_validation_prompt(company_info, point_data)
                else:
                    continue
                
                # Get validation result
                validation_result = self.validator.validate_data_point(prompt)
                
                # Add to results
                result = {
                    'Business Name': company_name,
                    'Data Point': point_name,
                    'Validation Result': validation_result
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing {point_name} for {company_name}: {e}")
                continue
        
        return results
    
    def _process_company_batch_mode(self, company_info):
        """Process multiple data points for a company in a single request"""
        results = []
        
        # Extract company name
        company_name = company_info.get('Business Name', company_info.get('Company', ''))
        if not company_name:
            logger.warning("Skipping row with no company name")
            return results
        
        # Prepare data points for batch validation
        data_points = {
            'CEO': {
                'value': f"{company_info.get('CEO Name', '')} ({company_info.get('CEO Title', '')})",
                'source': company_info.get('CEO Source', 'LinkedIn')
            },
            'Email': {
                'value': company_info.get('Email', ''),
                'source': company_info.get('Contact Source', 'LinkedIn')
            },
            'Phone': {
                'value': company_info.get('Phone', ''),
                'source': company_info.get('Contact Source', 'LinkedIn')
            }
        }
        
        try:
            # Get batch validation result
            prompt = self.prompt_templates.batch_validation_prompt(company_info, data_points)
            validation_result = self.validator.validate_data_point(prompt)
            
            # Add to results
            result = {
                'Business Name': company_name,
                'Data Points': data_points,
                'Validation Result': validation_result
            }
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing batch for {company_name}: {e}")
        
        return results