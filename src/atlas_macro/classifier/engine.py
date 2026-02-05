"""
ATLAS MACRO - Deterministic State Classifier

Rules (evaluated in order):
1. CRISIS if ANY single metric is at crisis level (signal == 2)
2. STRESSED if 2+ metrics are at stressed-or-above level (signal >= 1)
3. CALM otherwise

No hysteresis. No smoothing. Each day is independent.
"""

from __future__ import annotations

from atlas_macro.config import ClassifierConfig
from atlas_macro.types import MacroState, NormalizedSignals


def classify_state(signals: NormalizedSignals, config: ClassifierConfig) -> MacroState:
    """
    Deterministic state classification.

    Args:
        signals: Normalized stress signals (0/1/2 per metric).
        config: Classifier configuration.

    Returns:
        MacroState.CALM, MacroState.STRESSED, or MacroState.CRISIS
    """
    all_signals = [
        signals.vol_stress,
        signals.rate_stress,
        signals.yield_curve_stress,
        signals.credit_stress,
        signals.correlation_stress,
    ]

    crisis_count = sum(1 for s in all_signals if s >= 2)
    stressed_count = sum(1 for s in all_signals if s >= 1)

    # Rule 1: Any crisis signal -> CRISIS
    if crisis_count >= config.crisis_signals_required:
        return MacroState.CRISIS

    # Rule 2: 2+ stressed signals -> STRESSED
    if stressed_count >= config.stressed_signals_required:
        return MacroState.STRESSED

    # Rule 3: Otherwise CALM
    return MacroState.CALM
