import asyncio
import os
import time
from typing import Dict, List
import sys

# sys.path.append(os.path.abspath("d:/Caprae Capital/Work/LeadGenAI/phase_1/backend"))
# from config.browser_config import PlaywrightManager

from backend.config.browser_config import PlaywrightManager

# FIELDNAMES = ["Name", "Industry", "Address", "Business_phone", "BBB_rating"]

async def scrape_bbb(industry: str, location: str) -> List[Dict[str,str]]:  
    industry = industry.replace(" ", "+")
    location = location.replace(", ", "%2C")
    BASE_URL = f"https://www.bbb.org/search?find_country=USA&find_loc={location}&find_text={industry}"
    lead_list = []
   
    try:
        browser_manager = PlaywrightManager(headless=True)
        page = await browser_manager.start_browser(stealth_on=False)
        await page.goto(BASE_URL)
        
        while True:
            try:
                await page.wait_for_selector("div.stack.stack-space-20", timeout=5000)
                count = await page.locator("div.card.result-card").count()
            except:
                break
                       
            for i in range(3, count): # Skip the first 3 cards (ads)
                details = {}
                try:
                    card = page.locator("div.card.result-card").nth(i)
                    
                    business_name_selector = "h3.result-business-name a"
                    business_element = await card.locator(business_name_selector).count()
                    details['Name'] = await card.locator(business_name_selector).inner_text() if business_element > 0 else "NA"
                    details["Name"] = details["Name"].replace("advertisement:\n", "").strip()
                        
                    # Scrape industry
                    industry_selector = "p.bds-body.text-size-4.text-gray-70"
                    industry_element = await card.locator(industry_selector).count()
                    details['Industry'] = str(await card.locator(industry_selector).inner_text()).split(",")[0] if industry_element > 0 else "NA"

                    # Scrape phone number
                    phone_number_selector = "a.text-black[href^='tel:']"
                    phone_number_element = await card.locator(phone_number_selector).count()
                    details['Business_phone'] = await card.locator(phone_number_selector).inner_text() if phone_number_element > 0 else "NA"

                    # Scrape address
                    address_selector = "p.bds-body.text-size-5.text-gray-70"
                    address_element = await card.locator(address_selector).count()
                    details['Address'] = await card.locator(address_selector).inner_text() if address_element > 0 else "NA"
                    
                    # BBB rating
                    bbb_selector = "span.result-rating"
                    bbb_rating_element = await card.locator(bbb_selector).count()
                    if bbb_rating_element > 0:
                        rating_text = await card.locator(bbb_selector).inner_text()
                        details['BBB_rating'] = rating_text.split()[-1] 
                    else:
                        details['BBB_rating'] = "NA"
                    
                    details.update({
                        "Name": details['Name'],
                        "Industry": details['Industry'],
                        "Address": details['Address'],
                        "Business_phone": details['Business_phone'],
                        "BBB_rating": details['BBB_rating']
                    })
                    lead_list.append(details)
                    
                except Exception as e:
                    print(f"Error extracting data for card {i}: {e}")
                
            await asyncio.sleep(0.5)
            # Go to next page if available
            try:
                next_page_btn = page.locator('a[rel="next"]', has_text="Next")
                if await next_page_btn.count() > 0:
                    try:
                        await next_page_btn.click(timeout=10000)
                        # await page.wait_for_load_state("domcontentloaded")
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"Error clicking 'Next' button: {e}")
                        return lead_list  # Return the leads collected so far
                else:
                    break
                
            except Exception as e:
                print(f"Error during pagination: {e}")
                return lead_list  # Return the leads collected so far
                
        print(f"Found {len(lead_list)} leads in BBB")
        return lead_list
        
    except Exception as e:
        print(f"Error during search: {e}")
        return []
    
    finally:
        await browser_manager.stop_browser()
    
# if __name__ == "__main__":
#     query = "swimming pool contractors"
#     location = "carmel, in"
#     result = asyncio.run(scrape_bbb(query, location))
#     print(len(result))