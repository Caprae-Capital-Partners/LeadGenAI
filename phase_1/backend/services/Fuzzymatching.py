from rapidfuzz import fuzz
import re

def clean_phone(phone):
    """Extract only digits from phone number."""
    if not phone:
        return ""
    return re.sub(r'\D', '', str(phone))

def normalize_address(address):
    """Standardize address format."""
    if not address:
        return ""
    # Remove common terms and punctuation
    address = re.sub(r'\s+', ' ', str(address))
    address = address.lower().strip()
    return address

def combine_phone_numbers(existing_phone, new_phone):
    """
    Combine phone numbers if they are different.
    
    Args:
        existing_phone (str): Current phone number(s), possibly comma-separated
        new_phone (str): New phone number to potentially add
        
    Returns:
        str: Combined phone numbers if different, otherwise the existing phone
    """
    if not new_phone:
        return existing_phone
    
    if not existing_phone:
        return new_phone
    
    clean_new_phone = clean_phone(new_phone)
    
    # If existing phone has multiple numbers
    if ',' in existing_phone:
        existing_phones = [clean_phone(p.strip()) for p in existing_phone.split(',')]
        # Only add if not already in the list
        if clean_new_phone not in existing_phones:
            return existing_phone + ',' + new_phone
        return existing_phone
    else:
        # If single existing phone, combine if different
        clean_existing_phone = clean_phone(existing_phone)
        if clean_new_phone != clean_existing_phone:
            return existing_phone + ',' + new_phone
        return existing_phone

def deduplicate_businesses(businesses_list):
    """
    Remove duplicate businesses from a list of business dictionaries and
    combine phone numbers for businesses with the same name.
    
    Deduplication logic:
    - If companies have same name AND same phone, consider them duplicates
    - If companies have same name AND similar address, consider them duplicates
    - When duplicates are found, combine their phone numbers
    
    Args:
        businesses_list (List[Dict[str, str]]): List of dictionaries containing business information
        
    Returns:
        List[Dict[str, str]]: List of dictionaries with duplicates removed and phone numbers combined
    """
    if not businesses_list or len(businesses_list) == 0:
        return []
    
    # Initialize with first business
    unique_businesses = [businesses_list[0].copy()]  # Use copy to avoid modifying original
    
    for business in businesses_list[1:]:
        # Find name, address, and phone fields
        name_field = 'Name' if 'Name' in business else next((f for f in business if 'name' in f.lower() or 'company' in f.lower()), None)
        address_field = 'Address' if 'Address' in business else next((f for f in business if 'address' in f.lower()), None)
        phone_field = next((f for f in business if 'phone' in f.lower()), None)
        
        # Skip if essential fields are missing
        if not name_field:
            unique_businesses.append(business.copy())
            continue
        
        # Get current business info
        name = str(business.get(name_field, '')).lower().strip()
        address = normalize_address(business.get(address_field, '')) if address_field else ""
        phone = business.get(phone_field, '') if phone_field else ''
        clean_current_phone = clean_phone(phone)
        
        # Check if this business can be merged with an existing one
        merged = False
        
        for unique_business in unique_businesses:
            # Compare name
            unique_name = str(unique_business.get(name_field, '')).lower().strip()
            name_similarity = fuzz.token_sort_ratio(name, unique_name)
            
            # Only consider merging if names are similar enough
            if name_similarity >= 85:
                # Get unique business phone and address
                unique_phone = unique_business.get(phone_field, '') if phone_field else ''
                unique_address = normalize_address(unique_business.get(address_field, '')) if address_field else ""
                
                # Check if phones are the same
                phones_match = False
                if clean_current_phone and unique_phone:
                    clean_unique_phone = clean_phone(unique_phone)
                    # Check if phone numbers match (either exact or contained in comma-separated list)
                    if ',' in unique_phone:
                        unique_phones = [clean_phone(p.strip()) for p in unique_phone.split(',')]
                        phones_match = clean_current_phone in unique_phones
                    else:
                        phones_match = clean_current_phone == clean_unique_phone
                
                # Check if addresses are similar
                address_match = False
                if address and unique_address:
                    address_similarity = fuzz.token_set_ratio(address, unique_address)
                    address_match = address_similarity >= 75
                
                # Duplicate found if:
                # 1. Same name and same phone (regardless of address), OR
                # 2. Same name and similar address
                if (phones_match or address_match):
                    # Use the separate function to combine phone numbers
                    if phone and unique_phone and not phones_match:
                        unique_business[phone_field] = combine_phone_numbers(unique_phone, phone)
                    
                    # If only the new entry has a phone number, add it
                    elif phone and not unique_phone:
                        unique_business[phone_field] = phone
                    
                    # Mark as merged
                    merged = True
                    break
        
        # If not merged with any existing one, add as new unique business
        if not merged:
            unique_businesses.append(business.copy())
    
    return unique_businesses