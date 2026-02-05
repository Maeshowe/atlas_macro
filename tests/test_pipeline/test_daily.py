"""Tests for the daily pipeline (synchronous processing only)."""

from datetime import date

import pytest

from atlas_macro.config import AtlasConfig
from atlas_macro.pipeline.daily import DailyPipeline
from atlas_macro.types import MacroState, RawMarketData


class TestDailyPipelineProcess:
    """Test the synchronous process() method with synthetic data."""

    @pytest.fixture
    def pipeline(self, tmp_path):
        return DailyPipeline(output_dir=tmp_path)

    def test_calm_market(self, pipeline, calm_raw_data):
        result = pipeline.process(calm_raw_data)
        assert result.macro_state == MacroState.CALM
        assert result.confidence is not None
        assert len(result.drivers) >= 1

    def test_stressed_market(self, pipeline, stressed_raw_data):
        result = pipeline.process(stressed_raw_data)
        # With elevated VIX + rate stress + inverted yield curve, should be STRESSED or CRISIS
        assert result.macro_state in (MacroState.STRESSED, MacroState.CRISIS)
        assert len(result.drivers) >= 2

    def test_crisis_market(self, pipeline, crisis_raw_data):
        result = pipeline.process(crisis_raw_data)
        # VIX=42 (absolute crisis) should guarantee CRISIS
        assert result.macro_state == MacroState.CRISIS

    def test_empty_data(self, pipeline):
        data = RawMarketData(as_of_date=date(2026, 1, 1))
        result = pipeline.process(data)
        assert result.macro_state == MacroState.CALM
        assert result.signals.data_quality == 0.0

    def test_to_dict_format(self, pipeline, calm_raw_data):
        result = pipeline.process(calm_raw_data)
        d = result.to_dict()
        assert "date" in d
        assert "macro_state" in d
        assert "drivers" in d
        assert "confidence" in d
        assert d["macro_state"] in ("CALM", "STRESSED", "CRISIS")

    def test_save_and_load_history(self, pipeline, calm_raw_data, stressed_raw_data):
        """Test persistence round-trip."""
        r1 = pipeline.process(calm_raw_data)
        pipeline._save_result(r1)

        r2 = pipeline.process(stressed_raw_data)
        pipeline._save_result(r2)

        history = pipeline.get_history()
        assert len(history) >= 1  # May deduplicate on same date
