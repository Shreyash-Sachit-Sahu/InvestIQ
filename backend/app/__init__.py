import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

# Extensions (no app bound yet, for blueprint modularity)
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=None):
    app = Flask(__name__)
    # Load config from object, environment, or default
    app.config.from_object(config_class or os.environ.get("FLASK_APP_CONFIG") or "config.Config")

    # Initialize extensions with the app object
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # --- CORS SETUP ---
    raw = os.environ.get("CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,  # True if using cookies
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type", "Authorization"],
    )

    # Optional Redis integration (non-fatal if no REDIS_URL)
    try:
        import redis
        app.redis = redis.Redis.from_url(os.environ.get("REDIS_URL", ""), decode_responses=True)
    except Exception:
        app.redis = None

    # --- Register blueprints for modular API design ---
    from app.routes.auth import auth_bp
    from app.routes.stocks import stocks_bp
    from app.routes.ai_recommendations import ai_recommendations_bp
    from app.routes.portfolio import portfolio_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(stocks_bp, url_prefix="/api/stocks")
    app.register_blueprint(ai_recommendations_bp, url_prefix="/api/ai")
    app.register_blueprint(portfolio_bp, url_prefix="/api/portfolio")

    # --- FIX: Instantiate services INSIDE app context! ---
    with app.app_context():
        from app.services.ml_service import MLService
        from app.services.nse_data_service import NSEDataService

        app.ml_service = MLService()
        app.nse_data_service = NSEDataService()

    # Optionally, add before_request logging, Sentry, etc.
    @app.before_request
    def before_req_logging():
        pass

    return app
