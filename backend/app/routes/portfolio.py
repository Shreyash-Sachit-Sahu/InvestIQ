from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.portfolio import Portfolio, PortfolioHolding
from app.models.stock import NSEStock
from app.services.portfolio_service import PortfolioService
import logging
import csv
from io import StringIO

logger = logging.getLogger(__name__)

portfolio_bp = Blueprint('portfolio', __name__)
portfolio_service = PortfolioService()

@portfolio_bp.route('/', methods=['GET'])
@jwt_required()
def get_portfolios():
    try:
        user_id = get_jwt_identity()
        portfolios = Portfolio.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'success': True,
            'data': [portfolio.to_dict() for portfolio in portfolios]
        })
        
    except Exception as e:
        logger.error(f"Get portfolios error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch portfolios'
        }), 500

@portfolio_bp.route('/', methods=['POST'])
@jwt_required()
def create_portfolio():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'message': 'Portfolio name is required'
            }), 400
        
        portfolio = Portfolio(
            user_id=user_id,
            name=data['name'],
            total_value=0
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': portfolio.to_dict(),
            'message': 'Portfolio created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Create portfolio error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to create portfolio'
        }), 500

@portfolio_bp.route('/<int:portfolio_id>', methods=['PUT'])
@jwt_required()
def update_portfolio(portfolio_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'message': 'Portfolio not found'
            }), 404
        
        if 'name' in data:
            portfolio.name = data['name']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': portfolio.to_dict(),
            'message': 'Portfolio updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Update portfolio error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to update portfolio'
        }), 500

@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio(portfolio_id):
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'message': 'Portfolio not found'
            }), 404
        
        db.session.delete(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete portfolio error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to delete portfolio'
        }), 500

@portfolio_bp.route('/import-csv', methods=['POST'])
@jwt_required()
def import_csv():
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        portfolio_name = request.form.get('portfolio_name', 'Imported Portfolio')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        # Create portfolio
        portfolio = Portfolio(
            user_id=user_id,
            name=portfolio_name,
            total_value=0
        )
        db.session.add(portfolio)
        db.session.flush()  # Get portfolio ID
        
        total_value = 0
        holdings_created = 0
        
        for row in csv_reader:
            try:
                symbol = row.get('symbol', '').upper()
                quantity = int(row.get('quantity', 0))
                avg_price = float(row.get('average_price', 0))
                
                if not symbol or quantity <= 0 or avg_price <= 0:
                    continue
                
                # Check if stock exists
                stock = NSEStock.query.filter_by(symbol=symbol).first()
                if not stock:
                    continue
                
                current_value = quantity * avg_price
                total_value += current_value
                
                holding = PortfolioHolding(
                    portfolio_id=portfolio.id,
                    stock_symbol=symbol,
                    quantity=quantity,
                    average_price=avg_price,
                    current_value=current_value
                )
                
                db.session.add(holding)
                holdings_created += 1
                
            except (ValueError, KeyError):
                continue
        
        portfolio.total_value = total_value
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio': portfolio.to_dict(),
                'holdings_imported': holdings_created
            },
            'message': f'Portfolio imported successfully with {holdings_created} holdings'
        })
        
    except Exception as e:
        logger.error(f"Import CSV error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to import portfolio'
        }), 500
