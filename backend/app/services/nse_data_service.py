import yfinance as yf
import json
import os
from datetime import datetime, timedelta
from app import db
from app.models.stock import NSEStock, StockPriceHistory
import logging

logger = logging.getLogger(__name__)

class NSEDataService:
    def __init__(self):
        self.nse_stocks = self._load_stock_list()
        
    def _load_stock_list(self):
        """Load NSE stock list from JSON file"""
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'nse_stocks.json')
            if os.path.exists(data_path):
                with open(data_path, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_stock_list()
        except Exception as e:
            logger.error(f"Error loading stock list: {e}")
            return self._get_default_stock_list()
    
    def _get_default_stock_list(self):
        """Return default NSE stock list"""
        return [
            {'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries Ltd', 'sector': 'Energy'},
            {'symbol': 'TCS.NS', 'name': 'Tata Consultancy Services', 'sector': 'Information Technology'},
            {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank Limited', 'sector': 'Financial Services'},
            {'symbol': 'INFY.NS', 'name': 'Infosys Limited', 'sector': 'Information Technology'},
            {'symbol': 'HINDUNILVR.NS', 'name': 'Hindustan Unilever Ltd', 'sector': 'Consumer Goods'},
            {'symbol': 'ITC.NS', 'name': 'ITC Limited', 'sector': 'Consumer Goods'},
            {'symbol': 'HDFC.NS', 'name': 'Housing Development Finance Corporation', 'sector': 'Financial Services'},
            {'symbol': 'SBIN.NS', 'name': 'State Bank of India', 'sector': 'Financial Services'},
            {'symbol': 'BHARTIARTL.NS', 'name': 'Bharti Airtel Limited', 'sector': 'Telecommunications'},
            {'symbol': 'ICICIBANK.NS', 'name': 'ICICI Bank Limited', 'sector': 'Financial Services'},
            {'symbol': 'WIPRO.NS', 'name': 'Wipro Limited', 'sector': 'Information Technology'},
            {'symbol': 'ASIANPAINT.NS', 'name': 'Asian Paints Limited', 'sector': 'Consumer Goods'},
            {'symbol': 'MARUTI.NS', 'name': 'Maruti Suzuki India Limited', 'sector': 'Automobile'},
            {'symbol': 'KOTAKBANK.NS', 'name': 'Kotak Mahindra Bank Limited', 'sector': 'Financial Services'},
            {'symbol': 'LT.NS', 'name': 'Larsen & Toubro Limited', 'sector': 'Construction'},
        ]
    
    def get_all_stocks_data(self):
        """Get all NSE stocks data"""
        try:
            # First try to get from database
            stocks = NSEStock.query.all()
            if stocks:
                return [self._convert_stock_model_to_dict(stock) for stock in stocks]
            
            # If no data in database, fetch and populate
            self.update_stock_data()
            stocks = NSEStock.query.all()
            return [self._convert_stock_model_to_dict(stock) for stock in stocks]
            
        except Exception as e:
            logger.error(f"Error getting stock data: {e}")
            return self._get_synthetic_stock_data()
    
    def _convert_stock_model_to_dict(self, stock):
        """Convert SQLAlchemy model to dictionary"""
        return {
            'symbol': stock.symbol,
            'company_name': stock.company_name,
            'sector': stock.sector,
            'market_cap': int(stock.market_cap) if stock.market_cap else None,
            'current_price': float(stock.current_price) if stock.current_price else None,
            'pe_ratio': float(stock.pe_ratio) if stock.pe_ratio else None,
            'dividend_yield': float(stock.dividend_yield) if stock.dividend_yield else None,
            'beta': float(stock.beta) if stock.beta else None
        }
    
    def update_stock_data(self):
        """Update stock data from Yahoo Finance"""
        logger.info("Updating stock data from Yahoo Finance")
        updated_count = 0
        
        for stock_info in self.nse_stocks:
            try:
                symbol = stock_info['symbol']
                # Remove .NS suffix for database storage
                db_symbol = symbol.replace('.NS', '')
                
                # Get stock data from Yahoo Finance
                stock_data = self._fetch_stock_data(symbol)
                if not stock_data:
                    continue
                
                # Update or create stock record
                stock = NSEStock.query.filter_by(symbol=db_symbol).first()
                if not stock:
                    stock = NSEStock(symbol=db_symbol)
                    db.session.add(stock)
                
                # Update stock information
                stock.company_name = stock_info['name']
                stock.sector = stock_info['sector']
                stock.current_price = stock_data.get('current_price')
                stock.market_cap = stock_data.get('market_cap')
                stock.pe_ratio = stock_data.get('pe_ratio')
                stock.dividend_yield = stock_data.get('dividend_yield')
                stock.beta = stock_data.get('beta')
                stock.last_updated = datetime.utcnow()
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Error updating stock {stock_info['symbol']}: {e}")
                continue
        
        try:
            db.session.commit()
            logger.info(f"Updated {updated_count} stocks")
        except Exception as e:
            logger.error(f"Error committing stock updates: {e}")
            db.session.rollback()
    
    def _fetch_stock_data(self, symbol):
        """Fetch stock data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant data
            stock_data = {
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
                'dividend_yield': info.get('dividendYield') * 100 if info.get('dividendYield') else None,
                'beta': info.get('beta')
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _get_synthetic_stock_data(self):
        """Generate synthetic stock data for testing"""
        logger.warning("Using synthetic stock data")
        
        synthetic_data = []
        for stock_info in self.nse_stocks[:10]:  # Use first 10 stocks
            synthetic_data.append({
                'symbol': stock_info['symbol'].replace('.NS', ''),
                'company_name': stock_info['name'],
                'sector': stock_info['sector'],
                'current_price': 1000 + (hash(stock_info['symbol']) % 2000),
                'market_cap': 100000 + (hash(stock_info['symbol']) % 1000000),
                'pe_ratio': 15 + (hash(stock_info['symbol']) % 30),
                'dividend_yield': 1 + (hash(stock_info['symbol']) % 5),
                'beta': 0.8 + (hash(stock_info['symbol']) % 80) / 100
            })
        
        return synthetic_data
    
    def get_stock_by_symbol(self, symbol):
        """Get specific stock data by symbol"""
        try:
            stock = NSEStock.query.filter_by(symbol=symbol).first()
            if stock:
                return self._convert_stock_model_to_dict(stock)
            return None
        except Exception as e:
            logger.error(f"Error getting stock {symbol}: {e}")
            return None
    
    def search_stocks(self, query):
        """Search stocks by name or symbol"""
        try:
            stocks = NSEStock.query.filter(
                db.or_(
                    NSEStock.symbol.ilike(f'%{query}%'),
                    NSEStock.company_name.ilike(f'%{query}%')
                )
            ).limit(20).all()
            
            return [self._convert_stock_model_to_dict(stock) for stock in stocks]
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
    
    def get_sectors(self):
        """Get list of all sectors"""
        try:
            result = db.session.query(NSEStock.sector).distinct().all()
            return [row[0] for row in result if row[0]]
        except Exception as e:
            logger.error(f"Error getting sectors: {e}")
            return ['Information Technology', 'Financial Services', 'Consumer Goods', 
                   'Healthcare', 'Energy', 'Automobile', 'Telecommunications']
