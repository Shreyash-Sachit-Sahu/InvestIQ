import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///investiq.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    
    # ML Model Configuration
    MODEL_VERSION = os.environ.get('MODEL_VERSION', 'v1.0.0')
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models')
    
    # API Configuration
    CORS_ORIGINS = ['http://localhost:3000', 'https://your-frontend-domain.com']
    
    # Financial Modeling Prep API Configuration
    FMP_API_KEY = os.environ.get('FMP_API_KEY')
    FMP_DAILY_LIMIT = 250  # Free tier limit
    FMP_BASE_URL = 'https://financialmodelingprep.com/api/v3'
