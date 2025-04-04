import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import os
from dotenv import load_dotenv
import csv
import random  # Add random module for randomized wait times

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read the CSV file
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Successfully read CSV file: {file_path}")
        return df
    except Exception as e:
        logging.error(f"Error reading CSV file {file_path}: {e}")
        raise

# Function to log in to LinkedIn
def login_to_linkedin(driver, username, password):
    logging.info("Attempting to log in to LinkedIn")
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
        
        # Check if login was successful
        if "checkpoint" in driver.current_url or "login" in driver.current_url:
            logging.error("Login failed or hit a security checkpoint")
            raise Exception("LinkedIn security checkpoint detected")
            
        logging.info("Successfully logged in to LinkedIn")
        
    except Exception as e:
        logging.error(f"Error logging in: {e}")
        raise

# Function to scrape LinkedIn for business details
def scrape_linkedin(driver, business_name):
    logging.info(f"Searching for business: {business_name}")
    url = f"https://www.linkedin.com/search/results/companies/?keywords={business_name}"
    driver.get(url)
    time.sleep(2 + random.random())  # Reduced from 5 seconds
    
    try:
        # Log the current URL for debugging
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
                company_links = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                if company_links:
                    used_selector = selector
                    logging.info(f"Found {len(company_links)} company links using selector: {selector}")
                    break
            except Exception as e:
                logging.warning(f"Selector {selector} failed: {e}")
        
        if not company_links:
           
            screenshot_path = f"search_results_{business_name.replace(' ', '_')}.png"
            driver.save_screenshot(screenshot_path)
            logging.warning(f"No results found for {business_name}. Screenshot saved to {screenshot_path}")
            return {
                'LinkedIn Link': None,
                'Company Website': None,
                'Company Size': None,
                'Industry': None
            }
        
        for i, link in enumerate(company_links[:5]): 
            try:
                href = link.get_attribute('href')
                text = link.text
                logging.info(f"Link {i}: href={href}, text={text}")
            except:
                logging.info(f"Link {i}: Could not get attributes")
        
        # Click on the first result
        company_link = company_links[0].get_attribute('href')
        logging.info(f"Found company link: {company_link}")
        
        # Try different click methods
        try:
            logging.info("Attempting to click using .click() method")
            company_links[0].click()
        except Exception as e:
            logging.warning(f"Direct click failed: {e}")
            try:
                logging.info("Attempting to click using JavaScript")
                driver.execute_script("arguments[0].click();", company_links[0])
            except Exception as e:
                logging.warning(f"JavaScript click failed: {e}")
                logging.info("Attempting to navigate directly to the company URL")
                driver.get(company_link)
        
        time.sleep(2 + random.random())  # Reduced from 5 seconds
        
        # Log current URL to verify navigation occurred
        logging.info(f"Current URL after clicking: {driver.current_url}")
        
        # Directly navigate to the About page by modifying the URL
        about_url = company_link
        if not about_url.endswith('/'):
            about_url += '/'
        about_url += 'about/'
        logging.info(f"Navigating to About page: {about_url}")
        driver.get(about_url)
        
        # Allow more time for the page to fully load
        time.sleep(2.5 + random.random())  # Reduced from 6 seconds
        
        # Take a screenshot of the About page for debugging
        screenshot_path = f"about_page_{business_name.replace(' ', '_')}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Saved screenshot of About page to {screenshot_path}")
        
        # Scroll down to make sure all content is loaded
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(0.5 + 0.5 * random.random())  # Reduced from 2 seconds
        
        # Dump the HTML content to a file for debugging
        html_file = f"page_source_{business_name.replace(' ', '_')}.html"
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
            
            # If website not found in section text, try XPath selectors
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
                    "//div[contains(@class, 'core-section-container')]//div[contains(text(), 'Industry')]/following-sibling::div"
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
            
            # Last resort - try to extract keywords from the entire page
            if company_size == "Not found" or industry == "Not found" or company_website == "Not found":
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
                    
                    # If still not found, try one more approach - search in the source code
                    if industry == "Not found":
                        logging.info("Trying to extract industry from page source code")
                        
                        # Look for specific industry mentions in the source
                        industry_patterns = [
                            r'"name":"([^"]+)","entityUrn":"urn:li:fsd_industry:',
                            r'"name":"([^"]+)","entityUrn":"urn:li:fsd_industryV2:'
                        ]
                        
                        # First, try direct pattern matching
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
                
        # Final check before returning
        if industry == "":
            industry = "Not found"
        
        return {
            'LinkedIn Link': company_link,
            'Company Website': company_website,
            'Company Size': company_size,
            'Industry': industry
        }
        
    except Exception as e:
        logging.error(f"Error scraping {business_name}: {e}")
        # Take screenshot for debugging
        screenshot_path = f"error_{business_name.replace(' ', '_')}.png"
        try:
            driver.save_screenshot(screenshot_path)
            logging.info(f"Error screenshot saved to {screenshot_path}")
        except:
            logging.warning("Could not save error screenshot")
            
        return {
            'LinkedIn Link': None,
            'Company Website': None,
            'Company Size': None,
            'Industry': None
        }

