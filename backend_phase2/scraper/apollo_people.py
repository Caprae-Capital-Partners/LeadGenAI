from flask import Flask, request, jsonify
import requests
import os
import random

app = Flask(__name__)

APOLLO_API_KEY      = os.getenv("APOLLO_API_KEY")
APOLLO_SEARCH_URL   = "https://api.apollo.io/api/v1/mixed_people/search"
APOLLO_ENRICH_URL   = "https://api.apollo.io/api/v1/people/match"

# Titles given descending priority (lower index = higher priority)
priority_titles = [
    "founder",
    "co-founder",
    "cofounder",
    "ceo",
    "chief executive officer",
    "president",
    "coo",
    "chief operating officer",
    "cmo",
    "chief marketing officer",
    "svp",
    "vp",
    "director",
    "manager",
]


def get_priority_rank(title):
    # If title is None or empty, treat as lowest priority
    title = title or ""
    if not title:
        return len(priority_titles) + 1

    title_lower = title.lower()
    for idx, keyword in enumerate(priority_titles):
        if keyword in title_lower:
            return idx
    return len(priority_titles) + 1


def _friendly_fallback_person(field_type: str) -> str:
    """
    Returns a small friendly fallback for any missing person field.
    """
    messages = {
        "company": [
            "Company name not found.",
            "No organization data available.",
            "Organization info is missing."
        ],
        "first_name": [
            "First name unavailable.",
            "Could not locate a first name.",
            "No given name provided."
        ],
        "last_name": [
            "Last name unavailable.",
            "Could not locate a last name.",
            "No family name provided."
        ],
        "title": [
            "Title not specified.",
            "No job title found.",
            "Position information missing."
        ],
        "linkedin_url": [
            "LinkedIn link not available.",
            "Could not find a LinkedIn profile.",
            "LinkedIn information missing."
        ],
        "email": [
            "Email not available.",
            "No contact email found.",
            "Email information missing."
        ],
        "phone_number": [
            "Phone number unavailable.",
            "No phone contact found.",
            "Phone information missing."
        ],
        "domain": [
            "Domain not provided.",
            "No domain info available.",
            "Domain information missing."
        ],
    }
    return random.choice(messages.get(field_type, ["Information not available."]))


def normalize(value: any, field_type: str) -> str:
    """
    Takes any raw value and:
      1) Strips it.
      2) If empty or in ["", "not", "found", "not found", "none"], returns a friendly fallback.
      3) Otherwise returns the trimmed string.
    """
    raw = (value or "").strip()
    lower = raw.lower()
    if lower in ["", "not", "found", "not found", "none", "n/a", "na"]:
        return _friendly_fallback_person(field_type)
    return raw


def enrich_person(first_name, last_name, domain):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY,
    }

    params = {
        "first_name": first_name,
        "last_name": last_name,
        "domain": domain,
        "reveal_personal_emails": "true",
        "reveal_phone_number": "false",
    }

    response = requests.post(APOLLO_ENRICH_URL, headers=headers, params=params)
    if response.status_code != 200:
        return None

    person = response.json().get("person", {})

    # If Apollo returns locked‐mask (“email_not_unlocked@domain.com”), treat as missing
    if person.get("email", "").lower() == "email_not_unlocked@domain.com":
        person["email"] = ""

    return person


@app.route("/find-best-person-single", methods=["POST"])
def find_best_person_single():
    """
    Expects JSON: { "domain": "example.com" }
    Returns one best person or fallback messages for all fields if none found.
    """
    payload = request.get_json()
    domain = payload.get("domain")
    if not domain:
        return jsonify({"error": "Missing domain"}), 400

    result = find_best_person(domain.strip())
    return jsonify(result), 200


@app.route("/find-best-person-batch", methods=["POST"])
def find_best_person_batch():
    """
    Expects JSON: { "domains": ["a.com", "b.com", ...] }
    Returns a list of results, each with fallback messages as needed.
    """
    payload = request.get_json(silent=True) or {}
    domains = payload.get("domains", [])
    if not isinstance(domains, list):
        return jsonify({"error": "Expected a JSON array of domains"}), 400

    results = []
    for dom in domains:
        results.append(find_best_person(dom.strip()))
    return jsonify(results), 200


def find_best_person(domain: str) -> dict:
    """
    Common logic for single‐domain or batch:
      1) Query Apollo search.
      2) If no people or non-200, return full‐field fallbacks.
      3) Otherwise pick highest priority, then “enrich_person” for email/phone.
      4) Normalize each field via normalize(...).
      5) If any exception arises, return full‐field fallbacks.
    """
    # A helper to produce a “full fallback” dictionary in case anything goes wrong:
    def full_fallback():
        return {
            "company": _friendly_fallback_person("company"),
            "domain": domain or _friendly_fallback_person("domain"),
            "first_name": _friendly_fallback_person("first_name"),
            "last_name": _friendly_fallback_person("last_name"),
            "title": _friendly_fallback_person("title"),
            "linkedin_url": _friendly_fallback_person("linkedin_url"),
            "email": _friendly_fallback_person("email"),
            "phone_number": _friendly_fallback_person("phone_number"),
        }

    try:
        # ── 1) Query Apollo search ──
        params = {
            "person_titles[]": "",
            "person_seniorities[]": ["owner", "founder", "c_suite", "vp", "director", "manager"],
            "q_organization_domains_list[]": domain,
            "contact_email_status[]": "",
        }
        headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": APOLLO_API_KEY,
        }

        response = requests.post(APOLLO_SEARCH_URL, headers=headers, params=params)
        if response.status_code != 200:
            return full_fallback()

        data = response.json()
        people = data.get("people", [])

        # ── 2) If no “people” hit, return full fallback ──
        if not people:
            return full_fallback()

        # ── 3) Sort by priority_title and pick the top candidate ──
        people_sorted = sorted(people, key=lambda x: get_priority_rank(x.get("title") or ""))
        best_person = people_sorted[0]

        # ── 4) Attempt to “enrich_person” for email/phone ──
        enriched = enrich_person(
            first_name=best_person.get("first_name", ""),
            last_name=best_person.get("last_name", ""),
            domain=domain,
        )

        # ── 5) Build a combined result, normalizing each field ──
        combined_result = {
            "company": normalize(best_person.get("organization", {}).get("name"), "company"),
            "domain": domain or normalize("", "domain"),
            "first_name": normalize(best_person.get("first_name"), "first_name"),
            "last_name": normalize(best_person.get("last_name"), "last_name"),
            "title": normalize(best_person.get("title"), "title"),
            "linkedin_url": normalize(best_person.get("linkedin_url"), "linkedin_url"),
            "email": normalize(best_person.get("email"), "email"),
            "phone_number": normalize(
                best_person.get("organization", {}).get("primary_phone", {}).get("sanitized_number"),
                "phone_number"
            ),
        }

        # ── 6) Override with enriched values if available ──
        if enriched:
            combined_result["email"] = normalize(enriched.get("email"), "email")
            combined_result["linkedin_url"] = normalize(enriched.get("linkedin_url"), "linkedin_url")
            combined_result["phone_number"] = normalize(enriched.get("phone_number"), "phone_number")

        return combined_result

    except Exception:
        # If anything went wrong (e.g. “NoneType” has no .lower), return all‐fallbacks
        return full_fallback()
