from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import jwt_required
from app.services.ml_model_services import get_ai_recommendations
from app.utils import error_response

ai_advisor_bp = Blueprint('ai_advisor', __name__, url_prefix='/api/ai')

@ai_advisor_bp.route('/recommend-nse', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def recommend_nse():
    # Handle CORS preflight OPTIONS request: allow any origin
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")  # Always allow all origins
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.status_code = 200
        return response

    # Proceed with POST request handling
    preferences = request.get_json(force=True, silent=True)
    current_app.logger.info(f"Received preferences: {preferences}")

    if not preferences:
        current_app.logger.error("Missing or invalid JSON payload")
        return jsonify({"error": "Missing or invalid JSON payload"}), 400
    if not isinstance(preferences, dict):
        current_app.logger.error(f"Payload must be a JSON object but got: {type(preferences)}")
        return jsonify({"error": "Payload must be a JSON object"}), 400

    investment_goal = preferences.get("investment_goal")
    if not investment_goal or not isinstance(investment_goal, str) or investment_goal.strip() == "":
        current_app.logger.error(f"Missing or invalid 'investment_goal': {investment_goal}")
        return jsonify({"error": "Missing or invalid 'investment_goal'"}), 400

    risk_tolerance = preferences.get("risk_tolerance")
    if risk_tolerance is not None:
        try:
            preferences["risk_tolerance"] = str(risk_tolerance).strip()
        except Exception as e:
            current_app.logger.warning(f"Could not convert risk_tolerance to string: {e}")

    try:
        recommendations = get_ai_recommendations(preferences)
    except Exception as e:
        current_app.logger.exception(f"Error during recommendation processing: {e}")
        return jsonify({"error": "Internal server error"}), 500

    if isinstance(recommendations, dict) and "error" in recommendations:
        current_app.logger.error(f"Recommendation error: {recommendations.get('error')}")
        return jsonify({"error": str(recommendations.get("error"))}), 500

    response = jsonify(recommendations)
    response.headers.add("Access-Control-Allow-Origin", "*")  # Always allow all origins
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response
