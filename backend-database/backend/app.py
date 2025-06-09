from flask import Flask, has_request_context, g
from models.lead_model import db
from routes.lead_routes import lead_bp
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.credit_routes import credit_bp
from routes.lead_access_routes import access_bp
from routes.user_management_routes import user_management_bp
from config.config import config
from flask_login import LoginManager, current_user
from models.user_model import User
from sqlalchemy import event, text
from flask_cors import CORS
from routes.subscription_routes import subscription_bp
from logging_setup import setup_logging
from utils.email_utils import init_mail

def create_app(config_class=config):
    """Create and configure the Flask application"""
    setup_logging()
    app = Flask(__name__)
    app.config.from_object(config_class)

    # :white_check_mark: Production cookie settings for session auth
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True

    # Initialize CORS
    CORS(app, origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://capraeleadseekers.site",
        "https://35.165.209.201",
        "https://main.d2fzqm2i2qb7f3.amplifyapp.com",
        "http://35.165.209.201",
        "https://sandboxdev.saasquatchleads.com",
        "https://www.saasquatchleads.com",
        "http://54.166.155.63:3000",
        "http://54.166.155.63",
        "https://app.saasquatchleads.com",
        "https://sandbox-api.capraeleadseekers.site"
    ], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
       allow_headers=["Content-Type", "Authorization"],
       supports_credentials=True)

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Initialize Flask-Mail
    init_mail(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(str(user_id))

    def set_app_user_on_connect(dbapi_connection, connection_record):
        try:
            # Only set if in a request context and user is authenticated
            if has_request_context() and current_user.is_authenticated:
                username = getattr(current_user, 'username', None)
                if username:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("SELECT set_app_user(%s);", (username,))
                    cursor.close()
        except Exception:
            pass  # Ignore if user is not available (e.g., during migrations)

    @app.before_request
    def set_audit_user():
        if has_request_context() and current_user.is_authenticated:
            username = getattr(current_user, 'username', None)
            if username:
                # Use the current session, not a new engine connection
                db.session.execute(text("SELECT set_app_user(:username);"), {"username": username})

    # Register blueprints
    app.register_blueprint(main_bp)  # Register main routes first
    app.register_blueprint(auth_bp)  # Register auth routes
    app.register_blueprint(lead_bp)  # Then register other routes
    app.register_blueprint(subscription_bp)  # Register subscription routes
    app.register_blueprint(access_bp) # Register lead access routes
    app.register_blueprint(credit_bp)
    app.register_blueprint(user_management_bp)

    # Create database tables
    with app.app_context():
        db.create_all()
        event.listen(db.engine, "connect", set_app_user_on_connect)

        # Call the audit log setup from the model
        from models.audit_log_model import ensure_audit_log_infrastructure
        ensure_audit_log_infrastructure(db)

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)