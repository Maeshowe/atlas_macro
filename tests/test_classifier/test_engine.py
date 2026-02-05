"""Tests for the deterministic state classifier."""

from datetime import date

import pytest

from atlas_macro.classifier.engine import classify_state
from atlas_macro.config import ClassifierConfig
from atlas_macro.types import MacroState, NormalizedSignals


class TestClassifyState:
    """Test the classifier truth table."""

    @pytest.fixture
    def cfg(self):
        return ClassifierConfig()

    def _signals(self, vol=0, rate=0, yc=0, credit=0, corr=0):
        return NormalizedSignals(
            as_of_date=date(2026, 1, 1),
            vol_stress=vol,
            rate_stress=rate,
            yield_curve_stress=yc,
            credit_stress=credit,
            correlation_stress=corr,
        )

    def test_all_zero_is_calm(self, cfg):
        assert classify_state(self._signals(), cfg) == MacroState.CALM

    def test_single_stressed_is_calm(self, cfg):
        """Only 1 stressed signal is NOT enough for STRESSED."""
        assert classify_state(self._signals(vol=1), cfg) == MacroState.CALM
        assert classify_state(self._signals(rate=1), cfg) == MacroState.CALM
        assert classify_state(self._signals(yc=1), cfg) == MacroState.CALM

    def test_two_stressed_is_stressed(self, cfg):
        assert classify_state(self._signals(vol=1, rate=1), cfg) == MacroState.STRESSED
        assert classify_state(self._signals(rate=1, yc=1), cfg) == MacroState.STRESSED
        assert classify_state(self._signals(credit=1, corr=1), cfg) == MacroState.STRESSED

    def test_three_stressed_is_stressed(self, cfg):
        assert classify_state(self._signals(vol=1, rate=1, yc=1), cfg) == MacroState.STRESSED

    def test_single_crisis_is_crisis(self, cfg):
        """Any single crisis signal -> CRISIS."""
        assert classify_state(self._signals(vol=2), cfg) == MacroState.CRISIS
        assert classify_state(self._signals(credit=2), cfg) == MacroState.CRISIS
        assert classify_state(self._signals(corr=2), cfg) == MacroState.CRISIS

    def test_crisis_with_stressed(self, cfg):
        assert classify_state(self._signals(vol=2, rate=1), cfg) == MacroState.CRISIS

    def test_multiple_crisis(self, cfg):
        assert classify_state(self._signals(vol=2, credit=2), cfg) == MacroState.CRISIS

    def test_full_crisis(self, cfg):
        assert (
            classify_state(self._signals(vol=2, rate=1, yc=1, credit=2, corr=2), cfg)
            == MacroState.CRISIS
        )

    def test_crisis_overrides_stressed_count(self, cfg):
        """Even with 0 stressed signals, 1 crisis -> CRISIS."""
        assert classify_state(self._signals(vol=2), cfg) == MacroState.CRISIS
