"""Tests for volatility feature engineering."""

from datetime import date

import pytest

from atlas_macro.config import VolatilityThresholds
from atlas_macro.features.volatility import compute_vix_features
from atlas_macro.types import RawMarketData


class TestComputeVixFeatures:
    def test_none_vix(self):
        data = RawMarketData(as_of_date=date(2026, 1, 1), vix_current=None)
        result = compute_vix_features(data, VolatilityThresholds())
        assert result["vix_level"] is None
        assert result["vix_percentile"] is None

    def test_insufficient_history(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            vix_current=20.0,
            vix_history_63d=[15.0] * 5,
        )
        result = compute_vix_features(data, VolatilityThresholds())
        assert result["vix_level"] == 20.0
        assert result["vix_percentile"] is None

    def test_low_vix_low_percentile(self):
        history = [10.0 + i * 0.5 for i in range(63)]  # 10.0 to 41.0
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            vix_current=12.0,
            vix_history_63d=history,
        )
        result = compute_vix_features(data, VolatilityThresholds())
        assert result["vix_level"] == 12.0
        assert result["vix_percentile"] < 20.0

    def test_high_vix_high_percentile(self):
        history = [10.0 + i * 0.3 for i in range(63)]  # 10.0 to 28.6
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            vix_current=28.0,
            vix_history_63d=history,
        )
        result = compute_vix_features(data, VolatilityThresholds())
        assert result["vix_level"] == 28.0
        assert result["vix_percentile"] > 80.0

    def test_vix_at_maximum(self):
        history = [15.0] * 63
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            vix_current=15.0,
            vix_history_63d=history,
        )
        result = compute_vix_features(data, VolatilityThresholds())
        assert result["vix_percentile"] == 100.0
