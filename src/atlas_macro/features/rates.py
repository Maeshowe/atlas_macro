"""
ATLAS MACRO - Rate Stress Feature Engineering

Computes:
- RateStress_t = 1{TNX_t > SMA_20(TNX)}
- Yield curve inversion detection (T10Y2Y)
"""

from __future__ import annotations

from atlas_macro.config import RateThresholds, YieldCurveThresholds
from atlas_macro.types import RawMarketData


def compute_rate_features(
    data: RawMarketData,
    rate_thresholds: RateThresholds,
    yc_thresholds: YieldCurveThresholds,
) -> dict:
    """
    Compute rate stress and yield curve features.

    Args:
        data: Raw market data.
        rate_thresholds: Rate configuration.
        yc_thresholds: Yield curve configuration.

    Returns:
        {
            "rate_stress": 0|1|None,
            "tnx_vs_sma20": float|None,
            "yield_curve_spread": float|None,
            "yield_curve_inverted": bool|None,
        }
    """
    result: dict = {
        "rate_stress": None,
        "tnx_vs_sma20": None,
        "yield_curve_spread": None,
        "yield_curve_inverted": None,
    }

    # Rate stress: TNX vs SMA_20
    if data.tnx_current is not None and len(data.tnx_history_20d) >= rate_thresholds.sma_window:
        window = data.tnx_history_20d[-rate_thresholds.sma_window :]
        sma_20 = sum(window) / len(window)
        result["rate_stress"] = 1 if data.tnx_current > sma_20 else 0
        result["tnx_vs_sma20"] = round(data.tnx_current - sma_20, 4)

    # Yield curve
    if data.t10y2y_current is not None:
        result["yield_curve_spread"] = data.t10y2y_current
        result["yield_curve_inverted"] = data.t10y2y_current < yc_thresholds.inversion_threshold

    return result
