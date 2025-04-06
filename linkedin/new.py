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
    time.sleep(2)  # Give a moment for page to settle after manual action
    return True

# Function to log in to LinkedIn
def login_to_linkedin(driver, username, password):
    logging.info("Checking LinkedIn login status")
    
    # First check if we're already logged in by visiting LinkedIn homepage
    driver.get('https://www.linkedin.com/')
    time.sleep(2 + random.random())
    
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
    time.sleep(2 + random.random())  # Reduced from 5 seconds
    
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
        time.sleep(1 + random.random())  # Reduced from 2 seconds
        login_button.click()
        
        # Wait longer after login to ensure page loads
        time.sleep(4)  # Updated to exactly 4 seconds
        
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
                time.sleep(3)  # Wait a bit for page to update
                
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
            time.sleep(2)
            
        time.sleep(2 + random.random())  # Reduced from 5 seconds
        
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
                        time.sleep(2 + random.random())
                        
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
                            time.sleep(1 + random.random())
                            
                        except Exception as e:
                            logging.warning(f"Error checking location on company page: {e}")
                            driver.get(search_results_url)
                            time.sleep(1 + random.random())
                            
                    except Exception as e:
                        logging.warning(f"Error checking company {i+1}: {e}")
                        # Try to return to search results
                        driver.get(search_results_url)
                        time.sleep(1 + random.random())
        
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
        time.sleep(2 + random.random())
        
        # Check if we're on the "about" page, if not, navigate to it
        if '/about/' not in driver.current_url:
            about_url = company_link.rstrip('/') + '/about/'
            logging.info(f"Navigating to about page: {about_url}")
            driver.get(about_url)
            time.sleep(2 + random.random())
        
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
def main(csv_file, output_file, username, password, keep_browser_open=True):
    global global_driver
    
    # Check if required parameters are present
    if not username or not password:
        logging.error("LinkedIn credentials not provided")
        print("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables")
        return
    
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
            max_time_per_company = 90  # seconds
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
                result = scrape_linkedin(driver, business_name, city, state)
                result['Business Name'] = business_name
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
                        time.sleep(2)
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
                        results.append(result)
                        
                    except Exception as retry_error:
                        logging.error(f"Retry also failed for {business_name}: {retry_error}")
                        failed_businesses.append(business_name)
                        results.append({
                            'Business Name': business_name,
                            'LinkedIn Link': None,
                            'Company Website': None,
                            'Company Size': None,
                            'Industry': None,
                            'Headquarters': None,
                            'Founded': None,
                            'Specialties': None,
                            'Location Match': "Error: Manual intervention required"
                        })
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
                        
                    results.append({
                        'Business Name': business_name,
                        'LinkedIn Link': None,
                        'Company Website': None,
                        'Company Size': None,
                        'Industry': None,
                        'Headquarters': None,
                        'Founded': None,
                        'Specialties': None,
                        'Location Match': f"Error: {error_msg}"
                    })
            
            # Add random delay between 1.5-3 seconds to avoid detection (reduced from 3-8 seconds)
            sleep_time = 1.5 + 1.5 * random.random()
            logging.info(f"Waiting {sleep_time:.2f} seconds before next request")
            time.sleep(sleep_time)
            
            # Periodically save intermediate results
            if (i + 1) % 5 == 0 or (i + 1) == len(df['Company']):
                intermediate_df = pd.DataFrame(results)
                if not intermediate_df.empty and 'Business Name' in intermediate_df.columns:
                    cols = ['Business Name', 'LinkedIn Link', 'Company Website', 'Company Size', 'Industry', 'Headquarters', 'Founded', 'Specialties', 'Location Match']
                    intermediate_df = intermediate_df[cols]
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
            cols = ['Business Name', 'LinkedIn Link', 'Company Website', 'Company Size', 'Industry', 'Headquarters', 'Founded', 'Specialties', 'Location Match']
            results_df = results_df[cols]
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
        main(file_path, output_file, username, password, keep_browser_open=True)
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
