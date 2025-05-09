import asyncio
from typing import List, Dict
import pandas as pd

import sys
import os
# sys.path.append("backend")
sys.path.append(os.path.abspath("C:/Work/Internship/Web Scraper Caprae/LeadGenAI/phase_1/"))
from backend.services.Fuzzymatching import deduplicate_businesses
from backend.services.yellowpages_scraper import scrape_yellowpages
from backend.services.bbb_scraper import scrape_bbb
from backend.services.google_maps_scraper import scrape_lead_by_industry
from backend.services.merge_sources import merge_data_sources
from backend.services.parser import parse_data
from backend.services.hotfrog_scraper import scrape_hotfrog

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
    bbb_data, google_maps_data, yp_data, hf_data = await asyncio.gather(
        scrape_bbb(industry, location),
        scrape_lead_by_industry(industry, location),
        scrape_yellowpages(industry, location, max_pages=5),
        scrape_hotfrog(industry, location, max_pages=5)
    )
        
    print(f"Fetched: BBB={len(bbb_data)}, GMaps={len(google_maps_data)}, YP={len(yp_data)}, HF={len(hf_data)}")

    # Merge data on name and address
    merged_data = merge_data_sources(FIELDNAMES, bbb_data, google_maps_data, yp_data, hf_data)
    
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

async def fetch_and_merge_seq(industry: str, location: str) -> List[Dict[str,str]]:
    bbb_data = []
    google_maps_data = []

    # Fetch data from BBB scraper
    try:
        print(f"Fetching BBB data for industry: {industry}, location: {location}")
        bbb_data = await scrape_bbb(industry, location)
        print(f"BBB data fetched: {len(bbb_data)} records")
    except Exception as e:
        print(f"Error fetching BBB data: {e}")  

    # Fetch data from Google Maps scraper
    try:
        print(f"Fetching Google Maps data for industry: {industry}, location: {location}")
        google_maps_data = await scrape_lead_by_industry(industry, location)
        print(f"Google Maps data fetched: {len(google_maps_data)} records")
    except Exception as e:
        print(f"Error fetching Google Maps data: {e}")

    # Merge the results
    try:
        print("Merging data from both sources...")
        merged_data = merge_data_sources(bbb_data, google_maps_data, fieldnames=FIELDNAMES)
        print(f"Merged data contains {len(merged_data)} records")
        return merged_data
    except Exception as e:
        print(f"Error merging data: {e}")
        return []

if __name__ == "__main__":
    # Run the async function in an event loop
    result = asyncio.run(fetch_and_merge_data("plumbing services", "Carmel, IN"))
    # save_to_csv(result, filename="merged_output.csv", headers=FIELDNAMES)