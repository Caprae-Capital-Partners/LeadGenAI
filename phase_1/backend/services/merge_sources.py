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
    seen_keys = set()  # Used to track unique records by Name or Address
    duplicate_count = 0
    
    def get_key(record: Dict[str, str]) -> str:
        # Use Name or Address as unique identifier
        return (record.get("Company", "") + record.get("Address", "")).strip().lower()

    # Helper to add record to merged list safely
    def add_record(record: Dict[str, str]):
        nonlocal duplicate_count
        key = get_key(record)
        if key not in seen_keys:
            seen_keys.add(key)
            merged.append({field: record.get(field, "") for field in fieldnames})
        else:
            duplicate_count += 1

    for record in data1:
        # Map Rating field to BBB_rating if present
        if "BBB_rating" not in record:
            record["BBB_rating"] = record.get("Rating", "NA")
        add_record(record)

    for record in data2:
        # Map Rating from data2, keep as is
        add_record(record)
        
    for record in data3:
        add_record(record)
        
    # print(f"Duplicates found: {duplicate_count}")
    # print(f"Total entries after deduplication: {len(merged)}")

    return merged