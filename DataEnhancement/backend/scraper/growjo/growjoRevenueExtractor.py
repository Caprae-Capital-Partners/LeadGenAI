import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
from backend.scraper.growjo.pageValidator import is_valid_company_page

def get_revenue_from_direct_page(name_variant):
    base_url = "https://growjo.com/company/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    company_url = base_url + quote(name_variant)

    res = requests.get(company_url, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    if not is_valid_company_page(soup):
        return None

    revenue = "<$5M"
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if "estimated annual revenue" in text.lower():
            match = re.search(r"\$\d[\d\.]*[MB]?", text)
            if match:
                revenue = match.group(0)
                break

    return {
        "matched_variant": name_variant,
        "estimated_revenue": revenue,
        "url": company_url
    }
