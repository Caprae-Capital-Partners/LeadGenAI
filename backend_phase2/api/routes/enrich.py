from flask import Blueprint, request, jsonify
from backend_phase2.scraper.apollo_scraper import enrich_single_company
from backend_phase2.scraper.growjoScraper import GrowjoScraper
from backend_phase2.scraper.apollo_people import find_best_person

enrich_bp = Blueprint('enrich', __name__)


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