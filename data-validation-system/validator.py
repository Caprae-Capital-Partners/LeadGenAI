# validator.py
import time
import json
import logging
import re
from datetime import datetime, timedelta
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='chatgpt_validation.log'
)
logger = logging.getLogger('chatgpt_validator')

class ChatGPTValidator:
    """Uses OpenAI API to validate business data"""
    
    def __init__(self, email, password, headless=False, use_gpt4=True):
        """
        Initialize the validator
        
        Args:
            email: Not used
            password: API key
            headless: Not used
            use_gpt4: Not used
        """
        self.api_key = password
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        # Rate limiting tracking
        self.last_request_time = datetime.now()
        self.request_count = 0
        self.last_reset_time = datetime.now()
        
        logger.info("API client initialized successfully")
    
    def _apply_rate_limiting(self):
        """Apply rate limiting to avoid hitting API limits"""
        now = datetime.now()
        
        # Reset counter if more than 1 minute has passed
        if (now - self.last_reset_time) > timedelta(minutes=1):
            self.request_count = 0
            self.last_reset_time = now
        
        # If we've made 60 requests in the last minute, wait
        if self.request_count >= 60:
            time.sleep(1)
            self.request_count = 0
            self.last_reset_time = datetime.now()
        
        self.request_count += 1
    
    def validate_data_point(self, prompt):
        """
        Validate a data point using API
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Apply rate limiting
            self._apply_rate_limiting()
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare data
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            # Make API request
            response = requests.post(self.api_url, headers=headers, json=data)
            
            # Check for errors
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    'error': error_msg,
                    'confidence': 0.0,
                    'explanation': f'API request failed: {response.text}',
                    'flags': ['API error']
                }
            
            response_data = response.json()
            response_text = response_data['choices'][0]['message']['content']
            
            # Try to parse as JSON
            try:
                # Find JSON in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    validation_result = json.loads(json_str)
                    
                    # Ensure required fields are present
                    if 'confidence' not in validation_result:
                        validation_result['confidence'] = 0.0
                    if 'explanation' not in validation_result:
                        validation_result['explanation'] = 'No explanation provided'
                    if 'flags' not in validation_result:
                        validation_result['flags'] = []
                        
                    return validation_result
                else:
                    return {
                        'confidence': 0.0,
                        'explanation': 'Could not parse API response as JSON',
                        'flags': ['Parse error']
                    }
            except json.JSONDecodeError:
                return {
                    'confidence': 0.0,
                    'explanation': 'Invalid JSON in API response',
                    'flags': ['JSON error']
                }
                
        except Exception as e:
            logger.error(f"Error in validate_data_point: {str(e)}")
            return {
                'confidence': 0.0,
                'explanation': f'Error: {str(e)}',
                'flags': ['Exception']
            }

    def close(self):
        """Cleanup - not needed for API but kept for compatibility"""
        pass