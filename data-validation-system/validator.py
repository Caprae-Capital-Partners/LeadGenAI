# validator.py
import time
import json
import re
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='chatgpt_validation.log'
)
logger = logging.getLogger('chatgpt_validator')

class ChatGPTValidator:
    """Uses ChatGPT to validate business data through browser automation"""
    
    def __init__(self, email, password, headless=False, use_gpt4=True):
        """
        Initialize the ChatGPT validator
        
        Args:
            email: ChatGPT account email
            password: ChatGPT account password
            headless: Run browser in headless mode (no GUI)
            use_gpt4: Try to use GPT-4 model when available
        """
        self.email = email
        self.password = password
        self.use_gpt4 = use_gpt4
        
        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Initialize WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.is_logged_in = False
        
        # Rate limiting tracking
        self.last_request_time = datetime.now()
        self.request_count = 0
        self.last_reset_time = datetime.now()
    
    def __del__(self):
        """Close browser when object is destroyed"""
        self.close()
    
    def login(self):
        """Log in to ChatGPT"""
        if self.is_logged_in:
            return True
            
        try:
            logger.info("Attempting to log in to ChatGPT")
            
            # Navigate to login page
            self.driver.get("https://chat.openai.com/auth/login")
            time.sleep(3)  # Wait for page to load
            
            # Click "Log in" button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in')]"))
            )
            login_button.click()
            
            # Wait for email input and enter email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.send_keys(self.email)
            
            # Click continue
            continue_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]")
            continue_button.click()
            
            # Wait for password input and enter password
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_input.send_keys(self.password)
            
            # Click login
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            
            # Wait for chat page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[contains(@placeholder, 'Message ChatGPT')]"))
            )
            
            self.is_logged_in = True
            logger.info("Successfully logged in to ChatGPT")
            
            # Select GPT-4 model if requested
            if self.use_gpt4:
                self._select_gpt4_model()
            
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _select_gpt4_model(self):
        """Try to select GPT-4 model"""
        try:
            # Click model selector button
            model_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Model') or contains(@class, 'model-switcher')]"))
            )
            model_button.click()
            time.sleep(1)
            
            # Try different possible selectors for GPT-4
            gpt4_selectors = [
                "//div[contains(text(), 'GPT-4') and not(contains(text(), 'Vision'))]",
                "//div[text()='GPT-4']",
                "//div[contains(@class, 'model') and contains(text(), 'GPT-4')]"
            ]
            
            for selector in gpt4_selectors:
                try:
                    gpt4_option = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    gpt4_option.click()
                    logger.info("Selected GPT-4 model")
                    return
                except:
                    continue
            
            logger.warning("Could not select GPT-4 model, using default")
        except Exception as e:
            logger.warning(f"Error selecting GPT-4 model: {e}")
    
    def validate_data_point(self, prompt):
        """
        Submit a validation prompt to ChatGPT and get the response
        
        Args:
            prompt: The validation prompt to submit
            
        Returns:
            Dict with validation results
        """
        # Rate limiting - ensure we don't exceed ChatGPT Plus limits
        self._apply_rate_limiting()
        
        if not self.is_logged_in:
            success = self.login()
            if not success:
                return {"error": "Not logged in to ChatGPT"}
        
        try:
            # Create a new chat
            try:
                new_chat_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@aria-label, 'New chat')]"))
                )
                new_chat_button.click()
                time.sleep(1)
            except:
                # If we can't find the new chat button, we might already be in a new chat
                pass
            
            # Find the input field
            input_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[contains(@placeholder, 'Message ChatGPT')]"))
            )
            
            # Type the prompt
            input_field.clear()
            input_field.send_keys(prompt)
            input_field.send_keys(Keys.RETURN)
            
            # Update request tracking
            self.request_count += 1
            self.last_request_time = datetime.now()
            
            # Wait for response to appear
            response_selector = "//div[contains(@class, 'markdown')]"
            
            # Wait for the typing indicator to disappear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'result-streaming')]"))
                )
                logger.info("ChatGPT is typing...")
            except:
                pass
                
            # Wait for response to complete (typing indicator to disappear)
            WebDriverWait(self.driver, 60).until_not(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'result-streaming')]"))
            )
            
            # Get the response
            time.sleep(2)  # Give a moment for the response to fully render
            response_elements = self.driver.find_elements(By.XPATH, response_selector)
            response_text = response_elements[-1].text if response_elements else ""
            
            logger.info(f"Received response from ChatGPT ({len(response_text)} chars)")
            
            # Extract the JSON from the response
            try:
                # Try to find JSON in the response
                json_match = re.search(r'({[\s\S]*})', response_text)
                if json_match:
                    json_str = json_match.group(1)
                    validation = json.loads(json_str)
                else:
                    # Try to extract values directly with regex
                    confidence_match = re.search(r'confidence"?\s*:\s*([0-9.]+)', response_text)
                    confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                    
                    explanation_match = re.search(r'explanation"?\s*:\s*"([^"]+)"', response_text)
                    explanation = explanation_match.group(1) if explanation_match else "Could not extract explanation"
                    
                    validation = {
                        "confidence": confidence,
                        "explanation": explanation,
                        "flags": []
                    }
                
                # Add raw response for reference
                validation["raw_response"] = response_text
                return validation
            except Exception as e:
                logger.error(f"Error extracting validation from response: {e}")
                return {
                    "confidence": 0.4,
                    "explanation": f"Error extracting validation: {str(e)}",
                    "flags": ["PARSING_ERROR"],
                    "raw_response": response_text
                }
                
        except Exception as e:
            logger.error(f"Error validating data point: {e}")
            # Attempt to recover by refreshing if needed
            if "stale element reference" in str(e).lower():
                self.driver.refresh()
                time.sleep(5)
                self.is_logged_in = False
            return {
                "confidence": 0.0,
                "explanation": f"Error: {str(e)}",
                "flags": ["VALIDATION_ERROR"]
            }
    
    def _apply_rate_limiting(self):
        """Apply rate limiting to respect ChatGPT Plus limits"""
        current_time = datetime.now()
        
        # Check if we need to reset the counter (3-hour window)
        if (current_time - self.last_reset_time) > timedelta(hours=3):
            logger.info("Resetting rate limit counter (3-hour window passed)")
            self.request_count = 0
            self.last_reset_time = current_time
        
        # If we've hit the limit, wait until reset
        if self.request_count >= 50:
            wait_time = self.last_reset_time + timedelta(hours=3) - current_time
            wait_seconds = max(10, wait_time.total_seconds())
            logger.warning(f"Rate limit reached. Waiting {wait_seconds/60:.1f} minutes before continuing")
            time.sleep(wait_seconds)
            # Reset after waiting
            self.request_count = 0
            self.last_reset_time = datetime.now()
        
        # Always add a small delay between requests
        time_since_last_request = (current_time - self.last_request_time).total_seconds()
        if time_since_last_request < 15:  # Minimum 15 seconds between requests
            time.sleep(15 - time_since_last_request)
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.is_logged_in = False
            logger.info("Browser closed")