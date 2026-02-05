"""Tests for feature normalization."""

from datetime import date

from atlas_macro.config import AtlasConfig
from atlas_macro.normalization.normalizer import normalize_features
from atlas_macro.types import FeatureVector


class TestNormalizeFeatures:
    def test_all_calm(self, config):
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            vix_level=14.0,
            vix_percentile=30.0,
            rate_stress=0,
            yield_curve_inverted=False,
            credit_spread=3.0,
            credit_spread_percentile=40.0,
            mean_pairwise_correlation=0.50,
            correlation_percentile=45.0,
        )
        signals = normalize_features(features, config)
        assert signals.vol_stress == 0
        assert signals.rate_stress == 0
        assert signals.yield_curve_stress == 0
        assert signals.credit_stress == 0
        assert signals.correlation_stress == 0
        assert signals.data_quality == 1.0

    def test_vix_stressed(self, config):
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            vix_level=25.0,
            vix_percentile=85.0,
        )
        signals = normalize_features(features, config)
        assert signals.vol_stress == 1

    def test_vix_crisis_by_percentile(self, config):
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            vix_level=30.0,
            vix_percentile=96.0,
        )
        signals = normalize_features(features, config)
        assert signals.vol_stress == 2

    def test_vix_crisis_by_absolute(self, config):
        """VIX >= 35 is crisis regardless of percentile."""
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            vix_level=36.0,
            vix_percentile=None,
        )
        signals = normalize_features(features, config)
        assert signals.vol_stress == 2

    def test_rate_stress_passes_through(self, config):
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            rate_stress=1,
        )
        signals = normalize_features(features, config)
        assert signals.rate_stress == 1

    def test_yield_curve_inverted(self, config):
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            yield_curve_inverted=True,
        )
        signals = normalize_features(features, config)
        assert signals.yield_curve_stress == 1

    def test_credit_crisis_absolute(self, config):
        """HY spread >= 6.0 is crisis."""
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            credit_spread=6.5,
            credit_spread_percentile=90.0,
        )
        signals = normalize_features(features, config)
        assert signals.credit_stress == 2

    def test_correlation_crisis_absolute(self, config):
        """Mean pairwise corr >= 0.85 is crisis."""
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            mean_pairwise_correlation=0.90,
            correlation_percentile=90.0,
        )
        signals = normalize_features(features, config)
        assert signals.correlation_stress == 2

    def test_data_quality_partial(self, config):
        """Only 2 of 5 metrics available."""
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            vix_level=14.0,
            rate_stress=0,
        )
        signals = normalize_features(features, config)
        assert signals.data_quality == 2 / 5

    def test_data_quality_none(self, config):
        """No metrics available."""
        features = FeatureVector(as_of_date=date(2026, 1, 1))
        signals = normalize_features(features, config)
        assert signals.data_quality == 0.0
