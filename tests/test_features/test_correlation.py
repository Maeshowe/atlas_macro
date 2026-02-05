"""Tests for correlation feature engineering."""

import math
from datetime import date

from atlas_macro.config import CorrelationThresholds
from atlas_macro.features.correlation import (
    _pearson,
    compute_correlation_features,
)
from atlas_macro.types import RawMarketData


class TestPearson:
    def test_perfect_positive(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        assert abs(_pearson(x, y) - 1.0) < 1e-10

    def test_perfect_negative(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        assert abs(_pearson(x, y) - (-1.0)) < 1e-10

    def test_no_correlation(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 1.0, 4.0, 2.0, 3.0]
        corr = _pearson(x, y)
        assert corr is not None
        assert abs(corr) < 0.5

    def test_too_few_points(self):
        assert _pearson([1.0, 2.0], [3.0, 4.0]) is None

    def test_constant_returns_none(self):
        assert _pearson([1.0, 1.0, 1.0, 1.0], [1.0, 2.0, 3.0, 4.0]) is None


class TestComputeCorrelationFeatures:
    def test_insufficient_data(self):
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            spy_prices=[100.0] * 5,
        )
        result = compute_correlation_features(data, CorrelationThresholds())
        assert result["mean_pairwise_correlation"] is None
        assert result["correlation_percentile"] is None

    def test_correlated_markets(self):
        """Strongly trending markets should show high correlation."""
        n = 63
        base = [100.0 + i * 1.0 for i in range(n)]
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            spy_prices=base,
            qqq_prices=[p * 0.9 for p in base],
            iwm_prices=[p * 0.5 for p in base],
            dia_prices=[p * 0.8 for p in base],
        )
        result = compute_correlation_features(data, CorrelationThresholds())
        assert result["mean_pairwise_correlation"] is not None
        assert result["mean_pairwise_correlation"] > 0.8

    def test_only_two_series(self):
        """Should still compute with only 2 valid series."""
        n = 63
        data = RawMarketData(
            as_of_date=date(2026, 1, 1),
            spy_prices=[100.0 + i for i in range(n)],
            qqq_prices=[80.0 + i * 0.9 for i in range(n)],
            iwm_prices=[],
            dia_prices=[],
        )
        result = compute_correlation_features(data, CorrelationThresholds())
        assert result["mean_pairwise_correlation"] is not None
