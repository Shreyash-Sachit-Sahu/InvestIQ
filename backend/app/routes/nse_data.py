from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils import error_response
from datetime import datetime, timedelta
import random

nse_data_bp = Blueprint('nse_data', __name__, url_prefix='/api/nse')

MOCK_STOCKS = {
    "RELIANCE": {"name": "Reliance Industries", "sector": "Oil & Gas", "currentPrice": 2600},
    "TCS": {"name": "Tata Consultancy Services", "sector": "IT", "currentPrice": 3700},
    # Add more as needed
}

@nse_data_bp.route('/stock/<symbol>', methods=['GET'])
@jwt_required()
def get_stock(symbol):
    symbol = symbol.upper()
    stock = MOCK_STOCKS.get(symbol)
    if not stock:
        return error_response(f"Symbol '{symbol}' not found.", 404)
    return jsonify({
        "symbol": symbol,
        "name": stock["name"],
        "currentPrice": stock["currentPrice"],
        "sector": stock["sector"]
    }), 200

@nse_data_bp.route('/historical/<symbol>', methods=['GET'])
@jwt_required()
def get_historical(symbol):
    symbol = symbol.upper()
    stock = MOCK_STOCKS.get(symbol)
    if not stock:
        return error_response(f"Symbol '{symbol}' not found.", 404)
    today = datetime.today()
    labels = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(364, -1, -1)]
    base = stock["currentPrice"]
    datasets = [{"label": symbol, "data": [round(base * random.uniform(0.9, 1.1), 2) for _ in labels]}]
    return jsonify({"labels": labels, "datasets": datasets}), 200
