import yfinance as yf
import json
import os
import time
import random
from datetime import datetime, timedelta
from app import db
from app.models.stock import NSEStock, StockPriceHistory
import logging

logger = logging.getLogger(__name__)

class NSEDataService:
    def __init__(self):
        self.nse_stocks = self._load_stock_list()
        self.base_delay = 2.0       # per-symbol delay (seconds)
        self.batch_size = 12        # number of stocks per batch
        self.batch_sleep = 20       # seconds between batches
        self.max_retries = 3

    def _load_stock_list(self):
        """Load NSE stock list from JSON file — now always loads full file."""
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'nse_stocks.json')
            if os.path.exists(data_path):
                with open(data_path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} stocks from nse_stocks.json")
                    return data   # FULL list now
            else:
                raise FileNotFoundError(f"{data_path} not found!")
        except Exception as e:
            logger.error(f"Error loading stock list: {e}")
            return []  # No fallback list

    def test_api_connection(self):
        """Test yfinance connection."""
        try:
            logger.info("Testing yfinance connection...")
            ticker = yf.Ticker("RELIANCE.NS")
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                return {
                    'success': True,
                    'message': 'yfinance connection successful',
                    'test_data': {
                        'symbol': 'RELIANCE.NS',
                        'name': 'Reliance Industries',
                        'price': round(current_price, 2)
                    }
                }
            return {
                'success': False,
                'error': 'No data received from yfinance',
                'troubleshooting': [
                    'Yahoo Finance may be temporarily unavailable',
                    'Try again in 10-15 minutes',
                    'Check internet connection'
                ]
            }
        except Exception as e:
            if "429" in str(e):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded (429 error)',
                    'troubleshooting': [
                        'Yahoo Finance is rate limiting requests',
                        'Wait 15-30 minutes before trying again',
                        'Reduce the number of stocks being processed',
                        'Consider using bulk data requests'
                    ]
                }
            return {
                'success': False,
                'error': f'Connection failed: {str(e)}',
                'troubleshooting': [
                    'Check internet connection',
                    'Try again later',
                    'Yahoo Finance may be temporarily down'
                ]
            }

    def update_stock_data(self):
        """Update stock data in batches to avoid rate limits."""
        if not self.nse_stocks:
            logger.error("No stocks loaded to update!")
            return

        logger.info(f"🚀 Starting update for {len(self.nse_stocks)} stocks using {self.batch_size} per batch...")

        updated_count = failed_count = rate_limited_count = 0
        start_time = datetime.now()

        for batch_start in range(0, len(self.nse_stocks), self.batch_size):
            batch = self.nse_stocks[batch_start: batch_start + self.batch_size]
            logger.info(f"📦 Batch {batch_start//self.batch_size + 1} — Processing {len(batch)} stocks")

            for i, stock_info in enumerate(batch):
                symbol = stock_info['symbol']

                # Delay before request
                if i > 0:
                    delay = self.base_delay + random.uniform(0.5, 1.5)
                    time.sleep(delay)

                # Attempt fetch
                stock_data = self._fetch_with_retries(symbol)

                if stock_data:
                    if self._save_stock_data(symbol, stock_info, stock_data):
                        updated_count += 1
                        logger.info(f"✅ Updated {symbol}: ₹{stock_data.get('current_price', 'N/A')}")
                    else:
                        failed_count += 1
                elif stock_data is False:
                    rate_limited_count += 1
                    logger.warning(f"⚠️ Rate limit hit for {symbol}")
                    if rate_limited_count >= 3:
                        logger.error("Too many rate limit errors — stopping update")
                        return
                else:
                    failed_count += 1

                # Commit every 5 successful updates
                if updated_count > 0 and updated_count % 5 == 0:
                    db.session.commit()
                    logger.info(f"💾 Committed progress — {updated_count} updated")

            # End of batch sleep
            logger.info(f"⏳ Sleeping {self.batch_sleep}s between batches...")
            time.sleep(self.batch_sleep)

        # Final commit
        try:
            db.session.commit()
            elapsed = datetime.now() - start_time
            logger.info(f"🎉 Update finished in {elapsed.total_seconds()/60:.1f} mins — {updated_count} updated, {failed_count} failed")
        except Exception as e:
            logger.error(f"Final commit error: {e}")
            db.session.rollback()

    def _fetch_with_retries(self, symbol):
        """Fetch stock data with retry logic."""
        for attempt in range(self.max_retries):
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                hist = ticker.history(period="1d")
                if hist.empty:
                    return None
                current_price = hist['Close'].iloc[-1]

                # Additional info (optional)
                additional_data = {}
                try:
                    info = ticker.info
                    if info and len(info) > 1:
                        additional_data = {
                            'market_cap': self._safe_extract(info, 'marketCap'),
                            'pe_ratio': self._safe_extract(info, ['trailingPE', 'forwardPE']),
                            'dividend_yield': self._calculate_dividend_yield(info, current_price),
                            'beta': self._safe_extract(info, 'beta'),
                            'company_name': info.get('longName', info.get('shortName', '')),
                            'sector': info.get('sector', '')
                        }
                except Exception as info_error:
                    logger.debug(f"⚠️ Could not get info for {symbol}: {info_error}")

                return {'current_price': round(float(current_price), 2), **additional_data}

            except Exception as e:
                if "429" in str(e):
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Rate limited for {symbol}, attempt {attempt+1}, waiting {wait_time}s...")
                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    return False
                else:
                    logger.debug(f"Error fetching {symbol} on attempt {attempt+1}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(5)
                        continue
        return None

    def _safe_extract(self, info, keys):
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            try:
                value = info.get(key)
                if value is not None and isinstance(value, (int, float)) and str(value).lower() not in ['nan', 'none']:
                    return float(value)
            except:
                continue
        return None

    def _calculate_dividend_yield(self, info, current_price):
        try:
            div_rate = info.get('dividendRate')
            if div_rate and current_price:
                return round((div_rate / current_price) * 100, 2)
            div_yield = info.get('dividendYield')
            if div_yield:
                return round(div_yield * 100, 2)
        except:
            pass
        return None

    def _save_stock_data(self, symbol, stock_info, stock_data):
        try:
            db_symbol = symbol.upper()
            stock = NSEStock.query.filter_by(symbol=db_symbol).first()
            if not stock:
                stock = NSEStock(symbol=db_symbol)
                db.session.add(stock)

            stock.company_name = stock_data.get('company_name') or stock_info['name']
            stock.sector = stock_data.get('sector') or stock_info['sector']
            stock.current_price = stock_data.get('current_price')
            stock.market_cap = stock_data.get('market_cap')
            stock.pe_ratio = stock_data.get('pe_ratio')
            stock.dividend_yield = stock_data.get('dividend_yield')
            stock.beta = stock_data.get('beta')
            stock.last_updated = datetime.utcnow()
            return True
        except Exception as e:
            logger.error(f"Error saving data for {symbol}: {e}")
            return False

    def get_all_stocks_data(self):
        try:
            stocks = NSEStock.query.all()
            if stocks and len(stocks) > 3:
                return [self._convert_stock_model_to_dict(stock) for stock in stocks]
            self.update_stock_data()
            stocks = NSEStock.query.all()
            return [self._convert_stock_model_to_dict(stock) for stock in stocks]
        except Exception as e:
            logger.error(f"Error in get_all_stocks_data: {e}")
            return []

    def _convert_stock_model_to_dict(self, stock):
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

    def get_stock_by_symbol(self, symbol):
        try:
            stock = NSEStock.query.filter_by(symbol=symbol.upper()).first()
            if stock:
                return self._convert_stock_model_to_dict(stock)
            return None
        except Exception as e:
            logger.error(f"Error getting stock {symbol}: {e}")
            return None

    def search_stocks(self, query):
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
        try:
            result = db.session.query(NSEStock.sector).distinct().all()
            return [row for row in result if row]
        except Exception as e:
            logger.error(f"Error getting sectors: {e}")
            return ['Information Technology', 'Financial Services', 'Consumer Goods',
                    'Healthcare', 'Energy', 'Automobile', 'Telecommunications', 'Construction']

    def get_api_usage_stats(self):
        try:
            stocks_updated_today = NSEStock.query.filter(
                NSEStock.last_updated >= datetime.utcnow().date()
            ).count()
            total_stocks = NSEStock.query.count()
            return {
                'stocks_updated_today': stocks_updated_today,
                'total_stocks_in_db': total_stocks,
                'daily_limit': 'Yahoo Finance Rate Limited',
                'api_provider': f'yfinance {yf.__version__}',
                'last_update': datetime.now().isoformat(),
                'status': 'OK' if total_stocks > 0 else 'NO_DATA'
            }
        except Exception as e:
            logger.error(f"Error getting API stats: {e}")
            return {'error': str(e)}
