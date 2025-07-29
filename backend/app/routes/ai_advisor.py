from flask import Blueprint, request, jsonify, current_app
from app.services.ml_model_services import get_ai_recommendations
from app.utils import error_response

ai_advisor_bp = Blueprint('ai_advisor', __name__, url_prefix='/api/ai')

@ai_advisor_bp.route('/recommend-nse', methods=['POST', 'OPTIONS'])
def recommend_nse():
    # Handle preflight OPTIONS early
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json()
    if not data:
        return error_response("Missing JSON payload.", 400)

    investment_goal = data.get('investment_goal')
    if not investment_goal or not isinstance(investment_goal, str) or not investment_goal.strip():
        return error_response("Invalid or missing 'investment_goal'.", 422)

    risk_tolerance = data.get('risk_tolerance')
    if risk_tolerance is not None and not isinstance(risk_tolerance, str):
        return error_response("'risk_tolerance' must be a string if provided.", 422)

    preferences = {
        'investment_goal': investment_goal,
        'risk_tolerance': risk_tolerance,
    }

    try:
        recommendations = get_ai_recommendations(preferences)
    except Exception as e:
        current_app.logger.exception(f"Failed to generate recommendations: {e}")
        return error_response("Internal server error during recommendation processing.", 500)

    if isinstance(recommendations, dict) and 'error' in recommendations:
        return error_response(str(recommendations['error']), 500)

    return jsonify(recommendations), 200
