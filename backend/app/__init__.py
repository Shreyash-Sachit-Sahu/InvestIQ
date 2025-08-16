import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

# Initialize extensions (do not bind to app here for blueprints modularity)
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=None):
    app = Flask(__name__)
    # Load configuration
    app.config.from_object(config_class or os.environ.get("FLASK_APP_CONFIG") or "config.Config")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # --- CORS SETUP ---
    # Fetch CORS_ORIGINS env (comma-separated), safely as a list
    raw = os.environ.get("CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,  # True if using cookies; else False
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type", "Authorization"],
    )

    # Optional: Redis (only if you use it)
    try:
        import redis
        app.redis = redis.Redis.from_url(os.environ.get("REDIS_URL", ""), decode_responses=True)
    except Exception:
        app.redis = None

    # Register blueprints for modular routes
    from app.routes.auth import auth_bp
    from app.routes.stocks import stocks_bp
    from app.routes.ai_recommendations import ai_recommendations_bp
    from app.routes.portfolio import portfolio_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(stocks_bp, url_prefix="/api/stocks")
    app.register_blueprint(ai_recommendations_bp, url_prefix="/api/ai")
    app.register_blueprint(portfolio_bp, url_prefix="/api/portfolio")

    # Optionally: import your ML or data services and attach to app
    from app.services.ml_service import MLService
    from app.services.nse_data_service import NSEDataService

    # One global service instance each
    app.ml_service = MLService()
    app.nse_data_service = NSEDataService()

    # Application context hooks, logging setup if needed
    @app.before_request
    def before_req_logging():
        # Optional: Add logging, correlation-id, etc.
        pass

    return app
