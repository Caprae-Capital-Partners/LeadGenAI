from flask import Flask, jsonify
from flask_cors import CORS
from routes.enrich import enrich_bp

app = Flask(__name__)

# Configure CORS with explicit settings
CORS(app, 
     resources={
         r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"]
         }
     })

@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})

app.register_blueprint(enrich_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)