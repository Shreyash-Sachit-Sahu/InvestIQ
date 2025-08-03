import numpy as np
from scipy import stats

class RiskAssessmentModel:
    def __init__(self):
        self.confidence_level = 0.95
        
    def assess_portfolio_risk(self, portfolio, market_data=None):
        """
        Assess comprehensive risk metrics for the portfolio
        
        Args:
            portfolio: List of portfolio allocations
            market_data: Historical market data (optional)
        
        Returns:
            Dictionary with risk metrics
        """
        if not portfolio:
            return self._get_default_risk_metrics()
        
        # Calculate portfolio-level risk metrics
        portfolio_risk_score = self._calculate_portfolio_risk_score(portfolio)
        diversification_score = self._calculate_diversification_score(portfolio)
        var_95 = self._calculate_value_at_risk(portfolio)
        max_drawdown = self._estimate_max_drawdown(portfolio)
        sharpe_ratio = self._estimate_sharpe_ratio(portfolio)
        
        return {
            'portfolioRiskScore': round(portfolio_risk_score, 2),
            'diversificationScore': diversification_score,
            'valueAtRisk95': round(var_95, 2),
            'maxDrawdown': round(max_drawdown, 2),
            'sharpeRatio': round(sharpe_ratio, 2),
            'riskMetrics': {
                'volatility': round(self._calculate_portfolio_volatility(portfolio), 2),
                'beta': round(self._calculate_portfolio_beta(portfolio), 2),
                'correlation': round(self._calculate_avg_correlation(portfolio), 2)
            }
        }
    
    def _calculate_portfolio_risk_score(self, portfolio):
        """Calculate weighted average risk score"""
        if not portfolio:
            return 3.0
            
        total_weighted_risk = 0
        total_weight = 0
        
        for holding in portfolio:
            weight = holding.get('allocation', 0) / 100
            risk_score = holding.get('riskScore', 3)
            total_weighted_risk += weight * risk_score
            total_weight += weight
        
        return total_weighted_risk / total_weight if total_weight > 0 else 3.0
    
    def _calculate_diversification_score(self, portfolio):
        """Calculate diversification score (1-10 scale)"""
        if not portfolio:
            return 5
            
        # Sector diversification
        sectors = {}
        for holding in portfolio:
            sector = holding.get('sector', 'Other')
            allocation = holding.get('allocation', 0)
            sectors[sector] = sectors.get(sector, 0) + allocation
        
        # Calculate Herfindahl-Hirschman Index for sectors
        hhi_sectors = sum((allocation/100)**2 for allocation in sectors.values())
        sector_diversification = max(0, (1 - hhi_sectors) * 10)
        
        # Stock count diversification
        num_stocks = len(portfolio)
        stock_diversification = min(10, num_stocks * 1.2)
        
        # Allocation concentration
        max_allocation = max(holding.get('allocation', 0) for holding in portfolio)
        concentration_penalty = max_allocation / 10 if max_allocation > 30 else 0
        
        # Combined diversification score
        diversification_score = (sector_diversification + stock_diversification) / 2 - concentration_penalty
        
        return max(1, min(10, int(round(diversification_score))))
    
    def _calculate_value_at_risk(self, portfolio, confidence_level=0.95):
        """Calculate portfolio Value at Risk (VaR)"""
        if not portfolio:
            return -15.0
        
        # Estimate portfolio volatility
        portfolio_volatility = self._calculate_portfolio_volatility(portfolio)
        
        # Calculate VaR using normal distribution assumption
        z_score = stats.norm.ppf(1 - confidence_level)  # For 95% confidence
        var_95 = z_score * portfolio_volatility * 100  # Convert to percentage
        
        return var_95
    
    def _calculate_portfolio_volatility(self, portfolio):
        """Estimate portfolio volatility"""
        if not portfolio:
            return 0.2
        
        # Weight individual stock volatilities
        portfolio_vol = 0
        
        for holding in portfolio:
            weight = holding.get('allocation', 0) / 100
            
            # Estimate stock volatility based on characteristics
            stock_vol = 0.2  # Base volatility
            
            # Adjust based on sector
            sector = holding.get('sector', '')
            sector_vol_multiplier = {
                'Information Technology': 1.25,
                'Financial Services': 1.5,
                'Healthcare': 1.0,
                'Consumer Goods': 0.9,
                'Energy': 1.75,
                'Automobile': 1.4
            }
            stock_vol *= sector_vol_multiplier.get(sector, 1.0)
            
            # Adjust based on market cap (assuming smaller = more volatile)
            market_cap = holding.get('marketCap', 100000)
            if market_cap and market_cap < 50000:  # Small cap
                stock_vol *= 1.3
            elif market_cap and market_cap > 500000:  # Large cap
                stock_vol *= 0.8
            
            portfolio_vol += (weight * stock_vol) ** 2
        
        # Add correlation benefits (simplified)
        num_stocks = len(portfolio)
        correlation_benefit = 0.8 if num_stocks > 5 else 0.9
        
        return np.sqrt(portfolio_vol) * correlation_benefit
    
    def _calculate_portfolio_beta(self, portfolio):
        """Estimate portfolio beta"""
        if not portfolio:
            return 1.0
        
        weighted_beta = 0
        total_weight = 0
        
        for holding in portfolio:
            weight = holding.get('allocation', 0) / 100
            # Use sector-based beta estimates if individual beta not available
            beta = self._estimate_stock_beta(holding)
            weighted_beta += weight * beta
            total_weight += weight
        
        return weighted_beta / total_weight if total_weight > 0 else 1.0
    
    def _estimate_stock_beta(self, holding):
        """Estimate stock beta based on sector and characteristics"""
        # Use provided beta if available
        if holding.get('beta'):
            return holding['beta']
        
        # Sector-based beta estimates
        sector_betas = {
            'Information Technology': 1.2,
            'Financial Services': 1.4,
            'Healthcare': 0.9,
            'Consumer Goods': 0.8,
            'Energy': 1.3,
            'Automobile': 1.1
        }
        
        return sector_betas.get(holding.get('sector', ''), 1.0)
    
    def _calculate_avg_correlation(self, portfolio):
        """Estimate average correlation between portfolio holdings"""
        if len(portfolio) < 2:
            return 0.0
        
        # Simplified correlation estimation based on sectors
        same_sector_pairs = 0
        total_pairs = 0
        
        for i in range(len(portfolio)):
            for j in range(i+1, len(portfolio)):
                total_pairs += 1
                if portfolio[i].get('sector') == portfolio[j].get('sector'):
                    same_sector_pairs += 1
        
        if total_pairs == 0:
            return 0.3
        
        # Higher correlation for same sector stocks
        same_sector_ratio = same_sector_pairs / total_pairs
        avg_correlation = 0.2 + (same_sector_ratio * 0.3)  # 0.2-0.5 range
        
        return avg_correlation
    
    def _estimate_max_drawdown(self, portfolio):
        """Estimate potential maximum drawdown"""
        portfolio_volatility = self._calculate_portfolio_volatility(portfolio)
        portfolio_beta = self._calculate_portfolio_beta(portfolio)
        
        # Estimate based on volatility and beta
        # Higher volatility and beta = higher potential drawdown
        base_drawdown = 15.0  # Base 15% drawdown
        volatility_adjustment = (portfolio_volatility - 0.15) * 50  # Scale volatility impact
        beta_adjustment = (portfolio_beta - 1.0) * 10  # Scale beta impact
        
        max_drawdown = base_drawdown + volatility_adjustment + beta_adjustment
        
        return max(8.0, min(35.0, max_drawdown))  # Cap between 8% and 35%
    
    def _estimate_sharpe_ratio(self, portfolio):
        """Estimate portfolio Sharpe ratio"""
        if not portfolio:
            return 1.0
        
        # Calculate expected portfolio return
        expected_return = 0
        for holding in portfolio:
            weight = holding.get('allocation', 0) / 100
            expected_return += weight * holding.get('expectedReturn', 10) / 100
        
        # Risk-free rate (assume 6% for Indian market)
        risk_free_rate = 0.06
        
        # Portfolio volatility
        portfolio_volatility = self._calculate_portfolio_volatility(portfolio)
        
        # Calculate Sharpe ratio
        if portfolio_volatility > 0:
            sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility
        else:
            sharpe_ratio = 0
        
        return max(0, min(3.0, sharpe_ratio))  # Cap between 0 and 3
    
    def _get_default_risk_metrics(self):
        """Return default risk metrics when portfolio is empty"""
        return {
            'portfolioRiskScore': 3.0,
            'diversificationScore': 5,
            'valueAtRisk95': -15.0,
            'maxDrawdown': 20.0,
            'sharpeRatio': 1.0,
            'riskMetrics': {
                'volatility': 20.0,
                'beta': 1.0,
                'correlation': 0.3
            }
        }
