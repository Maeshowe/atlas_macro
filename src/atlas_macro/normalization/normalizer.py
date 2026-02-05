"""
ATLAS MACRO - Feature Normalization

Converts raw feature values into discrete 0/1/2 stress signals
using configured thresholds. No async. No side effects.
"""

from __future__ import annotations

from atlas_macro.config import AtlasConfig
from atlas_macro.types import FeatureVector, NormalizedSignals


def normalize_features(features: FeatureVector, config: AtlasConfig) -> NormalizedSignals:
    """
    Convert feature vector to normalized stress signals.

    Each metric maps to a discrete stress level:
    - 0: calm / normal
    - 1: stressed / elevated
    - 2: crisis / extreme

    Args:
        features: Computed features.
        config: Thresholds configuration.

    Returns:
        NormalizedSignals with discrete stress levels and data quality.
    """
    # --- Volatility stress ---
    vol_stress = 0
    if features.vix_level is not None:
        if features.vix_level >= config.volatility.crisis_absolute:
            vol_stress = 2
        elif features.vix_percentile is not None:
            if features.vix_percentile >= config.volatility.crisis_percentile:
                vol_stress = 2
            elif features.vix_percentile >= config.volatility.stressed_percentile:
                vol_stress = 1

    # --- Rate stress (binary: 0 or 1) ---
    rate_stress_signal = 0
    if features.rate_stress is not None:
        rate_stress_signal = features.rate_stress

    # --- Yield curve stress (binary: 0 or 1) ---
    yc_stress = 0
    if features.yield_curve_inverted is True:
        yc_stress = 1

    # --- Credit stress ---
    credit_stress = 0
    if features.credit_spread is not None:
        if features.credit_spread >= config.credit.crisis_absolute:
            credit_stress = 2
        elif features.credit_spread_percentile is not None:
            if features.credit_spread_percentile >= config.credit.crisis_percentile:
                credit_stress = 2
            elif features.credit_spread_percentile >= config.credit.stressed_percentile:
                credit_stress = 1

    # --- Correlation stress ---
    corr_stress = 0
    if features.mean_pairwise_correlation is not None:
        if features.mean_pairwise_correlation >= config.correlation.crisis_absolute:
            corr_stress = 2
        elif features.correlation_percentile is not None:
            if features.correlation_percentile >= config.correlation.crisis_percentile:
                corr_stress = 2
            elif features.correlation_percentile >= config.correlation.stressed_percentile:
                corr_stress = 1

    # --- Data quality: fraction of 5 metrics available ---
    available = sum(
        1
        for check in [
            features.vix_level is not None,
            features.rate_stress is not None,
            features.yield_curve_inverted is not None,
            features.credit_spread is not None,
            features.mean_pairwise_correlation is not None,
        ]
        if check
    )

    return NormalizedSignals(
        as_of_date=features.as_of_date,
        vol_stress=vol_stress,
        rate_stress=rate_stress_signal,
        yield_curve_stress=yc_stress,
        credit_stress=credit_stress,
        correlation_stress=corr_stress,
        data_quality=available / 5,
    )
