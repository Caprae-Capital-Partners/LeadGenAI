# main.py
import os
import argparse
import logging
from datetime import datetime
from validator import ChatGPTValidator
from batch_processor import BatchProcessor
from utils import save_validation_summary, merge_validation_results

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=f'validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)
logger = logging.getLogger('main')

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Validate business data using ChatGPT')
    
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--email', required=True, help='ChatGPT account email')
    parser.add_argument('--password', required=True, help='ChatGPT account password')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of companies to process before saving')
    parser.add_argument('--batch-mode', choices=['single', 'batch'], default='single', 
                      help='Process data points individually or in batches')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--summary', default=None, help='Path to save validation summary JSON')
    
    return parser.parse_args()

def main():
    """Main function to run the validation process"""
    # Parse command line arguments
    args = parse_args()
    
    try:
        # Log start
        logger.info(f"Starting validation process for {args.input}")
        print(f"Starting validation process for {args.input}")
        
        # Initialize the validator
        validator = ChatGPTValidator(
            email=args.email,
            password=args.password,
            headless=args.headless,
            use_gpt4=True  # Try to use GPT-4 when available
        )
        
        # Initialize the batch processor
        processor = BatchProcessor(
            validator=validator,
            batch_mode=args.batch_mode,
            batch_size=args.batch_size
        )
        
        # Process the file
        output_file = processor.process_file(args.input, args.output)
        
        # Generate summary if requested
        if args.summary:
            import pandas as pd
            df = pd.read_csv(output_file)
            summary = save_validation_summary(df, args.summary)
            print(f"Validation summary saved to {args.summary}")
        
        # Clean up
        validator.close()
        
        logger.info("Validation process completed successfully")
        print("Validation process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in validation process: {e}")
        print(f"Error in validation process: {e}")
        raise

if __name__ == "__main__":
    main()