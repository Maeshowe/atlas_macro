"""Shared fixtures for ATLAS MACRO tests."""

import sys
from datetime import date
from pathlib import Path

import pytest

# Ensure atlas_macro is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from atlas_macro.config import AtlasConfig
from atlas_macro.types import FeatureVector, NormalizedSignals, RawMarketData


@pytest.fixture
def config() -> AtlasConfig:
    return AtlasConfig()


@pytest.fixture
def calm_raw_data() -> RawMarketData:
    """Raw data representing calm market conditions."""
    # Use alternating offsets to break perfect correlation between indices
    import math

    spy = [450.0 + math.sin(i * 0.5) * 3.0 + i * 0.1 for i in range(63)]
    qqq = [380.0 + math.cos(i * 0.7) * 4.0 + i * 0.05 for i in range(63)]
    iwm = [200.0 + math.sin(i * 0.3 + 1.0) * 2.0 - i * 0.02 for i in range(63)]
    dia = [350.0 + math.cos(i * 0.4 + 2.0) * 3.5 + i * 0.08 for i in range(63)]

    return RawMarketData(
        as_of_date=date(2026, 1, 15),
        vix_current=14.0,
        vix_history_63d=[12.0 + i * 0.1 for i in range(63)],
        tnx_current=4.10,
        tnx_history_20d=[4.20] * 20,  # SMA = 4.20, current 4.10 < SMA -> rate_stress=0
        t10y2y_current=0.45,
        hy_spread_current=3.5,
        hy_spread_history_63d=[3.2 + i * 0.01 for i in range(63)],
        spy_prices=spy,
        qqq_prices=qqq,
        iwm_prices=iwm,
        dia_prices=dia,
    )


@pytest.fixture
def stressed_raw_data() -> RawMarketData:
    """Raw data representing stressed market conditions."""
    return RawMarketData(
        as_of_date=date(2026, 1, 15),
        vix_current=28.0,
        vix_history_63d=[15.0 + i * 0.15 for i in range(63)],
        tnx_current=4.60,
        tnx_history_20d=[4.40 + i * 0.005 for i in range(20)],  # Ascending, current > SMA
        t10y2y_current=-0.15,
        hy_spread_current=4.8,
        hy_spread_history_63d=[3.5 + i * 0.02 for i in range(63)],
        spy_prices=[450.0 - i * 0.8 for i in range(63)],
        qqq_prices=[380.0 - i * 0.7 for i in range(63)],
        iwm_prices=[200.0 - i * 0.5 for i in range(63)],
        dia_prices=[350.0 - i * 0.6 for i in range(63)],
    )


@pytest.fixture
def crisis_raw_data() -> RawMarketData:
    """Raw data representing crisis market conditions."""
    return RawMarketData(
        as_of_date=date(2026, 1, 15),
        vix_current=42.0,
        vix_history_63d=[14.0 + i * 0.2 for i in range(63)],
        tnx_current=4.80,
        tnx_history_20d=[4.50 + i * 0.01 for i in range(20)],
        t10y2y_current=-0.50,
        hy_spread_current=7.5,
        hy_spread_history_63d=[3.0 + i * 0.05 for i in range(63)],
        spy_prices=[450.0 - i * 2.0 for i in range(63)],
        qqq_prices=[380.0 - i * 2.0 for i in range(63)],
        iwm_prices=[200.0 - i * 1.5 for i in range(63)],
        dia_prices=[350.0 - i * 1.8 for i in range(63)],
    )


@pytest.fixture
def calm_features() -> FeatureVector:
    return FeatureVector(
        as_of_date=date(2026, 1, 15),
        vix_level=14.0,
        vix_percentile=30.0,
        rate_stress=0,
        tnx_vs_sma20=-0.05,
        yield_curve_spread=0.45,
        yield_curve_inverted=False,
        credit_spread=3.5,
        credit_spread_percentile=40.0,
        mean_pairwise_correlation=0.55,
        correlation_percentile=45.0,
    )


@pytest.fixture
def stressed_features() -> FeatureVector:
    return FeatureVector(
        as_of_date=date(2026, 1, 15),
        vix_level=28.0,
        vix_percentile=85.0,
        rate_stress=1,
        tnx_vs_sma20=0.15,
        yield_curve_spread=-0.15,
        yield_curve_inverted=True,
        credit_spread=4.8,
        credit_spread_percentile=75.0,
        mean_pairwise_correlation=0.70,
        correlation_percentile=72.0,
    )


@pytest.fixture
def calm_signals() -> NormalizedSignals:
    return NormalizedSignals(
        as_of_date=date(2026, 1, 15),
        vol_stress=0,
        rate_stress=0,
        yield_curve_stress=0,
        credit_stress=0,
        correlation_stress=0,
        data_quality=1.0,
    )


@pytest.fixture
def stressed_signals() -> NormalizedSignals:
    return NormalizedSignals(
        as_of_date=date(2026, 1, 15),
        vol_stress=1,
        rate_stress=1,
        yield_curve_stress=1,
        credit_stress=0,
        correlation_stress=0,
        data_quality=1.0,
    )


@pytest.fixture
def crisis_signals() -> NormalizedSignals:
    return NormalizedSignals(
        as_of_date=date(2026, 1, 15),
        vol_stress=2,
        rate_stress=1,
        yield_curve_stress=1,
        credit_stress=2,
        correlation_stress=1,
        data_quality=1.0,
    )
