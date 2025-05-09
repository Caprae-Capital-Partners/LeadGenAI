from ast import parse
import asyncio
import csv
import os
import sys
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
    consent_selectors = [
        'button#onetrust-accept-btn-handler',
        'button.accept-cookies',
        'button.consent-accept',
        'button[aria-label="Accept"]',
        'button[aria-label="Accept all"]',
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
    page_height = await page.evaluate("document.body.scrollHeight")
    steps = 8
    for i in range(1, steps + 1):
        position = (page_height * i) / steps
        await page.evaluate(f"window.scrollTo(0, {int(position)})")
        await asyncio.sleep(1)

async def extract_business_details(container: Locator, search_term: str) -> Dict[str, str] | None:
    try:
        info = {
            'Company': 'NA',
            'Phone': 'NA',
            'Website': 'NA',
            'Address': 'NA',
            'Category': search_term.title()
        }

        # Extract business name - try different selector approaches
        name = container.locator('h2 a span')
        if await name.count() > 0:
            info['Company'] = (await name.first.text_content()).strip()
        else:
            # Try alternative selector
            name_alt = container.locator('h2 a')
            if await name_alt.count() > 0:
                info['Company'] = (await name_alt.first.text_content()).strip()

        # Extract phone number
        phone = container.locator('a.phones.phone.primary')
        if await phone.count() > 0:
            phone_text = await phone.first.text_content()
            # Clean up phone number to get just the digits
            digits = ''.join(char for char in phone_text if char.isdigit())
            if digits:
                info['Phone'] = digits
        else:
            # Try alternative selector
            phone_alt = container.locator('a[href^="tel:"]')
            if await phone_alt.count() > 0:
                phone_text = await phone_alt.first.text_content()
                digits = ''.join(char for char in phone_text if char.isdigit())
                if digits:
                    info['Phone'] = digits

        # Extract website if available
        website = container.locator('a.weblink-button')
        if await website.count() > 0:
            href = await website.first.get_attribute('href')
            if href:
                info['Website'] = href
        else:
            # Try alternative selector
            website_alt = container.locator('a[target="_blank"][rel="nofollow noopener"]')
            if await website_alt.count() > 0:
                href = await website_alt.first.get_attribute('href')
                if href:
                    info['Website'] = href

        # Extract address
        address = container.locator('span.street-address')
        if await address.count() > 0:
            info['Address'] = (await address.first.text_content()).strip()
        else:
            # Try alternative selector
            address_alt = container.locator('p:has(span)')
            if await address_alt.count() > 0:
                info['Address'] = (await address_alt.first.text_content()).strip()

        # Only return if we have at least a company name or phone number
        if info['Company'] != 'NA' or info['Phone'] != 'NA':
            return info
        
        return None
    except Exception as e:
        print(f"Error extracting business details: {e}")
        return None

async def extract_businesses(page, search_term: str) -> List[Dict[str, str]]:
    results = []
    
    # Wait for any element to load to ensure the page is ready
    await page.wait_for_load_state("networkidle")
    
    # First, let's try to find the main container
    main_selectors = [
        'div.search-results',
        'div.listing-results',
        '#main-content',
        'div.business-listing',
        'div[id^="lid-"]'  # IDs that start with "lid-"
    ]
    
    main_container = None
    used_selector = None
    
    for selector in main_selectors:
        count = await page.locator(selector).count()
        if count > 0:
            main_container = page.locator(selector)
            used_selector = selector
            break
    
    if not main_container:
        print("Could not find any main container for business listings")
        return []
    
    # Now try to find individual business listings
    if used_selector == 'div[id^="lid-"]':
        # If we found businesses by their lid- ID, use those directly
        containers = main_container
    else:
        # Try different child selectors depending on the parent container we found
        child_selectors = [
            'div.business-listing',
            'div[id^="lid-"]',
            '> div',
            'div.listing-item'
        ]
        
        containers = None
        for child_selector in child_selectors:
            full_selector = f"{used_selector} {child_selector}"
            count = await page.locator(full_selector).count()
            if count > 0:
                containers = page.locator(full_selector)
                break
        
        if not containers:
            print("Could not find any business listings within the main container")
            return []
    
    count = await containers.count()
    print(f"Found {count} business listings")
    
    for i in range(count):
        container = containers.nth(i)
        data = await extract_business_details(container, search_term)
        if data:
            results.append(data)
            print(f"Extracted: {data['Company']}")
    
    return results

async def scrape_single_page(browser, url: str, search_term: str) -> List[Dict[str, str]]:
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = await context.new_page()
    
    try:
        print(f"Navigating to {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        await asyncio.sleep(5)  # Give the page time to fully load
        await handle_cookie_consent(page)
        await slow_scroll(page)
        
        results = await extract_businesses(page, search_term)
        return results
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []
    finally:
        await context.close()

async def scrape_superpages(search_term: str, location: str, max_pages: int = 5) -> List[Dict[str, str]]:
    # Format the search parameters for the URL
    search_term_clean = search_term.replace(' ', '+')
    location_clean = location.replace(' ', '+').replace(',', '%2C')
    
    # Generate URLs for pagination
    urls = [
        f"https://www.superpages.com/search?search_terms={search_term_clean}&geo_location_terms={location_clean}" if i == 1
        else f"https://www.superpages.com/search?search_terms={search_term_clean}&geo_location_terms={location_clean}&page={i}"
        for i in range(1, max_pages + 1)
    ]

    print(f"Will scrape URLs: {urls}")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)  # Changed to headless=True for production
        
        try:
            all_results = []
            for url in urls:
                results = await scrape_single_page(browser, url, search_term)
                all_results.extend(results)

            # Deduplicate
            seen = set()
            unique = []
            for item in all_results:
                key = f"{item['Company']}_{item['Phone']}"
                if key not in seen:
                    seen.add(key)
                    unique.append(item)
            return unique
        
        except Exception as e:
            print(f"Error during scraping: {e}")
            return []
        finally:
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