from flask import Blueprint, request, jsonify, current_app
from time import time
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ml_model_services import get_ai_recommendations
from app.utils.contract_mapping import (
    make_success_response,
    make_error_response,
    yfinance_enrich,
)

ai_advisor_bp = Blueprint('ai_advisor', __name__, url_prefix='/api/ai')


@ai_advisor_bp.route('/recommend-nse', methods=['POST', 'OPTIONS'])
@jwt_required()
def recommend_nse():
    start_time = time()
    user_id = get_jwt_identity()

    if request.method == "OPTIONS":
        return '', 200

    preferences = request.get_json()
    if not preferences or not isinstance(preferences, dict):
        return jsonify(make_error_response(
            "Missing JSON payload.", user_id, int((time() - start_time) * 1000)
        )), 400

    investment_goal = preferences.get("investment_goal")
    if not investment_goal or not isinstance(investment_goal, str) or not investment_goal.strip():
        return jsonify(make_error_response(
            "Missing or invalid 'investment_goal'.", user_id, int((time() - start_time) * 1000)
        )), 422

    risk_tolerance = preferences.get("risk_tolerance")
    if risk_tolerance is not None and not isinstance(risk_tolerance, str):
        return jsonify(make_error_response(
            "'risk_tolerance' must be a string if provided.", user_id, int((time() - start_time) * 1000)
        )), 422

    try:
        engine_result = get_ai_recommendations(preferences)
    except Exception:
        current_app.logger.exception("AI recommendation error")
        return jsonify(make_error_response(
            "Internal error in AI recommendation service.", user_id, int((time() - start_time) * 1000)
        )), 500

    if isinstance(engine_result, dict) and engine_result.get("error"):
        return jsonify(make_error_response(
            engine_result.get("error"),
            user_id=user_id,
            processing_time=int((time() - start_time) * 1000)
        )), 200

    portfolio = []
    for rec in engine_result.get("portfolio", []):
        enrich = yfinance_enrich(rec["symbol"])
        portfolio.append({
            "symbol": rec["symbol"],
            "name": rec.get("name", enrich["name"]),
            "allocation": rec.get("weight", 0),
            "confidence": rec.get("confidence", 80),
            "reasoning": rec.get("reasoning", ""),
            "sector": rec.get("sector", enrich["sector"]),
            "expectedReturn": rec.get("expectedReturn", None),
            "riskScore": rec.get("riskScore", rec.get("portfolio_metrics", {}).get("risk_score", 0)),
            "currentPrice": enrich["currentPrice"],
            "marketCap": enrich["marketCap"],
            "pe": enrich["pe"],
            "dividend": enrich["dividend"],
        })

    summary = engine_result.get("summary", {})
    mapped_summary = {
        "totalExpectedReturn": summary.get("totalExpectedReturn", 0),
        "portfolioRiskScore": summary.get("portfolioRiskScore", 0),
        "diversificationScore": summary.get("diversificationScore", 0),
        "alignmentScore": summary.get("alignmentScore", 0),
    }
    insights = engine_result.get("insights", [])

    return jsonify(make_success_response(
        portfolio=portfolio,
        summary=mapped_summary,
        insights=insights,
        user_id=user_id,
        processing_time=int((time() - start_time) * 1000)
    )), 200
