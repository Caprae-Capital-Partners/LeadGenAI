# backend_phase2/api/routes/enrich.py

import threading
from flask import Blueprint, request, jsonify
from backend_phase2.scraper.apollo_scraper import enrich_single_company
from backend_phase2.scraper.growjoScraper import GrowjoScraper
from backend_phase2.scraper.apollo_people import find_best_person
from selenium.common.exceptions import WebDriverException

enrich_bp = Blueprint('enrich', __name__)

# ── Module‐level singleton and timer for GrowjoScraper ──
growjo_scraper_instance: GrowjoScraper | None = None
expiration_timer: threading.Timer | None = None

# How long (in seconds) before the scraper auto‐closes due to inactivity:
ttl_seconds = 30 * 60  # e.g. 30 minutes


def _auto_close():
    """
    Called by the Timer once TTL elapses. Quits both browsers and resets state.
    """
    global growjo_scraper_instance, expiration_timer

    if growjo_scraper_instance:
        try:
            growjo_scraper_instance.close()
        except Exception:
            pass

    growjo_scraper_instance = None
    expiration_timer = None
    print("[INFO] GrowjoScraper auto‐closed after TTL.")


def _reset_timer():
    """
    Cancel any existing timer and start a new one for ttl_seconds.
    """
    global expiration_timer

    if expiration_timer:
        expiration_timer.cancel()

    expiration_timer = threading.Timer(ttl_seconds, _auto_close)
    expiration_timer.daemon = True
    expiration_timer.start()

# === CHECK IF SCRAPER IS STILL RUNNING ===
@enrich_bp.route("/is-growjo-scraper", methods=["GET"])
def is_growjo_scraper():
    """
    Return whether the GrowjoScraper singleton is currently initialized *and*
    its underlying Edge browser tabs are still alive. If either tab has been
    closed manually, we clean up the instance and return initialized=False.
    """
    global growjo_scraper_instance

    if growjo_scraper_instance is None:
        return jsonify({"initialized": False}), 200

    try:
        # Try a very cheap operation on the public driver to see if it's still alive.
        # For example, get current URL or window handle. If the browser was closed
        # manually, Selenium will raise a WebDriverException.
        _ = growjo_scraper_instance.driver_public.current_url
        _ = growjo_scraper_instance.driver_logged_in.current_url

        # Both tabs still exist, so we remain “initialized”
        return jsonify({"initialized": True}), 200

    except WebDriverException:
        # One (or both) of the Edge windows was closed manually → clean up
        try:
            growjo_scraper_instance.close()
        except Exception:
            pass

        growjo_scraper_instance = None
        return jsonify({"initialized": False}), 200

# === GROWJO INITIALIZATION & TEARDOWN ===
@enrich_bp.route("/init-growjo-scraper", methods=["POST"])
def init_growjo_scraper():
    """
    Initialize a singleton GrowjoScraper (headless=False). 
    Opens two Edge browser tabs (public + logged‐in), logs in on the private tab,
    and starts the inactivity timer.
    """
    global growjo_scraper_instance

    if growjo_scraper_instance is not None:
        # Already initialized → just restart the TTL countdown
        _reset_timer()
        return jsonify({"status": "already initialized"}), 200

    try:
        scraper = GrowjoScraper(headless=True)

        # Open the "public" tab at https://growjo.com/ so it's ready for scraping
        scraper.driver_public.get("https://growjo.com/")

        # Immediately log in on the private tab
        scraper.login_logged_in_browser()

        growjo_scraper_instance = scraper

        # Start (or reset) the inactivity timer
        _reset_timer()

        return jsonify({"status": "initialized"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to initialize GrowjoScraper: {str(e)}"}), 500


@enrich_bp.route("/close-growjo-scraper", methods=["POST"])
def close_growjo_scraper():
    """
    Manually close the existing GrowjoScraper (quit both Edge tabs),
    cancel the inactivity timer, and clear the singleton.
    """
    global growjo_scraper_instance, expiration_timer

    if growjo_scraper_instance is None:
        return jsonify({"status": "not initialized"}), 200

    try:
        if expiration_timer:
            expiration_timer.cancel()
            expiration_timer = None

        growjo_scraper_instance.close()
        growjo_scraper_instance = None
        return jsonify({"status": "closed"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to close GrowjoScraper: {str(e)}"}), 500


# === GROWJO SCRAPE: SINGLE ===
@enrich_bp.route("/scrape-growjo-single", methods=["POST"])
def scrape_growjo_single():
    """
    - If no singleton exists, initialize it now (headless=False + login).
    - Do NOT reset the inactivity timer here; only /init-growjo-scraper should do that.
    - Call scrape_full_pipeline(...) on the existing instance.
    """
    global growjo_scraper_instance

    payload = request.get_json() or {}
    name = payload.get("company") or payload.get("name")
    if not name:
        return jsonify({"error": "Missing company name"}), 400

    try:
        # If not already initialized, spin it up (headless=False) and login
        if growjo_scraper_instance is None:
            scraper = GrowjoScraper(headless=True)
            scraper.driver_public.get("https://growjo.com/")
            scraper.login_logged_in_browser()
            growjo_scraper_instance = scraper

            # (Since we just initialized here, we start the timer now)
            _reset_timer()

        scraper = growjo_scraper_instance
        result = scraper.scrape_full_pipeline(name)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === APOLLO PEOPLE ===
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
