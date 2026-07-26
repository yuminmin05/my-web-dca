import logging

try:
    from celery import shared_task
except ImportError:  # pragma: no cover - fallback for environments without Celery
    class _FallbackTask:
        def __init__(self, func, **kwargs):
            self.func = func
            self.__name__ = getattr(func, '__name__', 'task')
            self.__doc__ = getattr(func, '__doc__', '')

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

        def delay(self, *args, **kwargs):
            return self(*args, **kwargs)

    def shared_task(func=None, **kwargs):
        if func is None:
            return lambda f: _FallbackTask(f, **kwargs)
        return _FallbackTask(func, **kwargs)

logger = logging.getLogger(__name__)


@shared_task(retry_kwargs={"max_retries": 3, "countdown": 5})
def optimize_portfolio_task(user_plan_id):
    """Run the long-running GA optimization asynchronously and save the result as a snapshot."""
    from .ga_optimizer import run_genetic_algorithm as run_ga_optimization
    from .models import GAResultSnapshot, UserPlan
    from .services import build_dca_projection

    plan = UserPlan.objects.get(id=user_plan_id)
    assets = [symbol.strip() for symbol in plan.selected_stocks.split(',') if symbol.strip()]
    results = run_ga_optimization(assets=assets)

    projection = build_dca_projection(
        monthly_investment=plan.monthly_investment,
        duration_years=plan.duration_years,
        target_amount=plan.target_amount,
        expected_return=results.get('expected_return', 0.0),
    )

    snapshot = GAResultSnapshot.objects.create(
        user=plan.user,
        expected_return=results.get('expected_return'),
        sharpe_ratio=results.get('sharpe_ratio'),
        weights=results.get('weights'),
        monthly_investment=plan.monthly_investment,
        duration_years=plan.duration_years,
        target_amount=plan.target_amount,
        final_portfolio_value=results.get('final_portfolio_value', 0),
        chart_labels=projection['chart_labels'],
        chart_data=projection['chart_data'],
    )
    return snapshot.id
