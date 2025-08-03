from app import db
from datetime import datetime

class Portfolio(db.Model):
    __tablename__ = 'user_portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    total_value = db.Column(db.Numeric(15, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    holdings = db.relationship('PortfolioHolding', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'totalValue': float(self.total_value) if self.total_value else 0,
            'holdings': [holding.to_dict() for holding in self.holdings],
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }

class PortfolioHolding(db.Model):
    __tablename__ = 'portfolio_holdings'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('user_portfolios.id'), nullable=False)
    stock_symbol = db.Column(db.String(20), db.ForeignKey('nse_stocks.symbol'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)
    current_value = db.Column(db.Numeric(15, 2))
    allocation_percentage = db.Column(db.Numeric(5, 2))
    
    def to_dict(self):
        return {
            'symbol': self.stock_symbol,
            'quantity': self.quantity,
            'averagePrice': float(self.average_price),
            'currentValue': float(self.current_value) if self.current_value else 0,
            'allocation': float(self.allocation_percentage) if self.allocation_percentage else 0
        }
