import os
import ast

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret')

    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI',
                                            'sqlite:///instance/investiq.db')  # fallback only locally

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 900))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    MODEL_DIR = os.path.abspath(os.environ.get('MODEL_DIR', '../MLmodel/models/'))
    CORS_ORIGINS = ast.literal_eval(os.environ.get('CORS_ORIGINS', '["http://localhost:3000"]'))
