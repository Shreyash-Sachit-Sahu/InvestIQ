import json
import os
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def format_currency(amount, currency="₹"):
    """Format amount as currency"""
    try:
        if amount is None:
            return f"{currency}0.00"
        
        # Handle large numbers with appropriate suffixes
        if amount >= 10000000:  # 1 crore
            return f"{currency}{amount/10000000:.2f}Cr"
        elif amount >= 100000:  # 1 lakh
            return f"{currency}{amount/100000:.2f}L"
        elif amount >= 1000:  # 1 thousand
            return f"{currency}{amount/1000:.2f}K"
        else:
            return f"{currency}{amount:.2f}"
            
    except (ValueError, TypeError):
        return f"{currency}0.00"

def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    try:
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return ((new_value - old_value) / old_value) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0

def normalize_stock_symbol(symbol):
    """Normalize stock symbol (remove .NS suffix for NSE stocks)"""
    if not symbol:
        return ""
    
    return symbol.upper().replace('.NS', '')

def get_risk_level_name(risk_score):
    """Convert numeric risk score to descriptive name"""
    if risk_score <= 2:
        return "Low Risk"
    elif risk_score <= 3:
        return "Moderate Risk"
    elif risk_score <= 4:
        return "High Risk"
    else:
        return "Very High Risk"

def get_file_size(filepath):
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

def create_error_response(message, code=400, details=None):
    """Create standardized error response"""
    response = {
        'success': False,
        'message': message
    }
    
    if details:
        response['details'] = details
    
    return response, code

def create_success_response(data=None, message="Success"):
    """Create standardized success response"""
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return response

def load_json_file(filepath, default=None):
    """Safely load JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load JSON file {filepath}: {e}")
        return default or {}

def save_json_file(data, filepath):
    """Safely save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=json_serial)
        return True
    except Exception as e:
        logger.error(f"Could not save JSON file {filepath}: {e}")
        return False

def get_sector_color(sector):
    """Get color code for sector visualization"""
    sector_colors = {
        'Information Technology': '#007acc',
        'Financial Services': '#28a745',
        'Consumer Goods': '#ffc107',
        'Healthcare': '#dc3545',
        'Energy': '#fd7e14',
        'Automobile': '#6610f2',
        'Telecommunications': '#20c997',
        'Construction': '#6f42c1',
        'Real Estate': '#e83e8c'
    }
    
    return sector_colors.get(sector, '#6c757d')  # Default gray color

def calculate_sharpe_ratio(returns, risk_free_rate=0.06):
    """Calculate Sharpe ratio"""
    try:
        if not returns or len(returns) == 0:
            return 0.0
        
        import numpy as np
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns)
        
    except Exception as e:
        logger.error(f"Error calculating Sharpe ratio: {e}")
        return 0.0
