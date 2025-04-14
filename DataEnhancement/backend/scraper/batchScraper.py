from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.scraper.revenueScraper import get_company_revenue_from_growjo
from backend.scraper.loggerConfig import setup_logger

import logging
from datetime import datetime
from tqdm import tqdm
import csv
import time
import random


setup_logger()

# Sample list: Replace or load from file
test_companies = [
    "Notion", "Datadog", "Louis-Dreyfus", "H&M", "Zoëtry Wellness & Spa",
    "Tokopedia", "Gojek", "Figma", "OpenAI", "Stripe"
]

def scrape_with_error_handling(company):
    try:
        result = get_company_revenue_from_growjo(company)
        return result
    except Exception as e:
        logging.error(f"❌ Exception while scraping '{company}': {e}")
        return {
            "company": company,
            "error": str(e)
        }

def batch_scrape_revenue(company_list, batch_size=10, output_path="scraped_results.csv", enable_retry=True, max_threads=5):
    total = len(company_list)
    results = []
    failed = []
    start_time = datetime.now()

    logging.info(f" Starting threaded batch scrape for {total} companies with {max_threads} threads")

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "estimated_revenue", "matched_variant", "url", "error"])
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_company = {executor.submit(scrape_with_error_handling, c): c for c in company_list}
            for i, future in enumerate(tqdm(as_completed(future_to_company), total=len(future_to_company), desc="📊 Scraping Progress"), 1):
                company = future_to_company[future]
                result = future.result()
                results.append(result)

                if "error" in result:
                    failed.append(company)

                writer.writerow({
                    "company": result.get("company", ""),
                    "estimated_revenue": result.get("estimated_revenue", ""),
                    "matched_variant": result.get("matched_variant", ""),
                    "url": result.get("url", ""),
                    "error": result.get("error", "")
                })

                # Sleep every batch_size results
                if i % batch_size == 0:
                    sleep_time = random.uniform(1.5, 3.0)
                    logging.info(f"⏸️ Pausing for {sleep_time:.1f} seconds after {i} companies...")
                    time.sleep(sleep_time)

    # Retry failed companies once if enabled
    if enable_retry and failed:
        logging.info(f"🔁 Retrying {len(failed)} failed companies...")
        retry_results, retry_failed = batch_scrape_revenue(failed, batch_size, output_path, enable_retry=False, max_threads=max_threads)
        results.extend(retry_results)
        failed = retry_failed

    end_time = datetime.now()
    duration = end_time - start_time

    # Summary
    logging.info("✅ Threaded batch scraping complete")
    logging.info(f"🕒 Time elapsed: {duration}")
    logging.info(f"✔️ Success: {total - len(failed)}")
    logging.info(f"❌ Failed: {len(failed)}")
    logging.info(f"📁 Results saved to: {output_path}")

    return results, failed

# Entry point for manual testing
if __name__ == "__main__":
    batch_scrape_revenue(test_companies)
