import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import os
import json
import socket
from dotenv import load_dotenv
import csv
import random  # Add random module for randomized wait times
import threading  # Add threading module for timeout monitoring
import re
import spacy
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline

try:
    nltk.download('punkt', quiet=True)
except:
    logging.warning("Failed to download NLTK punkt. Sentence tokenization may be limited.")


# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global WebDriver instance that can be reused
global_driver = None

# File to store Chrome debugging port
CHROME_INFO_FILE = 'chrome_debug_info.json'

# Debug folder path
DEBUG_FOLDER = 'debug'
# Ensure debug folder exists
os.makedirs(DEBUG_FOLDER, exist_ok=True)

# Port range for Chrome debugging
DEBUG_PORT_START = 9222
DEBUG_PORT_END = 9230

# Check if a port is available
def is_port_available(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', port))
        s.close()
        return True
    except:
        return False

# Find an available port for Chrome debugging
def find_available_port():
    for port in range(DEBUG_PORT_START, DEBUG_PORT_END + 1):
        if is_port_available(port):
            return port
    return None

# Save Chrome debugging information to a file
def save_chrome_info(port, user_data_dir):
    chrome_info = {
        'port': port,
        'user_data_dir': user_data_dir
    }
    with open(CHROME_INFO_FILE, 'w') as f:
        json.dump(chrome_info, f)
    logging.info(f"Chrome debugging info saved to {CHROME_INFO_FILE}")

# Load Chrome debugging information from file
def load_chrome_info():
    if os.path.exists(CHROME_INFO_FILE):
        try:
            with open(CHROME_INFO_FILE, 'r') as f:
                chrome_info = json.load(f)
            return chrome_info
        except Exception as e:
            logging.error(f"Error loading Chrome info: {e}")
    return None

# Function to check if Chrome is still running on the debug port
def is_chrome_running(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('localhost', port))
        s.close()
        return result == 0  # If result is 0, port is open and Chrome is running
    except:
        return False

# Function to check if the driver is still active/valid
def is_driver_active(driver):
    if driver is None:
        return False
    try:
        # Try to get the current URL as a simple check that the driver is still working
        current_url = driver.current_url
        return True
    except:
        return False

# Function to read the CSV file
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Successfully read CSV file: {file_path}")
        return df
    except Exception as e:
        logging.error(f"Error reading CSV file {file_path}: {e}")
        raise

# Function to handle manual intervention for security checkpoints
def wait_for_manual_intervention(driver, message):
    """
    Pauses script execution to allow user to manually complete security checks.
    
    Args:
        driver: Selenium WebDriver instance
        message: Message to display to user
    
    Returns:
        True when user confirms they've completed the action
    """
    logging.info(f"MANUAL INTERVENTION REQUIRED: {message}")
    print("\n" + "="*80)
    print(f"ATTENTION: {message}")
    print("The browser window is now open for you to complete this action manually.")
    print("When you have completed the security check, press Enter to continue.")
    print("="*80 + "\n")
    
    input("Press Enter when you have completed the security verification...")
    logging.info("User confirmed manual intervention completed")
    time.sleep(1)  # Give a moment for page to settle after manual action
    return True

# Function to log in to LinkedIn
def login_to_linkedin(driver, username, password):
    logging.info("Checking LinkedIn login status")
    
    # First check if we're already logged in by visiting LinkedIn homepage
    driver.get('https://www.linkedin.com/')
    time.sleep(0.5 + 0.5 * random.random())
    
    current_url = driver.current_url
    logging.info(f"Current URL: {current_url}")
    
    # Check for signs of being already logged in
    if ("feed" in current_url or 
        "mynetwork" in current_url or 
        "/in/" in current_url):
        logging.info("User is already logged in to LinkedIn. Skipping login process.")
        print("Already logged in to LinkedIn. Continuing with scraping.")
        return
    
    # Try to find elements that are only visible when logged in
    try:
        # Check for common elements that appear when logged in
        logged_in_elements = driver.find_elements(By.ID, 'global-nav')
        if logged_in_elements:
            logging.info("Found global nav element - user appears to be logged in already")
            print("Already logged in to LinkedIn. Continuing with scraping.")
            return
    except Exception as e:
        logging.info(f"Error checking for logged-in elements: {e}")
    
    # If we're here, we need to log in
    logging.info("User is not logged in. Proceeding with login process.")
    print("Not logged in. Attempting to log in to LinkedIn...")
    
    driver.get('https://www.linkedin.com/login')
    time.sleep(0.5 + 0.5 * random.random())  # Reduced from 5 seconds
    
    try:
        # Wait for the username and password fields to be present
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'password'))
        )
        
        # Type slower like a human
        for char in username:
            username_field.send_keys(char)
            time.sleep(0.1)  # Back to the original typing speed
            
        for char in password:
            password_field.send_keys(char)
            time.sleep(0.1)  # Back to the original typing speed
        
        # Wait for the login button to be clickable
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        time.sleep(0.5 + 0.5 * random.random())  # Reduced from 2 seconds
        login_button.click()
        
        # Wait longer after login to ensure page loads
        time.sleep(1)  
        
        # Check for security checkpoint or CAPTCHA
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            # Check for various security checkpoint indicators
            if ("checkpoint" in current_url or 
                "login" in current_url or 
                "captcha" in page_source or 
                "security verification" in page_source or
                "unusual login activity" in page_source or
                "verify your identity" in page_source):
                
                # Take a screenshot for debugging
                screenshot_path = os.path.join(DEBUG_FOLDER, "security_checkpoint.png")
                driver.save_screenshot(screenshot_path)
                logging.info(f"Security checkpoint detected. Screenshot saved to {screenshot_path}")
                
                # Ask user to manually complete the security check
                wait_for_manual_intervention(driver, 
                    "LinkedIn security checkpoint or CAPTCHA detected. Please complete the verification in the browser window.")
                
                # After manual intervention, check if we're logged in
                time.sleep(1)  # Wait a bit for page to update
                
                if "feed" in driver.current_url or "mynetwork" in driver.current_url:
                    logging.info("Successfully logged in after manual intervention")
                    break
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logging.error("Maximum retries reached for security checkpoint")
                        raise Exception("Failed to pass LinkedIn security checkpoint after multiple attempts")
                    logging.info(f"Still not logged in after manual intervention. Retry {retry_count}/{max_retries}")
            else:
                # No security checkpoint detected, we're good
                break
        
        # Final check if login succeeded
        if "feed" not in driver.current_url and "mynetwork" not in driver.current_url:
            logging.warning("Login might not be successful. Current URL: " + driver.current_url)
        else:
            logging.info("Successfully logged in to LinkedIn")
        
    except Exception as e:
        logging.error(f"Error during login process: {e}")
        raise

