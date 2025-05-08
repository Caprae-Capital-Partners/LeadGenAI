from flask import Blueprint, request, jsonify

import asyncio
from backend.main import fetch_and_merge_data

# Create a Blueprint for the scraper routes
scraper_bp = Blueprint('scraper', __name__)

@scraper_bp.route('/scrape', methods=['POST'])
def scrape():
    try:
        # Get the request data
        data = request.get_json()
        industry = data.get('industry')
        location = data.get('location')
        
        if not industry or not location:
            return jsonify({"error": "Missing industry or location"}), 400
        
        # Run the async function to fetch and merge data
        results = asyncio.run(fetch_and_merge_data(industry, location))
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"Internal error: ": str(e)}), 500