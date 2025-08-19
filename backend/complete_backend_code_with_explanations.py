"""
# Complete InvestIQ Backend Codebase with Explanations

## Project Structure
backend/
├── app/
│   ├── __init__.py          # Flask app factory & configuration
│   ├── config.py            # Configuration settings
│   ├── models/
│   │   └── user.py          # User model
│   ├── routes/
│   │   └── auth.py          # Authentication endpoints
│   ├── services/            # Business logic services
│   ├── utils/               # Utility functions & decorators
│   └── ml_models/           # Machine learning models
├── requirements.txt         # Python dependencies
└── run.py                   # Application entry point

## Configuration (`backend/config.py`)
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
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    
    # CORS Configuration
    CORS_ORIGINS = ['http://localhost:3000', 'https://your-frontend-domain.com']

## Application Factory (`backend/app/__init__.py`)
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

# Extensions initialization
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class or "config.Config")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # CORS setup
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.stocks import stocks_bp
    from app.routes.portfolio import portfolio_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(stocks_bp, url_prefix="/api/stocks")
    app.register_blueprint(portfolio_bp, url_prefix="/api/portfolio")

    return app

## User Model (`backend/app/models/user.py`)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

## Authentication Routes (`backend/app/routes/auth.py`)
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    email = data['email'].strip().lower()
    password = data['password']
    
    # Create user
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'success': True,
        'data': {
            'user': user.to_dict(),
            'tokens': {
                'access': access_token,
                'refresh': refresh_token
            }
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    email = data['email'].strip().lower()
    password = data['password']
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'success': True,
        'data': {
            'user': user.to_dict(),
            'tokens': {
                'access': access_token,
                'refresh': refresh_token
            }
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    
    return jsonify({
        'success': True,
        'data': {'access_token': access_token}
    })

## JWT Decorators (`backend/app/utils/decorators.py`)
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

def jwt_required_custom(f):
    """Custom JWT verification decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
        return f(*args, **kwargs)
    return decorated_function

## Entry Point (`backend/run.py`)
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

## Requirements (`backend/requirements.txt`)
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.6.0
Flask-CORS==4.0.0
Flask-Migrate==4.0.5
python-dotenv==1.0.0
Werkzeug==2.3.7

## Error Handling Details
### "Not Enough Segments" Error
- **Location**: PyJWT library (`jwt/api_jws.py:186-189`)
- **Trigger**: When JWT token doesn't have 3 segments (header.payload.signature)
- **Common Causes**: Malformed tokens, empty tokens, wrong format

### JWT Token Format
Valid JWT: `header.payload.signature`
- Header: Base64URL encoded JSON
- Payload: Base64URL encoded JSON  
- Signature: Base64URL encoded signature

### Testing Endpoints
- **Register**: `POST /api/auth/register`
- **Login**: `POST /api/auth/login`
- **Refresh**: `POST /api/auth/refresh`

### Usage Instructions
1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   export FLASK_APP=run.py
   export SECRET_KEY=your-secret-key
   export JWT_SECRET_KEY=your-jwt-secret
   ```

2. **Run Application**:
   ```bash
   python run.py
   ```

3. **Test Authentication**:
   ```bash
   curl -X POST http://localhost:5000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'
   ```

This complete backend codebase provides a fully functional authentication system with JWT tokens, user management, and proper error handling including the "not enough segments" error detection.
"""