# Function to scrape LinkedIn for business details
def scrape_linkedin(driver, business_name, expected_city=None, expected_state=None):
    logging.info(f"Searching for business: {business_name}")
    print(f"Searching for: {business_name}")
    
    # Format the business name for the URL (replace spaces with %20)
    formatted_name = business_name.replace(' ', '%20')
    url = f"https://www.linkedin.com/search/results/companies/?keywords={formatted_name}"
    
    try:
        print(f"Navigating to search URL: {url}")
        
        # Set a page load timeout to prevent hanging
        driver.set_page_load_timeout(30)  # 30 seconds timeout
        
        try:
            driver.get(url)
        except Exception as timeout_error:
            print(f"Page load timed out: {timeout_error}")
            logging.warning(f"Page load timed out: {timeout_error}")
            # Try to refresh the page
            driver.refresh()
            time.sleep(1)
            
        time.sleep(0.5 + 0.5 * random.random())  # Reduced from 5 seconds
        
        # Check the current URL to see if we were redirected to a captcha page
        current_url = driver.current_url
        if "checkpoint/challenge" in current_url or "captcha" in current_url.lower():
            logging.warning("Redirected to a security checkpoint or captcha")
            
            # Take a screenshot for debugging
            driver.save_screenshot("security_checkpoint.png")
            
            raise Exception("Security checkpoint detected. Please check the browser.")
            
        logging.info(f"Current URL after search: {driver.current_url}")
        
        # Try multiple selectors to find company results
        selectors = [
            "//a[contains(@class, 'app-aware-link') and contains(@href, '/company/')]",
            "//div[contains(@class, 'search-results')]//*[contains(@href, '/company/')]",
            "//ul[contains(@class, 'reusable-search__entity-result-list')]/li//a[contains(@href, '/company/')]",
            "//span[contains(@class, 'entity-result__title')]//a[contains(@href, '/company/')]"
        ]
        
        company_links = None
        used_selector = None
        
        # Try each selector until we find company links
        for selector in selectors:
            try:
                logging.info(f"Trying selector: {selector}")
                print(f"Trying selector: {selector}")
                company_links = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                if company_links:
                    used_selector = selector
                    print(f"Found {len(company_links)} company links using selector: {selector}")
                    logging.info(f"Found {len(company_links)} company links using selector: {selector}")
                    break
            except Exception as e:
                logging.warning(f"Selector {selector} failed: {e}")
                print(f"Selector {selector} failed: {e}")
        
        if not company_links:
            screenshot_path = os.path.join(DEBUG_FOLDER, f"search_results_{business_name.replace(' ', '_')}.png")
            driver.save_screenshot(screenshot_path)
            print(f"No results found for {business_name}. Screenshot saved to {screenshot_path}")
            logging.warning(f"No results found for {business_name}. Screenshot saved to {screenshot_path}")
            return {
                'LinkedIn Link': None,
                'Company Website': None,
                'Company Size': None,
                'Industry': None,
                'Headquarters': None,
                'Founded': None,
                'Specialties': None,
                'Location Match': "No results found"
            }
        
        for i, link in enumerate(company_links[:5]): 
            try:
                href = link.get_attribute('href')
                text = link.text
                logging.info(f"Link {i}: href={href}, text={text}")
            except:
                logging.info(f"Link {i}: Could not get attributes")
        
        # NEW LOCATION VALIDATION LOGIC
        # If expected city and state are provided, try to find a matching company
        matched_company = None
        location_match_status = "Not found"  # Simplified default status
        
        if expected_city and expected_state:
            print(f"Looking for a company in {expected_city}, {expected_state}")
            logging.info(f"Looking for a company in {expected_city}, {expected_state}")
            
            # Normalize expected location for comparison
            expected_city = expected_city.strip().lower()
            expected_state = expected_state.strip().lower()
            
            # First, try to find location information in search results
            for i, link in enumerate(company_links[:min(5, len(company_links))]):
                # Get the parent elements to find location information
                try:
                    # Try multiple approaches to find location
                    # 1. First try to get the parent container and look for location text
                    parent_container = link
                    for _ in range(5):  # Try up to 5 levels up
                        if parent_container:
                            parent_container = parent_container.find_element(By.XPATH, "./..")
                            container_text = parent_container.text
                            
                            # Check for location in the container text
                            if container_text:
                                logging.info(f"Container text for link {i}: {container_text}")
                                print(f"Evaluating container text for link {i}: {container_text}")
                                
                                # Split the container text into lines for better parsing
                                lines = container_text.lower().split('\n')
                                
                                # Look specifically for location lines that might contain city/state
                                for line in lines:
                                    # Common location patterns in LinkedIn search results
                                    if any(location_indicator in line for location_indicator in ['location', 'headquarter', 'based in', ' in ']):
                                        logging.info(f"Potential location line: {line}")
                                        print(f"Potential location line: {line}")
                                    
                                    # Check for city match
                                    city_match = city_names_match(expected_city, line)
                                    # Check for state match
                                    state_match = state_in_text(expected_state, line)
                                    
                                    # Accept both strong matches (city AND state) and partial matches (city OR state)
                                    if city_match and state_match:
                                        matched_company = link
                                        # Simplified status - just "Location matched" instead of detailed description
                                        location_match_status = "Location matched"
                                        print(f"Strong location match found: {line}")
                                        logging.info(f"Strong location match found: {line}")
                                        break
                                    elif city_match:
                                        matched_company = link
                                        # Simplified status - just "Location matched" instead of detailed description
                                        location_match_status = "Location matched"
                                        print(f"Partial location match (city only) found: {line}")
                                        logging.info(f"Partial location match (city only) found: {line}")
                                        # Don't break here to keep looking for a strong match
                                    elif state_match:
                                        matched_company = link
                                        # Simplified status - just "Location matched" instead of detailed description
                                        location_match_status = "Location matched"
                                        print(f"Partial location match (state only) found: {line}")
                                        logging.info(f"Partial location match (state only) found: {line}")
                                        # Don't break here to keep looking for a strong match
                                    
                                    # Old way - required both city and state
                                    # if ((city_names_match(expected_city, line)) and 
                                    #    (state_in_text(expected_state, line))):
                                            
                                    #    matched_company = link
                                    #    location_match_status = f"Strong match found: both {expected_city} and {expected_state} in '{line}'"
                                    #    print(f"Strong location match found: {line}")
                                    #    logging.info(f"Strong location match found: {line}")
                                    #    break
                                
                                # Fallback: check if both city and state are in the entire container text
                                if not matched_company:
                                    # Check for city match with normalization
                                    container_city_match = city_names_match(expected_city, container_text)
                                    
                                    # Check for state match using our improved function
                                    container_state_match = state_in_text(expected_state, container_text)
                                    
                                    if container_city_match and container_state_match:
                                        matched_company = link
                                        # Simplified status
                                        location_match_status = "Location matched"
                                        print(f"Location match found in complete text: {expected_city}, {expected_state}")
                                        logging.info(f"Location match found in complete text: {expected_city}, {expected_state}")
                                        break
                                    elif container_city_match:
                                        matched_company = link
                                        # Simplified status
                                        location_match_status = "Location matched"
                                        print(f"Partial location match (city only) in container text")
                                        logging.info(f"Partial location match (city only) in container text")
                                        # Don't break to keep looking for a stronger match
                                    elif container_state_match:
                                        matched_company = link
                                        # Simplified status
                                        location_match_status = "Location matched"
                                        print(f"Partial location match (state only) in container text")
                                        logging.info(f"Partial location match (state only) in container text")
                                        # Don't break to keep looking for a stronger match
                    
                    # If a strong match found in this iteration, break out of the loop
                    if matched_company and "Strong match" in location_match_status:
                        break
                        
                except Exception as e:
                    logging.warning(f"Error checking location for link {i}: {e}")
                    print(f"Error checking location for link {i}: {e}")

            # If we only have a partial match but there are more links to check, continue looking
            partial_match = None
            partial_match_status = None
            if False and matched_company and "Partial match" in location_match_status and len(company_links) > 1:
                # DISABLED THIS SECTION - we now accept partial matches as valid
                partial_match = matched_company  # Store the partial match
                partial_match_status = location_match_status
                matched_company = None  # Reset to keep searching
                location_match_status = "Continuing search after partial match"
            
            # Add confirmation message when we find any match
            if matched_company:
                print(f"Found a valid location match. Using this company without further validation.")
                logging.info(f"Found a valid location match. Using this company without further validation.")
            
            # If no match found in search results, we'll need to check each company page
            if not matched_company and len(company_links) > 0:
                logging.info("No location match found in search results, will check individual company pages")
                print("No location match found in search results, will check individual company pages")
                
                # We'll check the first few results
                for i, link in enumerate(company_links[:min(3, len(company_links))]):
                    try:
                        # Save the search results URL so we can come back to it
                        search_results_url = driver.current_url
                        
                        # Click on this result
                        company_link = link.get_attribute('href')
                        logging.info(f"Checking company {i+1}: {company_link}")
                        print(f"Checking company {i+1}: {company_link}")
                        
                        try:
                            link.click()
                        except Exception as e:
                            logging.warning(f"Direct click failed: {e}")
                            try:
                                driver.execute_script("arguments[0].click();", link)
                            except Exception as e2:
                                logging.warning(f"JavaScript click also failed: {e2}")
                                driver.get(company_link)
                        
                        # Wait for the page to load
                        time.sleep(0.5 + 0.5 * random.random())
                        
                        # Try to find the headquarters or location information
                        try:
                            # Look for "Headquarters" section
                            headquarters_selectors = [
                                "//dt[contains(.//text(), 'Headquarters')]/following-sibling::dd[1]",
                                "//h3[contains(text(), 'Headquarters')]/following-sibling::dd",
                                "//span[contains(text(), 'Headquarters')]/following::dd[1]",
                                "//div[contains(text(), 'Headquarters')]/following-sibling::div",
                                "//div[contains(text(), 'Headquarters')]/../following-sibling::*",
                                "//dt[contains(text(), 'Headquarters')]/following-sibling::dd"
                            ]
                            
                            # Log the page contents for debugging
                            logging.info("Examining company page to find headquarters information")
                            
                            # First, do a scan of the full page for headquarters
                            try:
                                full_page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                                if "headquarters" in full_page_text:
                                    logging.info("Found 'headquarters' in full page text, searching for specific elements")
                                    
                                    # Try to capture the context around headquarters
                                    lines = full_page_text.split("\n")
                                    for i, line in enumerate(lines):
                                        if "headquarters" in line:
                                            context_start = max(0, i-2)
                                            context_end = min(len(lines), i+3)
                                            context = "\n".join(lines[context_start:context_end])
                                            logging.info(f"Headquarters context: {context}")
                                            
                                            # Check if city or state is in this context
                                            city_in_context = city_names_match(expected_city, context)
                                            state_in_context = state_in_text(expected_state, context)
                                            if city_in_context or state_in_context:
                                                matched_company = link
                                                match_details = []
                                                if city_in_context:
                                                    match_details.append(f"city '{expected_city}'")
                                                if state_in_context:
                                                    match_details.append(f"state '{expected_state}'")
                                                
                                                location_match_status = f"Match found near headquarters text for {', '.join(match_details)}"
                                                print(f"Location match found near headquarters: {context}")
                                                logging.info(f"Location match found near headquarters: {context}")
                                                break
                            except Exception as e:
                                logging.warning(f"Error scanning full page text: {e}")
                            
                            # If still no match, try the selectors
                            if not matched_company:
                                for selector in headquarters_selectors:
                                    try:
                                        location_elements = driver.find_elements(By.XPATH, selector)
                                        if location_elements:
                                            for element in location_elements:
                                                # Check if our expected location is in this text using improved matching
                                                location_text = element.text.strip().lower()
                                                logging.info(f"Found potential headquarters: {location_text}")
                                                print(f"Found potential headquarters: {location_text}")
                                                
                                                # Use improved city and state matching
                                                city_match = city_names_match(expected_city, location_text)
                                                state_match = state_in_text(expected_state, location_text)
                                                
                                                if city_match or state_match:
                                                    matched_company = link
                                                    match_details = []
                                                    if city_match:
                                                        match_details.append(f"city '{expected_city}'")
                                                    if state_match:
                                                        match_details.append(f"state '{expected_state}'")
                                                    
                                                    location_match_status = f"Match found in headquarters for {', '.join(match_details)}"
                                                    print(f"Location match found in headquarters: {location_text}")
                                                    logging.info(f"Location match found in headquarters: {location_text}")
                                                    break
                                            
                                            if matched_company:
                                                break
                                    except Exception as e:
                                        logging.warning(f"Error with headquarters selector {selector}: {e}")
                            
                            # If still not matched, use more general approach - look for any location mention
                            if not matched_company:
                                # Try to find any divs or spans with location-related content
                                location_content_selectors = [
                                    "//div[contains(@class, 'location')]",
                                    "//span[contains(@class, 'location')]",
                                    "//div[contains(text(), 'Area')]",
                                    "//div[contains(text(), 'Location')]",
                                    "//section[contains(@class, 'location')]"
                                ]
                                
                                for selector in location_content_selectors:
                                    try:
                                        elements = driver.find_elements(By.XPATH, selector)
                                        for element in elements:
                                            content = element.text.lower()
                                            print(f"Found potential location content: {content}")
                                            logging.info(f"Found potential location content: {content}")
                                            
                                            city_match = city_names_match(expected_city, content)
                                            state_match = state_in_text(expected_state, content)
                                            
                                            if city_match or state_match:
                                                matched_company = link
                                                match_details = []
                                                if city_match:
                                                    match_details.append(f"city '{expected_city}'")
                                                if state_match:
                                                    match_details.append(f"state '{expected_state}'")
                                                
                                                location_match_status = f"Match found in location element for {', '.join(match_details)}"
                                                print(f"Location match found in element: {content}")
                                                logging.info(f"Location match found in element: {content}")
                                                break
                                        
                                        if matched_company:
                                            break
                                    except Exception as e:
                                        logging.warning(f"Error with location content selector {selector}: {e}")
                            
                            # If we found a match, break out of the loop
                            if matched_company:
                                break
                                
                            # If not found, go back to search results
                            driver.get(search_results_url)
                            time.sleep(0.5 + 0.5 * random.random())
                            
                        except Exception as e:
                            logging.warning(f"Error checking location on company page: {e}")
                            driver.get(search_results_url)
                            time.sleep(0.5 + 0.5 * random.random())
                            
                    except Exception as e:
                        logging.warning(f"Error checking company {i+1}: {e}")
                        # Try to return to search results
                        driver.get(search_results_url)
                        time.sleep(0.5 + 0.5 * random.random())
        
        # If we didn't find a matching location but need to select a company
        if expected_city and expected_state and not matched_company:
            logging.warning(f"No location match found for {business_name} in {expected_city}, {expected_state}")
            print(f"No location match found for {business_name} in {expected_city}, {expected_state}")
            
            # We'll still select the first result but mark it as a non-match
            matched_company = company_links[0]
            # Setting this to a simple "Not found" status
            location_match_status = "Not found"
            
        # If no expected location was provided, or if we've done the location check,
        # proceed with the selected company (either the matched one or the first one)
        company_to_use = matched_company if matched_company else company_links[0]
        company_link = company_to_use.get_attribute('href')
        logging.info(f"Using company link: {company_link}")
        print(f"Using company link: {company_link}")
        
        # Try different click methods
        try:
            logging.info("Attempting to click using .click() method")
            company_to_use.click()
        except Exception as e:
            logging.warning(f"Direct click failed: {e}")
            try:
                logging.info("Attempting to click using JavaScript")
                driver.execute_script("arguments[0].click();", company_to_use)
            except Exception as e2:
                logging.warning(f"JavaScript click also failed: {e2}")
                logging.info("Falling back to navigating directly to the URL")
                driver.get(company_link)
                
        # Wait for the page to load
        time.sleep(0.5 + 0.5 * random.random())
        
        # Check if we're on the "about" page, if not, navigate to it
        if '/about/' not in driver.current_url:
            about_url = company_link.rstrip('/') + '/about/'
            logging.info(f"Navigating to about page: {about_url}")
            driver.get(about_url)
            time.sleep(0.5 + 0.5 * random.random())
        
        # Take screenshot of the about page
        screenshot_path = os.path.join(DEBUG_FOLDER, f"about_page_{business_name.replace(' ', '_')}.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Saved screenshot of About page to {screenshot_path}")
        
        # Scroll down to make sure all content is loaded
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(0.5 + 0.5 * random.random())  # Reduced from 2 seconds
        
        # Dump the HTML content to a file for debugging
        html_file = os.path.join(DEBUG_FOLDER, f"page_source_{business_name.replace(' ', '_')}.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info(f"Saved page source to {html_file}")
        
        # Initialize company website variable
        company_website = "Not found"
        
        # Try to find company size, industry, and website
        try:
            # Extract using both XPath and CSS selectors
            company_size = "Not found"
            industry = "Not found"
            headquarters = "Not found"  # Add new field for headquarters
            founded = "Not found"  # Add new field for founded date
            specialties = "Not found"  # Add new field for specialties
            
            # First try a more general approach - look for key information sections
            info_sections = driver.find_elements(By.CSS_SELECTOR, "section.artdeco-card")
            logging.info(f"Found {len(info_sections)} information sections")
            
            # Log all text sections to help debug
            logging.info("Searching page for information sections...")
            
            # Try CSS selectors first (often more reliable than XPath)
            size_css_selectors = [
                "dt:contains('Company size'), dd",
                ".org-about-company-module__company-size",
                ".org-about-module__company-size",
                ".org-page-details__definition-text",
                ".org-about-company-module__company-staff-count-range"
            ]
            
            # Try to extract website from the sections
            for section in info_sections:
                section_text = section.text
                if section_text:
                    logging.info(f"Section text: {section_text[:200]}...")  # Log first 200 chars
                    
                    # Look specifically for associated members in section text
                    if "associated member" in section_text.lower():
                        logging.info("Found section with associated members information")
                        import re
                        matches = re.findall(r'(\d+[,\d]*)\s+associated members', section_text, re.IGNORECASE)
                        if matches:
                            company_size = f"{matches[0]} associated members"
                            logging.info(f"Extracted associated members count: {company_size}")
                    
                    # Look for website in section text
                    if "website" in section_text.lower():
                        logging.info("Found section with website information")
                        lines = section_text.split('\n')
                        for i, line in enumerate(lines):
                            if "website" in line.lower():
                                if i + 1 < len(lines):
                                    potential_website = lines[i + 1].strip()
                                    if potential_website and "http" in potential_website:
                                        company_website = potential_website
                                        logging.info(f"Extracted company website: {company_website}")
                                        break
                                    # Sometimes the website URL is on the same line
                                    elif "http" in line:
                                        parts = line.split()
                                        for part in parts:
                                            if part.startswith("http"):
                                                company_website = part.strip()
                                                logging.info(f"Extracted company website from same line: {company_website}")
                                                break
                    
                    # Look for headquarters in section text
                    if "headquarters" in section_text.lower():
                        logging.info("Found section with headquarters information")
                        lines = section_text.split('\n')
                        for i, line in enumerate(lines):
                            if "headquarters" in line.lower():
                                if i + 1 < len(lines):
                                    headquarters = lines[i + 1].strip()
                                    logging.info(f"Extracted headquarters: {headquarters}")
                                    break
                    
                    # Look for founded date in section text
                    if "founded" in section_text.lower():
                        logging.info("Found section with founded information")
                        lines = section_text.split('\n')
                        for i, line in enumerate(lines):
                            if "founded" in line.lower():
                                if i + 1 < len(lines):
                                    founded = lines[i + 1].strip()
                                    logging.info(f"Extracted founded date: {founded}")
                                    break
                    
                    # Look for specialties in section text
                    if "specialties" in section_text.lower():
                        logging.info("Found section with specialties information")
                        lines = section_text.split('\n')
                        for i, line in enumerate(lines):
                            if "specialties" in line.lower():
                                if i + 1 < len(lines):
                                    specialties = lines[i + 1].strip()
                                    logging.info(f"Extracted specialties: {specialties}")
                                    break
                    
                    if "company size" in section_text.lower() or "associated members" in section_text.lower():
                        logging.info("Found section with company size information")
                        # Extract using regex pattern or line by line analysis
                        lines = section_text.split('\n')
                        for i, line in enumerate(lines):
                            if "company size" in line.lower():
                                if i + 1 < len(lines):
                                    company_size = lines[i + 1]
                                    logging.info(f"Extracted company size: {company_size}")
                                    break
                    
                    if "industry" in section_text.lower():
                        logging.info("Found section with industry information")
                        lines = section_text.split('\n')
                        for i, line in enumerate(lines):
                            if "industry" in line.lower():
                                if i + 1 < len(lines):
                                    industry = lines[i + 1]
                                    logging.info(f"Extracted industry: {industry}")
                                    break
            
            # If website not found in section text, try XPath selectors for all fields
            if company_website == "Not found":
                website_selectors = [
                    "//dt[text()='Website']/following-sibling::dd//a",
                    "//dt[contains(text(), 'Website')]/following-sibling::dd//a",
                    "//span[contains(text(), 'Website')]/following::a[1]",
                    "//h3[contains(text(), 'Website')]/following-sibling::*//a",
                    "//a[contains(@class, 'org-about-us-company-module__website')]",
                    "//a[contains(@class, 'link-without-visited-state')]",
                    "//div[contains(text(), 'Website')]/following-sibling::div//a"
                ]
                
                for selector in website_selectors:
                    try:
                        website_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying website selector: {selector}, found {len(website_elements)} elements")
                        for element in website_elements:
                            href = element.get_attribute('href')
                            if href and href.startswith('http') and 'linkedin.com' not in href:
                                company_website = href
                                logging.info(f"Found company website using selector: {selector}, URL: {company_website}")
                                break
                        if company_website != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Website selector {selector} failed: {e}")
            
            # If not found yet, try XPath selectors (original approach)
            if company_size == "Not found":
                size_selectors = [
                    "//dt[text()='Company size']/following-sibling::dd",
                    "//dt[contains(text(), 'Company size')]/following-sibling::dd",
                    "//span[contains(text(), 'Company size')]/following::span[1]",
                    "//h3[contains(text(), 'Company size')]/following-sibling::*[1]",
                    "//div[contains(@class, 'org-about-company-module__company-size')]",
                    "//span[contains(text(), 'employees')]/parent::*",
                    "//div[contains(@class, 'core-section-container')]//dt[contains(text(), 'Company size')]/following-sibling::dd",
                    "//div[contains(@class, 'core-section-container')]//div[contains(text(), 'Company size')]/following-sibling::div"
                ]
                
                for selector in size_selectors:
                    try:
                        company_size_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying size selector: {selector}, found {len(company_size_elements)} elements")
                        for element in company_size_elements:
                            potential_size = element.text.strip()
                            logging.info(f"Potential company size: '{potential_size}'")
                            if potential_size and ('employee' in potential_size.lower() or potential_size.isdigit() or '-' in potential_size):
                                company_size = potential_size
                                logging.info(f"Found company size using selector: {selector}")
                                break
                        if company_size != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Size selector {selector} failed: {e}")
            
                # Look for associated members specifically
                associated_members_selectors = [
                    "//span[contains(text(), 'associated member')]/parent::*",
                    "//span[contains(text(), 'associated member')]",
                    "//div[contains(text(), 'associated member')]",
                    "//li[contains(text(), 'associated member')]"
                ]
                
                for selector in associated_members_selectors:
                    try:
                        associated_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying associated members selector: {selector}, found {len(associated_elements)} elements")
                        for element in associated_elements:
                            text = element.text.strip()
                            logging.info(f"Potential associated members text: '{text}'")
                            # Extract numbers from text like "1,234 associated members"
                            import re
                            matches = re.findall(r'(\d+[,\d]*)\s+associated members', text, re.IGNORECASE)
                            if matches:
                                company_size = f"{matches[0]} associated members"
                                logging.info(f"Found associated members: {company_size}")
                                break
                        if "associated members" in company_size:
                            break
                    except Exception as e:
                        logging.warning(f"Associated members selector {selector} failed: {e}")
            
            if industry == "Not found":
                industry_selectors = [
                    "//dt[text()='Industry']/following-sibling::dd",
                    "//dt[contains(text(), 'Industry')]/following-sibling::dd",
                    "//span[contains(text(), 'Industry')]/following::span[1]",
                    "//h3[contains(text(), 'Industry')]/following-sibling::*[1]",
                    "//div[contains(@class, 'org-about-company-module__industry')]",
                    "//span[contains(text(), 'Industry')]/parent::*",
                    "//div[contains(@class, 'core-section-container')]//dt[contains(text(), 'Industry')]/following-sibling::dd",
                    "//div[contains(@class, 'core-section-container')]//div[contains(text(), 'Industry')]/following-sibling::div",
                    # Add more precise selectors that match the SafetySkills HTML structure
                    "//h3[text()='Industry']/parent::dt/following-sibling::dd",
                    "//h3[text()='Industry']/ancestor::dt/following-sibling::dd",
                    "//dt/h3[text()='Industry']/../../dd"
                ]
                
                for selector in industry_selectors:
                    try:
                        industry_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying industry selector: {selector}, found {len(industry_elements)} elements")
                        for element in industry_elements:
                            potential_industry = element.text.strip()
                            logging.info(f"Potential industry: '{potential_industry}'")
                            if potential_industry and len(potential_industry) > 3:  # Basic validation
                                industry = potential_industry
                                logging.info(f"Found industry using selector: {selector}")
                                break
                        if industry != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Industry selector {selector} failed: {e}")
            
            # If website not found in section text, try XPath selectors for all fields
            if company_website == "Not found":
                website_selectors = [
                    "//dt[text()='Website']/following-sibling::dd//a",
                    "//dt[contains(text(), 'Website')]/following-sibling::dd//a",
                    "//span[contains(text(), 'Website')]/following::a[1]",
                    "//h3[contains(text(), 'Website')]/following-sibling::*//a",
                    "//a[contains(@class, 'org-about-us-company-module__website')]",
                    "//a[contains(@class, 'link-without-visited-state')]",
                    "//div[contains(text(), 'Website')]/following-sibling::div//a"
                ]
                
                for selector in website_selectors:
                    try:
                        website_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying website selector: {selector}, found {len(website_elements)} elements")
                        for element in website_elements:
                            href = element.get_attribute('href')
                            if href and href.startswith('http') and 'linkedin.com' not in href:
                                company_website = href
                                logging.info(f"Found company website using selector: {selector}, URL: {company_website}")
                                break
                        if company_website != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Website selector {selector} failed: {e}")
            
            # If not found yet, try XPath selectors (original approach)
            if company_size == "Not found":
                size_selectors = [
                    "//dt[text()='Company size']/following-sibling::dd",
                    "//dt[contains(text(), 'Company size')]/following-sibling::dd",
                    "//span[contains(text(), 'Company size')]/following::span[1]",
                    "//h3[contains(text(), 'Company size')]/following-sibling::*[1]",
                    "//div[contains(@class, 'org-about-company-module__company-size')]",
                    "//span[contains(text(), 'employees')]/parent::*",
                    "//div[contains(@class, 'core-section-container')]//dt[contains(text(), 'Company size')]/following-sibling::dd",
                    "//div[contains(@class, 'core-section-container')]//div[contains(text(), 'Company size')]/following-sibling::div"
                ]
                
                for selector in size_selectors:
                    try:
                        company_size_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying size selector: {selector}, found {len(company_size_elements)} elements")
                        for element in company_size_elements:
                            potential_size = element.text.strip()
                            logging.info(f"Potential company size: '{potential_size}'")
                            if potential_size and ('employee' in potential_size.lower() or potential_size.isdigit() or '-' in potential_size):
                                company_size = potential_size
                                logging.info(f"Found company size using selector: {selector}")
                                break
                        if company_size != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Size selector {selector} failed: {e}")
            
            # If not found yet, try XPath selectors for all fields
            if headquarters == "Not found":
                headquarters_selectors = [
                    "//dt[text()='Headquarters']/following-sibling::dd",
                    "//dt[contains(text(), 'Headquarters')]/following-sibling::dd",
                    "//span[contains(text(), 'Headquarters')]/following::span[1]",
                    "//h3[contains(text(), 'Headquarters')]/following-sibling::*[1]",
                    "//div[contains(@class, 'org-location-info')]",
                    "//div[contains(text(), 'Headquarters')]/following-sibling::div"
                ]
                
                for selector in headquarters_selectors:
                    try:
                        headquarters_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying headquarters selector: {selector}, found {len(headquarters_elements)} elements")
                        for element in headquarters_elements:
                            potential_hq = element.text.strip()
                            logging.info(f"Potential headquarters: '{potential_hq}'")
                            if potential_hq and len(potential_hq) > 3:  # Basic validation
                                headquarters = potential_hq
                                logging.info(f"Found headquarters using selector: {selector}")
                                break
                        if headquarters != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Headquarters selector {selector} failed: {e}")
            
            if founded == "Not found":
                founded_selectors = [
                    "//dt[text()='Founded']/following-sibling::dd",
                    "//dt[contains(text(), 'Founded')]/following-sibling::dd",
                    "//span[contains(text(), 'Founded')]/following::span[1]",
                    "//h3[contains(text(), 'Founded')]/following-sibling::*[1]",
                    "//div[contains(text(), 'Founded')]/following-sibling::div"
                ]
                
                for selector in founded_selectors:
                    try:
                        founded_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying founded selector: {selector}, found {len(founded_elements)} elements")
                        for element in founded_elements:
                            potential_founded = element.text.strip()
                            logging.info(f"Potential founded date: '{potential_founded}'")
                            if potential_founded:
                                founded = potential_founded
                                logging.info(f"Found founded date using selector: {selector}")
                                break
                        if founded != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Founded selector {selector} failed: {e}")
            
            if specialties == "Not found":
                specialties_selectors = [
                    "//dt[text()='Specialties']/following-sibling::dd",
                    "//dt[contains(text(), 'Specialties')]/following-sibling::dd",
                    "//span[contains(text(), 'Specialties')]/following::span[1]",
                    "//h3[contains(text(), 'Specialties')]/following-sibling::*[1]",
                    "//div[contains(text(), 'Specialties')]/following-sibling::div"
                ]
                
                for selector in specialties_selectors:
                    try:
                        specialties_elements = driver.find_elements(By.XPATH, selector)
                        logging.info(f"Trying specialties selector: {selector}, found {len(specialties_elements)} elements")
                        for element in specialties_elements:
                            potential_specialties = element.text.strip()
                            logging.info(f"Potential specialties: '{potential_specialties}'")
                            if potential_specialties and len(potential_specialties) > 3:  # Basic validation
                                specialties = potential_specialties
                                logging.info(f"Found specialties using selector: {selector}")
                                break
                        if specialties != "Not found":
                            break
                    except Exception as e:
                        logging.warning(f"Specialties selector {selector} failed: {e}")
            
            # Last resort - try to extract keywords from the entire page
            if company_size == "Not found" or industry == "Not found" or company_website == "Not found" or headquarters == "Not found" or founded == "Not found" or specialties == "Not found":
                logging.info("Using last resort method - scanning entire page for keywords")
                page_text = driver.find_element(By.TAG_NAME, "body").text
                page_source = driver.page_source
                
                # Last resort for company website - look for website URLs in the source
                if company_website == "Not found":
                    import re
                    # Look for website patterns in the source
                    website_patterns = [
                        r'Website</dt><dd.+?href="([^"]+)"',
                        r'website.+?href="([^"]+)"',
                        r'href="(https?://[^"]+?)"'
                    ]
                    
                    for pattern in website_patterns:
                        matches = re.findall(pattern, page_source, re.IGNORECASE)
                        for match in matches:
                            if 'linkedin.com' not in match and match.startswith('http'):
                                company_website = match
                                logging.info(f"Found company website using regex: {company_website}")
                                break
                        if company_website != "Not found":
                            break
                
                if company_size == "Not found":
                    # Look for patterns like "501-1,000 employees" or similar
                    import re
                    employee_patterns = [
                        r'(\d+[-–]\d+,?\d*\s+employees)',
                        r'(\d+,?\d*\s+employees)',
                        r'(\d+[,\d]*)\s+associated members'
                    ]
                    
                    for pattern in employee_patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            if "associated members" in pattern:
                                company_size = f"{matches[0]} associated members"
                            else:
                                company_size = matches[0]
                            logging.info(f"Found company size using regex: {company_size}")
                            break
                
                if industry == "Not found":
                    # Look for common industry terms after "Industry" keyword
                    industry_idx = page_text.lower().find("industry")
                    if industry_idx != -1:
                        potential_industry = page_text[industry_idx:industry_idx+100]  # Get 100 chars after "industry"
                        lines = potential_industry.split('\n')
                        if len(lines) > 1:
                            potential_industry = lines[1].strip()
                            if potential_industry and len(potential_industry) > 3:
                                industry = potential_industry
                                logging.info(f"Found industry by page scanning: {industry}")
                        
                        # If still not found, try with different line parsing approach
                        if industry == "Not found" and len(lines) > 2:
                            potential_industry = lines[2].strip()
                            if potential_industry and len(potential_industry) > 3:
                                industry = potential_industry
                                logging.info(f"Found industry by page scanning (line 2): {industry}")
                        
                        # If still not found, try one more approach - search in the source code
                        if industry == "Not found":
                            logging.info("Trying to extract industry from page source code")
                            
                            # Add simplified regex patterns that match the SafetySkills HTML structure
                            html_industry_patterns = [
                                r'<h3[^>]*>Industry</h3>.*?<dd[^>]*>(.*?)</dd>',
                                r'Industry</h3>.*?<dd[^>]*>(.*?)</dd>'
                            ]
                            
                            for pattern in html_industry_patterns:
                                matches = re.findall(pattern, page_source, re.DOTALL)
                                if matches and matches[0]:
                                    # Clean up the text - remove HTML tags and trim
                                    cleaned_match = re.sub(r'<.*?>', '', matches[0]).strip()
                                    if cleaned_match and len(cleaned_match) > 3:
                                        industry = cleaned_match
                                        logging.info(f"Found industry using HTML pattern: {industry}")
                                        break
                            
                            # Look for specific industry mentions in the source
                            industry_patterns = [
                                r'"name":"([^"]+)","entityUrn":"urn:li:fsd_industry:',
                                r'"name":"([^"]+)","entityUrn":"urn:li:fsd_industryV2:'
                            ]
                            
                            # If still not found, try direct pattern matching
                            if industry == "Not found":
                                for pattern in industry_patterns:
                                    matches = re.findall(pattern, page_source)
                                    if matches and matches[0]:
                                        # Just take the first industry mentioned
                                        industry = matches[0]
                                        logging.info(f"Found industry in source: {industry}")
                                        break
            
        except Exception as e:
            logging.warning(f"Error extracting company details: {e}")
            company_size = "Not found"
            industry = "Not found"
            company_website = "Not found"
        
        # Final data cleaning and prioritization
        # If we found both employee count and associated members, prioritize associated members
        if company_size != "Not found" and "associated members" not in company_size:
            # Do one more full page scan for associated members
            try:
                full_page_text = driver.find_element(By.TAG_NAME, "body").text
                import re
                associated_matches = re.findall(r'(\d+[,\d]*)\s+associated members', full_page_text, re.IGNORECASE)
                if associated_matches:
                    company_size = f"{associated_matches[0]} associated members"
                    logging.info(f"Final scan: Found associated members count: {company_size}")
            except Exception as e:
                logging.warning(f"Final scan for associated members failed: {e}")
        
        # Final check for location match using the headquarters information
        if expected_city and expected_state and location_match_status == "Not found" and headquarters != "Not found":
            logging.info(f"Performing final location verification using headquarters: '{headquarters}'")
            print(f"Verifying location using extracted headquarters: '{headquarters}'")
            
            # Check if city or state is in the headquarters
            city_in_hq = city_names_match(expected_city, headquarters)
            state_in_hq = state_in_text(expected_state, headquarters)
            
            if city_in_hq and state_in_hq:
                location_match_status = "Location matched"
                logging.info(f"Location match confirmed using headquarters: {headquarters}")
                print(f"Location match confirmed using headquarters: {headquarters}")
            elif city_in_hq:
                # Simplified status
                location_match_status = "Location matched"
                logging.info(f"Location match (city) confirmed using headquarters: {headquarters}")
                print(f"Location match (city) confirmed using headquarters: {headquarters}")
            elif state_in_hq:
                # Simplified status
                location_match_status = "Location matched"
                logging.info(f"Location match (state) confirmed using headquarters: {headquarters}")
                print(f"Location match (state) confirmed using headquarters: {headquarters}")
            else:
                # If we still haven't found a location match, do a final scan of the entire page
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    if city_names_match(expected_city, body_text) and state_in_text(expected_state, body_text):
                        location_match_status = "Location matched"
                        logging.info("Location match found in complete page content")
                        print("Location match found in complete page content")
                    elif city_names_match(expected_city, body_text):
                        location_match_status = "Location matched"
                        logging.info(f"Partial match (city only) in complete page content")
                        print(f"Partial match (city only) in complete page content")
                    elif state_in_text(expected_state, body_text):
                        location_match_status = "Location matched"
                        logging.info(f"Partial match (state only) in complete page content")
                        print(f"Partial match (state only) in complete page content")
                except Exception as e:
                    logging.warning(f"Error during final page scan: {e}")
                
        # Final check before returning
        if industry == "":
            industry = "Not found"
        
        return {
            'LinkedIn Link': company_link,
            'Company Website': company_website,
            'Company Size': company_size,
            'Industry': industry,
            'Headquarters': headquarters,
            'Founded': founded,
            'Specialties': specialties,
            'Location Match': location_match_status
        }
        
    except Exception as e:
        print(f"Error scraping {business_name}: {e}")
        logging.error(f"Error scraping {business_name}: {e}")
        # Take screenshot for debugging
        screenshot_path = os.path.join(DEBUG_FOLDER, f"error_{business_name.replace(' ', '_')}.png")
        try:
            driver.save_screenshot(screenshot_path)
            logging.info(f"Error screenshot saved to {screenshot_path}")
        except:
            logging.warning("Could not save error screenshot")
            
        # Extract just the main error message without the stack trace
        error_msg = str(e)
        # Get only the first line or a shorter version of the error message
        if '\n' in error_msg:
            error_msg = error_msg.split('\n')[0]
        # Limit the length of the error message
        if len(error_msg) > 100:
            error_msg = error_msg[:97] + "..."
            
        return {
            'LinkedIn Link': None,
            'Company Website': None,
            'Company Size': None,
            'Industry': None,
            'Headquarters': None,
            'Founded': None,
            'Specialties': None,
            'Location Match': f"Error: {error_msg}"
        }

def load_ner_models():
    """
    Load named entity recognition models
    """
    models = {}
    
    try:
        # Load spaCy model for general NER
        models['spacy'] = spacy.load("en_core_web_sm")
        logging.info("Successfully loaded spaCy NER model")
    except Exception as e:
        logging.warning(f"Could not load spaCy model: {e}")
        models['spacy'] = None
    
    try:
        # Load Hugging Face transformer model for NER
        models['transformers'] = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
        logging.info("Successfully loaded transformers NER model")
    except Exception as e:
        logging.warning(f"Could not load transformers NER model: {e}")
        models['transformers'] = None
    
    return models

# Function to extract text from website
def extract_text_from_website(url, max_pages=5):
    """
    Extract text content from a company website
    
    Args:
        url: The website URL
        max_pages: Maximum number of pages to crawl
    
    Returns:
        dict: Dictionary containing page texts and potential contact/about page URLs
    """
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return {"error": "Invalid URL", "pages": {}, "about_pages": [], "contact_pages": [], "team_pages": []}
    
    # Normalize URL
    if not url.endswith('/'):
        url = url + '/'
    
    # Parse domain for internal link identification
    domain = urlparse(url).netloc
    
    # Pages already visited
    visited_urls = set()
    
    # Dictionary to store text from each page
    page_texts = {}
    
    # Pages likely to contain leadership info
    about_pages = []
    team_pages = []
    leadership_pages = []
    contact_pages = []
    
    # Keywords for identifying relevant pages
    about_keywords = ['about', 'company', 'who-we-are', 'about-us', 'our-company', 'our-story']
    team_keywords = ['team', 'people', 'staff', 'our-team', 'management', 'employees', 'our-people']
    leadership_keywords = ['leadership', 'executives', 'board', 'management-team', 'directors', 'founders', 'executive-team']
    contact_keywords = ['contact', 'contact-us', 'get-in-touch', 'reach-us']
    
    # Headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    def is_internal_link(href):
        """Check if a URL is internal to the website"""
        if not href:
            return False
        if href.startswith('/'):
            return True
        if domain in href:
            return True
        return False
    
    def categorize_url(href):
        """Categorize URL based on keywords"""
        href_lower = href.lower()
        
        if any(keyword in href_lower for keyword in about_keywords):
            about_pages.append(href)
        
        if any(keyword in href_lower for keyword in team_keywords):
            team_pages.append(href)
        
        if any(keyword in href_lower for keyword in leadership_keywords):
            leadership_pages.append(href)
        
        if any(keyword in href_lower for keyword in contact_keywords):
            contact_pages.append(href)
    
    def process_page(page_url):
        """Process a single page to extract text and links"""
        if page_url in visited_urls:
            return
        
        visited_urls.add(page_url)
        
        try:
            logging.info(f"Fetching page: {page_url}")
            response = requests.get(page_url, headers=headers, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {page_url}, status code: {response.status_code}")
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text from the page, removing script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator="\n")
            
            # Clean text
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)
            
            # Add to page texts
            page_texts[page_url] = text
            
            # Categorize this page
            categorize_url(page_url)
            
            # Extract links for further crawling
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # Skip empty or non-http/https links
                if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                    continue
                
                # Make absolute URL
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(page_url, href)
                
                # Only follow internal links
                if is_internal_link(href):
                    # Normalize URL
                    href = href.split('#')[0]  # Remove fragment
                    href = href.split('?')[0]  # Remove query params
                    
                    # Categorize URL
                    categorize_url(href)
                    
                    # Add to links for crawling
                    if href not in visited_urls:
                        links.append(href)
            
            return links
        
        except Exception as e:
            logging.warning(f"Error processing {page_url}: {e}")
            return []
    
    # Start with homepage
    pages_to_visit = [url]
    
    # Crawl the website
    page_count = 0
    
    while pages_to_visit and page_count < max_pages:
        current_url = pages_to_visit.pop(0)
        new_links = process_page(current_url)
        page_count += 1
        
        if new_links:
            for link in new_links:
                if link not in visited_urls and link not in pages_to_visit:
                    pages_to_visit.append(link)
    
    # Prioritize leadership and team pages
    priority_pages = leadership_pages + team_pages + about_pages
    
    # If we have not reached max pages, process priority pages first
    while priority_pages and page_count < max_pages:
        for page in priority_pages[:]:
            if page not in visited_urls:
                process_page(page)
                priority_pages.remove(page)
                page_count += 1
                if page_count >= max_pages:
                    break
    
    logging.info(f"Crawled {len(visited_urls)} pages from {url}")
    logging.info(f"Found {len(about_pages)} about pages, {len(team_pages)} team pages, {len(leadership_pages)} leadership pages")
    
    return {
        "pages": page_texts,
        "about_pages": about_pages,
        "team_pages": team_pages,
        "leadership_pages": leadership_pages,
        "contact_pages": contact_pages
    }

