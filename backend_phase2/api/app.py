from flask import Flask, jsonify
from flask_cors import CORS
from backend_phase2.api.routes.enrich import enrich_bp

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://yourdomain.com"])

@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})

app.register_blueprint(enrich_bp, url_prefix="/api")
