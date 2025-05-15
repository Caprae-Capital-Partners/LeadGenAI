# phase_1/backend/api/routes/scraper.py
from quart import Blueprint, request, jsonify, abort
from backend.main import fetch_and_merge_data

scraper_bp = Blueprint("scraper", __name__)

@scraper_bp.post("/lead-scrape")
async def lead_scrape():
    payload = await request.get_json()
    if not payload:
        abort(400, description="Missing JSON body")

    industry = (payload.get("industry") or "").strip()
    location = (payload.get("location") or "").strip()
    if not industry or not location:
        abort(400, description="Both 'industry' and 'location' are required")

    try:
        results = await fetch_and_merge_data(industry, location)
        return jsonify(results)
    except Exception as e:
        # logs full traceback server-side if you configure logging
        abort(500, description=f"Scraping failed: {e}")
