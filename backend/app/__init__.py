from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
import redis
from config import Config
import os

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS
    CORS(
    app,
    resources={r"/api/*": {"origins": os.environ.get("CORS_ORIGINS").split(",")}},
    )
    
    # Initialize Redis
    try:
        app.redis = redis.from_url(app.config['REDIS_URL'])
        app.redis.ping()
    except:
        app.redis = None
        print("Warning: Redis connection failed")
    
    # Register blueprints
    from app.routes import auth_bp, ai_recommendations_bp, portfolio_bp, stocks_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(ai_recommendations_bp, url_prefix='/api/ai')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(stocks_bp, url_prefix='/api/stocks')
    
    # Initialize ML services
    with app.app_context():
        from app.services.ml_service import MLService
        app.ml_service = MLService()
    
    return app
