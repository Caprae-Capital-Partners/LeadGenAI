import json
import os

CACHE_FILE = "cache.json"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w") as f:
            json.dump({}, f)
        return {}

    with open(CACHE_FILE) as f:
        return json.load(f)

def get_cached_match(source, company_name):
    cache = load_cache()
    return cache.get(source, {}).get(company_name)

def set_cached_match(source, company_name, matched_name):
    cache = load_cache()

    if source not in cache:
        cache[source] = {}

    cache[source][company_name] = matched_name

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