# Main function
def main(csv_file, output_file, username, password):
    # Check if required parameters are present
    if not username or not password:
        logging.error("LinkedIn credentials not provided")
        print("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables")
        return
    
    # Read the CSV file
    try:
        df = read_csv(csv_file)
    except Exception as e:
        logging.error(f"Failed to read CSV: {e}")
        return
    
    # Setup Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode (no GUI) - temporarily disabled for debugging
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
        logging.info("WebDriver initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Chrome driver: {e}")
        return
    
    # Log in to LinkedIn
    try:
        login_to_linkedin(driver, username, password)
    except Exception as e:
        logging.error(f"Failed to log in: {e}")
        driver.quit()
        return
    
    # Scrape LinkedIn for each business
    results = []
    for business_name in df['Company']:
        try:
            result = scrape_linkedin(driver, business_name)
            result['Business Name'] = business_name
            results.append(result)
            # Add random delay between 1.5-3 seconds to avoid detection (reduced from 3-8 seconds)
            sleep_time = 1.5 + 1.5 * random.random()
            logging.info(f"Waiting {sleep_time:.2f} seconds before next request")
            time.sleep(sleep_time)
        except Exception as e:
            logging.error(f"Error processing {business_name}: {e}")
            results.append({
                'Business Name': business_name,
                'LinkedIn Link': None,
                'Company Website': None,
                'Company Size': None,
                'Industry': None
            })
    
    # Close the WebDriver
    driver.quit()
    
    # Save the results to a CSV file
    results_df = pd.DataFrame(results)
    # Reorder columns to have Business Name first
    if not results_df.empty and 'Business Name' in results_df.columns:
        cols = ['Business Name', 'LinkedIn Link', 'Company Website', 'Company Size', 'Industry']
        results_df = results_df[cols]
    results_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
    logging.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    file_path = 'sample_data.csv'
    output_file = 'scraped_results.csv'
    
    print("Starting LinkedIn scraper script...")
    print(f"Looking for data in: {file_path}")
    
    # Get LinkedIn credentials from environment variables
    load_dotenv()
    username = os.getenv('LINKEDIN_USERNAME')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    print(f"Loaded environment variables - Username present: {'Yes' if username else 'No'}")
    
    if not username or not password:
        print("LinkedIn credentials not found in environment variables. Using fallback:")
        username = "lim193208@gmail.com"
        password = "123Testing90."
    
    try:
        print("Starting main process...")
        main(file_path, output_file, username, password)
        print("Process completed successfully!")
    except Exception as e:
        print(f"ERROR: Script failed with error: {e}")
        logging.error(f"Script failed with error: {e}", exc_info=True)
        
        # Save all available diagnostic information to a file
        try:
            with open("error_diagnostic.log", "w") as f:
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