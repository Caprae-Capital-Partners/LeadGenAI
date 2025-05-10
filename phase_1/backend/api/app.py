from quart import Quart
from backend.api.routes.scraper import scraper_bp

app = Quart(__name__)
app.register_blueprint(scraper_bp, url_prefix='/api')