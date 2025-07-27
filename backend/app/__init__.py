from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging

db = SQLAlchemy()
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)

    # Load configuration from Config class
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    
    # Enhanced CORS configuration to fix preflight issues
    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS"),
        supports_credentials=True,
        methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Health check endpoint
    @app.route("/", methods=["GET", "HEAD"])
    def health_check():
        logger.debug("Health check received")
        return jsonify(status="ok"), 200

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.portfolio import portfolio_bp
    from app.routes.ai_advisor import ai_advisor_bp
    from app.routes.nse_data import nse_data_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(ai_advisor_bp)
    app.register_blueprint(nse_data_bp)

    # Register custom error handlers
    from app.utils import register_error_handlers
    register_error_handlers(app)

    return app
