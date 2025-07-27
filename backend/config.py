import os
import ast

# Use the absolute path to the instance folder for reliable DB storage.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_FILENAME = "investiq.db"
DB_PATH = os.path.join(INSTANCE_DIR, DB_FILENAME)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret')
    # Always use absolute path for SQLite URI.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        f'sqlite:///{DB_PATH}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 900))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    MODEL_DIR = os.path.abspath(os.environ.get('MODEL_DIR', '../MLmodel/models/'))
    CORS_ORIGINS = ast.literal_eval(os.environ.get('CORS_ORIGINS', '["http://localhost:3000"]'))
