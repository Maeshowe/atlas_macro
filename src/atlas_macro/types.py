"""
ATLAS MACRO - Core Type Definitions

All dataclasses and enums used across the system.
No logic, only data structures.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class MacroState(Enum):
    """Discrete macro states. No numeric score."""

    CALM = "CALM"
    STRESSED = "STRESSED"
    CRISIS = "CRISIS"


class Confidence(Enum):
    """Confidence in state classification."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class RawMarketData:
    """Raw data from ingest layer. Immutable."""

    as_of_date: date
    # VIX
    vix_current: Optional[float] = None
    vix_history_63d: list[float] = field(default_factory=list)
    # Rates
    tnx_current: Optional[float] = None
    tnx_history_20d: list[float] = field(default_factory=list)
    # Yield curve
    t10y2y_current: Optional[float] = None
    # Credit spreads
    hy_spread_current: Optional[float] = None
    hy_spread_history_63d: list[float] = field(default_factory=list)
    # Index prices for correlation (closing prices, 63 trading days)
    spy_prices: list[float] = field(default_factory=list)
    qqq_prices: list[float] = field(default_factory=list)
    iwm_prices: list[float] = field(default_factory=list)
    dia_prices: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class FeatureVector:
    """Computed features from raw data."""

    as_of_date: date
    vix_level: Optional[float] = None
    vix_percentile: Optional[float] = None
    rate_stress: Optional[int] = None
    tnx_vs_sma20: Optional[float] = None
    yield_curve_spread: Optional[float] = None
    yield_curve_inverted: Optional[bool] = None
    credit_spread: Optional[float] = None
    credit_spread_percentile: Optional[float] = None
    mean_pairwise_correlation: Optional[float] = None
    correlation_percentile: Optional[float] = None


@dataclass(frozen=True)
class NormalizedSignals:
    """Binary/categorical stress signals after normalization."""

    as_of_date: date
    vol_stress: int = 0  # 0=calm, 1=stressed, 2=crisis
    rate_stress: int = 0  # 0=calm, 1=stressed
    yield_curve_stress: int = 0  # 0=normal, 1=inverted
    credit_stress: int = 0  # 0=calm, 1=stressed, 2=crisis
    correlation_stress: int = 0  # 0=calm, 1=stressed, 2=crisis
    data_quality: float = 1.0  # fraction of metrics available (0-1)


@dataclass(frozen=True)
class MacroResult:
    """Final ATLAS output."""

    date: date
    macro_state: MacroState
    drivers: list[str]
    confidence: Confidence
    signals: NormalizedSignals
    features: FeatureVector

    def to_dict(self) -> dict:
        """Serialize to output JSON format."""
        return {
            "date": self.date.isoformat(),
            "macro_state": self.macro_state.value,
            "drivers": self.drivers,
            "confidence": self.confidence.value,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
