from ast import parse
import asyncio
import csv
import os
import sys
from typing import Dict, List
from playwright.async_api import Locator
# from playwright_stealth import stealth_async

# sys.path.append(os.path.abspath("d:/Caprae Capital/Work/LeadGenAI/phase_1/backend"))
# from config.browser_config import PlaywrightManager
from backend.services.parser import parse_number
# from parser import parse_number

from backend.config.browser_config import PlaywrightManager

def save_to_csv(businesses, filename='hotfrog_data.csv'):
    """Save extracted business data to CSV file."""
    if not businesses:
        print("No data to save to CSV.")
        return None
    
    output_dir = "yellowpages_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Company', 'Industry', 'Address', 'Business_phone']
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
            'Industry': search_term.title(),
            'Address': 'NA',
            'Business_phone': 'NA'
        }

        name = container.locator('h3 a strong')
        if await name.count() > 0:
            info['Company'] = (await name.first.text_content()).strip()

        spans = await container.locator('span.small').all()
        for span in spans:
            text = (await span.text_content()).strip()
            if (
                text and
                "Is this your business" not in text and
                "Claim this business" not in text and
                "Review now" not in text and
                any(char.isdigit() for char in text) and
                len(text) > 5
            ):
                info['Address'] = "[H]" + text
            else:
                info['Address'] = "NA"

        phone = container.locator('a[href^="tel:"] strong')
        if await phone.count() > 0:
            raw = (await phone.first.text_content()).strip()
            parsed_num = parse_number(raw)
            info['Business_phone'] = parsed_num

        if info['Company'] != 'NA' or info['Business_phone'] != 'NA':
            return info
        
        return None
    except Exception:
        return None

async def extract_businesses(page, search_term: str) -> List[Dict[str, str]]:
    results = []
    main = page.locator('.col-lg-8.hf-serps-main')
    if await main.count() > 0:
        containers = main.locator('> div')
        for i in range(await containers.count()):
            container = containers.nth(i)
            data = await extract_business_details(container, search_term)
            if data:
                results.append(data)
    return results

async def scrape_single_page(context, url: str, search_term: str) -> List[Dict[str, str]]:
    page = await context.new_page()
    try:
        # await stealth_async(page)
        await page.goto(url, wait_until='domcontentloaded')
        await asyncio.sleep(2)
        await handle_cookie_consent(page)
        await slow_scroll(page)
        return await extract_businesses(page, search_term)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []
    finally:
        await page.close()

async def scrape_hotfrog(search_term: str, location: str, max_pages: int = 5) -> List[Dict[str, str]]:
    search_term_clean = search_term.lower().replace(' ', '-')
    location_clean = location.lower().replace(', ', '-')
    urls = [
        f"https://www.hotfrog.com/search/{location_clean}/{search_term_clean}" if i == 1
        else f"https://www.hotfrog.com/search/{location_clean}/{search_term_clean}/{i}"
        for i in range(1, max_pages + 1)
    ]

    manager = PlaywrightManager(headless=True)
    await manager.start_browser(stealth_on=True)

    try:
        tasks = [
            scrape_single_page(manager.context, url, search_term)
            for url in urls
        ]
        results_nested = await asyncio.gather(*tasks)
        all_results = [item for sublist in results_nested for item in sublist]

        # Deduplicate
        seen = set()
        unique = []
        for item in all_results:
            key = f"{item['Company']}_{item['Business_phone']}"
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
    
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []
    finally:
        await manager.stop_browser()

# if __name__ == "__main__":
#     search_term = "gun stores"
#     location = "san diego, ca"
#     results = asyncio.run(scrape_hotfrog(search_term, location, max_pages=5))
    
#     filename = f"{search_term.replace(' ', '_')}_{location.replace(' ', '_')}.csv"
#     save_to_csv(results, filename=filename)
    
    