# Function to extract decision makers using NER
def extract_decision_makers_from_text(text, models, company_name=None):
    """
    Use NER to identify potential decision makers from text
    
    Args:
        text: The text to analyze
        models: Dictionary of loaded NER models
        company_name: Name of the company for context
    
    Returns:
        list: List of potential decision makers with their titles
    """
    decision_makers = []
    
    # Common executive titles
    executive_titles = [
        'CEO', 'Chief Executive Officer', 
        'President', 
        'Founder', 'Co-Founder', 'Cofounder',
        'Owner', 
        'Chairman', 'Chairwoman', 'Chair',
        'Managing Director',
        'Chief Operating Officer', 'COO',
        'Chief Financial Officer', 'CFO',
        'Chief Technology Officer', 'CTO',
        'Chief Marketing Officer', 'CMO',
        'Chief Information Officer', 'CIO',
        'Chief People Officer', 'CPO',
        'Chief Revenue Officer', 'CRO',
        'Chief Product Officer',
        'VP', 'Vice President',
        'Director',
        'Managing Partner',
        'Executive Director'
    ]
    
    # Try to use spaCy if available
    potential_people = set()
    potential_titles = {}
    
    try:
        if models['spacy']:
            # Process text in manageable chunks
            # Split into sentences
            sentences = sent_tokenize(text)
            
            # Process each sentence
            for sentence in sentences:
                doc = models['spacy'](sentence)
                
                # Extract named entities of type PERSON
                for ent in doc.ents:
                    if ent.label_ == 'PERSON':
                        person_name = ent.text.strip()
                        
                        # Skip very short names
                        if len(person_name.split()) < 2:
                            continue
                        
                        potential_people.add(person_name)
                        
                        # Look for titles before or after the name
                        sentence_lower = sentence.lower()
                        
                        # Check if any executive title is present in the same sentence
                        for title in executive_titles:
                            if title.lower() in sentence_lower:
                                # Keep track of this title for this person
                                if person_name not in potential_titles:
                                    potential_titles[person_name] = []
                                
                                # Find the exact match with proper case
                                title_pattern = re.compile(re.escape(title), re.IGNORECASE)
                                title_matches = title_pattern.finditer(sentence)
                                
                                for match in title_matches:
                                    exact_title = sentence[match.start():match.end()]
                                    # Get context around the title (to capture "CEO of XYZ")
                                    start_pos = max(0, match.start() - 20)
                                    end_pos = min(len(sentence), match.end() + 50)
                                    title_context = sentence[start_pos:end_pos].strip()
                                    
                                    potential_titles[person_name].append({
                                        'title': exact_title,
                                        'context': title_context
                                    })
    except Exception as e:
        logging.warning(f"Error using spaCy for NER: {e}")
    
    # Try to use transformers if available
    try:
        if models['transformers'] and len(potential_people) < 3:  # Only use transformers as backup
            # Process text in manageable chunks due to token limits
            # Split into sentences and process each sentence
            sentences = sent_tokenize(text[:10000])  # Limit to first 10K chars to avoid long processing
            
            for sentence in sentences:
                # Skip very short sentences
                if len(sentence) < 10:
                    continue
                
                # Process with transformer
                ner_results = models['transformers'](sentence)
                
                # Extract person entities
                current_entity = {'text': '', 'type': ''}
                
                for token in ner_results:
                    if token['entity'].startswith('B-PER'):  # Beginning of person entity
                        if current_entity['text'] and current_entity['type'] == 'PER':
                            person_name = current_entity['text'].strip()
                            if len(person_name.split()) >= 2:  # Only consider full names
                                potential_people.add(person_name)
                        
                        current_entity = {'text': token['word'], 'type': 'PER'}
                    
                    elif token['entity'].startswith('I-PER'):  # Inside person entity
                        if current_entity['type'] == 'PER':
                            current_entity['text'] += ' ' + token['word'].lstrip('##')
                    
                    else:  # Not a person entity
                        if current_entity['text'] and current_entity['type'] == 'PER':
                            person_name = current_entity['text'].strip()
                            if len(person_name.split()) >= 2:  # Only consider full names
                                potential_people.add(person_name)
                        
                        current_entity = {'text': '', 'type': ''}
                
                # Add the last entity if there is one
                if current_entity['text'] and current_entity['type'] == 'PER':
                    person_name = current_entity['text'].strip()
                    if len(person_name.split()) >= 2:  # Only consider full names
                        potential_people.add(person_name)
                
                # Look for titles in the sentence
                sentence_lower = sentence.lower()
                
                for person in potential_people:
                    if person.lower() in sentence_lower:
                        for title in executive_titles:
                            if title.lower() in sentence_lower:
                                # Find the exact match with proper case
                                title_pattern = re.compile(re.escape(title), re.IGNORECASE)
                                title_matches = title_pattern.finditer(sentence)
                                
                                for match in title_matches:
                                    exact_title = sentence[match.start():match.end()]
                                    
                                    # Get context around the title
                                    start_pos = max(0, match.start() - 20)
                                    end_pos = min(len(sentence), match.end() + 50)
                                    title_context = sentence[start_pos:end_pos].strip()
                                    
                                    if person not in potential_titles:
                                        potential_titles[person] = []
                                    
                                    potential_titles[person].append({
                                        'title': exact_title,
                                        'context': title_context
                                    })
    except Exception as e:
        logging.warning(f"Error using transformers for NER: {e}")
    
    # Try rule-based approach as well
    try:
        # Pattern for finding titles followed by names: "CEO John Smith"
        title_name_pattern = r'(' + '|'.join(re.escape(title) for title in executive_titles) + r')\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        title_name_matches = re.finditer(title_name_pattern, text)
        
        for match in title_name_matches:
            title = match.group(1)
            name = match.group(2)
            
            if len(name.split()) >= 2:  # Only consider full names
                potential_people.add(name)
                
                if name not in potential_titles:
                    potential_titles[name] = []
                
                # Get some context around this match
                start_pos = max(0, match.start() - 20)
                end_pos = min(len(text), match.end() + 50)
                context = text[start_pos:end_pos].strip()
                
                potential_titles[name].append({
                    'title': title,
                    'context': context
                })
        
        # Pattern for finding names followed by titles: "John Smith, CEO"
        name_title_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,\-–—]\s*(' + '|'.join(re.escape(title) for title in executive_titles) + r')'
        name_title_matches = re.finditer(name_title_pattern, text)
        
        for match in name_title_matches:
            name = match.group(1)
            title = match.group(2)
            
            if len(name.split()) >= 2:  # Only consider full names
                potential_people.add(name)
                
                if name not in potential_titles:
                    potential_titles[name] = []
                
                # Get some context around this match
                start_pos = max(0, match.start() - 20)
                end_pos = min(len(text), match.end() + 50)
                context = text[start_pos:end_pos].strip()
                
                potential_titles[name].append({
                    'title': title,
                    'context': context
                })
    except Exception as e:
        logging.warning(f"Error using rule-based extraction: {e}")
    
    # Process the collected potential decision makers
    for person in potential_people:
        # Skip very short or very long names
        if len(person.split()) < 2 or len(person.split()) > 4:
            continue
        
        # Check if this person has titles
        titles = potential_titles.get(person, [])
        
        if titles:
            # Sort titles by executive level (preference to CEO, Founder, etc.)
            def title_priority(title_info):
                title = title_info['title'].lower()
                if any(role in title for role in ['ceo', 'chief executive']):
                    return 0
                if any(role in title for role in ['founder', 'co-founder']):
                    return 1
                if any(role in title for role in ['president', 'owner', 'chairman', 'chairwoman', 'chair']):
                    return 2
                if any(role in title for role in ['chief']):
                    return 3
                if any(role in title for role in ['vp', 'vice president']):
                    return 4
                return 5
            
            titles.sort(key=title_priority)
            
            # Check if any title context mentions the company name
            company_relevance = 0
            if company_name:
                for title_info in titles:
                    if company_name.lower() in title_info['context'].lower():
                        company_relevance = 1
                        break
            
            # Add to decision makers
            decision_makers.append({
                'name': person,
                'title': titles[0]['title'],  # Use highest priority title
                'title_context': titles[0]['context'],
                'all_titles': [t['title'] for t in titles],
                'company_relevance': company_relevance,
                'source': 'website'
            })
    
    # Sort decision makers by company relevance and title priority
    decision_makers.sort(key=lambda dm: (
        -dm['company_relevance'],  # Higher relevance first
        0 if any('ceo' in t.lower() for t in dm['all_titles']) else 1,  # CEOs first
        0 if any('founder' in t.lower() for t in dm['all_titles']) else 1,  # Then founders
        0 if any('president' in t.lower() for t in dm['all_titles']) else 1,  # Then presidents
        0 if any('chief' in t.lower() for t in dm['all_titles']) else 1,  # Then other C-level
        0 if any('vp' in t.lower() or 'vice president' in t.lower() for t in dm['all_titles']) else 1  # Then VPs
    ))
    
    return decision_makers

