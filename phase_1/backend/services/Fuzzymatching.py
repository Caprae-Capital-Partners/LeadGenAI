from fuzzywuzzy import fuzz
import re

def clean_phone(phone):
    """Extract only digits from phone number."""
    if not phone or not isinstance(phone, str):
        return ""
    return re.sub(r'\D', '', phone)

def deduplicate_businesses(businesses_list):
    """
    Remove duplicate businesses from a list of business dictionaries.
    
    Deduplication logic:
    - If companies have same name AND same phone number, treat as duplicates (even if addresses differ)
    - If companies have same name but different phone numbers, treat as different branches (not duplicates)
    
    Args:
        businesses_list: List[Dict[str, str]] containing business information
        
    Returns:
        List[Dict[str, str]]: List of dictionaries with duplicates removed
    """
    if not businesses_list or len(businesses_list) == 0:
        return []
    
    # Initialize with first business
    unique_businesses = [businesses_list[0]]
    
    for business in businesses_list[1:]:
        is_duplicate = False
        
        for unique_business in unique_businesses:
            # Find name fields (may vary in different datasets)
            name_field = 'Name' if 'Name' in business else next((f for f in business if 'name' in f.lower() or 'company' in f.lower()), None)
            
            # If no name field found, can't compare
            if not name_field:
                continue
                
            # Get names and convert to lowercase for comparison
            name1 = str(business.get(name_field, '')).lower().strip()
            name2 = str(unique_business.get(name_field, '')).lower().strip()
            
            # If either name is empty, they're not duplicates
            if not name1 or not name2:
                continue
                
            # Use fuzzy matching to compare names
            name_similarity = fuzz.token_sort_ratio(name1, name2)
            
            # Only consider as potential duplicates if names are similar enough
            if name_similarity >= 85:
                # Find phone number fields (may vary in different datasets)
                phone_field = next((f for f in business if 'phone' in f.lower()), None)
                
                # If phone field exists, compare phone numbers
                if phone_field:
                    phone1 = clean_phone(business.get(phone_field, ''))
                    phone2 = clean_phone(unique_business.get(phone_field, ''))
                    
                    # If both phone numbers exist and are the same, it's a duplicate
                    if phone1 and phone2 and phone1 == phone2:
                        is_duplicate = True
                        break
                    # If both phone numbers exist but are different, these are different branches
                    elif phone1 and phone2 and phone1 != phone2:
                        continue
                
                # If phone numbers don't exist or one is missing, use very high name similarity
                if name_similarity >= 95:
                    is_duplicate = True
                    break
        
        # Add to unique businesses if it's not a duplicate
        if not is_duplicate:
            unique_businesses.append(business)
    
    return unique_businesses