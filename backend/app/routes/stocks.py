from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.services.nse_data_service import NSEDataService
import logging

logger = logging.getLogger(__name__)

stocks_bp = Blueprint('stocks', __name__)
nse_service = NSEDataService()

@stocks_bp.route('/nse', methods=['GET'])
@jwt_required()
def get_nse_stocks():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        sector = request.args.get('sector')
        
        # Get all stocks
        stocks = nse_service.get_all_stocks_data()
        
        # Filter by sector if provided
        if sector:
            stocks = [stock for stock in stocks if stock.get('sector') == sector]
        
        # Implement simple pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_stocks = stocks[start_idx:end_idx]
        
        total_stocks = len(stocks)
        total_pages = (total_stocks + per_page - 1) // per_page
        
        return jsonify({
            'success': True,
            'data': {
                'stocks': paginated_stocks,
                'pagination': {
                    'page': page,
                    'pages': total_pages,
                    'per_page': per_page,
                    'total': total_stocks
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Get NSE stocks error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch NSE stocks'
        }), 500

@stocks_bp.route('/nse/<symbol>', methods=['GET'])
@jwt_required()
def get_nse_stock(symbol):
    try:
        stock = nse_service.get_stock_by_symbol(symbol.upper())
        
        if not stock:
            return jsonify({
                'success': False,
                'message': 'Stock not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stock
        })
        
    except Exception as e:
        logger.error(f"Get NSE stock error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch stock data'
        }), 500

@stocks_bp.route('/sectors', methods=['GET'])
@jwt_required()
def get_sectors():
    try:
        sectors = nse_service.get_sectors()
        
        return jsonify({
            'success': True,
            'data': sectors
        })
        
    except Exception as e:
        logger.error(f"Get sectors error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch sectors'
        }), 500

@stocks_bp.route('/search', methods=['GET'])
@jwt_required()
def search_stocks():
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'message': 'Search query must be at least 2 characters'
            }), 400
        
        results = nse_service.search_stocks(query)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Search stocks error: {e}")
        return jsonify({
            'success': False,
            'message': 'Search failed'
        }), 500
