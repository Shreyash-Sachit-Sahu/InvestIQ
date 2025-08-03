from app import db
from app.models.portfolio import Portfolio, PortfolioHolding
from app.models.stock import NSEStock
from app.services.nse_data_service import NSEDataService
import logging

logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(self):
        self.nse_service = NSEDataService()
    
    def calculate_portfolio_value(self, portfolio_id):
        """Calculate current portfolio value"""
        try:
            holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()
            total_value = 0
            
            for holding in holdings:
                # Get current stock price
                stock_data = self.nse_service.get_stock_by_symbol(holding.stock_symbol)
                if stock_data and stock_data.get('current_price'):
                    current_price = stock_data['current_price']
                    holding.current_value = holding.quantity * current_price
                    total_value += holding.current_value
                else:
                    # Use average price if current price not available
                    holding.current_value = holding.quantity * holding.average_price
                    total_value += holding.current_value
            
            # Update portfolio total value
            portfolio = Portfolio.query.get(portfolio_id)
            if portfolio:
                portfolio.total_value = total_value
                db.session.commit()
            
            return total_value
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return 0
    
    def update_portfolio_allocations(self, portfolio_id):
        """Update allocation percentages for portfolio holdings"""
        try:
            portfolio = Portfolio.query.get(portfolio_id)
            if not portfolio or not portfolio.total_value:
                return False
            
            holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()
            
            for holding in holdings:
                if holding.current_value and portfolio.total_value:
                    allocation = (holding.current_value / portfolio.total_value) * 100
                    holding.allocation_percentage = round(allocation, 2)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating portfolio allocations: {e}")
            return False
    
    def get_portfolio_performance(self, portfolio_id):
        """Calculate portfolio performance metrics"""
        try:
            holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio_id).all()
            
            total_invested = 0
            total_current = 0
            
            for holding in holdings:
                invested = holding.quantity * holding.average_price
                current = holding.current_value or invested
                
                total_invested += invested
                total_current += current
            
            if total_invested > 0:
                total_return = total_current - total_invested
                return_percentage = (total_return / total_invested) * 100
            else:
                total_return = 0
                return_percentage = 0
            
            return {
                'total_invested': total_invested,
                'current_value': total_current,
                'total_return': total_return,
                'return_percentage': return_percentage
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance: {e}")
            return None