# Function to extract contact information from text
def extract_contact_info_from_text(text):
    """
    Extract email addresses and phone numbers from text
    
    Args:
        text: The text to analyze
    
    Returns:
        dict: Dictionary containing extracted emails and phone numbers
    """
    contact_info = {
        'email': "Not found",
        'phone': "Not found"
    }
    
    # Extract email addresses
    email_patterns = [
        r'[\w\.-]+@[\w\.-]+\.\w+',  # Basic email pattern
        r'[\w\.-]+\s+@\s+[\w\.-]+\.\w+',  # Email with spaces around @
        r'[\w\.-]+\s+\[at\]\s+[\w\.-]+\.\w+',  # [at] instead of @
        r'[\w\.-]+\s+\(at\)\s+[\w\.-]+\.\w+'   # (at) instead of @
    ]
    
    for pattern in email_patterns:
        emails = re.findall(pattern, text)
        if emails:
            # Clean up the found email
            email = emails[0].replace('[at]', '@').replace('(at)', '@').replace(' ', '')
            contact_info['email'] = email
            break
    
    # Extract phone numbers
    phone_patterns = [
        r'\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{4}',  # International format
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',       # US format
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'        # US format with parentheses
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
            break
    
    return contact_info

# New function to find decision makers from company website
def find_decision_makers_from_website(company_name, company_website):
    """
    Find decision makers by scraping and analyzing company website
    
    Args:
        company_name: Name of the company
        company_website: URL of the company website
    
    Returns:
        list: List of dictionaries containing decision maker information
    """
    if not company_website or not isinstance(company_website, str) or not company_website.startswith('http'):
        logging.warning(f"Invalid website URL for {company_name}: {company_website}")
        return []
    
    logging.info(f"Searching for decision makers on website: {company_website}")
    print(f"Searching for decision makers on {company_website}...")
    
    try:
        # Load NER models
        ner_models = load_ner_models()
        
        # Extract text from the website
        website_data = extract_text_from_website(company_website, max_pages=5)
        
        if "error" in website_data:
            logging.warning(f"Error extracting text from {company_website}: {website_data['error']}")
            return []
        
        # Combine text from all pages
        all_text = ""
        
        # Prioritize leadership and team pages
        priority_pages = []
        
        # First add leadership pages
        for page_url in website_data.get('leadership_pages', []):
            if page_url in website_data['pages']:
                priority_pages.append(page_url)
        
        # Then add team pages
        for page_url in website_data.get('team_pages', []):
            if page_url in website_data['pages'] and page_url not in priority_pages:
                priority_pages.append(page_url)
        
        # Then add about pages
        for page_url in website_data.get('about_pages', []):
            if page_url in website_data['pages'] and page_url not in priority_pages:
                priority_pages.append(page_url)
        
        # Add prioritized pages first
        for page_url in priority_pages:
            all_text += website_data['pages'][page_url] + "\n\n"
        
        # Add remaining pages
        for page_url, text in website_data['pages'].items():
            if page_url not in priority_pages:
                all_text += text + "\n\n"
        
        # Extract decision makers from the combined text
        decision_makers = extract_decision_makers_from_text(all_text, ner_models, company_name)
        
        # Limit to top 3 decision makers
        decision_makers = decision_makers[:3]
        
        # Look for contact information for each decision maker
        for dm in decision_makers:
            # First look for name in nearby context
            name_context = ""
            for page_url, text in website_data['pages'].items():
                if dm['name'] in text:
                    # Extract paragraph containing the name
                    paragraphs = text.split('\n\n')
                    for para in paragraphs:
                        if dm['name'] in para:
                            name_context += para + "\n\n"
            
            # Extract contact info
            contact_info = extract_contact_info_from_text(name_context)
            
            # If not found in name context, try contact pages
            if contact_info['email'] == "Not found" or contact_info['phone'] == "Not found":
                contact_text = ""
                for page_url in website_data.get('contact_pages', []):
                    if page_url in website_data['pages']:
                        contact_text += website_data['pages'][page_url] + "\n\n"
                
                if contact_text:
                    general_contact = extract_contact_info_from_text(contact_text)
                    
                    if contact_info['email'] == "Not found":
                        contact_info['email'] = general_contact['email']
                    
                    if contact_info['phone'] == "Not found":
                        contact_info['phone'] = general_contact['phone']
            
            # Add contact info
            dm['email'] = contact_info['email']
            dm['phone'] = contact_info['phone']
            
            # Add LinkedIn URL placeholder (will be searched later if needed)
            dm['linkedin_url'] = "Not found"
        
        logging.info(f"Found {len(decision_makers)} potential decision makers on website")
        return decision_makers
    
    except Exception as e:
        logging.error(f"Error finding decision makers from website: {e}")
        return []

# Modify the main function to include a new combined decision-maker finding function
def find_decision_makers(driver, business_name, company_website, company_linkedin_url=None):
    """
    Find decision makers using both website scraping with NER and LinkedIn as a fallback
    
    Args:
        driver: Selenium WebDriver instance
        business_name: Name of the company
        company_website: URL of the company website
        company_linkedin_url: LinkedIn URL of the company (optional)
    
    Returns:
        list: List of dictionaries containing decision maker information
    """
    logging.info(f"Finding decision makers for {business_name}")
    print(f"\n" + "-" * 40)
    print(f"🔍 Searching for top decision makers at {business_name}...")
    print("-" * 40)
    
    decision_makers = []
    
    # First try the company website if available
    if company_website and company_website != "Not found" and isinstance(company_website, str):
        if not company_website.startswith(('http://', 'https://')):
            company_website = 'https://' + company_website
        
        print(f"Searching for decision makers on company website: {company_website}")
        website_decision_makers = find_decision_makers_from_website(business_name, company_website)
        
        if website_decision_makers:
            print(f"Found {len(website_decision_makers)} potential decision makers on website")
            decision_makers.extend(website_decision_makers)
    
    # If we didn't find enough decision makers, try LinkedIn
    if len(decision_makers) < 3:
        print(f"Looking for additional decision makers on LinkedIn...")
        
        # Find company on LinkedIn if not provided
        if not company_linkedin_url:
            print("Searching for company on LinkedIn...")
            company_linkedin_url = find_company_by_name(driver, business_name)
        
        # Find top decision maker
        linkedin_dm = find_top_decision_maker(driver, business_name, company_linkedin_url)
        
        if linkedin_dm:
            # Convert to the same format as website results
            linkedin_result = {
                'name': linkedin_dm['name'],
                'title': linkedin_dm['title'],
                'title_context': '',
                'linkedin_url': linkedin_dm['linkedin_url'],
                'email': linkedin_dm['email'],
                'phone': linkedin_dm['phone'],
                'source': 'linkedin'
            }
            
            # Check if this person is already in our list (avoid duplicates)
            existing_names = [dm['name'].lower() for dm in decision_makers]
            if linkedin_result['name'].lower() not in existing_names:
                decision_makers.append(linkedin_result)
    
    # Sort decision makers (prioritize CEOs, Founders, etc.)
    decision_makers.sort(key=lambda dm: (
        0 if 'ceo' in dm['title'].lower() or 'chief executive' in dm['title'].lower() else 1,
        0 if 'founder' in dm['title'].lower() or 'co-founder' in dm['title'].lower() else 1,
        0 if 'president' in dm['title'].lower() or 'owner' in dm['title'].lower() else 1,
        0 if 'chief' in dm['title'].lower() else 1,
        0 if 'vp' in dm['title'].lower() or 'vice president' in dm['title'].lower() else 1
    ))
    
    # Limit to top 3
    decision_makers = decision_makers[:3]
    
    # Format the results for display
    if decision_makers:
        print("\n" + "✓" * 40)
        print(f"✅ Found {len(decision_makers)} decision makers for {business_name}:")
        for i, dm in enumerate(decision_makers):
            print(f"{i+1}. {dm['name']} - {dm['title']}")
            
            contact_info = []
            if dm['email'] != "Not found":
                contact_info.append(f"Email: {dm['email']}")
            if dm['phone'] != "Not found":
                contact_info.append(f"Phone: {dm['phone']}")
            
            if contact_info:
                print(f"   Contact: {', '.join(contact_info)}")
            
            print(f"   Source: {dm['source']}")
        print("✓" * 40 + "\n")
    else:
        print("\n" + "-" * 40)
        print(f"❌ No decision makers found for {business_name}")
        print("-" * 40 + "\n")
    
    return decision_makers
# Function to scrape decision makers from LinkedIn
def find_top_decision_maker(driver, company_name, company_linkedin_url):
    """
    Find the top decision maker (CEO or Founder) using direct LinkedIn search
    
    Args:
        driver: Selenium WebDriver instance
        company_name: Name of the company
        company_linkedin_url: LinkedIn URL of the company page (optional)
        
    Returns:
        Dictionary containing top decision maker details or None if not found
    """
    logging.info(f"Searching for top decision maker at {company_name}")
    print(f"Searching for top decision maker at {company_name}...")
    
    try:
        # Extract company ID and official name if company URL is available
        official_company_name = company_name
        if company_linkedin_url:
            try:
                # Visit company page to get official name
                driver.get(company_linkedin_url)
                time.sleep(1 + random.random() * 0.5)
                
                # Try to extract official company name
                name_selectors = [
                    "//h1[contains(@class, 'org-top-card-summary__title')]",
                    "//span[contains(@class, 'org-top-card-summary__title')]",
                    "//h1[contains(@class, 'org-top-card__title')]"
                ]
                
                for selector in name_selectors:
                    try:
                        name_element = driver.find_element(By.XPATH, selector)
                        if name_element:
                            official_name = name_element.text.strip()
                            if official_name:
                                official_company_name = official_name
                                logging.info(f"Found official company name: {official_company_name}")
                                break
                    except:
                        pass
            except Exception as e:
                logging.warning(f"Error getting official company name: {e}")
        
        # Priority list of titles to search for
        search_titles = [
            "CEO", 
            "Chief Executive Officer", 
            "Founder", 
            "Co-Founder", 
            "President", 
            "Owner", 
            "Chairman"
        ]
        
        # Try each title in order
        for title in search_titles:
            try:
                # Format search query with exact company name in quotes for better matching
                search_query = f'{title} "{official_company_name}"'
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
                
                logging.info(f"Trying direct search for: {search_query}")
                print(f"Searching for {title} of {official_company_name}...")
                
                driver.get(search_url)
                time.sleep(1.5 + random.random() * 0.5)
                
                # Check if we have results
                # First look for "no results" indicators
                try:
                    no_results_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'search-no-results')]")
                    if no_results_elements and len(no_results_elements) > 0:
                        logging.info(f"No results found for {search_query}")
                        continue  # Try next title
                except:
                    pass
                
                # Selectors for result items
                result_selectors = [
                    # Profile link selectors
                    "//span[contains(@class, 'entity-result__title-text')]/a[contains(@href, '/in/')]",
                    "//a[contains(@class, 'app-aware-link') and contains(@href, '/in/')]",
                    "//ul[contains(@class, 'reusable-search__entity-result-list')]//a[contains(@href, '/in/')]",
                    # Fallback to any result item
                    "//li[contains(@class, 'reusable-search__result-container')]"
                ]
                
                # Try each selector
                for selector in result_selectors:
                    try:
                        results = driver.find_elements(By.XPATH, selector)
                        if results and len(results) > 0:
                            logging.info(f"Found {len(results)} results with selector: {selector}")
                            
                            # Check each result (up to first 3) to find the best match
                            for i, result in enumerate(results[:min(3, len(results))]):
                                try:
                                    # Get profile URL
                                    profile_url = result.get_attribute('href')
                                    if not profile_url or '/in/' not in profile_url:
                                        # If we don't have a direct link, try to find it within this result
                                        try:
                                            link_element = result.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
                                            profile_url = link_element.get_attribute('href')
                                        except:
                                            continue  # Skip this result if no profile URL
                                    
                                    # Get name and title based on result structure
                                    name = ""
                                    position = ""
                                    company = ""
                                    
                                    # Different approaches to extract info based on result structure
                                    try:
                                        # First try: look for name in the clicked element
                                        if selector.endswith("a[contains(@href, '/in/')]"):
                                            name = result.text.strip()
                                            
                                            # Try to find parent container for more info
                                            parent = result.find_element(By.XPATH, "./ancestor::li[contains(@class, 'reusable-search__result-container')]")
                                            
                                            # Look for subtitle (usually contains title + company)
                                            try:
                                                subtitle_element = parent.find_element(By.XPATH, ".//div[contains(@class, 'entity-result__primary-subtitle') or contains(@class, 'search-result__subtitle')]")
                                                subtitle_text = subtitle_element.text.strip()
                                                
                                                # Usually format is "Title at Company"
                                                if " at " in subtitle_text:
                                                    position_parts = subtitle_text.split(" at ", 1)
                                                    position = position_parts[0].strip()
                                                    company = position_parts[1].strip() if len(position_parts) > 1 else ""
                                                else:
                                                    position = subtitle_text
                                            except:
                                                pass
                                        else:
                                            # Second approach: scan the container for specific elements
                                            parent = result if selector.endswith("result-container')]") else result.find_element(By.XPATH, "./ancestor::li[contains(@class, 'reusable-search__result-container')]")
                                            
                                            # Look for name
                                            try:
                                                name_element = parent.find_element(By.XPATH, ".//span[contains(@class, 'entity-result__title-text')] | .//span[contains(@class, 'actor-name')]")
                                                name = name_element.text.strip()
                                            except:
                                                name = f"Person {i+1}"
                                            
                                            # Look for position/title
                                            try:
                                                position_element = parent.find_element(By.XPATH, ".//div[contains(@class, 'entity-result__primary-subtitle') or contains(@class, 'search-result__subtitle')]")
                                                position_text = position_element.text.strip()
                                                
                                                # Usually format is "Title at Company"
                                                if " at " in position_text:
                                                    position_parts = position_text.split(" at ", 1)
                                                    position = position_parts[0].strip()
                                                    company = position_parts[1].strip() if len(position_parts) > 1 else ""
                                                else:
                                                    position = position_text
                                            except:
                                                position = f"{title} (assumed)"
                                    except Exception as e:
                                        logging.warning(f"Error parsing result {i+1}: {e}")
                                        name = f"Person {i+1}"
                                        position = f"{title} at {official_company_name}"
                                    
                                    # Verify this is really for our target company
                                    # Only accept if the company name appears in their title/position
                                    # or if this was a very specific search with the exact company name
                                    is_match = False
                                    
                                    # If company string contains our company name
                                    if company and official_company_name.lower() in company.lower():
                                        is_match = True
                                        logging.info(f"Company match found in position: {company}")
                                    
                                    # If position contains our company name
                                    elif official_company_name.lower() in position.lower():
                                        is_match = True
                                        logging.info(f"Company match found in position: {position}")
                                    
                                    # If this was a specific CEO/Founder search with exact company name
                                    elif title in ["CEO", "Founder", "Co-Founder", "Owner"] and i == 0:
                                        is_match = True
                                        logging.info(f"Accepting first result for specific {title} search")
                                    
                                    if is_match:
                                        # Create decision maker entry
                                        top_decision_maker = {
                                            'name': name,
                                            'title': position if position else f"{title} at {official_company_name}",
                                            'linkedin_url': profile_url,
                                            'email': "Not found",
                                            'phone': "Not found",
                                            'search_term': title
                                        }
                                        
                                        logging.info(f"Found potential top decision maker: {name}, {position}")
                                        
                                        # Try to get contact information
                                        try:
                                            contact_info = get_contact_information(driver, profile_url)
                                            if contact_info:
                                                top_decision_maker['email'] = contact_info.get('email', "Not found")
                                                top_decision_maker['phone'] = contact_info.get('phone', "Not found")
                                        except Exception as e:
                                            logging.warning(f"Error getting contact info: {e}")
                                        
                                        return top_decision_maker
                                    else:
                                        logging.info(f"Skipping result as company doesn't match: {company}")
                                
                                except Exception as e:
                                    logging.warning(f"Error processing result {i+1}: {e}")
                            
                            # If we get here, we found results but none matched our company
                            logging.info(f"Found results but none matched our target company")
                            break  # Break out of selector loop, try next title
                    
                    except Exception as e:
                        logging.warning(f"Error with result selector {selector}: {e}")
                
                # If we get here with no result, try next title
                logging.info(f"No suitable match found for {search_query}")
            
            except Exception as e:
                logging.warning(f"Error searching for {title}: {e}")
        
        # If we get here, we couldn't find a suitable decision maker
        logging.warning(f"Could not find top decision maker for {company_name} after trying all titles")
        return None
        
    except Exception as e:
        logging.error(f"Error in find_top_decision_maker: {e}")
        return None



