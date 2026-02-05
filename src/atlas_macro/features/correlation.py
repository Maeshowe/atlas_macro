"""
ATLAS MACRO - Cross-Asset Correlation Feature Engineering

Computes rolling mean pairwise correlation between SPY/QQQ/IWM/DIA.
Uses pure Python math (no numpy dependency).
"""

from __future__ import annotations

import math

from atlas_macro.config import CorrelationThresholds
from atlas_macro.types import RawMarketData


def compute_correlation_features(
    data: RawMarketData,
    thresholds: CorrelationThresholds,
) -> dict:
    """
    Compute rolling pairwise correlation between index ETFs.

    Uses log returns for correlation calculation.
    Rolling window = 21 days, percentile computed over 63-day history.

    Args:
        data: Raw market data with index prices.
        thresholds: Correlation configuration.

    Returns:
        {
            "mean_pairwise_correlation": float|None,
            "correlation_percentile": float|None,
        }
    """
    prices = {
        "SPY": data.spy_prices,
        "QQQ": data.qqq_prices,
        "IWM": data.iwm_prices,
        "DIA": data.dia_prices,
    }

    # Need at least window+1 prices for log returns over the window
    min_len = thresholds.window + 1
    valid_series = {k: v for k, v in prices.items() if len(v) >= min_len}

    if len(valid_series) < 2:
        return {"mean_pairwise_correlation": None, "correlation_percentile": None}

    # Compute log returns
    returns = {k: _log_returns(v) for k, v in valid_series.items()}

    # Trim to common length
    min_return_len = min(len(r) for r in returns.values())
    returns = {k: v[-min_return_len:] for k, v in returns.items()}

    if min_return_len < thresholds.window:
        return {"mean_pairwise_correlation": None, "correlation_percentile": None}

    # Current rolling correlation (last `window` returns)
    tickers = list(returns.keys())
    current_corr = _mean_pairwise_corr(
        {k: returns[k][-thresholds.window :] for k in tickers}
    )

    # Rolling history of mean correlations for percentile calc
    history_len = min(min_return_len, thresholds.history_window + thresholds.window)
    corr_history = []
    for end_idx in range(thresholds.window, history_len + 1):
        start_idx = end_idx - thresholds.window
        window_returns = {k: returns[k][start_idx:end_idx] for k in tickers}
        corr_history.append(_mean_pairwise_corr(window_returns))

    percentile = None
    if corr_history and current_corr is not None:
        valid_history = [c for c in corr_history if c is not None]
        if valid_history:
            count_below = sum(1 for c in valid_history if c <= current_corr)
            percentile = round((count_below / len(valid_history)) * 100.0, 1)

    return {
        "mean_pairwise_correlation": round(current_corr, 4) if current_corr is not None else None,
        "correlation_percentile": percentile,
    }


def _log_returns(prices: list[float]) -> list[float]:
    """Compute log returns from price series."""
    return [
        math.log(prices[i] / prices[i - 1])
        for i in range(1, len(prices))
        if prices[i - 1] > 0 and prices[i] > 0
    ]


def _mean_pairwise_corr(returns_dict: dict[str, list[float]]) -> float | None:
    """Compute mean Pearson correlation across all pairs."""
    tickers = list(returns_dict.keys())
    correlations = []
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            corr = _pearson(returns_dict[tickers[i]], returns_dict[tickers[j]])
            if corr is not None:
                correlations.append(corr)
    if not correlations:
        return None
    return sum(correlations) / len(correlations)


def _pearson(x: list[float], y: list[float]) -> float | None:
    """Pearson correlation coefficient. Pure Python, no numpy."""
    n = len(x)
    if n < 3 or n != len(y):
        return None
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    denom = (var_x * var_y) ** 0.5
    if denom == 0:
        return None
    return cov / denom
