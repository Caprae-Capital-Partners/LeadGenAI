import csv
from typing import Dict, List

def save_to_csv(data: List[Dict[str, str]], headers: List[str], filename: str = "output.csv") -> None:
    with open(filename, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        for row in data:
            # Build row using headers to ensure consistency and default to ""
            formatted_row = {
                "Name": row.get("Name", "NA"),
                "Industry": row.get("Industry", "NA"),
                "Address": row.get("Address", "NA"),
                "Rating": row.get("Rating", "NA"),
                "BBB_rating": row.get("BBB_rating", "NA"),
                "Business_phone": row.get("Business_phone", "NA"),
                "Website": row.get("Website", "NA")
            }
            writer.writerow(formatted_row)

    print(f"Data saved to {filename}")


def merge_data_sources(data1: List[Dict[str, str]],
                       data2: List[Dict[str, str]],
                       data3: List[Dict[str, str]],
                       fieldnames: List[str]) -> List[Dict[str, str]]:
    merged = []
    seen_keys = set()  # Used to track unique records by Company and Address

    def get_key(record: Dict[str, str]) -> str:
        """Generate a unique key for deduplication based on Company and Address."""
        company = record.get("Company", "").strip().lower()
        address = record.get("Address", "").replace("[G]", "").strip().lower()
        return company + address

    def add_record(record: Dict[str, str]):
        """Add a record to the merged list, ensuring no duplicates."""
        key = get_key(record)
        if key not in seen_keys:
            seen_keys.add(key)
            # Normalize the record to include all required fields
            normalized_record = {field: record.get(field, "NA") for field in fieldnames}
            merged.append(normalized_record)

    # Process each data source
    for record in data1:
        add_record(record)

    for record in data2:
        add_record(record)

    for record in data3:
        add_record(record)

    return merged