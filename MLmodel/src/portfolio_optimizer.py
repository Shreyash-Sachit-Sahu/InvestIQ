import numpy as np
import pandas as pd
from scipy.optimize import minimize

class PortfolioOptimizer:
    def __init__(self, stock_data, config):
        self.stock_data = stock_data
        self.config = config
        self.returns_data = self._calculate_returns()

    def _calculate_returns(self):
        returns = pd.DataFrame()
        for symbol, data in self.stock_data.items():
            returns[symbol] = data['Close'].pct_change()
        return returns.dropna()

    def calculate_portfolio_metrics(self, weights):
        rets = self.returns_data
        port_return = np.sum(rets.mean() * weights) * 252
        port_vol = np.sqrt(np.dot(weights.T, np.dot(rets.cov() * 252, weights)))
        sharpe = (port_return - self.config.risk_free_rate) / port_vol
        return port_return, port_vol, sharpe

    def optimize_all_strategies(self):
        portfolios = {}
        n_assets = len(self.returns_data.columns)
        initial = np.array([1/n_assets] * n_assets)
        bounds = tuple((0, 1) for _ in range(n_assets))
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        def neg_sharpe(w): return -self.calculate_portfolio_metrics(w)[2]
        def port_variance(w): return np.dot(w.T, np.dot(self.returns_data.cov() * 252, w))
        res = minimize(neg_sharpe, initial, bounds=bounds, constraints=constraints)
        ms = res.x
        mr, mv, msharpe = self.calculate_portfolio_metrics(ms)
        portfolios['Max Sharpe'] = {
            'weights': ms, 'return': mr, 'volatility': mv, 'sharpe_ratio': msharpe
        }
        res2 = minimize(port_variance, initial, bounds=bounds, constraints=constraints)
        mvw = res2.x
        pvr, pvv, pvsharpe = self.calculate_portfolio_metrics(mvw)
        portfolios['Min Variance'] = {
            'weights': mvw, 'return': pvr, 'volatility': pvv, 'sharpe_ratio': pvsharpe
        }
        vol = self.returns_data.std() * np.sqrt(252)
        invvol = 1/vol
        rp_w = invvol / np.sum(invvol)
        rpr, rpv, rps = self.calculate_portfolio_metrics(rp_w)
        portfolios['Risk Parity'] = {
            'weights': rp_w, 'return': rpr, 'volatility': rpv, 'sharpe_ratio': rps
        }
        ew = np.array([1/n_assets] * n_assets)
        ewr, ewv, ews = self.calculate_portfolio_metrics(ew)
        portfolios['Equal Weight'] = {
            'weights': ew, 'return': ewr, 'volatility': ewv, 'sharpe_ratio': ews
        }
        return portfolios
