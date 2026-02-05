"""
ATLAS MACRO - Explanation Generator

Produces human-readable driver list and confidence level.
Drivers are factual statements about threshold breaches.
No predictions, no narratives.
"""

from __future__ import annotations

from atlas_macro.types import Confidence, FeatureVector, MacroState, NormalizedSignals


def generate_explanation(
    state: MacroState,
    signals: NormalizedSignals,
    features: FeatureVector,
) -> tuple[list[str], Confidence]:
    """
    Generate driver list and confidence.

    Args:
        state: Classified macro state.
        signals: Normalized signals.
        features: Raw feature values for driver descriptions.

    Returns:
        (drivers: list[str], confidence: Confidence)
    """
    drivers: list[str] = []

    # Volatility drivers
    if signals.vol_stress >= 2 and features.vix_level is not None:
        pctl_str = f", percentile: {features.vix_percentile:.0f}" if features.vix_percentile is not None else ""
        drivers.append(f"VIX at crisis level: {features.vix_level:.1f}{pctl_str}")
    elif signals.vol_stress >= 1 and features.vix_level is not None:
        pctl_str = f"{features.vix_percentile:.0f}" if features.vix_percentile is not None else "N/A"
        drivers.append(f"VIX elevated: {features.vix_level:.1f} (percentile: {pctl_str} > 80)")

    # Rate stress drivers
    if signals.rate_stress >= 1 and features.tnx_vs_sma20 is not None:
        drivers.append(f"10Y yield above 20D SMA by {features.tnx_vs_sma20:+.3f}%")

    # Yield curve drivers
    if signals.yield_curve_stress >= 1 and features.yield_curve_spread is not None:
        drivers.append(
            f"Yield curve inverted: 10Y-2Y spread = {features.yield_curve_spread:+.2f}%"
        )

    # Credit spread drivers
    if signals.credit_stress >= 2 and features.credit_spread is not None:
        pctl_str = f", percentile: {features.credit_spread_percentile:.0f}" if features.credit_spread_percentile is not None else ""
        drivers.append(f"Credit spread at crisis: {features.credit_spread:.2f}{pctl_str}")
    elif signals.credit_stress >= 1 and features.credit_spread is not None:
        pctl_str = f"{features.credit_spread_percentile:.0f}" if features.credit_spread_percentile is not None else "N/A"
        drivers.append(
            f"Credit spread elevated: {features.credit_spread:.2f} (percentile: {pctl_str} > 80)"
        )

    # Correlation drivers
    if signals.correlation_stress >= 2 and features.mean_pairwise_correlation is not None:
        pctl_str = f", percentile: {features.correlation_percentile:.0f}" if features.correlation_percentile is not None else ""
        drivers.append(
            f"Cross-asset correlation crisis: {features.mean_pairwise_correlation:.3f}{pctl_str}"
        )
    elif signals.correlation_stress >= 1 and features.mean_pairwise_correlation is not None:
        pctl_str = f"{features.correlation_percentile:.0f}" if features.correlation_percentile is not None else "N/A"
        drivers.append(
            f"Cross-asset correlation elevated: {features.mean_pairwise_correlation:.3f} "
            f"(percentile: {pctl_str} > 80)"
        )

    # CALM gets a default message
    if not drivers:
        drivers.append("All metrics within normal ranges")

    confidence = _compute_confidence(signals, state)
    return drivers, confidence


def _compute_confidence(signals: NormalizedSignals, state: MacroState) -> Confidence:
    """
    Compute confidence based on data quality and signal agreement.

    HIGH: data_quality >= 0.8 AND state is unambiguous
    MEDIUM: data_quality >= 0.6
    LOW: data_quality < 0.6
    """
    if signals.data_quality < 0.6:
        return Confidence.LOW

    if signals.data_quality < 0.8:
        return Confidence.MEDIUM

    all_signals = [
        signals.vol_stress,
        signals.rate_stress,
        signals.yield_curve_stress,
        signals.credit_stress,
        signals.correlation_stress,
    ]

    if state == MacroState.CALM:
        if sum(1 for s in all_signals if s == 0) >= 4:
            return Confidence.HIGH
        return Confidence.MEDIUM

    if state == MacroState.CRISIS:
        crisis_count = sum(1 for s in all_signals if s >= 2)
        return Confidence.HIGH if crisis_count >= 2 else Confidence.MEDIUM

    # STRESSED
    stressed_count = sum(1 for s in all_signals if s >= 1)
    return Confidence.HIGH if stressed_count >= 3 else Confidence.MEDIUM
