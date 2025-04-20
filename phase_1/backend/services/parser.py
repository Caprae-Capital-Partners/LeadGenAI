import pandas as pd
import re
from collections import defaultdict

def remove_last_word(text, word):
    matches = list(re.finditer(rf'\b{re.escape(word)}\b', text, flags=re.IGNORECASE))
    if matches:
        last_match = matches[-1]
        start, end = last_match.span()
        text = text[:start] + text[end:]
    return re.sub(r'(,\s*)+', ', ', text.strip())

def parse_address(address, data):
    places = pd.DataFrame()
    places['Address'] = [address]
    places['Street'] = pd.NA
    places['City'] = pd.NA
    places['State'] = pd.NA
    
    if pd.isna(address):
        return places

    cities = list(data['city'])
    states = list(data['state'])
    cities_ori = list(data['city_ori'])
    states_ori = list(data['state_ori'])

    street = address
    state_get = ''
    city_get = ''

    possible_states = []
    get_index = []

    for i in range(len(states)):
        if (states[i] in street.lower() and len(states[i]) > 3):
            possible_states.append(states[i])
            get_index.append(i)

    reversed_address = street.lower().split(' ')[::-1]
    found = 0
    confident_state = 0

    for i in range(len(reversed_address)):
        for j in range(len(possible_states)):
            if re.sub(r'[^\w\s]', '', reversed_address[i]) == possible_states[j]:
                state_get = possible_states[j]
                places['State'] = states_ori[get_index[j]]
                found = 1
                confident_state = 1
                break
            if (possible_states[j] in reversed_address[i]) and (found == 0):
                state_get = possible_states[j]
                places['State'] = states_ori[get_index[j]]
                found = 1
        if confident_state == 1:
            break

    street = remove_last_word(street, state_get)

    if confident_state == 1:
        cities = list(data[data['state'] == state_get]['city'])
        cities_ori = list(data[data['state'] == state_get]['city_ori'])

    get_index = []
    possible_cities = []

    for i in range(len(cities)):
        if (cities[i] in street.lower() and len(cities[i]) > 3):
            possible_cities.append(cities[i])
            get_index.append(i)

    found = 0
    confident_city = 0
    for i in range(len(reversed_address)):
        for j in range(len(possible_cities)):
            if re.sub(r'[^\w\s]', '', reversed_address[i]) == possible_cities[j]:
                city_get = possible_cities[j]
                places['City'] = cities_ori[get_index[j]]
                confident_city = 1
                found = 1
                break
            if (possible_cities[j] in reversed_address[i]) and (found == 0):
                city_get = possible_cities[j]
                places['City'] = cities_ori[get_index[j]]
                found = 1
        if confident_city == 1:
            break

    street = remove_last_word(street, city_get)

    reversed_address = address.lower().split(' ')[::-1]

    if (confident_state == 0) and (confident_city == 1):
        possible_states = list(data[data['city'] == city_get]['state'])
        states_ori = list(data[data['city'] == city_get]['state_ori'])

        found = 0
        for i in range(len(reversed_address)):
            for j in range(len(possible_states)):
                if re.sub(r'[^\w\s]', '', reversed_address[i]) == possible_states[j]:
                    state_get = possible_states[j]
                    places['State'] = states_ori[j]
                    confident_state = 1
                    break
                if (possible_states[j] in reversed_address[i]) and (found == 0):
                    state_get = possible_states[j]
                    places['State'] = states_ori[j]
                    found = 1
            if confident_state == 1:
                break
        
        street = remove_last_word(street, state_get)

    reversed_address = street.split(' ')[::-1]

    if confident_city == 1 and state_get == '':
        states = list(data[(data['city'] == city_get) & (data['state'].apply(len) > 1)]['state_code'])
        states_ori = list(data[(data['city'] == city_get) & (data['state'].apply(len) > 1)]['state_ori'])
        for i in range(len(reversed_address)):
            for j in range(len(states)):
                if re.sub(r'[^\w\s]', '', reversed_address[i].upper()) == states[j]:
                    state_get = states_ori[j]
                    street = remove_last_word(street, state_get)
                    places['State'] = state_get
                    break
            if state_get != '':
                break

    street = re.sub(r'(,\s*)+', ', ', street.strip())
    places['Street'] = re.sub(r'[, ]+$', '', street)

    return places

def parse_number(raw):
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

# def parse_data(scraped, data):
#     address_column = list(scraped['Address'])
#     phone_column = list(scraped['Business_phone'])
    
#     address_df = pd.DataFrame()
#     for i in address_column:
#         address_df = pd.concat([address_df, parse_address(i, data)], axis = 0)
    
#     phone_list = []
#     for i in phone_column:
#         phone_list.append(parse_number(i))
        
#     scraped['Business_phone'] = phone_list
#     scraped = pd.merge(scraped, address_df, on='Address', how='inner')
    
#     scraped.to_csv('../data/Parsed_output.csv', index=False)
    
    # return scraped #if needed
    
def parse_data(scraped, data):
    # Apply parse_address to each address and collect into list of DataFrames
    address_dfs = [parse_address(address, data) for address in scraped['Address']]
    
    # Combine all address DataFrames at once
    address_df = pd.concat(address_dfs, ignore_index=True)

    # Apply parse_number using vectorized .apply()
    scraped['Business_phone'] = scraped['Business_phone'].apply(parse_number)

    # Merge parsed address data
    scraped = pd.merge(scraped, address_df, on='Address', how='inner')

    # Save output
    scraped.to_csv('../data/Parsed_output.csv', index=False)


if __name__ == "__main__":
    data = pd.read_csv('normalized_city_state_dataset.csv')
    data.dropna(inplace=True)
    scraped = pd.read_csv('merged_output.csv')
    parse_data(scraped, data)
    # print(parse_address('1300 E 86th St Ste 14 Box 130, Indianapolis, IN 46240-1910', data))
    # print(parse_number('+1 317-241-4327'))