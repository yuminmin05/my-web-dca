from .base import BaseOptimizer


class EqualWeightOptimizer(BaseOptimizer):
    """Simple baseline optimizer that distributes weight evenly across stocks."""

    def optimize(self, stocks, target_amount):
        if not stocks:
            return {}

        weight_per_stock = 1.0 / len(stocks)
        return {stock.symbol if hasattr(stock, 'symbol') else str(stock): weight_per_stock for stock in stocks}
