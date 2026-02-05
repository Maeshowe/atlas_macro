"""Tests for credit spread feature engineering."""

from datetime import date

from atlas_macro.config import CreditThresholds
from atlas_macro.features.credit import compute_credit_features
from atlas_macro.types import RawMarketData


class TestComputeCreditFeatures:
    def test_none_spread(self):
        data = RawMarketData(as_of_date=date(2026, 1, 1))
        result = compute_credit_features(data, CreditThresholds())
        assert result["credit_spread"] is None
        assert result["credit_spread_percentile"] is None

    def test_spread_with_history(self):
        history = [3.0 + i * 0.05 for i in range(63)]
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            hy_spread_current=5.0,
            hy_spread_history_63d=history,
        )
        result = compute_credit_features(data, CreditThresholds())
        assert result["credit_spread"] == 5.0
        assert result["credit_spread_percentile"] is not None
        assert result["credit_spread_percentile"] > 50.0

    def test_spread_without_sufficient_history(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            hy_spread_current=4.0,
            hy_spread_history_63d=[3.5] * 5,
        )
        result = compute_credit_features(data, CreditThresholds())
        assert result["credit_spread"] == 4.0
        assert result["credit_spread_percentile"] is None

    def test_low_spread_low_percentile(self):
        history = [3.0 + i * 0.1 for i in range(63)]
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            hy_spread_current=3.0,
            hy_spread_history_63d=history,
        )
        result = compute_credit_features(data, CreditThresholds())
        assert result["credit_spread_percentile"] < 20.0
