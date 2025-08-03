from app import db
from datetime import datetime

class NSEStock(db.Model):
    __tablename__ = 'nse_stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    market_cap = db.Column(db.BigInteger)
    current_price = db.Column(db.Numeric(10, 2))
    pe_ratio = db.Column(db.Numeric(8, 2))
    dividend_yield = db.Column(db.Numeric(5, 2))
    beta = db.Column(db.Numeric(5, 2))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'name': self.company_name,
            'sector': self.sector,
            'marketCap': int(self.market_cap) if self.market_cap else None,
            'currentPrice': float(self.current_price) if self.current_price else None,
            'pe': float(self.pe_ratio) if self.pe_ratio else None,
            'dividend': float(self.dividend_yield) if self.dividend_yield else None,
            'beta': float(self.beta) if self.beta else None,
            'lastUpdated': self.last_updated.isoformat() if self.last_updated else None
        }

class StockPriceHistory(db.Model):
    __tablename__ = 'stock_price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), db.ForeignKey('nse_stocks.symbol'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Numeric(10, 2))
    high_price = db.Column(db.Numeric(10, 2))
    low_price = db.Column(db.Numeric(10, 2))
    close_price = db.Column(db.Numeric(10, 2))
    volume = db.Column(db.BigInteger)
    adjusted_close = db.Column(db.Numeric(10, 2))
    
    __table_args__ = (db.UniqueConstraint('symbol', 'date'),)
