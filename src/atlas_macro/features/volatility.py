"""
ATLAS MACRO - Volatility Feature Engineering

Computes VIX level and percentile rank against 63-day baseline.
"""

from __future__ import annotations

from atlas_macro.config import VolatilityThresholds
from atlas_macro.types import RawMarketData


def compute_vix_features(
    data: RawMarketData,
    thresholds: VolatilityThresholds,
) -> dict:
    """
    Compute VIX level and percentile.

    Percentile = fraction of 63-day history values <= current VIX.

    Args:
        data: Raw market data with vix_current and vix_history_63d.
        thresholds: Volatility configuration.

    Returns:
        {"vix_level": float|None, "vix_percentile": float|None}
    """
    if data.vix_current is None:
        return {"vix_level": None, "vix_percentile": None}

    history = data.vix_history_63d
    if not history or len(history) < 10:
        return {"vix_level": data.vix_current, "vix_percentile": None}

    count_below = sum(1 for v in history if v <= data.vix_current)
    percentile = (count_below / len(history)) * 100.0

    return {
        "vix_level": data.vix_current,
        "vix_percentile": round(percentile, 1),
    }
