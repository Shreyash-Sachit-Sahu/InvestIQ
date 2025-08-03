import re
from email_validator import validate_email as email_validate, EmailNotValidError

def validate_email(email):
    """Validate email format"""
    try:
        email_validate(email)
        return True
    except:
        # Fallback to regex validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False
    return True

def validate_user_preferences(preferences):
    """Validate user investment preferences"""
    if not isinstance(preferences, dict):
        return False
    
    required_fields = ['investment_amount', 'risk_tolerance', 'primary_goal']
    
    # Check required fields
    for field in required_fields:
        if field not in preferences:
            return False
    
    # Validate investment amount
    try:
        amount = float(preferences['investment_amount'])
        if amount <= 0:
            return False
    except (ValueError, TypeError):
        return False
    
    # Validate risk tolerance
    risk_tolerance = preferences.get('risk_tolerance')
    if risk_tolerance not in [1, 2, 3]:
        return False
    
    # Validate primary goal
    valid_goals = ['growth', 'income', 'balanced', 'preservation']
    if preferences.get('primary_goal') not in valid_goals:
        return False
    
    return True
