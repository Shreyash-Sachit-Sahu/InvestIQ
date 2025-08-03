import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

class PortfolioOptimizer:
    def __init__(self):
        self.risk_aversion = 1.0
        self.min_weight = 0.01  # Minimum 1% allocation
        self.max_weight = 0.3   # Maximum 30% allocation per stock
        
    def optimize_portfolio(self, stock_scores, user_preferences, max_stocks=10):
        """
        Optimize portfolio allocation using Modern Portfolio Theory
        
        Args:
            stock_scores: List of scored stocks
            user_preferences: User risk tolerance and preferences
            max_stocks: Maximum number of stocks in portfolio
        """
        if not stock_scores or len(stock_scores) == 0:
            return self._get_default_portfolio()
            
        # Select top stocks based on scores
        top_stocks = stock_scores[:max_stocks]
        n_stocks = len(top_stocks)
        
        if n_stocks == 0:
            return self._get_default_portfolio()
        
        # Extract expected returns and create covariance matrix
        expected_returns = np.array([stock['score'] for stock in top_stocks])
        
        # Create synthetic covariance matrix (in real implementation, use historical data)
        covariance_matrix = self._create_covariance_matrix(top_stocks)
        
        # Adjust risk aversion based on user risk tolerance
        risk_tolerance = user_preferences.get('risk_tolerance', 2)  # 1=conservative, 2=moderate, 3=aggressive
        self.risk_aversion = {1: 3.0, 2: 1.0, 3: 0.3}[risk_tolerance]
        
        # Optimize weights
        weights = self._mean_variance_optimization(expected_returns, covariance_matrix, n_stocks)
        
        # Create portfolio allocation
        portfolio = []
        total_allocation = 0
        
        for i, stock in enumerate(top_stocks):
            allocation = weights[i] * 100  # Convert to percentage
            if allocation >= 1.0:  # Only include if allocation is at least 1%
                portfolio_item = {
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'allocation': round(allocation, 1),
                    'confidence': min(95, max(60, int(stock['score'] * 100 + 50))),
                    'reasoning': self._generate_reasoning(stock, allocation, user_preferences),
                    'sector': stock['sector'],
                    'expectedReturn': round(max(8, min(20, stock['score'] * 100 + 10)), 1),
                    'riskScore': self._calculate_risk_score(stock, user_preferences),
                    'currentPrice': stock['current_price'],
                    'marketCap': stock['market_cap'],
                    'pe': stock['pe_ratio'],
                    'dividend': stock['dividend_yield']
                }
                portfolio.append(portfolio_item)
                total_allocation += allocation
        
        # Normalize allocations to sum to 100%
        if total_allocation > 0:
            for item in portfolio:
                item['allocation'] = round((item['allocation'] / total_allocation) * 100, 1)
        
        return portfolio[:8]  # Return top 8 stocks maximum
    
    def _create_covariance_matrix(self, stocks):
        """Create a synthetic covariance matrix based on stock characteristics"""
        n = len(stocks)
        
        # Base volatilities based on sector and market cap
        volatilities = []
        for stock in stocks:
            base_vol = 0.2  # 20% base volatility
            
            # Adjust based on sector
            sector_vol = {
                'Information Technology': 0.25,
                'Financial Services': 0.3,
                'Healthcare': 0.2,
                'Consumer Goods': 0.18,
                'Energy': 0.35,
                'Automobile': 0.28
            }
            vol = sector_vol.get(stock.get('sector'), base_vol)
            
            # Adjust based on market cap (smaller = more volatile)
            if stock.get('market_cap'):
                if stock['market_cap'] > 500000:  # Large cap
                    vol *= 0.8
                elif stock['market_cap'] < 50000:  # Small cap
                    vol *= 1.3
            
            volatilities.append(vol)
        
        # Create correlation matrix
        correlations = np.eye(n)
        for i in range(n):
            for j in range(i+1, n):
                # Higher correlation for same sector stocks
                if stocks[i].get('sector') == stocks[j].get('sector'):
                    corr = np.random.uniform(0.3, 0.6)
                else:
                    corr = np.random.uniform(0.1, 0.3)
                correlations[i, j] = correlations[j, i] = corr
        
        # Convert to covariance matrix
        vol_matrix = np.outer(volatilities, volatilities)
        covariance_matrix = correlations * vol_matrix
        
        return covariance_matrix
    
    def _mean_variance_optimization(self, expected_returns, covariance_matrix, n_stocks):
        """Perform mean-variance optimization"""
        
        # Objective function: maximize return - risk_aversion * variance
        def objective(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))
            return -(portfolio_return - self.risk_aversion * portfolio_variance)
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        ]
        
        # Bounds for each weight
        bounds = [(self.min_weight, self.max_weight) for _ in range(n_stocks)]
        
        # Initial guess (equal weights)
        initial_weights = np.array([1.0/n_stocks] * n_stocks)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            return result.x
        else:
            # Fall back to equal weights
            return initial_weights
    
    def _calculate_risk_score(self, stock, user_preferences):
        """Calculate risk score for a stock (1-5 scale)"""
        base_risk = 3.0
        
        # Adjust based on beta
        if stock.get('beta'):
            if stock['beta'] > 1.5:
                base_risk += 1
            elif stock['beta'] < 0.8:
                base_risk -= 0.5
        
        # Adjust based on sector
        sector_risk = {
            'Information Technology': 3.5,
            'Financial Services': 4.0,
            'Healthcare': 2.5,
            'Consumer Goods': 2.0,
            'Energy': 4.5,
            'Automobile': 3.5
        }
        sector_adjustment = sector_risk.get(stock.get('sector'), 3.0) - 3.0
        base_risk += sector_adjustment
        
        return max(1, min(5, int(round(base_risk))))
    
    def _generate_reasoning(self, stock, allocation, user_preferences):
        """Generate reasoning for stock selection"""
        reasons = []
        
        if stock['score'] > 0.1:
            reasons.append("Strong fundamental and technical indicators")
        
        if allocation > 15:
            reasons.append("High conviction pick with excellent risk-adjusted returns")
        elif allocation > 10:
            reasons.append("Solid investment opportunity with good growth potential")
        else:
            reasons.append("Diversification play with stable outlook")
        
        # Sector-specific reasoning
        sector_reasoning = {
            'Information Technology': "benefits from digital transformation trends",
            'Financial Services': "positioned well in the growing economy",
            'Healthcare': "defensive sector with consistent demand",
            'Consumer Goods': "stable demand and strong brand presence",
            'Energy': "potential beneficiary of commodity price cycles",
            'Automobile': "growth potential in emerging markets"
        }
        
        if stock.get('sector') in sector_reasoning:
            reasons.append(sector_reasoning[stock['sector']])
        
        return '. '.join(reasons[:2])  # Return first 2 reasons
    
    def _get_default_portfolio(self):
        """Return a default portfolio when optimization fails"""
        return [
            {
                'symbol': 'RELIANCE',
                'name': 'Reliance Industries Ltd',
                'allocation': 20.0,
                'confidence': 85,
                'reasoning': 'Market leader with diversified business model',
                'sector': 'Energy',
                'expectedReturn': 12.0,
                'riskScore': 3,
                'currentPrice': 2456.30,
                'marketCap': 1658420,
                'pe': 15.2,
                'dividend': 2.1
            },
            {
                'symbol': 'TCS',
                'name': 'Tata Consultancy Services',
                'allocation': 18.0,
                'confidence': 88,
                'reasoning': 'Leading IT services company with global presence',
                'sector': 'Information Technology',
                'expectedReturn': 14.0,
                'riskScore': 3,
                'currentPrice': 3245.60,
                'marketCap': 1235680,
                'pe': 22.5,
                'dividend': 1.8
            }
        ]
