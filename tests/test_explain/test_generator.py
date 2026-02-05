"""Tests for the explanation generator."""

from datetime import date

from atlas_macro.explain.generator import generate_explanation
from atlas_macro.types import Confidence, FeatureVector, MacroState, NormalizedSignals


class TestGenerateExplanation:
    def test_calm_default_message(self):
        signals = NormalizedSignals(as_of_date=date(2026, 1, 1), data_quality=1.0)
        features = FeatureVector(as_of_date=date(2026, 1, 1))
        drivers, confidence = generate_explanation(MacroState.CALM, signals, features)
        assert "All metrics within normal ranges" in drivers

    def test_vix_stressed_driver(self):
        signals = NormalizedSignals(
            as_of_date=date(2026, 1, 1), vol_stress=1, data_quality=1.0
        )
        features = FeatureVector(
            as_of_date=date(2026, 1, 1), vix_level=25.0, vix_percentile=85.0
        )
        drivers, _ = generate_explanation(MacroState.STRESSED, signals, features)
        assert any("VIX elevated" in d for d in drivers)

    def test_vix_crisis_driver(self):
        signals = NormalizedSignals(
            as_of_date=date(2026, 1, 1), vol_stress=2, data_quality=1.0
        )
        features = FeatureVector(
            as_of_date=date(2026, 1, 1), vix_level=40.0, vix_percentile=98.0
        )
        drivers, _ = generate_explanation(MacroState.CRISIS, signals, features)
        assert any("crisis" in d.lower() for d in drivers)

    def test_rate_stress_driver(self):
        signals = NormalizedSignals(
            as_of_date=date(2026, 1, 1), rate_stress=1, data_quality=1.0
        )
        features = FeatureVector(
            as_of_date=date(2026, 1, 1), tnx_vs_sma20=0.15
        )
        drivers, _ = generate_explanation(MacroState.STRESSED, signals, features)
        assert any("10Y yield above 20D SMA" in d for d in drivers)

    def test_yield_curve_driver(self):
        signals = NormalizedSignals(
            as_of_date=date(2026, 1, 1), yield_curve_stress=1, data_quality=1.0
        )
        features = FeatureVector(
            as_of_date=date(2026, 1, 1), yield_curve_spread=-0.25
        )
        drivers, _ = generate_explanation(MacroState.STRESSED, signals, features)
        assert any("Yield curve inverted" in d for d in drivers)

    def test_confidence_high_with_full_data(self):
        signals = NormalizedSignals(
            as_of_date=date(2026, 1, 1),
            vol_stress=0,
            rate_stress=0,
            yield_curve_stress=0,
            credit_stress=0,
            correlation_stress=0,
            data_quality=1.0,
        )
        features = FeatureVector(as_of_date=date(2026, 1, 1))
        _, confidence = generate_explanation(MacroState.CALM, signals, features)
        assert confidence == Confidence.HIGH

    def test_confidence_low_with_missing_data(self):
        signals = NormalizedSignals(
            as_of_date=date(2026, 1, 1), data_quality=0.4
        )
        features = FeatureVector(as_of_date=date(2026, 1, 1))
        _, confidence = generate_explanation(MacroState.CALM, signals, features)
        assert confidence == Confidence.LOW

    def test_multiple_drivers(self):
        signals = NormalizedSignals(
            as_of_date=date(2026, 1, 1),
            vol_stress=1,
            rate_stress=1,
            yield_curve_stress=1,
            data_quality=1.0,
        )
        features = FeatureVector(
            as_of_date=date(2026, 1, 1),
            vix_level=25.0,
            vix_percentile=85.0,
            tnx_vs_sma20=0.10,
            yield_curve_spread=-0.15,
        )
        drivers, _ = generate_explanation(MacroState.STRESSED, signals, features)
        assert len(drivers) == 3
