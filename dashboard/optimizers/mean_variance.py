import logging

import numpy as np
import yfinance as yf

from .base import BaseOptimizer

logger = logging.getLogger(__name__)


class MeanVarianceOptimizer(BaseOptimizer):
    """Mean-variance optimizer using a closed-form tangency portfolio."""

    def optimize(self, stocks, target_amount=None):
        if not stocks:
            return {'expected_return': 0.0, 'sharpe_ratio': 0.0, 'weights': {}}

        assets = [stock.symbol if hasattr(stock, 'symbol') else str(stock) for stock in stocks]
        if len(assets) == 1:
            return {'expected_return': 0.0, 'sharpe_ratio': 0.0, 'weights': {assets[0]: 1.0}}

        try:
            tickers = [f"{s}.BK" for s in assets]
            data = yf.download(tickers, period='3y', progress=False)['Close']
            if data.empty:
                raise ValueError('No price data returned')

            if isinstance(data, np.ndarray):
                data = data.reshape(-1, 1)

            if len(data.shape) == 1:
                data = data.to_frame()

            data = data.ffill().dropna()
            if data.empty:
                raise ValueError('No valid price data after cleanup')

            returns = data.pct_change().dropna()
            mean_returns = returns.mean().values * 252
            cov_matrix = returns.cov().values * 252
            risk_free_rate = 0.02

            covariance_inv = np.linalg.inv(cov_matrix)
            excess_returns = mean_returns - risk_free_rate
            weights = covariance_inv.dot(excess_returns)
            weights = np.clip(weights, 0.0, None)

            weight_sum = weights.sum()
            if weight_sum <= 0:
                weights = np.ones(len(assets)) / len(assets)
            else:
                weights = weights / weight_sum

            weights_dict = {assets[i]: float(weights[i]) for i in range(len(assets))}
            expected_return = float(np.dot(mean_returns, weights))
            volatility = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))
            sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0.0
            return {'expected_return': expected_return, 'sharpe_ratio': sharpe_ratio, 'weights': weights_dict}
        except Exception:
            logger.exception('Mean variance optimizer failed, falling back to equal weights')
            equal_weight = 1.0 / len(assets)
            return {
                'expected_return': 0.0,
                'sharpe_ratio': 0.0,
                'weights': {symbol: equal_weight for symbol in assets},
            }
