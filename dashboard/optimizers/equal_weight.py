import logging

import numpy as np
import yfinance as yf

from .base import BaseOptimizer

logger = logging.getLogger(__name__)


class EqualWeightOptimizer(BaseOptimizer):
    """Simple baseline optimizer that distributes weight evenly across stocks."""

    def optimize(self, stocks, target_amount):
        if not stocks:
            return {'expected_return': 0.0, 'sharpe_ratio': 0.0, 'weights': {}}

        assets = [stock.symbol if hasattr(stock, 'symbol') else str(stock) for stock in stocks]
        if len(assets) == 1:
            return {'expected_return': 0.0, 'sharpe_ratio': 0.0, 'weights': {assets[0]: 1.0}}

        weight_per_stock = 1.0 / len(assets)
        weights = {symbol: weight_per_stock for symbol in assets}

        try:
            tickers = [f"{symbol}.BK" for symbol in assets]
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

            expected_return = float(np.dot(mean_returns, np.array(list(weights.values()))))
            volatility = float(np.sqrt(np.dot(np.array(list(weights.values())).T, np.dot(cov_matrix, np.array(list(weights.values()))))))
            sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0.0
            return {'expected_return': expected_return, 'sharpe_ratio': sharpe_ratio, 'weights': weights}
        except Exception:
            logger.exception('Equal weight optimizer failed, falling back to zero metrics')
            return {'expected_return': 0.0, 'sharpe_ratio': 0.0, 'weights': weights}
