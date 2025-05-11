import asyncio
import csv
import os
from typing import Dict, List
from playwright.async_api import Locator, async_playwright

async def save_to_csv(businesses, filename='superpages_data.csv'):
    """Save extracted business data to CSV file."""
    if not businesses:
        print("No data to save to CSV.")
        return None
    
    output_dir = "superpages_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Company', 'Phone', 'Website', 'Address', 'Category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for business in businesses:
            writer.writerow(business)
    
    print(f"CSV file saved to: {filepath}")

async def handle_cookie_consent(page):
    """Handle cookie consent dialogs."""
    consent_selectors = [
        'button#onetrust-accept-btn-handler',
        'button.accept-cookies',
        'button:has-text("Accept")',
        'button:has-text("Accept All")'
    ]
    for selector in consent_selectors:
        try:
            if await page.locator(selector).count() > 0:
                await page.locator(selector).click()
                await asyncio.sleep(1)
                break
        except Exception:
            pass

async def slow_scroll(page):
    """Scroll down the page gradually."""
    page_height = await page.evaluate("document.body.scrollHeight")
    steps = 5
    for i in range(1, steps + 1):
        position = (page_height * i) / steps
        await page.evaluate(f"window.scrollTo(0, {int(position)})")
        await asyncio.sleep(0.5)

async def extract_business_details(container: Locator, search_term: str) -> Dict[str, str] | None:
    """Extract business information from a listing container."""
    try:
        info = {
            'Company': 'NA',
            'Phone': 'NA',
            'Website': 'NA',
            'Address': 'NA',
            'Category': search_term.title()
        }

        # Extract business name
        name = container.locator('h2 a span, h2 a')
        if await name.count() > 0:
            info['Company'] = (await name.first.text_content()).strip()

        # Extract phone number
        phone = container.locator('a.phones.phone.primary, a[href^="tel:"]')
        if await phone.count() > 0:
            phone_text = await phone.first.text_content()
            digits = ''.join(char for char in phone_text if char.isdigit())
            if digits:
                info['Phone'] = digits

        # Extract website
        website = container.locator('a.weblink-button, a[target="_blank"][rel="nofollow noopener"]')
        if await website.count() > 0:
            href = await website.first.get_attribute('href')
            if href:
                info['Website'] = href

        # Extract address
        address = container.locator('span.street-address, p:has(span)')
        if await address.count() > 0:
            info['Address'] = (await address.first.text_content()).strip()

        # Only return if we have at least a company name or phone number
        if info['Company'] != 'NA' or info['Phone'] != 'NA':
            return info
        
        return None
    except Exception as e:
        print(f"Error extracting business details: {e}")
        return None

async def extract_businesses(page, search_term: str) -> List[Dict[str, str]]:
    """Extract all business listings from the current page."""
    results = []
    
    # Wait for the page to load completely
    await page.wait_for_load_state("networkidle")
    
    # Look for business listings with different selectors
    listing_selectors = [
        'div.business-listing',
        'div[id^="lid-"]',
        '.search-results > div',
        '.listing-results > div',
        '#main-content > div'
    ]
    
    # Try each selector until we find business listings
    for selector in listing_selectors:
        containers = page.locator(selector)
        count = await containers.count()
        if count > 0:
            print(f"Found {count} business listings with selector: {selector}")
            
            for i in range(count):
                container = containers.nth(i)
                data = await extract_business_details(container, search_term)
                if data:
                    results.append(data)
            
            # If we found results with this selector, stop trying others
            if results:
                break
    
    return results

async def click_next_page(page) -> bool:
    """Attempt to click the next page button."""
    # Simplified selectors for next page buttons
    next_page_selectors = [
        '.pagination li:not(.active) a',
        '.pagination a[rel="next"]',
        'a.next-page',
        '.pagination a[data-page]:not(.active)'
    ]
    
    for selector in next_page_selectors:
        try:
            next_button = page.locator(selector)
            if await next_button.count() > 0:
                await next_button.first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)  # Wait for page to stabilize
                return True
        except Exception:
            continue
    
    # If none of the selectors worked, try JavaScript approach
    try:
        clicked = await page.evaluate('''() => {
            const paginationLinks = document.querySelectorAll('.pagination a, a[data-page]');
            for (let link of paginationLinks) {
                const text = link.textContent.trim().toLowerCase();
                if (text === 'next' || text.includes('›') || text.includes('>')) {
                    link.click();
                    return true;
                }
            }
            return false;
        }''')
        
        if clicked:
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            return True
    except Exception:
        pass
    
    return False

async def scrape_superpages(search_term: str, location: str, max_pages: int = 5) -> List[Dict[str, str]]:
    """Scrape Superpages using sequential navigation through paginated results."""
    # Format the search URL
    search_term_clean = search_term.replace(' ', '+')
    location_clean = location.replace(' ', '+').replace(',', '%2C')
    start_url = f"https://www.superpages.com/search?search_terms={search_term_clean}&geo_location_terms={location_clean}"
    
    print(f"Starting scrape at URL: {start_url}")
    
    async with async_playwright() as playwright:
        # Launch browser and create context
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        # Create a single page for sequential navigation
        page = await context.new_page()
        
        try:
            # Navigate to the first URL
            await page.goto(start_url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)
            await handle_cookie_consent(page)
            
            all_results = []
            current_page = 1
            
            # Process each page sequentially
            while current_page <= max_pages:
                print(f"Scraping page {current_page} of {max_pages}")
                await slow_scroll(page)
                
                # Extract businesses from the current page
                results = await extract_businesses(page, search_term)
                all_results.extend(results)
                print(f"Found {len(results)} businesses on page {current_page}")
                
                # Check if we've reached the maximum pages
                if current_page >= max_pages:
                    break
                
                # Try to navigate to the next page
                print(f"Attempting to navigate to page {current_page + 1}")
                if await click_next_page(page):
                    current_page += 1
                else:
                    print("No more pages available")
                    break
            
            # Deduplicate results
            seen = set()
            unique = []
            for item in all_results:
                key = f"{item['Company']}_{item['Phone']}"
                if key not in seen:
                    seen.add(key)
                    unique.append(item)
            
            print(f"Total unique businesses found: {len(unique)}")
            return unique
        
        except Exception as e:
            print(f"Error during scraping: {e}")
            return []
        finally:
            # Close the browser
            await context.close()
            await browser.close()

if __name__ == "__main__":
    search_term = input("Enter search term (e.g., 'Italian Restaurants'): ")
    location = input("Enter location (e.g., 'San Francisco, CA'): ")
    max_pages = int(input("Enter maximum number of pages to scrape (default 5): ") or "5")
    
    print(f"Scraping {search_term} in {location} from Superpages.com...")
    results = asyncio.run(scrape_superpages(search_term, location, max_pages=max_pages))
    
    if results:
        filename = f"{search_term.replace(' ', '_')}_{location.replace(' ', '_').replace(',', '')}.csv"
        asyncio.run(save_to_csv(results, filename=filename))
    
    print(f"Scraped {len(results)} unique businesses.")