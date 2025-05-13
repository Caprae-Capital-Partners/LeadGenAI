from quart import Blueprint, request, jsonify
from backend.main import fetch_and_merge_data

scraper_bp = Blueprint('scraper', __name__)

@scraper_bp.route('/lead-scrape', methods=['POST'])
async def scrape():
    try:
        # Get the request data
        data = await request.get_json()
        industry = data.get('industry')
        location = data.get('location')
        
        if not industry or not location:
            return jsonify({"error": "Missing industry or location"}), 400
        
        try:
            results = await fetch_and_merge_data(industry, location)
        except Exception as e:
            return jsonify({"Scraping failed": str(e)}), 500
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"Internal error": str(e)}), 500