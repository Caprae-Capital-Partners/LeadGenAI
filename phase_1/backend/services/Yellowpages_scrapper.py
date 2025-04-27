from playwright.sync_api import sync_playwright
import time
import random
import csv
import os
import logging
from urllib.parse import quote_plus

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("yellowpages_scraper")

def setup_browser(playwright, headless=True, with_custom_headers=False):
    """Set up and return a configured Playwright browser instance with improved anti-detection."""
    # Select random user agent - using more diverse and up-to-date options
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Edge/121.0.0.0'
    ]
    user_agent = random.choice(user_agents)
    
    # Enhanced browser arguments
    browser_args = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-site-isolation-trials',
        f'--user-agent={user_agent}'
    ]
    
    # Launch browser with an appropriate choice
    # Using Firefox instead of Chromium sometimes helps avoid detection
    if random.random() < 0.3:  # 30% chance to use Firefox
        browser = playwright.firefox.launch(
            headless=headless,
            firefox_user_prefs={
                "general.useragent.override": user_agent,
                "privacy.resistFingerprinting": False,  # We want normal browser behavior
            }
        )
        logger.info("Using Firefox browser")
    else:
        browser = playwright.chromium.launch(
            headless=headless,
            args=browser_args
        )
        logger.info("Using Chromium browser")
    
    # Create browser context with more realistic settings
    viewport_width = random.choice([1280, 1366, 1440, 1536, 1600, 1920])
    viewport_height = random.choice([768, 800, 900, 1024, 1080])
    
    # Custom headers to mimic real browsers
    extra_headers = {}
    if with_custom_headers:
        extra_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
    
    # Create context with more randomized options
    context = browser.new_context(
        viewport={'width': viewport_width, 'height': viewport_height},
        user_agent=user_agent,
        java_script_enabled=True,
        locale='en-US',
        timezone_id=random.choice(['America/New_York', 'America/Chicago', 'America/Los_Angeles']),
        geolocation={"latitude": 37.7749, "longitude": -122.4194},  # San Francisco
        permissions=['geolocation'],
        color_scheme=random.choice(['light', 'dark', 'no-preference']),
        reduced_motion=random.choice(['reduce', 'no-preference']),
        extra_http_headers=extra_headers
    )
    
    # Create page and add enhanced anti-detection scripts
    page = context.new_page()
    
    # More sophisticated anti-detection script
    page.add_init_script("""
    // Mask webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false
    });
    
    // Mask automation-related properties
    if (window.navigator.plugins) {
        // Add a fake plugin
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                }
            ]
        });
    }
    
    // Add language and platform details if missing
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32'
    });
    """)
    
    # Set a cookie to look more like a returning visitor
    context.add_cookies([{
        'name': 'returning_visitor',
        'value': 'true',
        'domain': '.yellowpages.com',
        'path': '/',
    }])
    
    return browser, context, page

def subtle_scrolling(page):
    """More subtle scrolling behavior that doesn't overdo it."""
    # Get page dimensions
    viewport_height = page.evaluate("window.innerHeight")
    page_height = page.evaluate("document.body.scrollHeight")
    
    # Calculate a reasonable scroll limit - don't go all the way to bottom
    # Stop at about 70-90% of the page height
    scroll_limit = page_height * random.uniform(0.7, 0.9)
    
    # Start scrolling from current position
    current_position = page.evaluate("window.scrollY")
    
    # Do gentle scrolling with natural pauses
    while current_position < scroll_limit:
        # Random small scroll amount
        scroll_amount = random.randint(100, 300)
        current_position += scroll_amount
        
        # Add randomness to avoid pattern detection
        if random.random() < 0.1:  # 10% chance to scroll less
            scroll_amount = random.randint(50, 100)
        
        # Scroll to position
        page.evaluate(f"window.scrollTo(0, {current_position})")
        
        # Random pause duration
        pause_time = random.uniform(0.3, 0.8)
        if random.random() < 0.15:  # 15% chance for longer pause
            pause_time = random.uniform(1.0, 2.0)
        
        time.sleep(pause_time)
        
        # Occasionally scroll back up a little bit, like a human looking for something
        if random.random() < 0.15:
            back_amount = random.randint(40, 150)
            current_position -= back_amount
            page.evaluate(f"window.scrollTo(0, {current_position})")
            time.sleep(random.uniform(0.3, 0.7))
    
    # Don't go straight to the bottom
    # Instead scroll to approximately middle of the page
    final_position = page_height * random.uniform(0.5, 0.7)
    page.evaluate(f"window.scrollTo(0, {final_position})")
    time.sleep(random.uniform(0.8, 1.5))

