# RUN THIS
from backend.scraper.nameCleaner import clean_company_name_variants
from backend.scraper.growjo.growjoFallbackSearch import get_growjo_company_list
from backend.scraper.growjo.growjoRevenueExtractor import get_revenue_from_direct_page
from backend.scraper.cacheStore import get_cached_match, set_cached_match
from backend.scraper.loggerConfig import setup_logger
import logging

setup_logger()

def get_company_revenue_from_growjo(company_name, depth=0):
    source = "growjo"
    name_variants = clean_company_name_variants(company_name)

    logging.info(f"Starting revenue scrape for '{company_name}'")
    logging.debug(f"Name variants: {name_variants}")

    # Check source-based cache
    cached_match = get_cached_match(source, company_name)
    if cached_match:
        logging.info(f"Found cached match for '{company_name}': '{cached_match}'")
        return get_company_revenue_from_growjo(cached_match, depth=1)

    # Attempt direct scraping
    for variant in name_variants:
        result = get_revenue_from_direct_page(variant)
        if result:
            logging.info(f"✅ Direct scrape successful for variant '{variant}'")
            return {
                "company": company_name,
                **result
            }

    # Fallback search if direct scraping failed
    if depth == 0:
        for variant in name_variants:
            fallback_names = get_growjo_company_list(variant)
            logging.info(f"Fallback search for variant '{variant}' returned: {fallback_names}")

            if fallback_names:
                top_result = fallback_names[0]
                logging.info(f"Retrying with top Growjo match: '{top_result}'")

                # Save to cache
                set_cached_match(source, company_name, top_result)

                return get_company_revenue_from_growjo(top_result, depth=1)

    # All attempts failed
    logging.warning(f"Revenue not found for '{company_name}' after all fallbacks.")
    return {
        "company": company_name,
        "error": "Not found in Growjo after variants + fallback search",
        "attempted_variants": name_variants
    }

# Example CLI test
if __name__ == "__main__":
    result = get_company_revenue_from_growjo("Louis-Dreyfus")
    print(result)
