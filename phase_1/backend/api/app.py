from quart import Quart
# from quart_cors import cors
from backend.api.routes.scraper import scraper_bp

app = Quart(__name__)
# app = cors(app, allow_origin="*")  # You can restrict to frontend domain if needed

app.register_blueprint(scraper_bp, url_prefix='/api')

# ------- TESTING LOCAL ------ #

# from quart import Quart
# from quart_cors import cors
# from backend.api.routes.scraper import scraper_bp

# app = Quart(__name__)
# app = cors(app, allow_origin="*", allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

# app.register_blueprint(scraper_bp, url_prefix="/api")

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5001, debug=True)