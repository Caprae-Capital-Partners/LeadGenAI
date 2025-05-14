import asyncio
from typing import List, Dict
import pandas as pd
<<<<<<< HEAD
import sys
import os

# import sys
# sys.path.append("backend")
sys.path.append(os.path.abspath("C:/Work/Internship/Web Scraper Caprae/LeadGenAI/phase_1/"))

=======
import os
import sys
# sys.path.append("backend")
# sys.path.append(os.path.abspath("C:/Work/Internship/Web Scraper Caprae/LeadGenAI/phase_1/"))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
>>>>>>> 78be9c19546baca4dd0d5f3025e02c4d0763dfaa
from backend.services.Fuzzymatching import deduplicate_businesses
from backend.services.yellowpages_scraper import scrape_yellowpages
from backend.services.bbb_scraper import scrape_bbb
from backend.services.google_maps_scraper import scrape_lead_by_industry
from backend.services.merge_sources import merge_data_sources
from backend.services.parser import parse_data
from backend.services.hotfrog_scraper import scrape_hotfrog
from backend.services.superpages import scrape_superpages
from backend.config.browser_config import PlaywrightManager

from config.browser_config import PlaywrightManager

import psutil
import time

FIELDNAMES = [
    "Company",
    "Industry",
    "Address",
    "BBB_rating",
    "Business_phone",
    "Website"
]

async def fetch_and_merge_data(industry: str, location: str) -> List[Dict[str, str]]:
    
    start_time = time.perf_counter()
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / 1024 / 1024  # In MB
    
    # Running parallel
    manager = PlaywrightManager(headless=True)
    await manager.start_browser(stealth_on=True)
    
    start_time = time.perf_counter()
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / 1024 / 1024  # In MB
    
    gmaps_page = await manager.context.new_page()
    bbb_page = await manager.context.new_page()
    hf_page = await manager.context.new_page()
    sp_page = await manager.context.new_page()
    
    bbb_data, google_maps_data, yp_data, hf_data, sp_data = await asyncio.gather(
        scrape_bbb(industry, location, bbb_page),
        scrape_lead_by_industry(industry, location, gmaps_page),
        scrape_yellowpages(industry, location, max_pages=5),
        scrape_hotfrog(industry, location, hf_page, max_pages=5),
        scrape_superpages(industry, location, sp_page, max_pages=5)
    )
    
    await manager.stop_browser()
        
    print(f"Fetched: BBB={len(bbb_data)}, GMaps={len(google_maps_data)}, YP={len(yp_data)}, HF={len(hf_data)}, SP={len(sp_data)}")

    # Merge data on name and address
    merged_data = merge_data_sources(FIELDNAMES, bbb_data, google_maps_data, yp_data, hf_data, sp_data)
    print(f"Total entries after merging: {len(merged_data)}")
    
    df = pd.DataFrame(merged_data)

    parsed_data = parse_data(df, FIELDNAMES, location)
    data = parsed_data.to_dict(orient='records')
    # De duplify using fuzzy matching    
    deduplified_data = deduplicate_businesses(data)
      
    print(f"Total entries after deduplication: {len(deduplified_data)}")
    
    end_time = time.perf_counter()
    end_mem = process.memory_info().rss / 1024 / 1024  # In MB
    
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    print(f"RAM usage: {end_mem - start_mem:.2f} MB")
    
    return deduplified_data

if __name__ == "__main__":
    # Run the async function in an event loop
    result = asyncio.run(fetch_and_merge_data("gun store", "Carmel, IN"))
    # save_to_csv(result, filename="merged_output.csv", headers=FIELDNAMES)