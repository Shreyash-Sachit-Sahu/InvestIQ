from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models import db, User
from app.utils import error_response
import re
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask_login import logout_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

def is_valid_password(password):
    # Password policy: 8+ chars, upper, lower, digit, special
    return (len(password) >= 8 and re.search(r'[A-Z]', password)
            and re.search(r'[a-z]', password)
            and re.search(r'\d', password)
            and re.search(r'\W', password))

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return error_response("Missing JSON payload.", 400)
    email = data.get('email')
    password = data.get('password')
    if not email or not re.match(EMAIL_REGEX, email):
        return error_response("Invalid or missing email.", 400)
    if not password or not is_valid_password(password):
        return error_response("Password must be 8+ chars with upper, lower, digit, special.", 400)
    user = User(email=email)
    user.set_password(password)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("User with this email already exists.", 409)
    return jsonify({"message": "Registered successfully."}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return error_response("Missing JSON payload.", 400)
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return error_response("Invalid email or password.", 401)
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # If using flask-login
    logout_user()
    
    # Or if using session directly; clear session data
    session.clear()

    # Optionally also clear tokens server-side if applicable

    return jsonify({"message": "Logged out successfully"}), 200

