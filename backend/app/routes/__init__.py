from flask import Blueprint
from app.routes.auth import auth_bp
from app.routes.ai_recommendations import ai_recommendations_bp
from app.routes.portfolio import portfolio_bp
from app.routes.stocks import stocks_bp

__all__ = ['auth_bp', 'ai_recommendations_bp', 'portfolio_bp', 'stocks_bp']
