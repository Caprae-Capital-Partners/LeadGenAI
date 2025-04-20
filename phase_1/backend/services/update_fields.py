import asyncio
import os
import sys
from typing import Dict, List, Tuple
from urllib.parse import quote_plus
from playwright.async_api import Page

# sys.path.append(os.path.abspath("d:/Caprae Capital/Work/LeadGenAI/phase_1/backend"))
# from config.browser_config import PlaywrightManager

from backend.config.browser_config import PlaywrightManager

async def handle_tabs(page: Page, query: str, url: str):
    """Handles the initial tab navigation and returns the new tab or current tab."""
    try:
        await page.goto(url)
        await page.evaluate("""
            const contentDiv = document.querySelector('#b_content');
            if (contentDiv && contentDiv.style.visibility === 'hidden') {
                contentDiv.style.visibility = 'visible';
            }
        """)
        await asyncio.sleep(1)

        bbb_link_elem = await page.query_selector('li.b_algo a[href*="bbb.org"]')
        if not bbb_link_elem:
            print(f"BBB element not found for query: {query}")
            return None
        # print(f"BBB link element found: {bbb_link_elem}")

        await bbb_link_elem.click()
        # print("Clicked on BBB link")

        try:
            new_tab = await page.wait_for_event('popup', timeout=3000)
            # print("Opened BBB link in new tab")
        except Exception:
            # print("No new tab opened, using current tab")
            new_tab = page

        return new_tab
    except Exception as e:
        print(f"Error in handle_tabs: {e}")
        return None

async def update_rating_and_website(page, company_name: str, location: str) -> Tuple[str, str]:
    query = quote_plus(f"{company_name} {location} site:bbb.org")
    url = f"https://www.bing.com/search?q={query}"
    new_tab = await handle_tabs(page, query, url)

    if not new_tab:
        return "NA", "NA"

    try:
        await new_tab.wait_for_selector("div.bpr-header-business-info", timeout=3000)
        rating_status_div = await new_tab.query_selector('.bpr-header-accreditation-rating')
        # print(f"Rating status div found: {rating_status_div}")
        rating = "NA"
        if rating_status_div:
            rating_elem = await new_tab.query_selector('span.bpr-header-rating')
            if rating_elem:
                rating = await rating_elem.inner_text()

        website_elem = await new_tab.query_selector('a:has-text("Visit Website")')
        # print(f"Website element found: {website_elem}")
        website = await website_elem.get_attribute('href') if website_elem else "NA"

        return rating, website
    except Exception as e:
        print(f"Error in update_rating_and_website: {e}")
        return "NA", "NA"
    finally:
        if new_tab and new_tab != page:
            await new_tab.close()
        await page.bring_to_front()


async def add_management_details(page, company_name: str, location: str) -> List[str]:
    query = quote_plus(f"{company_name} {location} site:bbb.org")
    url = f"https://www.bing.com/search?q={query}"
    new_tab = await handle_tabs(page, query, url)

    if not new_tab:
        return []

    try:
        await new_tab.wait_for_selector("div.bpr-details-section", timeout=3000)
        management_divs = await new_tab.query_selector_all('.bpr-details-dl-data[data-type="on-separate-lines"]')

        management_data = []
        for div in management_divs:
            dt_elem = await div.query_selector('dt')
            if dt_elem:
                dt_text = await dt_elem.inner_text()
                if "Business Management" in dt_text:
                    dd_elems = await div.query_selector_all('dd')
                    for dd_elem in dd_elems:
                        dd_text = await dd_elem.inner_text()
                        if dd_text:
                            try:
                                name, title = dd_text.split(",", 1)
                                management_data.append({"name": name.strip(), "title": title.strip()})
                            except ValueError as e:
                                print(f"Error splitting dd text '{dd_text}': {e}")
                                management_data.append("NA")
                    break
        return management_data
    except Exception as e:
        print(f"Error in add_management_details: {e}")
        return ["NA"]
    finally:
        if new_tab and new_tab != page:
            await new_tab.close()
        await page.bring_to_front()
        

async def update_websites(data: List[Dict[str,str]], location) -> List[Dict[str,str]]:
    manager = PlaywrightManager(headless=False)
    try:
        page = await manager.start_browser(stealth_on=True)
        for idx, company in enumerate(data):
            # Check if the website is blank or "NA"
            if not company.get("Website") or company["Website"] == "NA":
                print(f"Company name: {company.get('Name')}")
                if idx > 0:
                    await asyncio.sleep(2)  # Add 2 sec delay between tabs
                
                # Extract name and address for the query
                name = company.get("Name", "")
                
                # Fetch updated rating and website
                _, website = await update_rating_and_website(page, name, location)
                
                # Update the website field in the original data
                company["Website"] = website
                
        print("Updated websites")
        return data
    
    except Exception as e:
        print(f"Error in fetching websites: {e}")
        # Return original data
        return data
        
    finally:
        await manager.stop_browser()

async def get_management_details(data: List[Tuple[str,str]]) -> List[str]:
    manager = PlaywrightManager(headless=True)
    results = []

    try:
        page = await manager.start_browser(stealth_on=True)
        for idx, (name, loc) in enumerate(data):
            if idx > 0:
                await asyncio.sleep(2)  # Add 2 sec delay between tabs
            management = await add_management_details(page, name, loc)
            print(f"Management for {name}: {management}")
            results.append(management)
            
        return results
    
    except Exception as e:
        print(f"Error occured when fetching details: {e}")
        return []
    
    finally:
        await manager.stop_browser()
        
               
# if __name__ == "__main__":
#     companies = [
#         ("Independence Pools Glendale", "glendale, az"),
#         ("All Valley Pools AZ", "Phoenix, AZ"),
#         ("Remodel Your Pool", "Glendale, AZ"),
#         ("Sun State Pools", "Glendale, AZ"),
#         ("Thunderbird Pools & Spas", "Glendale, AZ")
#     ]
#     asyncio.run(add_management(companies))