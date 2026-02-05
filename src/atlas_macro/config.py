"""
ATLAS MACRO - Configuration & Thresholds

Single source of truth for all numerical thresholds.
All values are named, documented, and centralized.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VolatilityThresholds:
    """VIX classification thresholds."""

    baseline_window: int = 63  # Trading days for percentile (~3 months)
    stressed_percentile: float = 80.0
    crisis_percentile: float = 95.0
    crisis_absolute: float = 35.0  # VIX >= 35 is CRISIS regardless of percentile


@dataclass(frozen=True)
class RateThresholds:
    """Rate stress thresholds."""

    sma_window: int = 20  # Trading days for SMA


@dataclass(frozen=True)
class YieldCurveThresholds:
    """Yield curve thresholds."""

    inversion_threshold: float = 0.0  # T10Y2Y < 0 means inverted


@dataclass(frozen=True)
class CreditThresholds:
    """Credit spread thresholds."""

    baseline_window: int = 63
    stressed_percentile: float = 80.0
    crisis_percentile: float = 95.0
    crisis_absolute: float = 6.0  # HY spread >= 600bps is CRISIS


@dataclass(frozen=True)
class CorrelationThresholds:
    """Correlation stress thresholds."""

    window: int = 21  # Rolling correlation window (1 month)
    history_window: int = 63  # History for percentile calc
    stressed_percentile: float = 80.0
    crisis_percentile: float = 95.0
    crisis_absolute: float = 0.85  # Mean pairwise >= 0.85 is CRISIS


@dataclass(frozen=True)
class ClassifierConfig:
    """Deterministic classifier rules."""

    crisis_signals_required: int = 1  # Any single crisis signal -> CRISIS
    stressed_signals_required: int = 2  # 2+ stressed signals -> STRESSED


@dataclass(frozen=True)
class AtlasConfig:
    """Master configuration for ATLAS MACRO."""

    volatility: VolatilityThresholds = VolatilityThresholds()
    rates: RateThresholds = RateThresholds()
    yield_curve: YieldCurveThresholds = YieldCurveThresholds()
    credit: CreditThresholds = CreditThresholds()
    correlation: CorrelationThresholds = CorrelationThresholds()
    classifier: ClassifierConfig = ClassifierConfig()
    lookback_calendar_days: int = 120  # Calendar days to fetch for 63 trading days
