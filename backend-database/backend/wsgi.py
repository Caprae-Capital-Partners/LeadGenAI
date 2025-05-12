from app import app
from flask_cors import CORS

# Apply CORS to the imported app instance
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

if __name__ == "__main__":
    app.run(debug=True, port=8000)