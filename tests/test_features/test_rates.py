"""Tests for rate stress feature engineering."""

from datetime import date

import pytest

from atlas_macro.config import RateThresholds, YieldCurveThresholds
from atlas_macro.features.rates import compute_rate_features
from atlas_macro.types import RawMarketData


class TestComputeRateFeatures:
    def test_tnx_above_sma(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            tnx_current=4.50,
            tnx_history_20d=[4.30] * 20,
        )
        result = compute_rate_features(data, RateThresholds(), YieldCurveThresholds())
        assert result["rate_stress"] == 1
        assert result["tnx_vs_sma20"] > 0

    def test_tnx_below_sma(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            tnx_current=4.10,
            tnx_history_20d=[4.30] * 20,
        )
        result = compute_rate_features(data, RateThresholds(), YieldCurveThresholds())
        assert result["rate_stress"] == 0
        assert result["tnx_vs_sma20"] < 0

    def test_insufficient_history(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            tnx_current=4.50,
            tnx_history_20d=[4.30] * 10,
        )
        result = compute_rate_features(data, RateThresholds(), YieldCurveThresholds())
        assert result["rate_stress"] is None

    def test_yield_curve_inverted(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            t10y2y_current=-0.25,
        )
        result = compute_rate_features(data, RateThresholds(), YieldCurveThresholds())
        assert result["yield_curve_inverted"] is True
        assert result["yield_curve_spread"] == -0.25

    def test_yield_curve_normal(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            t10y2y_current=0.50,
        )
        result = compute_rate_features(data, RateThresholds(), YieldCurveThresholds())
        assert result["yield_curve_inverted"] is False

    def test_missing_data_returns_none(self):
        data = RawMarketData(as_of_date=date(2026, 1, 1))
        result = compute_rate_features(data, RateThresholds(), YieldCurveThresholds())
        assert result["rate_stress"] is None
        assert result["yield_curve_inverted"] is None
