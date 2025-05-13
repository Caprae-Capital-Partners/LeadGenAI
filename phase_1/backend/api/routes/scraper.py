from quart import Blueprint, request, jsonify
from backend.main import fetch_and_merge_data

scraper_bp = Blueprint('scraper', __name__)

@scraper_bp.route('/lead-scrape', methods=['POST'])
async def scrape():
    try:
        data = await request.get_json()
        industry = data.get('industry')
        location = data.get('location')

        # ✅ Parse from query params instead
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 100))

        if not industry or not location:
            return jsonify({"error": "Missing industry or location"}), 400

        results = await fetch_and_merge_data(industry, location, offset=offset, limit=limit)
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"Internal error": str(e)}), 500
