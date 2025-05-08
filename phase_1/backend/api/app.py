from flask import Flask
from backend.api.routes.scraper import scraper_routes

def create_app():
    app = Flask(__name__)

    # Register the scraper routes
    app.register_blueprint(scraper_routes, url_prefix='/api')

    return app