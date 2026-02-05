"""
ATLAS MACRO - Credit Spread Feature Engineering

Computes HY spread level and percentile rank against 63-day baseline.
"""

from __future__ import annotations

from atlas_macro.config import CreditThresholds
from atlas_macro.types import RawMarketData


def compute_credit_features(
    data: RawMarketData,
    thresholds: CreditThresholds,
) -> dict:
    """
    Compute credit spread stress features.

    Args:
        data: Raw market data with hy_spread_current and hy_spread_history_63d.
        thresholds: Credit configuration.

    Returns:
        {"credit_spread": float|None, "credit_spread_percentile": float|None}
    """
    if data.hy_spread_current is None:
        return {"credit_spread": None, "credit_spread_percentile": None}

    history = data.hy_spread_history_63d
    percentile = None
    if history and len(history) >= 10:
        count_below = sum(1 for v in history if v <= data.hy_spread_current)
        percentile = round((count_below / len(history)) * 100.0, 1)

    return {
        "credit_spread": data.hy_spread_current,
        "credit_spread_percentile": percentile,
    }
