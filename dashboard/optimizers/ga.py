from .base import BaseOptimizer
from ..ga_optimizer import run_genetic_algorithm


class GAOptimizer(BaseOptimizer):
    """Genetic algorithm based optimizer."""

    def optimize(self, stocks, target_amount):
        assets = [stock.symbol if hasattr(stock, 'symbol') else str(stock) for stock in stocks]
        return run_genetic_algorithm(assets=assets)
