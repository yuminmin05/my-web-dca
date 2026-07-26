from abc import ABC, abstractmethod


class BaseOptimizer(ABC):
    """Base interface for portfolio optimization strategies."""

    @abstractmethod
    def optimize(self, stocks, target_amount):
        raise NotImplementedError("Subclasses must implement optimize()")