def get_contact_information(driver, profile_url):
    """
    Extracts contact information from a LinkedIn profile
    
    Args:
        driver: Selenium WebDriver instance
        profile_url: URL of the LinkedIn profile
    
    Returns:
        Dictionary containing contact information (email, phone)
    """
    contact_info = {
        'email': "Not found",
        'phone': "Not found"
    }
    
    try:
        logging.info(f"Getting contact information from {profile_url}")
        
        # First navigate to the profile
        try:
            current_url = driver.current_url
            driver.get(profile_url)
            time.sleep(2 + random.random())
        except Exception as e:
            logging.warning(f"Error navigating to profile: {e}")
            return contact_info
        
        # Now navigate to contact info page
        try:
            # Construct the contact info URL
            contact_url = profile_url.rstrip('/') + '/overlay/contact-info/'
            logging.info(f"Navigating to contact info: {contact_url}")
            
            driver.get(contact_url)
            time.sleep(2 + random.random())
            
            # Take a screenshot for debugging
            profile_id = profile_url.split('/in/')[-1].rstrip('/')
            screenshot_path = os.path.join(DEBUG_FOLDER, f"contact_info_{profile_id.replace('/', '_')}.png")
            driver.save_screenshot(screenshot_path)
            
            # Look for email addresses
            email_patterns = [
                r'[\w\.-]+@[\w\.-]+\.\w+',  # Basic email pattern
                r'[\w\.-]+\s+@\s+[\w\.-]+\.\w+',  # Email with spaces around @
                r'[\w\.-]+\s+\[at\]\s+[\w\.-]+\.\w+',  # [at] instead of @
                r'[\w\.-]+\s+\(at\)\s+[\w\.-]+\.\w+'   # (at) instead of @
            ]
            
            # Get the text from the contact info section
            contact_section_selectors = [
                "//div[contains(@class, 'pv-contact-info')]",
                "//div[contains(@class, 'artdeco-modal__content')]",
                "//div[contains(@class, 'pv-profile-section__section-info')]"
            ]
            
            contact_text = ""
            for selector in contact_section_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        contact_text += element.text + "\n"
                except:
                    pass
            
            logging.info(f"Contact text: {contact_text[:200]}...")  # Log first 200 chars
            
            # Process page source for email
            page_source = driver.page_source
            
            # Look for emails in contact text
            for pattern in email_patterns:
                emails = re.findall(pattern, contact_text)
                if emails:
                    # Clean up the found email
                    email = emails[0].replace('[at]', '@').replace('(at)', '@').replace(' ', '')
                    contact_info['email'] = email
                    logging.info(f"Found email in contact text: {email}")
                    break
            
            # If not found in text, try in source
            if contact_info['email'] == "Not found":
                for pattern in email_patterns:
                    emails = re.findall(pattern, page_source)
                    if emails:
                        # Clean up the found email
                        email = emails[0].replace('[at]', '@').replace('(at)', '@').replace(' ', '')
                        contact_info['email'] = email
                        logging.info(f"Found email in page source: {email}")
                        break
            
            # Look for phone numbers in the contact text
            phone_patterns = [
                r'\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{4}',  # International format
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',       # US format
                r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'        # US format with parentheses
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, contact_text)
                if phones:
                    contact_info['phone'] = phones[0]
                    logging.info(f"Found phone: {phones[0]}")
                    break
            
            # If still not found, try once more with the whole page source
            if contact_info['phone'] == "Not found":
                for pattern in phone_patterns:
                    phones = re.findall(pattern, page_source)
                    if phones:
                        contact_info['phone'] = phones[0]
                        logging.info(f"Found phone in page source: {phones[0]}")
                        break
        
        except Exception as e:
            logging.warning(f"Error extracting contact information: {e}")
        
        return contact_info
    
    except Exception as e:
        logging.error(f"Error in get_contact_information: {e}")
        return contact_info


    
