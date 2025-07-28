from flask import Blueprint, request, jsonify,current_app
from flask_jwt_extended import jwt_required
from app.services.ml_model_services import get_ai_recommendations
from app.utils import error_response

ai_advisor_bp = Blueprint('ai_advisor', __name__, url_prefix='/api/ai')

@ai_advisor_bp.route('/recommend-nse', methods=['POST'])
@jwt_required()
def recommend_nse():
    data = request.get_json(force=True, silent=True)
    current_app.logger.info(f"Received request data for /recommend-nse: {data}")

    if not data:
        current_app.logger.error("Missing or invalid JSON payload")
        return jsonify({"error": "Missing or invalid JSON payload"}), 400

    if not isinstance(data, dict):
        current_app.logger.error(f"Payload is not a JSON object: {type(data)}")
        return jsonify({"error": "Payload must be a JSON object"}), 400

    investment_goal = data.get("investment_goal")
    if not investment_goal or not isinstance(investment_goal, str) or not investment_goal.strip():
        current_app.logger.error(f"Missing or invalid 'investment_goal': {investment_goal}")
        return jsonify({"error": "Missing or invalid 'investment_goal'"}), 400

    try:
        recs = get_ai_recommendations(data)
    except FileNotFoundError as e:
        current_app.logger.error(f"File not found error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        current_app.logger.exception(f"ML model error: {e}")
        return jsonify({"error": f"ML model error: {str(e)}"}), 500

    if isinstance(recs, dict) and "error" in recs:
        err_msg = recs.get("error")
        current_app.logger.error(f"Recommendation error: {err_msg}")
        return jsonify({"error": str(err_msg)}), 500

    return jsonify(recs), 200