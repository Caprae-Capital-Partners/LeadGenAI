from flask import Flask
from models.lead_model import db
from routes.lead_routes import lead_bp
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from config.config import config
from flask_login import LoginManager
from models.user_model import User

def create_app(config_class=config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(main_bp)  # Register main routes first
    app.register_blueprint(auth_bp)  # Register auth routes
    app.register_blueprint(lead_bp)  # Then register other routes

    # Create database tables
    with app.app_context():
        db.create_all()

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=8000)