from backend.scraper.revenueScraper import get_company_revenue_from_growjo
from backend.scraper.nameCleaner import clean_company_name_variants
from backend.scraper.loggerConfig import setup_logger
from urllib.parse import quote


setup_logger()

test_inputs = [
    "Notion",
    "Johnson & Johnson",
    "H&M",
    "Louis-Dreyfus",
    "Zoëtry Wellness & Spa",
    "   Datadog   ",
    "FakeCorp123XYZ"
]

for company in test_inputs:
    print("\n" + "="*60)
    print(f"🔍 Original Input: '{company}'")

    variants = clean_company_name_variants(company)
    print("🧼 Cleaned Variants:")
    for v in variants:
        print(f"   - {v} → {quote(v)}")

    print("⚙️ Running Scraper...\n")
    result = get_company_revenue_from_growjo(company)
    print("📊 Result:")
    for k, v in result.items():
        print(f"   {k}: {v}")
