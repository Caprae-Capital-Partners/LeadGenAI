import pandas as pd
import re

def remove_last_word(text, word):
    matches = list(re.finditer(rf'\b{re.escape(word)}\b', text, flags=re.IGNORECASE))
    if matches:
        last_match = matches[-1]
        start, end = last_match.span()
        text = text[:start] + text[end:]
    return re.sub(r'(,\s*)+', ', ', text.strip())
    
def parse_address(address: str, location: str) -> pd.DataFrame:
    places = pd.DataFrame()
    places['Address'] = [address]
    places['Street'] = pd.NA
    places['City'] = pd.NA
    places['State'] = pd.NA
    
    location_parts = location.split(',')

    if pd.isna(address):
        return places
    
    if address.startswith("[GOOGLE]"):
        places['Address'] = [address.replace("[GOOGLE]", "")]
        places['Street'] = [address.replace("[GOOGLE]", "")]
        if len(location_parts) > 1:
            places['States'] = [location_parts[-1].replace(" ", "")]
            places['City'] = [location_parts[-2].replace(" ", "")]
        return places

    address = address.split(',')
    if len(address) == 3:
        places['Address'] = [address]
        places['Street'] = [address[0]]
        places['City'] = [address[1].replace(" ", "")]
        places['State'] = re.sub(r'[\d\s\-]', '', address[2])

    if len(address) == 2:
        places['Address'] = [address]
        places['City'] = [address[0].replace(" ", "")]
        places['State'] = re.sub(r'[\d\s\-]', '', address[1])

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
   
def parse_data(scraped: pd.DataFrame, location: str) -> pd.DataFrame:
    # Apply parse_address to each address and collect into list of DataFrames
    address_dfs = [parse_address(address, location) for address in scraped['Address']]
    
    # Combine all address DataFrames at once
    address_df = pd.concat(address_dfs, ignore_index=True)

    # Apply parse_number using vectorized .apply()
    scraped['Business_phone'] = scraped['Business_phone'].apply(parse_number)

    # Merge parsed address data
    scraped = pd.concat([scraped.reset_index(drop=True), address_df.drop(columns='Address').reset_index(drop=True)], axis=1)
    
    cols = list(scraped.columns)
    extra_cols = [col for col in ['Street', 'City', 'State'] if col in cols]

    if 'Address' in cols:
        addr_idx = cols.index('Address')
        reordered = (
            cols[:addr_idx + 1] +
            extra_cols +
            [col for col in cols if col not in extra_cols and col != 'Address'][addr_idx + 1:]
        )
        scraped = scraped[reordered]
        
    scraped = scraped.drop(columns='Address')

    # scraped.to_csv('../data/Parsed_output.csv', index=False)
    return scraped


# if __name__ == "__main__":
#     scraped = pd.read_csv('merged_output.csv')
#     parse_data(scraped)