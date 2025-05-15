from flask import Flask, jsonify
from flask_cors import CORS
from routes.enrich import enrich_bp

app = Flask(__name__)

# Enhanced CORS configuration
CORS(app, 
     resources={
         r"/api/*": {
             "origins": ["https://main.d2fzqm2i2qb7f3.amplifyapp.com"],
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "max_age": 86400
         }
     })

@app.after_request
def after_request(response):
    # Ensure these headers are added to every response
    response.headers.add('Access-Control-Allow-Origin', 'https://main.d2fzqm2i2qb7f3.amplifyapp.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})

app.register_blueprint(enrich_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)