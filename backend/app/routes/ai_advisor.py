from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.ml_model_services import get_ai_recommendations
from app.utils import error_response

ai_advisor_bp = Blueprint('ai_advisor', __name__, url_prefix='/api/ai')

@ai_advisor_bp.route('/recommend-nse', methods=['POST'])
@jwt_required()
def recommend_nse():
    data = request.get_json()
    # TODO: Add strong validation for preferences as needed
    try:
        recs = get_ai_recommendations(data)
    except FileNotFoundError as e:
        return error_response(str(e), 500)
    except Exception as e:
        return error_response(f"ML model error: {str(e)}", 500)
    return jsonify(recs), 200
