from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.services.ml_model_services import get_ai_recommendations

ai_advisor_bp = Blueprint('ai_advisor', __name__, url_prefix='/api/ai')

@ai_advisor_bp.route('/recommend-nse', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def recommend_nse():
    try:
        preferences = request.get_json(force=True, silent=False)
    except Exception as e:
        current_app.logger.error(f"JSON parsing error: {e}")
        return jsonify({"error": "Invalid JSON payload"}), 400

    if not preferences or not isinstance(preferences, dict):
        return jsonify({"error": "Missing or invalid JSON payload"}), 400

    investment_goal = preferences.get("investment_goal")
    if not investment_goal or not isinstance(investment_goal, str) or not investment_goal.strip():
        return jsonify({"error": "'investment_goal' must be a non-empty string"}), 422

    risk_tolerance = preferences.get("risk_tolerance")
    if risk_tolerance is not None and not isinstance(risk_tolerance, str):
        return jsonify({"error": "'risk_tolerance' must be a string if provided"}), 422

    # Optional: normalize inputs here if needed

    try:
        recommendations = get_ai_recommendations(preferences)
    except Exception as e:
        current_app.logger.exception(f"Error during recommendation processing: {e}")
        return jsonify({"error": "Internal server error"}), 500

    return jsonify(recommendations), 200
