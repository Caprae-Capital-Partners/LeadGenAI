from flask import Flask, jsonify
from routes.enrich import enrich_bp
app = Flask(__name__)
# :spanner: No Flask CORS — NGINX handles it in production
@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response

@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})
# Blueprint for enrichment routes
app.register_blueprint(enrich_bp, url_prefix="/api")
# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)