def find_company_by_name(driver, company_name):
    """
    Search for company LinkedIn page by name
    
    Args:
        driver: Selenium WebDriver instance
        company_name: Name of the company
        
    Returns:
        Company LinkedIn URL or None if not found
    """
    try:
        # Format the search query
        search_query = f"{company_name} company"
        search_url = f"https://www.linkedin.com/search/results/companies/?keywords={search_query.replace(' ', '%20')}"
        
        logging.info(f"Searching for company page: {search_query}")
        driver.get(search_url)
        time.sleep(1.5 + random.random() * 0.5)
        
        # Look for company results
        company_selectors = [
            "//a[contains(@class, 'app-aware-link') and contains(@href, '/company/')]",
            "//div[contains(@class, 'search-results')]//*[contains(@href, '/company/')]",
            "//span[contains(@class, 'entity-result__title')]/a[contains(@href, '/company/')]"
        ]
        
        for selector in company_selectors:
            try:
                company_links = driver.find_elements(By.XPATH, selector)
                if company_links and len(company_links) > 0:
                    # Get the first result URL
                    company_url = company_links[0].get_attribute('href')
                    if company_url:
                        logging.info(f"Found company page: {company_url}")
                        return company_url
            except:
                pass
        
        return None
    except Exception as e:
        logging.error(f"Error in find_company_by_name: {e}")
        return None

def get_contact_information(driver, profile_url):
    """
    Extracts contact information from a LinkedIn profile
    
    Args:
        driver: Selenium WebDriver instance
        profile_url: URL of the LinkedIn profile
    
    Returns:
        Dictionary containing contact information (email, phone)
    """
    contact_info = {
        'email': "Not found",
        'phone': "Not found"
    }
    
    try:
        logging.info(f"Getting contact information from {profile_url}")
        
        # First navigate to the profile
        try:
            current_url = driver.current_url
            driver.get(profile_url)
            time.sleep(0.5 + 0.5 * random.random())
        except Exception as e:
            logging.warning(f"Error navigating to profile: {e}")
            return contact_info
        
        # Now navigate to contact info page
        try:
            # Construct the contact info URL
            contact_url = profile_url.rstrip('/') + '/overlay/contact-info/'
            logging.info(f"Navigating to contact info: {contact_url}")
            
            driver.get(contact_url)
            time.sleep(0.5 + 0.5 * random.random())
            
            # Take a screenshot for debugging
            profile_id = profile_url.split('/in/')[-1].rstrip('/')
            screenshot_path = os.path.join(DEBUG_FOLDER, f"contact_info_{profile_id.replace('/', '_')}.png")
            driver.save_screenshot(screenshot_path)
            
            # Look for email addresses
            email_patterns = [
                r'[\w\.-]+@[\w\.-]+\.\w+',  # Basic email pattern
                r'[\w\.-]+\s+@\s+[\w\.-]+\.\w+',  # Email with spaces around @
                r'[\w\.-]+\s+\[at\]\s+[\w\.-]+\.\w+',  # [at] instead of @
                r'[\w\.-]+\s+\(at\)\s+[\w\.-]+\.\w+'   # (at) instead of @
            ]
            
            # Get the text from the contact info section
            contact_section_selectors = [
                "//div[contains(@class, 'pv-contact-info')]",
                "//div[contains(@class, 'artdeco-modal__content')]",
                "//div[contains(@class, 'pv-profile-section__section-info')]"
            ]
            
            contact_text = ""
            for selector in contact_section_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        contact_text += element.text + "\n"
                except:
                    pass
            
            logging.info(f"Contact text: {contact_text[:200]}...")  # Log first 200 chars
            
            # Process page source for email
            page_source = driver.page_source
            
            # Look for emails in contact text
            for pattern in email_patterns:
                emails = re.findall(pattern, contact_text)
                if emails:
                    # Clean up the found email
                    email = emails[0].replace('[at]', '@').replace('(at)', '@').replace(' ', '')
                    contact_info['email'] = email
                    logging.info(f"Found email in contact text: {email}")
                    break
            
            # If not found in text, try in source
            if contact_info['email'] == "Not found":
                for pattern in email_patterns:
                    emails = re.findall(pattern, page_source)
                    if emails:
                        # Clean up the found email
                        email = emails[0].replace('[at]', '@').replace('(at)', '@').replace(' ', '')
                        contact_info['email'] = email
                        logging.info(f"Found email in page source: {email}")
                        break
            
            # Look for phone numbers in the contact text
            phone_patterns = [
                r'\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{4}',  # International format
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',       # US format
                r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'        # US format with parentheses
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, contact_text)
                if phones:
                    contact_info['phone'] = phones[0]
                    logging.info(f"Found phone: {phones[0]}")
                    break
            
            # If still not found, try once more with the whole page source
            if contact_info['phone'] == "Not found":
                for pattern in phone_patterns:
                    phones = re.findall(pattern, page_source)
                    if phones:
                        contact_info['phone'] = phones[0]
                        logging.info(f"Found phone in page source: {phones[0]}")
                        break
        
        except Exception as e:
            logging.warning(f"Error extracting contact information: {e}")
        
        return contact_info
    
    except Exception as e:
        logging.error(f"Error in get_contact_information: {e}")
        return contact_info
    
# Helper functions for state name/abbreviation conversion
def state_abbreviation_to_full(abbr):
    state_dict = {
        'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 'AR': 'arkansas',
        'CA': 'california', 'CO': 'colorado', 'CT': 'connecticut', 'DE': 'delaware',
        'FL': 'florida', 'GA': 'georgia', 'HI': 'hawaii', 'ID': 'idaho',
        'IL': 'illinois', 'IN': 'indiana', 'IA': 'iowa', 'KS': 'kansas',
        'KY': 'kentucky', 'LA': 'louisiana', 'ME': 'maine', 'MD': 'maryland',
        'MA': 'massachusetts', 'MI': 'michigan', 'MN': 'minnesota', 'MS': 'mississippi',
        'MO': 'missouri', 'MT': 'montana', 'NE': 'nebraska', 'NV': 'nevada',
        'NH': 'new hampshire', 'NJ': 'new jersey', 'NM': 'new mexico', 'NY': 'new york',
        'NC': 'north carolina', 'ND': 'north dakota', 'OH': 'ohio', 'OK': 'oklahoma',
        'OR': 'oregon', 'PA': 'pennsylvania', 'RI': 'rhode island', 'SC': 'south carolina',
        'SD': 'south dakota', 'TN': 'tennessee', 'TX': 'texas', 'UT': 'utah',
        'VT': 'vermont', 'VA': 'virginia', 'WA': 'washington', 'WV': 'west virginia',
        'WI': 'wisconsin', 'WY': 'wyoming', 'DC': 'district of columbia'
    }
    if not abbr or not isinstance(abbr, str):
        return abbr
    return state_dict.get(abbr.upper(), abbr.lower())

