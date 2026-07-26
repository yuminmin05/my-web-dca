from decimal import Decimal
from typing import List, Dict, Any, Optional


def normalize_selected_stocks(value: str) -> List[str]:
    """Normalize selected stock symbols from form input."""
    if not value:
        return []
    return [item.strip().upper() for item in value.split(',') if item and item.strip()]


def build_dca_projection(monthly_investment: Decimal, duration_years: int, target_amount: Decimal, expected_return: float) -> Dict[str, Any]:
    """Build yearly projection for a DCA plan using the provided expected return."""
    monthly_rate = expected_return / 12
    monthly_inv = float(monthly_investment)
    duration_months = int(duration_years) * 12

    chart_labels = []
    chart_data = []
    current_value = 0.0
    achievement_month = None
    target_amount_value = float(target_amount)

    for month in range(1, duration_months + 1):
        current_value = (current_value + monthly_inv) * (1 + monthly_rate)
        if achievement_month is None and current_value >= target_amount_value:
            achievement_month = month
        if month % 12 == 0 or month == duration_months:
            chart_labels.append(f"ปีที่ {month // 12}")
            chart_data.append(round(current_value, 2))

    is_target_reached = current_value >= target_amount_value
    if achievement_month is not None:
        achievement_year = ((achievement_month - 1) // 12) + 1
        achievement_quarter = ((achievement_month - 1) // 3) + 1
        target_message = f"คาดว่าจะบรรลุเป้าหมายในปีที่ {achievement_year} (ไตรมาสที่ {achievement_quarter})"
    else:
        target_message = "คาดว่าจะไม่ถึงเป้าหมายภายในระยะเวลาที่กำหนด"

    return {
        "duration_months": duration_months,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "final_portfolio_value": round(current_value, 2),
        "is_target_reached": is_target_reached,
        "target_message": target_message,
    }


def build_saved_ga_summary(snapshot: Any, selected_assets: List[str], current_return: float, current_sharpe: float) -> Optional[Dict[str, Any]]:
    """Build a display-safe summary for a saved GA snapshot only when the stock set matches."""
    if snapshot is None:
        return None

    weights = snapshot.weights or {}
    snapshot_stocks = set(weights.keys())
    selected_stocks = set(selected_assets)

    if snapshot_stocks != selected_stocks:
        return None

    processed_allocations = []
    other_pct = 0.0
    other_count = 0

    sorted_allocations = sorted(weights.items(), key=lambda item: float(item[1]), reverse=True)
    for stock, pct in sorted_allocations:
        pct_value = float(pct) * 100
        if pct_value < 1.0:
            other_pct += pct_value
            other_count += 1
        else:
            processed_allocations.append({"name": stock, "pct": round(pct_value, 2)})

    if other_count > 0:
        processed_allocations.append({"name": f"อื่นๆ ({other_count} หุ้น)", "pct": round(other_pct, 2)})

    return {
        "timestamp": snapshot.saved_at,
        "allocations": processed_allocations,
        "expected_return": snapshot.expected_return,
        "sharpe_ratio": snapshot.sharpe_ratio,
        "return_diff": round(current_return - (snapshot.expected_return * 100 if snapshot.expected_return is not None else 0), 2),
        "sharpe_diff": round(current_sharpe - (snapshot.sharpe_ratio or 0), 2),
    }
