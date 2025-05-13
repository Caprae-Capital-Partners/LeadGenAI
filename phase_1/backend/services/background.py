import asyncio
import threading
import time
from typing import Dict, List, Any, Callable
import sys
import os
import pandas as pd
from copy import deepcopy
import inspect

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.append(os.path.abspath("C:/Work/Internship/Web Scraper Caprae/LeadGenAI/phase_1/backend"))

# Importing  scraper functions
from backend.services.yellowpages_scraper import scrape_yellowpages
from backend.services.bbb_scraper import scrape_bbb
from backend.services.google_maps_scraper import scrape_lead_by_industry
from backend.services.hotfrog_scraper import scrape_hotfrog
from backend.services.Fuzzymatching import deduplicate_businesses
from backend.services.parser import parse_data
from backend.services.merge_sources import merge_data_sources



# from backend.services.superpages_scraper import scrape_superpages  # Assuming this exists

def start_background_scraping(industry: str, location: str) -> Callable[[], Dict[str, Any]]:
    state = {
        "results": {
            "bbb": [],
            "google_maps": [],
            "yellowpages": [],
            "hotfrog": [],
            "superpages": []
        },
        "is_complete": False,
        "start_time": time.time(),
        "in_progress": {
            "bbb": True,
            "google_maps": True,
            "yellowpages": True, 
            "hotfrog": True,
            "superpages": True
        }
    }
    
    processed_state = {
        "processed_data": [],
        "last_total": 0
    }
    
    # Create a lock for thread safety
    lock = threading.Lock()
    
    # Define the async function to run all scrapers
    async def run_all_scrapers():
        # Create tasks for all scrapers
        tasks = [
            run_scraper(scrape_bbb, "bbb", industry, location),
            run_scraper(scrape_lead_by_industry, "google_maps", industry, location),
            run_scraper(scrape_yellowpages, "yellowpages", industry, location, max_pages=5),
            run_scraper(scrape_hotfrog, "hotfrog", industry, location, max_pages=5),
            # run_scraper(scrape_superpages, "superpages", industry, location)
        ]
        
        # Run all scrapers concurrently
        await asyncio.gather(*tasks)
        
        # Mark as complete
        with lock:
            state["is_complete"] = True
            print(f"Scraping complete! Total time: {time.time() - state['start_time']:.2f} seconds")
    
    # Function to run a single scraper
    # async def run_scraper(scraper_func, scraper_name, industry, location, **kwargs):
    #     try:
    #         print(f"Starting {scraper_name} scraper...")
    #         result = await scraper_func(industry, location, **kwargs)
            
    #         # Update results
    #         with lock:
    #             state["results"][scraper_name] = result
    #             state["in_progress"][scraper_name] = False
    #             print(f"{scraper_name} completed with {len(result)} results")
            
    #     except Exception as e:
    #         print(f"Error in {scraper_name} scraper: {e}")
    #         with lock:
    #             state["in_progress"][scraper_name] = False
                
    # async def run_scraper(scraper_func, scraper_name, industry, location, **kwargs):
    #     try:
    #         print(f"Starting {scraper_name} scraper...")

    #         result_list = []

    #         # Check if scraper_func is an async generator
    #         scraper = scraper_func(industry, location, **kwargs)
    #         if inspect.isasyncgen(scraper):
    #             async for item in scraper:
    #                 result_list.append(item)
    #         else:
    #             # Await normally if it's a coroutine
    #             result_list = await scraper

    #         # Update shared state
    #         with lock:
    #             state["results"][scraper_name] = result_list
    #             state["in_progress"][scraper_name] = False
    #             print(f"{scraper_name} completed with {len(result_list)} results")

    #     except Exception as e:
    #         print(f"Error in {scraper_name} scraper: {e}")
    #         with lock:
    #             state["in_progress"][scraper_name] = False
    
    async def run_scraper(scraper_func, scraper_name, industry, location, **kwargs):
        try:
            print(f"Starting {scraper_name} scraper...")

            # Initialize empty list in shared state at the start
            with lock:
                state["results"][scraper_name] = []
                state["in_progress"][scraper_name] = True

            scraper = scraper_func(industry, location, **kwargs)
            if inspect.isasyncgen(scraper):
                async for item in scraper:
                    with lock:
                        state["results"][scraper_name].append(item)
            else:
                result_list = await scraper
                with lock:
                    state["results"][scraper_name] = result_list

            with lock:
                state["in_progress"][scraper_name] = False
            print(f"{scraper_name} completed with {len(state['results'][scraper_name])} results")
        except Exception as e:
            print(f"Error in {scraper_name} scraper: {e}")
            with lock:
                state["in_progress"][scraper_name] = False
        
    # Function to get current results 
    # def get_results():
    #     with lock:
    #         total_results = sum(len(results) for results in state["results"].values())
    #         return {
    #             "is_complete": state["is_complete"],
    #             "scraper_status": {
    #                 k: {"done": not state["in_progress"][k], "count": len(v)} 
    #                 for k, v in state["results"].items()
    #             },
    #             "total_results": total_results,
    #             "results": state["results"],  # Return individual results from each scraper
    #             "elapsed_time": time.time() - state["start_time"]
    #         }
    
    # Run the async function in a background thread
    def run_in_background():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_all_scrapers())
        loop.close()
        
    def get_results():
        with lock:
            return {
                # "is_complete": state["is_complete"],
                # "elapsed_time": time.time() - state["start_time"],
                # "total_scraped": sum(len(v) for v in state["results"].values()),
                # "processed_data": deepcopy(processed_state["processed_data"]),
                # "scraper_status": {
                #     k: {"done": not state["in_progress"][k], "count": len(v)} 
                #     for k, v in state["results"].items()
                # }
                "processed_data": flatten(state["results"].values()),  # Combine all sources
                "elapsed_time": time.time() - state["start_time"],
                "total_scraped": sum(len(r) for r in state["results"].values()),
                "is_complete": state["is_complete"]
            }
            
    def flatten(list_of_lists):
        return [item for sublist in list_of_lists for item in sublist]

    def continuously_process_data():
        FIELDNAMES = [
            "Company",
            "Industry",
            "Address",
            "BBB_rating",
            "Business_phone",
            "Website"
        ]
        while not state["is_complete"]:
            time.sleep(2)  # Poll interval

            with lock:
                total_scraped = sum(len(v) for v in state["results"].values())

                if total_scraped > processed_state["last_total"]:
                    try:
                        merged = merge_data_sources(
                            FIELDNAMES,
                            state["results"]["bbb"],
                            state["results"]["google_maps"],
                            state["results"]["yellowpages"],
                            state["results"]["hotfrog"]
                        )
                        df = pd.DataFrame(merged)
                        parsed = parse_data(df, FIELDNAMES, location)
                        deduped = deduplicate_businesses(parsed.to_dict(orient='records'))
                        processed_state["processed_data"] = deduped
                        processed_state["last_total"] = total_scraped
                        print(f"[Processor] Updated deduplicated list: {len(deduped)} entries")

                    except Exception as e:
                        print(f"[Processor] Error during partial processing: {e}")
        # continuously_process_data()
    
    # Start the background thread
    thread = threading.Thread(target=run_in_background)
    threading.Thread(target=continuously_process_data, daemon=True).start()
    thread.daemon = True  # Thread will exit when main program exits
    thread.start()
    
    # Return function to get results
    return get_results


# if __name__ == "__main__":
#     # Example usage:
#     print("Starting background scraping...")
#     try:
#         get_results = start_background_scraping("Plumber", "New York")
        
#         # Check initial status
#         current_status = get_results()
#         print(f"Complete: {current_status['is_complete']}")
#         print(f"Results so far: {current_status['total_results']}")
        
#         # Print progress every few seconds until complete
#         while not get_results()['is_complete']:
#             time.sleep(2)
#             status = get_results()
#             print(f"Progress: {status['scraper_status']}")
#             print(f"Total results so far: {status['total_results']}")
        
#         # Get final results
#         final_results = get_results()
#         print(f"Final result count: {final_results['total_results']}")
        
#         # Print summary of results from each source
#         for source, data in final_results['results'].items():
#             print(f"{source}: {len(data)} results")
            
#         # Optionally, you can print a sample result from each source
#         for source, data in final_results['results'].items():
#             if data:
#                 print(f"\nSample from {source}:")
#                 print(data[0])
                
#     except Exception as e:
#         print(f"Error in background scraping: {e}")
#         import traceback
#         traceback.print_exc()    