def state_full_to_abbreviation(full_name):
    state_dict = {
        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
        'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
        'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
        'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
        'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
        'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
        'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
        'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
        'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
        'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
        'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
        'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
        'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
    }
    if not full_name or not isinstance(full_name, str):
        return full_name
    return state_dict.get(full_name.lower(), full_name)

# Add a new function to handle common city spelling variants
def normalize_city_name(city_name):
    if not city_name or not isinstance(city_name, str):
        return city_name
        
    city_name = city_name.lower().strip()
    
    # Common spelling variants and corrections
    city_variants = {
        'san fransisco': 'san francisco',
        'san fran': 'san francisco',
        'sf': 'san francisco',
        'new york city': 'new york',
        'nyc': 'new york',
        'la': 'los angeles',
        'nola': 'new orleans',
        'indy': 'indianapolis',
        'philly': 'philadelphia',
        'saint louis': 'st. louis',
        'saint paul': 'st. paul',
        'ft worth': 'fort worth',
        'ft. worth': 'fort worth',
    }
    
    # Check if this is a known variant
    if city_name in city_variants:
        return city_variants[city_name]
    
    return city_name

# Function to check if two city names might be the same despite minor spelling differences
def city_names_match(expected_city, actual_text):
    if not expected_city or not actual_text or not isinstance(expected_city, str) or not isinstance(actual_text, str):
        return False
        
    expected = normalize_city_name(expected_city)
    actual_text = actual_text.lower()
    
    # If the actual text is a complete address, try to extract just the city part
    # Common formats: "City, State", "City, State, Country", etc.
    parts = [part.strip() for part in actual_text.split(',')]
    
    # Try each part as a potential city
    for part in parts:
        # Skip very short parts which might just be state codes
        if len(part) <= 2:
            continue
            
        # Normalize this part and check for a match
        normalized_part = normalize_city_name(part)
        
        # Direct match after normalization
        if expected == normalized_part:
            return True
        
        # Check if one is contained within the other (for compound names)
        if expected in normalized_part or normalized_part in expected:
            # Only consider it a match if the contained part is a substantial portion
            shorter = min(len(expected), len(normalized_part))
            longer = max(len(expected), len(normalized_part))
            # If the shorter name is at least 60% of the longer name's length
            if shorter / longer > 0.6:
                return True
        
        # Calculate similarity for minor spelling differences
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(expected, normalized_part))
        max_len = max(len(expected), len(normalized_part))
        
        # If more than 75% of characters match (allowing for minor typos)
        if max_len > 0 and matches / max_len > 0.75:
            return True
    
    # Also check if the city is in the full text (for cases where it's not comma-separated)
    # This is less reliable but catches some cases
    if ' ' + expected + ' ' in ' ' + actual_text + ' ':
        return True
    
    return False

# New function to check if state is in text, handling multiple formats
def state_in_text(expected_state, text):
    if not expected_state or not text or not isinstance(expected_state, str) or not isinstance(text, str):
        return False
        
    # Normalize inputs
    expected_state = expected_state.lower().strip()
    text = text.lower().strip()
    
    # Get all possible representations of the state
    state_forms = [
        expected_state,
        state_abbreviation_to_full(expected_state),
        state_full_to_abbreviation(expected_state)
    ]
    
    # Remove None values
    state_forms = [form for form in state_forms if form]
    
    # Debug logging for transparency
    print(f"Checking state '{expected_state}' against text '{text}'")
    print(f"Using state forms: {state_forms}")
    
    # Direct contains check - simplest approach first
    for form in state_forms:
        if form.lower() in text.lower():
            print(f"Found state match: '{form}' in '{text}'")
            return True
    
    # Check each form against the text with more specific patterns
    for form in state_forms:
        # Check for exact match with word boundaries
        if f" {form.lower()} " in f" {text} ":
            print(f"Found state match with word boundaries: '{form}' in '{text}'")
            return True
            
        # Check for form followed by comma or at end of string
        if f" {form.lower()}," in f" {text}" or text.endswith(f" {form.lower()}"):
            print(f"Found state match with comma or end: '{form}' in '{text}'")
            return True
            
        # For two-letter state codes, also check without spaces (e.g., "NY" in "New York, NY")
        if len(form) == 2:
            if f", {form.upper()}" in text or f" {form.upper()} " in f" {text} " or text.endswith(f" {form.upper()}"):
                print(f"Found state match with abbreviation: '{form.upper()}' in '{text}'")
                return True
                
    # Also check each part of comma-separated text
    parts = [part.strip() for part in text.split(',')]
    for part in parts:
        for form in state_forms:
            if form.lower() == part.lower() or (len(form) == 2 and form.upper() == part.upper()):
                print(f"Found state match in part: '{form}' in part '{part}' of '{text}'")
                return True
    
    print(f"No state match found for '{expected_state}' in '{text}'")
    return False

