from flask import Flask, jsonify
from flask_cors import CORS
from routes.enrich import enrich_bp

app = Flask(__name__)
CORS(app, allow_origin="*")

@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})

app.register_blueprint(enrich_bp, url_prefix="/api")

# ✅ This part ensures the server runs when executed
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
