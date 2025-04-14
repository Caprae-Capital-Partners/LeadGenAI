def is_valid_company_page(soup):
    text = soup.get_text().lower()
    return (
        "page not found" not in text and
        "company not found" not in text and
        "rank not available" not in text and
        "estimated annual revenue" in text
    )