# Main function
def main(csv_file, output_file, username, password, keep_browser_open=True, find_decision_makers_flag=True):
    global global_driver
    
    # Check if required parameters are present
    if not username or not password:
        logging.error("LinkedIn credentials not provided")
        print("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables")
        return
    
    # Load NER models once for all companies if find_decision_makers_flag is True
    ner_models = None
    if find_decision_makers_flag:
        try:
            logging.info("Loading NER models...")
            ner_models = load_ner_models()
            logging.info("NER models loaded successfully")
        except Exception as e:
            logging.warning(f"Error loading NER models: {e}. Will rely more on LinkedIn for decision makers.")
    
    # Read the CSV file
    try:
        df = read_csv(csv_file)
        # Add debug information about the CSV
        print(f"CSV loaded successfully with {len(df)} rows")
        print("First few company names:")
        for name in df['Company'].head().tolist():
            print(f"  - {name}")
        
        # Check if Company column exists
        if 'Company' not in df.columns:
            logging.error("CSV file does not contain a 'Company' column")
            print("ERROR: Your CSV file must contain a column named 'Company'")
            return
            
        # Check if the Company column has data
        if df['Company'].empty or df['Company'].isna().all():
            logging.error("CSV file contains an empty 'Company' column")
            print("ERROR: Your CSV file must contain data in the 'Company' column")
            return
            
        # Check for City and State columns
        has_location_data = 'City' in df.columns and 'State' in df.columns
        if not has_location_data:
            logging.warning("CSV file does not contain 'City' and/or 'State' columns. Will not perform location validation.")
            print("WARNING: Your CSV file does not have 'City' and/or 'State' columns. Location validation will be skipped.")
        else:
            print("Found location data in CSV. Will perform location validation.")

    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        print(f"Error reading CSV file: {e}")
        return
    
    # Initialize variables
    results = []
    failed_businesses = []
    
    try:
        # Check if a WebDriver instance is already running (for reconnection)
        chrome_info = load_chrome_info()
        if chrome_info and global_driver and is_driver_active(global_driver):
            print("Using existing Chrome instance")
            driver = global_driver
        else:
            # Display error message if the info file exists but we couldn't connect
            if chrome_info:
                print("Could not reconnect to existing Chrome instance. Starting new browser.")
                if os.path.exists(CHROME_INFO_FILE):
                    os.remove(CHROME_INFO_FILE)
            
            # Initialize a new Chrome WebDriver
            port = find_available_port()
            user_data_dir = os.path.abspath("chrome_user_data")
            
            # Create user data directory if it doesn't exist
            os.makedirs(user_data_dir, exist_ok=True)
            
            print(f"Starting new Chrome instance on port {port}")
            print(f"User data directory: {user_data_dir}")
            
            chrome_options = Options()
            chrome_options.add_argument(f"--remote-debugging-port={port}")
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
            
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                driver.implicitly_wait(10)
                global_driver = driver
                
                # Save Chrome debugging info for future connections
                save_chrome_info(port, user_data_dir)
                
                logging.info("WebDriver initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize Chrome driver: {e}")
                print(f"ERROR: Could not initialize Chrome: {e}")
                return
            
            # Log in to LinkedIn
            try:
                print("Logging in to LinkedIn...")
                login_to_linkedin(driver, username, password)
                print("Login successful! Current URL: " + driver.current_url)
                print("Taking a screenshot after login...")
                driver.save_screenshot(os.path.join(DEBUG_FOLDER, "after_login.png"))
                print(f"Screenshot saved to {os.path.join(DEBUG_FOLDER, 'after_login.png')}")
            except Exception as e:
                logging.error(f"Failed to log in: {e}")
                if "security checkpoint" in str(e).lower():
                    print("\n" + "="*80)
                    print("SCRIPT STOPPED: Maximum retries for security checkpoint exceeded.")
                    print("Please try running the script again later, or use a different LinkedIn account.")
                    print("="*80 + "\n")
                driver.quit()
                global_driver = None
                if os.path.exists(CHROME_INFO_FILE):
                    os.remove(CHROME_INFO_FILE)
                return
        
        print("\n" + "="*80)
        print("STARTING COMPANY SCRAPING")
        print(f"Total companies to process: {len(df['Company'])}")
        print("="*80 + "\n")
        
        # Process each business
        for i, row in df.iterrows():
            business_name = row['Company']
            
            # Get city and state if available
            city = row.get('City') if has_location_data else None
            state = row.get('State') if has_location_data else None
            
            # Clean and normalize city and state if available
            if city and state:
                city = city.strip()
                state = state.strip()
                # Convert city to lowercase for better matching
                city = city.lower()
                # Normalize state name to consistent format
                if len(state) == 2:  # It's an abbreviation
                    state = state_abbreviation_to_full(state)
                else:
                    state = state.lower()
            
            print("\n" + "-"*50)
            print(f"Processing {i+1}/{len(df['Company'])}: {business_name}")
            if city and state:
                print(f"Expected location: {city}, {state}")
            print("-"*50)
            
            # Setup timeout monitoring
            max_time_per_company = 120  # seconds - increased from 90 to account for website scraping
            timeout_occurred = [False]  # Use array to allow modification in nested function
            start_time = time.time()  # Track the start time
            
            # Define timeout check function
            def check_timeout():
                # Get current time
                end_time = time.time()
                # If time exceeded, set flag and take screenshot
                if end_time - start_time > max_time_per_company:
                    print(f"WARNING: Processing of {business_name} is taking too long (over {max_time_per_company} seconds)")
                    print("The process may be stuck. Taking a screenshot for debugging...")
                    try:
                        driver.save_screenshot(os.path.join(DEBUG_FOLDER, f"timeout_{business_name.replace(' ', '_')}.png"))
                        timeout_occurred[0] = True
                    except:
                        print("Could not take timeout screenshot.")
            
            # Start timeout monitor
            timer = threading.Timer(max_time_per_company, check_timeout)
            timer.start()
            
            try:
                # Get company info from LinkedIn
                result = scrape_linkedin(driver, business_name, city, state)
                result['Business Name'] = business_name
                
                # Process decision makers if flag is set
                if find_decision_makers_flag:
                    print("\n" + "-" * 40)
                    print(f"🔍 Searching for decision makers at {business_name}...")
                    print("-" * 40)
                    
                    # First try to find decision makers from the company website
                    decision_makers = []
                    company_website = result.get('Company Website')
                    
                    if company_website and company_website != "Not found":
                        # Ensure website URL has protocol
                        if not company_website.startswith(('http://', 'https://')):
                            company_website = 'https://' + company_website
                        
                        print(f"Trying to find decision makers on company website: {company_website}")
                        try:
                            website_decision_makers = find_decision_makers_from_website(business_name, company_website)
                            if website_decision_makers:
                                print(f"Found {len(website_decision_makers)} decision makers from website")
                                decision_makers.extend(website_decision_makers)
                        except Exception as e:
                            logging.warning(f"Error finding decision makers from website: {e}")
                            print(f"Could not find decision makers from website: {str(e)[:100]}...")
                    
                    # If we didn't find enough decision makers (3), try LinkedIn as fallback
                    if len(decision_makers) < 3:
                        remaining_slots = 3 - len(decision_makers)
                        print(f"Looking for {remaining_slots} more decision makers on LinkedIn...")
                        
                        # Get LinkedIn company URL
                        company_linkedin_url = result.get('LinkedIn Link')
                        
                        # Try to find top decision makers via LinkedIn
                        top_dm = find_top_decision_maker(driver, business_name, company_linkedin_url)
                        
                        if top_dm:
                            # Convert to the same format as website results
                            linkedin_dm = {
                                'name': top_dm['name'],
                                'title': top_dm['title'],
                                'title_context': '',
                                'linkedin_url': top_dm['linkedin_url'],
                                'email': top_dm['email'],
                                'phone': top_dm['phone'],
                                'source': 'linkedin'
                            }
                            
                            # Check if this person is already in our list (avoid duplicates)
                            is_duplicate = False
                            for existing_dm in decision_makers:
                                # Simple name similarity check
                                if existing_dm['name'].lower() == linkedin_dm['name'].lower():
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                decision_makers.append(linkedin_dm)
                    
                    # Sort decision makers by role priority
                    def get_role_priority(dm):
                        title = dm['title'].lower()
                        if 'ceo' in title or 'chief executive' in title:
                            return 0
                        if 'founder' in title or 'co-founder' in title:
                            return 1
                        if 'president' in title or 'owner' in title:
                            return 2
                        if 'chief' in title:
                            return 3
                        if 'vp' in title or 'vice president' in title:
                            return 4
                        return 5
                    
                    decision_makers.sort(key=get_role_priority)
                    
                    # Take only top 3
                    decision_makers = decision_makers[:3]
                    
                    # Display results
                    if decision_makers:
                        print("\n" + "✓" * 40)
                        print(f"✅ Found {len(decision_makers)} decision makers for {business_name}:")
                        for i, dm in enumerate(decision_makers):
                            print(f"{i+1}. {dm['name']} - {dm['title']}")
                            
                            contact_info = []
                            if dm['email'] != "Not found":
                                contact_info.append(f"Email: {dm['email']}")
                            if dm['phone'] != "Not found":
                                contact_info.append(f"Phone: {dm['phone']}")
                            
                            if contact_info:
                                print(f"   Contact: {', '.join(contact_info)}")
                            
                            print(f"   Source: {dm['source']}")
                        print("✓" * 40 + "\n")
                        
                        # Add to result dict for CSV output
                        for i, dm in enumerate(decision_makers, 1):
                            result[f'Decision Maker {i} Name'] = dm['name']
                            result[f'Decision Maker {i} Title'] = dm['title']
                            result[f'Decision Maker {i} LinkedIn'] = dm.get('linkedin_url', 'Not found')
                            result[f'Decision Maker {i} Email'] = dm['email']
                            result[f'Decision Maker {i} Phone'] = dm['phone']
                            result[f'Decision Maker {i} Source'] = dm['source']
                        
                        # Fill in empty slots if we have fewer than 3
                        for i in range(len(decision_makers) + 1, 4):
                            result[f'Decision Maker {i} Name'] = "Not found"
                            result[f'Decision Maker {i} Title'] = "Not found"
                            result[f'Decision Maker {i} LinkedIn'] = "Not found"
                            result[f'Decision Maker {i} Email'] = "Not found"
                            result[f'Decision Maker {i} Phone'] = "Not found"
                            result[f'Decision Maker {i} Source'] = "Not found"
                    else:
                        print("\n" + "-" * 40)
                        print(f"❌ No decision makers found for {business_name}")
                        print("-" * 40 + "\n")
                        
                        # Add empty fields
                        for i in range(1, 4):
                            result[f'Decision Maker {i} Name'] = "Not found"
                            result[f'Decision Maker {i} Title'] = "Not found"
                            result[f'Decision Maker {i} LinkedIn'] = "Not found"
                            result[f'Decision Maker {i} Email'] = "Not found"
                            result[f'Decision Maker {i} Phone'] = "Not found"
                            result[f'Decision Maker {i} Source'] = "Not found"
                else:
                    # If search is disabled
                    logging.info(f"Decision maker search is disabled. Skipping for {business_name}")
                    
                    # Add placeholder fields
                    for i in range(1, 4):
                        result[f'Decision Maker {i} Name'] = "Not searched"
                        result[f'Decision Maker {i} Title'] = "Not searched"
                        result[f'Decision Maker {i} LinkedIn'] = "Not searched" 
                        result[f'Decision Maker {i} Email'] = "Not searched"
                        result[f'Decision Maker {i} Phone'] = "Not searched"
                        result[f'Decision Maker {i} Source'] = "Not searched"
                
                results.append(result)
                
                # Cancel timeout timer if successful
                timer.cancel()
                
                # Check if timeout occurred
                if timeout_occurred[0]:
                    print("WARNING: Processing completed but took longer than expected.")
                
            except Exception as e:
                # Cancel timeout timer
                timer.cancel()
                
                if timeout_occurred[0]:
                    print(f"ERROR: Processing timed out for {business_name}. Attempting to recover...")
                    try:
                        # Try to navigate to LinkedIn home to reset state
                        driver.get("https://www.linkedin.com/feed/")
                        time.sleep(1)
                        print("Navigated to LinkedIn feed to reset state")
                    except:
                        print("Could not navigate to LinkedIn feed")
                
                error_msg = str(e)
                logging.error(f"Error processing {business_name}: {error_msg}")
                
                # Check if this is a security checkpoint issue
                if "security checkpoint" in error_msg.lower() or "captcha" in error_msg.lower():
                    try:
                        # Take a screenshot to help user understand the issue
                        screenshot_path = os.path.join(DEBUG_FOLDER, f"error_checkpoint_{business_name.replace(' ', '_')}.png")
                        driver.save_screenshot(screenshot_path)
                        
                        # Ask for manual intervention for this critical error
                        wait_for_manual_intervention(driver, 
                            f"Critical security checkpoint encountered while processing {business_name}. Please complete the verification.")
                        
                        # Try once more after manual intervention
                        logging.info(f"Retrying {business_name} after manual security checkpoint intervention")
                        result = scrape_linkedin(driver, business_name, city, state)
                        result['Business Name'] = business_name
                        
                        # Add empty fields for decision makers
                        for i in range(1, 4):
                            result[f'Decision Maker {i} Name'] = "Not found"
                            result[f'Decision Maker {i} Title'] = "Not found"
                            result[f'Decision Maker {i} LinkedIn'] = "Not found"
                            result[f'Decision Maker {i} Email'] = "Not found"
                            result[f'Decision Maker {i} Phone'] = "Not found"
                            result[f'Decision Maker {i} Source'] = "Error"
                        
                        results.append(result)
                        
                    except Exception as retry_error:
                        logging.error(f"Retry also failed for {business_name}: {retry_error}")
                        failed_businesses.append(business_name)
                        result = {
                            'Business Name': business_name,
                            'LinkedIn Link': None,
                            'Company Website': None,
                            'Company Size': None,
                            'Industry': None,
                            'Headquarters': None,
                            'Founded': None,
                            'Specialties': None,
                            'Location Match': "Error: Manual intervention required"
                        }
                        
                        # Add empty fields for decision makers
                        for i in range(1, 4):
                            result[f'Decision Maker {i} Name'] = "Error"
                            result[f'Decision Maker {i} Title'] = "Error"
                            result[f'Decision Maker {i} LinkedIn'] = "Error"
                            result[f'Decision Maker {i} Email'] = "Error"
                            result[f'Decision Maker {i} Phone'] = "Error"
                            result[f'Decision Maker {i} Source'] = "Error"
                        
                        results.append(result)
                else:
                    # For non-security related errors, just add to failed list
                    failed_businesses.append(business_name)
                    
                    # Extract just the main error message without the stack trace
                    error_msg = str(e)
                    # Get only the first line or a shorter version of the error message
                    if '\n' in error_msg:
                        error_msg = error_msg.split('\n')[0]
                    # Limit the length of the error message
                    if len(error_msg) > 100:
                        error_msg = error_msg[:97] + "..."
                    
                    result = {
                        'Business Name': business_name,
                        'LinkedIn Link': None,
                        'Company Website': None,
                        'Company Size': None,
                        'Industry': None,
                        'Headquarters': None,
                        'Founded': None,
                        'Specialties': None,
                        'Location Match': f"Error: {error_msg}"
                    }
                    
                    # Add empty fields for decision makers
                    for i in range(1, 4):
                        result[f'Decision Maker {i} Name'] = "Error"
                        result[f'Decision Maker {i} Title'] = "Error"
                        result[f'Decision Maker {i} LinkedIn'] = "Error"
                        result[f'Decision Maker {i} Email'] = "Error"
                        result[f'Decision Maker {i} Phone'] = "Error"
                        result[f'Decision Maker {i} Source'] = "Error"
                    
                    results.append(result)
            
            # Add random delay between 1.5-3 seconds to avoid detection
            sleep_time = 1.5 + 1.5 * random.random()
            logging.info(f"Waiting {sleep_time:.2f} seconds before next request")
            time.sleep(sleep_time)
            
            # Periodically save intermediate results
            if (i + 1) % 5 == 0 or (i + 1) == len(df['Company']):
                intermediate_df = pd.DataFrame(results)
                if not intermediate_df.empty and 'Business Name' in intermediate_df.columns:
                    # Base columns
                    cols = ['Business Name', 'LinkedIn Link', 'Company Website', 'Company Size', 
                            'Industry', 'Headquarters', 'Founded', 'Specialties', 'Location Match']
                    
                    # Add decision maker columns with source field
                    decision_maker_cols = []
                    for j in range(1, 4):
                        for field in ['Name', 'Title', 'LinkedIn', 'Email', 'Phone', 'Source']:
                            col = f'Decision Maker {j} {field}'
                            if any(col in result for result in results):
                                decision_maker_cols.append(col)
                    
                    # Combine all columns
                    all_cols = cols + decision_maker_cols
                    
                    # Only include columns that exist in the data
                    available_cols = [col for col in all_cols if col in intermediate_df.columns]
                    intermediate_df = intermediate_df[available_cols]
                
                intermediate_file = os.path.join(DEBUG_FOLDER, f"intermediate_results_{i+1}.csv")
                intermediate_df.to_csv(intermediate_file, index=False, quoting=csv.QUOTE_ALL)
                logging.info(f"Saved intermediate results to {intermediate_file}")
                print(f"Progress: {i+1}/{len(df['Company'])} companies processed.")
        
    except Exception as e:
        logging.error(f"Critical error in main execution: {e}")
        print(f"CRITICAL ERROR: {e}")
        # Try to save any results we've collected so far
        if results:
            emergency_df = pd.DataFrame(results)
            emergency_file = os.path.join(DEBUG_FOLDER, "emergency_results.csv")
            emergency_df.to_csv(emergency_file, index=False, quoting=csv.QUOTE_ALL)
            print(f"Saved emergency results to {emergency_file}")
    
    finally:
        # Don't close the WebDriver if keep_browser_open is True
        if not keep_browser_open:
            if global_driver:
                global_driver.quit()
            global_driver = None
            if os.path.exists(CHROME_INFO_FILE):
                os.remove(CHROME_INFO_FILE)
        else:
            print("\n" + "="*80)
            print("CHROME BROWSER KEPT OPEN")
            print("The browser will remain open for future use. To close it, exit the program.")
            print("You can use the same browser session for the next scraping task.")
            print("="*80 + "\n")
        
        # Save the results to a CSV file
        results_df = pd.DataFrame(results)
        
        # Reorder columns to have Business Name first
        if not results_df.empty and 'Business Name' in results_df.columns:
            # Base columns
            cols = ['Business Name', 'LinkedIn Link', 'Company Website', 'Company Size', 
                    'Industry', 'Headquarters', 'Founded', 'Specialties', 'Location Match']
            
            # Add decision maker columns
            for i in range(1, 4):
                cols.extend([
                    f'Decision Maker {i} Name', 
                    f'Decision Maker {i} Title', 
                    f'Decision Maker {i} LinkedIn',
                    f'Decision Maker {i} Email', 
                    f'Decision Maker {i} Phone',
                    f'Decision Maker {i} Source'
                ])
            
            # Only include columns that exist in the data
            available_cols = [col for col in cols if col in results_df.columns]
            results_df = results_df[available_cols]
        
        results_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
        logging.info(f"Results saved to {output_file}")
        
        # Report on failed businesses
        if failed_businesses:
            failed_file = os.path.join(DEBUG_FOLDER, "failed_businesses.csv")
            pd.DataFrame({'Business Name': failed_businesses}).to_csv(failed_file, index=False)
            logging.info(f"List of {len(failed_businesses)} failed businesses saved to {failed_file}")
            print(f"\nNOTE: {len(failed_businesses)} businesses could not be scraped. See {failed_file} for details.")
            
if __name__ == "__main__":
    file_path = 'sample_data.csv'
    output_file = 'scraped_results.csv'
    
    print("Starting LinkedIn scraper script...")
    
    # Check if the sample data file exists, if not create it with sample data
    if not os.path.exists(file_path):
        print(f"Sample data file '{file_path}' not found. Creating a sample file...")
        try:
            # Create a simple CSV with a few company names for testing
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Company', 'City', 'State'])  # Header with location columns
                writer.writerow(['Microsoft', 'Redmond', 'Washington'])
                writer.writerow(['Google', 'Mountain View', 'California'])
                writer.writerow(['Apple', 'Cupertino', 'California'])
                writer.writerow(['Amazon', 'Seattle', 'Washington'])
                writer.writerow(['Meta', 'Menlo Park', 'California'])
            print(f"Created sample data file with 5 technology companies including location data")
        except Exception as e:
            print(f"Failed to create sample data file: {e}")
            logging.error(f"Failed to create sample data file: {e}")
            exit(1)
    
    print(f"Looking for data in: {file_path}")
    
    # Get LinkedIn credentials from environment variables
    load_dotenv()
    username = os.getenv('LINKEDIN_USERNAME')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    print(f"Loaded environment variables - Username present: {'Yes' if username else 'No'}")
    
    if not username or not password:
        print("LinkedIn credentials not found in environment variables. Using fallback:")
        username = "bob549108@gmail.com"
        password = "LinkedidBob123."
    
    try:
        print("Starting main process...")
        main(file_path, output_file, username, password, keep_browser_open=True, find_decision_makers_flag=True)
        print("Process completed successfully!")
        
        # Check if we have a Chrome session running
        chrome_info = load_chrome_info()
        if chrome_info and is_chrome_running(chrome_info['port']):
            print("\n" + "="*80)
            print(f"CHROME SESSION INFORMATION")
            print(f"Debug Port: {chrome_info['port']}")
            print(f"User Data Directory: {chrome_info['user_data_dir']}")
            print("This Chrome session will remain open even after this script exits.")
            print("You can run the script again to reuse this same Chrome instance.")
            print("="*80 + "\n")
            
        # Keep program running to maintain the browser session
        while global_driver is not None and is_driver_active(global_driver):
            try:
                print("\nBrowser is still running. Press Ctrl+C to exit and close the browser.")
                time.sleep(10)  # Check every 10 seconds
            except KeyboardInterrupt:
                print("\nUser interrupted. Closing browser and exiting...")
                if global_driver:
                    global_driver.quit()
                if os.path.exists(CHROME_INFO_FILE):
                    os.remove(CHROME_INFO_FILE)
                break
            
    except Exception as e:
        print(f"ERROR: Script failed with error: {e}")
        logging.error(f"Script failed with error: {e}", exc_info=True)
        
        # Save all available diagnostic information to a file
        try:
            with open(os.path.join(DEBUG_FOLDER, "error_diagnostic.log"), "w") as f:
                import traceback
                f.write("=== ERROR DETAILS ===\n")
                f.write(f"Error: {str(e)}\n\n")
                f.write("=== STACK TRACE ===\n")
                traceback.print_exc(file=f)
                f.write("\n=== ENVIRONMENT INFO ===\n")
                import platform
                import sys
                f.write(f"Python version: {sys.version}\n")
                f.write(f"Platform: {platform.platform()}\n")
                f.write(f"Working directory: {os.getcwd()}\n")
                f.write("\n=== FILE STATUS ===\n")
                if os.path.exists(file_path):
                    f.write(f"Input file exists: Yes (Size: {os.path.getsize(file_path)} bytes)\n")
                else:
                    f.write("Input file exists: No\n")
                
            print(f"Diagnostic information saved to error_diagnostic.log")
        except Exception as log_error:
            print(f"Failed to write diagnostic log: {log_error}")
