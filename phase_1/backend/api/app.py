from quart import Quart, request
# from quart_cors import cors
from backend.api.routes.scraper import scraper_bp

app = Quart(__name__)
# app = cors(app, allow_origin="*")  # You can restrict to frontend domain if needed

app.register_blueprint(scraper_bp, url_prefix='/api')

@app.before_request
async def block_options():
    if request.method == "OPTIONS":
        return "", 204