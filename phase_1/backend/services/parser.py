from typing import List
import pandas as pd
import re

def remove_last_word(text, word):
    matches = list(re.finditer(rf'\b{re.escape(word)}\b', text, flags=re.IGNORECASE))
    if matches:
        last_match = matches[-1]
        start, end = last_match.span()
        text = text[:start] + text[end:]
    return re.sub(r'(,\s*)+', ', ', text.strip())
#fixed the regex to remove extra commas
def parse_address(address: str, location: str) -> pd.DataFrame:
    places = pd.DataFrame()
    places['Address'] = [address]
    places['Street'] = pd.NA
    places['City'] = pd.NA
    places['State'] = pd.NA
    
    location_parts = location.split(',')

    if pd.isna(address):
        return places
    
    if address.startswith("[G]"):
        places['Address'] = [address.replace("[G]", "")]
        places['Street'] = [address.replace("[G]", "")]
        if len(location_parts) > 1:
            places['State'] = [location_parts[-1].strip().upper()]
            places['City'] = [location_parts[-2].strip().title()]
        return places
    if address.startswith("[H]"):
        places['Address'] = [address.replace("[H]", "")]
        if places['Address'].iloc[0].upper() == "NA":
            places['City'] = ["NA"]
            places['State'] = [location_parts[-1].strip().upper()]
            return places
        
        address_parts = address.replace("[H]", "").split(',')

        if len(address_parts) > 4:
            places['Street'] = [address_parts[0].strip()]
            places['City'] = [address_parts[-3].strip()]
            places['State'] = re.sub(r'[\d\s\-]', '', address_parts[-2].strip())
        elif len(address_parts) == 4:
            # Format: Street, City, State
            places['Street'] = [address_parts[0].strip()]
            places['City'] = [address_parts[1].strip()]
            places['State'] = re.sub(r'[\d\s\-]', '', address_parts[2].strip())
        elif len(address_parts) == 3:
            # Format: City, State
            places['Street'] = ["NA"]
            places['City'] = [address_parts[0].strip()]
            places['State'] = re.sub(r'[\d\s\-]', '', address_parts[1].strip())
        elif len(address_parts) == 1:
            # Format: Only Street or incomplete address
            places['Street'] = [address_parts[0].strip()]
            places['City'] = ["NA"]
            places['State'] = [location_parts[-1].strip().upper()]

        return places

    address = address.split(',')
    if len(address) >= 3:
        places['Address'] = [address]
        places['Street'] = [address[0]]
        places['City'] = [address[1].strip()]
        places['State'] = re.sub(r'[\d\s\-]', '', address[2].strip())

    if len(address) == 2:
        places['Address'] = [address]
        places['City'] = [address[0].strip()]
        places['State'] = re.sub(r'[\d\s\-]', '', address[1].strip())

    else:
        places['Street'] = [address[0]]

    return places

def parse_number(raw: str) -> str:
    # Remove country code and keep digits
    if pd.isna(raw):
        return raw
    
    digits_only = re.sub(r"[^\d]", "", raw)  # Keep only digits

    if len(digits_only) < 10:
        return raw

    local = digits_only[-10:]

    area = local[:3]
    mid = local[3:6]
    last = local[6:]
    
    return f"({area})-{mid}-{last}"
   
def parse_data(scraped: pd.DataFrame, fieldnames: List[str], location: str) -> pd.DataFrame:
    # Apply parse_address to each address and collect into list of DataFrames
    address_dfs = [parse_address(address, location) for address in scraped['Address']]
    
    # Combine all address DataFrames at once
    address_df = pd.concat(address_dfs, ignore_index=True)

    # Apply parse_number using vectorized .apply()
    scraped['Business_phone'] = scraped['Business_phone'].apply(parse_number)

    # Merge parsed address data
    scraped = pd.concat([scraped.reset_index(drop=True), address_df.drop(columns='Address').reset_index(drop=True)], axis=1)
    
    # Ensure all original columns are preserved
    og_fields = fieldnames
    extra_cols = [col for col in ['Street', 'City', 'State'] if col in scraped.columns]
    addr_idx = og_fields.index('Address')
    
    # Reorder columns to include original columns and parsed address fields
    reordered = (
        og_fields[:addr_idx] +   # Columns before Address
        extra_cols +            # Parsed address fields
        og_fields[addr_idx + 1:] # Columns after Address
    )
    scraped = scraped[[col for col in reordered if col in scraped.columns]]

    # Drop the original Address column if it still exists
    if 'Address' in scraped.columns:
        scraped = scraped.drop(columns='Address')

    return scraped


# if __name__ == "__main__":
#     scraped = pd.read_csv('merged_output.csv')
#     parse_data(scraped, "san diego, ca")