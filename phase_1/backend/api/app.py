from quart import Quart
# from quart_cors import cors
from backend.api.routes.scraper import scraper_bp

app = Quart(__name__)
# app = cors(app, allow_origin="*")  # You can restrict to frontend domain if needed

app.register_blueprint(scraper_bp, url_prefix='/api')
