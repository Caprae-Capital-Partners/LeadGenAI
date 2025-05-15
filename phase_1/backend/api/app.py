import asyncio
import sys
from quart import Quart
from quart_cors import cors
from backend.api.routes.scraper import scraper_bp

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = Quart(__name__)
app = cors(app, allow_origin="*")  # You can restrict to frontend domain if needed

app.register_blueprint(scraper_bp, url_prefix='/api')
