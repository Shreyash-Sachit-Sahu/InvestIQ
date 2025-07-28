from flask import Blueprint, request, jsonify,current_app
from flask_jwt_extended import jwt_required
from app.services.ml_model_services import get_ai_recommendations
from app.utils import error_response

ai_advisor_bp = Blueprint('ai_advisor', __name__, url_prefix='/api/ai')

@ai_advisor_bp.route('/recommend-nse', methods=['POST'])
@jwt_required()
def recommend_nse():
    preferences = request.get_json(force=True, silent=True)
    current_app.logger.info(f"Received preferences: {preferences}")

    if not preferences:
        return jsonify({"error": "Missing or invalid JSON payload"}), 400
    if not isinstance(preferences, dict):
        return jsonify({"error": "Payload must be a JSON object"}), 400
    investment_goal = preferences.get("investment_goal")
    if not investment_goal or not isinstance(investment_goal, str) or investment_goal.strip() == "":
        return jsonify({"error": "Missing or invalid 'investment_goal'"}), 400

    try:
        recommendations = get_ai_recommendations(preferences)
    except Exception as e:
        current_app.logger.error(f"Error during recommendation: {e}")
        return jsonify({"error": "Internal server error"}), 500

    if isinstance(recommendations, dict) and "error" in recommendations:
        return jsonify({"error": str(recommendations.get("error"))}), 500

    return jsonify(recommendations)