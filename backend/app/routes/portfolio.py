from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User, Portfolio, Holding
from app.services.csv_parser import parse_portfolio_csv
from app.utils import error_response
from datetime import datetime

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

def get_default_portfolio(user):
    portfolio = Portfolio.query.filter_by(user_id=user.id, name="Default Portfolio").first()
    if not portfolio:
        portfolio = Portfolio(user_id=user.id, name="Default Portfolio")
        db.session.add(portfolio)
        db.session.commit()
    return portfolio

@portfolio_bp.route('/upload-csv', methods=['POST'])
@jwt_required()
def upload_csv():
    if 'portfolio_csv' not in request.files:
        return error_response("No CSV file uploaded as 'portfolio_csv'.", 400)
    file = request.files['portfolio_csv']
    if not (file and file.filename.endswith('.csv')):
        return error_response("File must be a CSV.", 400)

    holdings_df, errors = parse_portfolio_csv(file)
    if holdings_df is None:
        return error_response("CSV parse error.", 400, errors)

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found.", 404)
    portfolio = get_default_portfolio(user)
    imported, error_rows = 0, []

    for idx, row in holdings_df.iterrows():
        symbol = row['Symbol']
        try:
            quantity = int(row['Quantity'])
            avg_price = float(row['Average Buy Price (INR)'])
        except Exception as e:
            error_rows.append(f"Row {idx+2}: Numeric conversion error. {str(e)}")
            continue
        purchase_date = row.get('Purchase Date (YYYY-MM-DD)', None)
        if not symbol or quantity <= 0 or avg_price <= 0:
            error_rows.append(f"Row {idx+2}: Invalid data: {row.to_dict()}")
            continue
        holding = Holding.query.filter_by(portfolio_id=portfolio.id, symbol=symbol).first()
        if holding:
            total_qty = holding.quantity + quantity
            if total_qty > 0:
                holding.average_buy_price = (
                    holding.average_buy_price * holding.quantity + avg_price * quantity
                ) / total_qty
            holding.quantity = total_qty
            if purchase_date:
                holding.purchase_date = purchase_date
            holding.updated_at = datetime.utcnow()
        else:
            holding = Holding(
                portfolio_id=portfolio.id,
                symbol=symbol,
                quantity=quantity,
                average_buy_price=avg_price,
                purchase_date=purchase_date if purchase_date else None
            )
            db.session.add(holding)
        imported += 1
    db.session.commit()
    return jsonify({
        "message": "Portfolio uploaded successfully.",
        "imported_holdings_count": imported,
        "errors": errors + error_rows
    }), 200

@portfolio_bp.route('/', methods=['GET'])
@jwt_required()
def get_portfolio():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found.", 404)
    portfolio = get_default_portfolio(user)
    enriched = []
    for holding in portfolio.holdings:
        current_price = holding.average_buy_price * 1.05
        predicted_price = holding.average_buy_price * 1.10
        change = 5.0
        name = f"{holding.symbol} Ltd."
        enriched.append({
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "average_buy_price": holding.average_buy_price,
            "purchase_date": holding.purchase_date,
            "currentPrice": current_price,
            "predictedPrice": predicted_price,
            "change": change,
            "name": name,
        })
    return jsonify(enriched), 200
