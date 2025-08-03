from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User
import time
import logging

logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not getattr(user, 'is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Admin privileges required'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(requests_per_minute=60):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple in-memory rate limiting (use Redis in production)
            if not hasattr(current_app, '_rate_limit_store'):
                current_app._rate_limit_store = {}
            
            client_id = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            cutoff_time = current_time - 60  # 1 minute ago
            current_app._rate_limit_store = {
                k: v for k, v in current_app._rate_limit_store.items()
                if any(timestamp > cutoff_time for timestamp in v)
            }
            
            # Check rate limit
            if client_id not in current_app._rate_limit_store:
                current_app._rate_limit_store[client_id] = []
            
            # Remove old timestamps
            current_app._rate_limit_store[client_id] = [
                timestamp for timestamp in current_app._rate_limit_store[client_id]
                if timestamp > cutoff_time
            ]
            
            if len(current_app._rate_limit_store[client_id]) >= requests_per_minute:
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded'
                }), 429
            
            # Add current request
            current_app._rate_limit_store[client_id].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_api_call(f):
    """Decorator to log API calls"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            logger.info(f"API Call: {request.method} {request.path} - "
                       f"Duration: {duration:.2f}ms - Status: Success")
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"API Call: {request.method} {request.path} - "
                        f"Duration: {duration:.2f}ms - Error: {str(e)}")
            raise
            
    return decorated_function