def handle_possible_block(page, attempt=1, max_attempts=3):
    """Handle possible blocking by taking recovery actions."""
    if attempt > max_attempts:
        logger.error("Maximum recovery attempts reached. Likely blocked.")
        return False
        
    logger.warning(f"Possible block detected. Recovery attempt {attempt}/{max_attempts}")
    
    # Take a screenshot of the blocked state
    try:
        page.screenshot(path=f"possible_block_state_attempt_{attempt}.png")
        with open(f"blocked_page_html_attempt_{attempt}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
    except Exception as e:
        logger.error(f"Couldn't save block state: {e}")
    
    # Possible recovery strategies
    
    # 1. Wait longer - sometimes this is enough
    wait_time = random.uniform(20, 40)
    logger.info(f"Waiting {wait_time:.1f} seconds to recover")
    time.sleep(wait_time)
    
    # 2. Try clearing cookies
    if attempt >= 2:
        try:
            logger.info("Clearing cookies")
            page.context.clear_cookies()
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
    
    # 3. Try refreshing the page
    try:
        logger.info("Attempting to refresh the page")
        page.reload(timeout=30000)
        time.sleep(random.uniform(5, 8))
    except Exception as e:
        logger.error(f"Page reload failed: {e}")
        return False
    
    # Check if we can still interact with the page
    try:
        # Try to interact with a basic element
        page.evaluate("document.querySelector('body').scrollTop")
        logger.info("Page seems interactive again")
        return True
    except:
        logger.warning("Page still appears to be blocked")
        return handle_possible_block(page, attempt + 1, max_attempts)

def scrape_yellowpages(search_term, location, max_pages=1):
    """
    Scrapes Yellow Pages with URL-based pagination instead of clicking.
    
    Args:
        search_term (str): The type of business to search for
        location (str): City, state, or zip code
        max_pages (int): Maximum number of pages to scrape
        
    Returns:
        list: List of dictionaries containing business information
    """
    businesses = []
    
    # Encode search parameters
    search_term_encoded = quote_plus(search_term)
    location_encoded = quote_plus(location)
    
    with sync_playwright() as playwright:
        browser, context, page = setup_browser(playwright, headless=False)
        
        try:
            # Iterate through pages using URL-based pagination
            for current_page in range(1, max_pages + 1):
                # Construct URL with page parameter
                if current_page == 1:
                    url = f"https://www.yellowpages.com/search?search_terms={search_term_encoded}&geo_location_terms={location_encoded}"
                else:
                    url = f"https://www.yellowpages.com/search?search_terms={search_term_encoded}&geo_location_terms={location_encoded}&page={current_page}"
                
                logger.info(f"Navigating directly to page {current_page}: {url}")
                
                # Navigate with longer timeout
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Initial wait with randomization
                initial_wait = random.uniform(4, 7)
                logger.info(f"Waiting {initial_wait:.1f} seconds for page {current_page} to load...")
                time.sleep(initial_wait)
                
                logger.info(f"Scraping page {current_page}")
                
                # Subtle scrolling that doesn't immediately go to the bottom
                subtle_scrolling(page)
                
                # Take a screenshot for debugging
                page.screenshot(path=f"page_{current_page}_content.png")
                
                # Check if we can find listings with various selectors
                listings = None
                selectors = [
                    '.result', 
                    '.organic', 
                    '.listing', 
                    '.info', 
                    'div.srp-listing', 
                    'div.v-card',
                    'div[class*="listing"]',
                    'div[class*="business"]',
                    '.business-name',  # Sometimes we need to go up from these elements
                    '.v-card'
                ]
                
                for selector in selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        listings = page.query_selector_all(selector)
                        if listings and len(listings) > 0:
                            logger.info(f"Found {len(listings)} listings with selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                
                # If no listings were found, try a more generic approach with container traversal
                if not listings or len(listings) == 0:
                    logger.info("No listings found with standard selectors, trying container traversal")
                    try:
                        # Look for any divs that might contain listings
                        containers = page.query_selector_all('div.search-results, div.organic-results, div.results, main, #content')
                        
                        for container in containers:
                            # Look for child divs that might be listings
                            potential_listings = container.query_selector_all('div')
                            
                            # Filter potential listings by checking for business-like content
                            filtered_listings = []
                            for item in potential_listings:
                                html = item.inner_html()
                                # Check if HTML contains typical business listing content
                                if ('class="business' in html or 'class="listing' in html or
                                    'phone' in html or 'address' in html):
                                    filtered_listings.append(item)
                            
                            if filtered_listings:
                                listings = filtered_listings
                                logger.info(f"Found {len(listings)} listings through container traversal")
                                break
                    except Exception as e:
                        logger.error(f"Container traversal approach failed: {e}")
                
                # If we still have no listings, check if we're blocked
                if not listings or len(listings) == 0:
                    logger.warning("No listings found. Checking for possible block...")
                    
                    # Save debug info
                    page.screenshot(path=f"possible_block_page_{current_page}.png")
                    with open(f"possible_block_source_{current_page}.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    
                    # Look for block indicators
                    block_indicators = [
                        'captcha',
                        'security check',
                        'verify you are human',
                        'access denied',
                        'ip has been blocked',
                        'automated access',
                        'suspicious activity'
                    ]
                    
                    page_content = page.content().lower()
                    is_blocked = any(indicator in page_content for indicator in block_indicators)
                    
                    if is_blocked:
                        logger.error("Block detected! Attempting recovery...")
                        recovery_success = handle_possible_block(page)
                        
                        if not recovery_success:
                            logger.error("Could not recover from block. Ending scrape.")
                            break
                        else:
                            # Try scraping this page again
                            continue
                    else:
                        logger.warning("No block detected, but also no listings found. This page may be empty.")
                        # Continue to next page anyway
                else:
                    # Process found listings
                    for listing in listings:
                        business_info = {'name': 'N/A', 'industry': 'N/A', 'address': 'N/A', 'phone': 'N/A', 'website': 'N/A'}
                        
                        # Extract business name
                        try:
                            name_element = listing.query_selector('.business-name, h2 a, .name, a.business-name')
                            if name_element:
                                business_info['name'] = name_element.inner_text().strip()
                            else:
                                # Try to find any prominent link or heading
                                alt_name = listing.query_selector('h2, .title, strong a, h3')
                                if alt_name:
                                    business_info['name'] = alt_name.inner_text().strip()
                        except Exception as e:
                            logger.debug(f"Error extracting name: {e}")
                        
                        # Extract category/industry
                        try:
                            category_element = listing.query_selector('.categories, .category, .business-categories')
                            if category_element:
                                business_info['industry'] = category_element.inner_text().strip()
                        except Exception:
                            pass
                        
                        # Extract address
                        try:
                            address_parts = []
                            street = listing.query_selector('.street-address')
                            if street:
                                address_parts.append(street.inner_text().strip())
                            
                            locality = listing.query_selector('.locality')
                            if locality:
                                address_parts.append(locality.inner_text().strip())
                            
                            if address_parts:
                                business_info['address'] = ", ".join(address_parts)
                            else:
                                # Try to find a complete address
                                full_address = listing.query_selector('.address')
                                if full_address:
                                    business_info['address'] = full_address.inner_text().strip()
                        except Exception:
                            pass
                        
                        # Extract phone
                        try:
                            phone_element = listing.query_selector('.phones, .phone, [class*="phone"]')
                            if phone_element:
                                business_info['phone'] = phone_element.inner_text().strip()
                        except Exception:
                            pass
                        
                        # Extract website
                        try:
                            website_element = listing.query_selector('.track-visit-website, a[class*="website"], a[href*="http"][target="_blank"]')
                            if website_element:
                                business_info['website'] = website_element.get_attribute('href')
                        except Exception:
                            pass
                        
                        # Only add businesses where we got at least a name
                        if business_info['name'] != 'N/A':
                            businesses.append(business_info)
                            logger.info(f"Added business: {business_info['name']}")
                
                # Add a delay between pages to appear more human-like
                if current_page < max_pages:
                    delay = random.uniform(3, 6)
                    logger.info(f"Waiting {delay:.1f} seconds before going to next page...")
                    time.sleep(delay)
        
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Close the browser
            logger.info("Closing browser")
            browser.close()
        
        return businesses

def scrape_yellowpages_with_fresh_sessions(search_term, location, max_pages=3):
    """
    Scrapes Yellow Pages using fresh browser sessions for each page
    """
    all_businesses = []
    search_term_encoded = quote_plus(search_term)
    location_encoded = quote_plus(location)
    
    for current_page in range(1, max_pages + 1):
        logger.info(f"Starting fresh session for page {current_page}")
        
        # Construct URL with page parameter
        if current_page == 1:
            url = f"https://www.yellowpages.com/search?search_terms={search_term_encoded}&geo_location_terms={location_encoded}"
        else:
            url = f"https://www.yellowpages.com/search?search_terms={search_term_encoded}&geo_location_terms={location_encoded}&page={current_page}"
        
        with sync_playwright() as playwright:
            browser = None
            try:
                # Create new browser instance with updated setup_browser function
                browser, context, page = setup_browser(playwright, headless=False, with_custom_headers=True)
                
                logger.info(f"Navigating to page {current_page}: {url}")
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Random longer wait time - Yellow Pages needs time to load
                wait_time = random.uniform(5, 8)
                logger.info(f"Waiting {wait_time:.1f} seconds for page to load...")
                time.sleep(wait_time)
                
                # Gentle scrolling
                subtle_scrolling(page)
                
                # Take screenshot for debugging
                page.screenshot(path=f"fresh_session_page_{current_page}.png")
                
                # Extract businesses
                businesses = []
                
                # Look for listings with various selectors
                listings = None
                selectors = [
                    '.result', 
                    '.organic', 
                    '.listing', 
                    '.info', 
                    'div.srp-listing', 
                    'div.v-card',
                    'div[class*="listing"]',
                    'div[class*="business"]',
                    '.business-name',
                    '.v-card'
                ]
                
                for selector in selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        listings = page.query_selector_all(selector)
                        if listings and len(listings) > 0:
                            logger.info(f"Found {len(listings)} listings with selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                
                # If we found listings, process them
                if listings and len(listings) > 0:
                    for listing in listings:
                        business_info = {'name': 'N/A', 'industry': 'N/A', 'address': 'N/A', 'phone': 'N/A', 'website': 'N/A'}
                        
                        # Extract business name
                        try:
                            name_element = listing.query_selector('.business-name, h2 a, .name, a.business-name')
                            if name_element:
                                business_info['name'] = name_element.inner_text().strip()
                            else:
                                # Try to find any prominent link or heading
                                alt_name = listing.query_selector('h2, .title, strong a, h3')
                                if alt_name:
                                    business_info['name'] = alt_name.inner_text().strip()
                        except Exception as e:
                            logger.debug(f"Error extracting name: {e}")
                        
                        # Extract category/industry
                        try:
                            category_element = listing.query_selector('.categories, .category, .business-categories')
                            if category_element:
                                business_info['industry'] = category_element.inner_text().strip()
                        except Exception:
                            pass
                        
                        # Extract address
                        try:
                            address_parts = []
                            street = listing.query_selector('.street-address')
                            if street:
                                address_parts.append(street.inner_text().strip())
                            
                            locality = listing.query_selector('.locality')
                            if locality:
                                address_parts.append(locality.inner_text().strip())
                            
                            if address_parts:
                                business_info['address'] = ", ".join(address_parts)
                            else:
                                # Try to find a complete address
                                full_address = listing.query_selector('.address')
                                if full_address:
                                    business_info['address'] = full_address.inner_text().strip()
                        except Exception:
                            pass
                        
                        # Extract phone
                        try:
                            phone_element = listing.query_selector('.phones, .phone, [class*="phone"]')
                            if phone_element:
                                business_info['phone'] = phone_element.inner_text().strip()
                        except Exception:
                            pass
                        
                        # Extract website
                        try:
                            website_element = listing.query_selector('.track-visit-website, a[class*="website"], a[href*="http"][target="_blank"]')
                            if website_element:
                                business_info['website'] = website_element.get_attribute('href')
                        except Exception:
                            pass
                        
                        # Only add businesses where we got at least a name
                        if business_info['name'] != 'N/A':
                            businesses.append(business_info)
                            logger.info(f"Added business: {business_info['name']}")
                
                if businesses:
                    all_businesses.extend(businesses)
                    logger.info(f"Found {len(businesses)} businesses on page {current_page}")
                else:
                    logger.warning(f"No businesses found on page {current_page}")
                
                # Random longer delay before closing this session
                delay = random.uniform(4, 8)
                logger.info(f"Session completed. Waiting {delay:.1f} seconds before closing...")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error scraping page {current_page}: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                # Close browser completely
                if browser:
                    browser.close()
                    logger.info(f"Browser session for page {current_page} closed")
                
                # Wait between sessions
                between_session_delay = random.uniform(15, 30)
                logger.info(f"Waiting {between_session_delay:.1f} seconds before starting next session...")
                time.sleep(between_session_delay)
    
    return all_businesses

def save_to_csv(businesses, filename='yellowpages_data.csv'):
    """Saves the scraped business data to a CSV file."""
    if not businesses:
        logger.warning("No data to save.")
        return
    
    # Create output directory if needed
    output_dir = "yellowpages_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'industry', 'address', 'phone', 'website']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for business in businesses:
            writer.writerow(business)
    
    logger.info(f"Data saved to {filepath}")
    return filepath

def main():
    """Main function to run the scraper."""
    print("\n=== Yellow Pages Scraper (Fresh Sessions Version) ===\n")
    
    search_term = input("Enter business type to search for (e.g., 'restaurants'): ")
    location = input("Enter location (city, state, or zip code): ")
    
    try:
        max_pages = int(input("Enter maximum number of pages to scrape (1-5 recommended): "))
        if max_pages < 1:
            max_pages = 1
        # Limit max pages to avoid blocks
        if max_pages > 5:
            print("Limiting to 5 pages maximum to avoid blocks")
            max_pages = 5
    except:
        print("Invalid input, defaulting to 1 page.")
        max_pages = 1
    
    print(f"\nScraping Yellow Pages for '{search_term}' in '{location}'...")
    print("This will use a visible browser window so you can monitor progress.")
    
    # Add a delay before starting
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    # Use the fresh sessions approach instead of the original scraper
    businesses = scrape_yellowpages_with_fresh_sessions(search_term, location, max_pages)
    
    if businesses:
        print(f"\nSuccessfully scraped {len(businesses)} businesses.")
        filename = f"{search_term.replace(' ', '_')}_{location.replace(' ', '_')}.csv"
        save_to_csv(businesses, filename)
        print(f"Data saved to yellowpages_data/{filename}")
    else:
        print("\nNo businesses were scraped. This could be due to:")
        print("1. Yellow Pages blocking automated access")
        print("2. No businesses found for your search criteria")
        print("3. Selectors not matching the current Yellow Pages layout")
        print("\nCheck the debug screenshots and HTML files for more information.")

if __name__ == "__main__":
    main()