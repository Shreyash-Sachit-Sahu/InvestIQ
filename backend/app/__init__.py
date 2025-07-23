from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    JWTManager(app)
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.portfolio import portfolio_bp
    from app.routes.ai_advisor import ai_advisor_bp
    from app.routes.nse_data import nse_data_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(ai_advisor_bp)
    app.register_blueprint(nse_data_bp)

    # Register error handlers
    from app.utils import register_error_handlers
    register_error_handlers(app)

    return app
