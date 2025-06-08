from flask import Blueprint, request, jsonify
from backend_phase2.scraper.apollo_scraper import enrich_single_company
from backend_phase2.scraper.growjoScraper import GrowjoScraper
from backend_phase2.scraper.apollo_people import find_best_person

enrich_bp = Blueprint('enrich', __name__)


# === GROWJO ===
@enrich_bp.route("/scrape-growjo-batch", methods=["POST"])
def scrape_growjo_batch():
    try:
        data_list = request.get_json()
        if not isinstance(data_list, list):
            return jsonify({"error": "Expected a JSON array"}), 400

        scraper = GrowjoScraper(headless=True)
        results = []
        for entry in data_list:
            name = entry.get("company") or entry.get("name")
            try:
                results.append(scraper.scrape_full_pipeline(name))
            except Exception as e:
                results.append({"error": str(e), "input_name": name})
        scraper.close()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@enrich_bp.route("/scrape-growjo-single", methods=["POST"])
def scrape_growjo_single():
    try:
        payload = request.get_json()
        name = payload.get("company") or payload.get("name")
        if not name:
            return jsonify({"error": "Missing company name"}), 400

        scraper = GrowjoScraper(headless=True)
        result = scraper.scrape_full_pipeline(name)
        scraper.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === APOLLO PEOPLE ===
@enrich_bp.route("/find-best-person-batch", methods=["POST"])
def find_best_person_batch():
    try:
        domains = request.get_json().get("domains", [])
        results = []
        for domain in domains:
            try:
                results.append(find_best_person(domain.strip()))
            except Exception as e:
                results.append({"domain": domain, "error": str(e)})
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@enrich_bp.route("/find-best-person-single", methods=["POST"])
def find_best_person_single():
    try:
        payload = request.get_json()
        domain = payload.get("domain")
        if not domain:
            return jsonify({"error": "Missing domain"}), 400

        result = find_best_person(domain.strip())
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === APOLLO COMPANY ===
@enrich_bp.route("/apollo-scrape-batch", methods=["POST"])
def apollo_scrape_batch():
    try:
        domains = request.get_json().get("domains", [])
        results = []
        for domain in domains:
            try:
                enriched = enrich_single_company(domain.strip())
                enriched["domain"] = domain
                results.append(enriched)
            except Exception as e:
                results.append({"domain": domain, "error": str(e)})
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@enrich_bp.route("/apollo-scrape-single", methods=["POST"])
def apollo_scrape_single():
    try:
        payload = request.get_json()
        domain = payload.get("domain")
        if not domain:
            return jsonify({"error": "Missing domain"}), 400

        enriched = enrich_single_company(domain.strip())
        enriched["domain"] = domain
        return jsonify(enriched), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
