"""
ATLAS MACRO - Daily Pipeline Orchestration

Flow: ingest -> features -> normalize -> classify -> explain -> persist

The pipeline.run() method is the single async entry point.
All processing after ingest is synchronous.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date
from pathlib import Path

import pandas as pd

from atlas_macro.classifier.engine import classify_state
from atlas_macro.config import AtlasConfig
from atlas_macro.explain.generator import generate_explanation
from atlas_macro.features.correlation import compute_correlation_features
from atlas_macro.features.credit import compute_credit_features
from atlas_macro.features.rates import compute_rate_features
from atlas_macro.features.volatility import compute_vix_features
from atlas_macro.ingest.fetcher import MacroDataFetcher
from atlas_macro.normalization.normalizer import normalize_features
from atlas_macro.types import FeatureVector, MacroResult, RawMarketData

logger = logging.getLogger(__name__)


class DailyPipeline:
    """
    ATLAS MACRO daily pipeline.

    Orchestrates: ingest -> features -> normalize -> classify -> explain -> persist
    """

    def __init__(
        self,
        config: AtlasConfig | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self.config = config or AtlasConfig()
        self.output_dir = output_dir or Path(__file__).resolve().parents[3] / "data" / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fetcher = MacroDataFetcher(config=self.config)

    async def run(self, as_of_date: date | None = None) -> MacroResult:
        """
        Run the full pipeline for a given date.

        This is the only async entry point. Calls the fetcher,
        then hands off to synchronous processing.

        Args:
            as_of_date: Target date (default: today).

        Returns:
            MacroResult with state, drivers, confidence.
        """
        as_of_date = as_of_date or date.today()
        logger.info(f"ATLAS MACRO pipeline starting for {as_of_date}")

        # Step 1: Ingest (async)
        raw_data = await self.fetcher.fetch(as_of_date)
        logger.info("Ingest complete")

        # Steps 2-5: Synchronous processing
        result = self.process(raw_data)

        # Step 6: Persist
        self._save_result(result)

        logger.info(
            f"ATLAS MACRO {as_of_date}: {result.macro_state.value} "
            f"[{result.confidence.value}] drivers={result.drivers}"
        )
        return result

    def process(self, raw_data: RawMarketData) -> MacroResult:
        """
        Synchronous processing: features -> normalize -> classify -> explain.

        Can be called independently for testing without async/API calls.

        Args:
            raw_data: Raw market data from ingest.

        Returns:
            MacroResult.
        """
        # Step 2: Feature engineering
        features = self._compute_features(raw_data)

        # Step 3: Normalization
        signals = normalize_features(features, self.config)

        # Step 4: Classification
        state = classify_state(signals, self.config.classifier)

        # Step 5: Explanation
        drivers, confidence = generate_explanation(state, signals, features)

        return MacroResult(
            date=raw_data.as_of_date,
            macro_state=state,
            drivers=drivers,
            confidence=confidence,
            signals=signals,
            features=features,
        )

    def _compute_features(self, raw_data: RawMarketData) -> FeatureVector:
        """Compute all features from raw data."""
        vix = compute_vix_features(raw_data, self.config.volatility)
        rates = compute_rate_features(raw_data, self.config.rates, self.config.yield_curve)
        corr = compute_correlation_features(raw_data, self.config.correlation)
        credit = compute_credit_features(raw_data, self.config.credit)

        return FeatureVector(
            as_of_date=raw_data.as_of_date,
            vix_level=vix["vix_level"],
            vix_percentile=vix["vix_percentile"],
            rate_stress=rates["rate_stress"],
            tnx_vs_sma20=rates["tnx_vs_sma20"],
            yield_curve_spread=rates["yield_curve_spread"],
            yield_curve_inverted=rates["yield_curve_inverted"],
            credit_spread=credit["credit_spread"],
            credit_spread_percentile=credit["credit_spread_percentile"],
            mean_pairwise_correlation=corr["mean_pairwise_correlation"],
            correlation_percentile=corr["correlation_percentile"],
        )

    def _save_result(self, result: MacroResult) -> Path:
        """Persist result to daily JSON and append to Parquet history."""
        # Daily JSON
        daily_file = self.output_dir / f"atlas_{result.date.isoformat()}.json"
        daily_file.write_text(json.dumps(result.to_dict(), indent=2))

        # Parquet history (append or create)
        history_file = self.output_dir / "atlas_history.parquet"
        row = {
            "date": result.date.isoformat(),
            "macro_state": result.macro_state.value,
            "confidence": result.confidence.value,
            "drivers": json.dumps(result.drivers),
            "vol_stress": result.signals.vol_stress,
            "rate_stress": result.signals.rate_stress,
            "yield_curve_stress": result.signals.yield_curve_stress,
            "credit_stress": result.signals.credit_stress,
            "correlation_stress": result.signals.correlation_stress,
            "data_quality": result.signals.data_quality,
            "vix_level": result.features.vix_level,
            "vix_percentile": result.features.vix_percentile,
            "tnx_vs_sma20": result.features.tnx_vs_sma20,
            "yield_curve_spread": result.features.yield_curve_spread,
            "credit_spread": result.features.credit_spread,
            "mean_pairwise_corr": result.features.mean_pairwise_correlation,
        }

        new_row = pd.DataFrame([row])
        if history_file.exists():
            existing = pd.read_parquet(history_file)
            # Ensure matching columns to avoid FutureWarning on concat with all-NA cols
            for col in new_row.columns:
                if col not in existing.columns:
                    existing[col] = None
            df = pd.concat([existing, new_row], ignore_index=True)
            df = df.drop_duplicates(subset=["date"], keep="last")
        else:
            df = new_row

        df.to_parquet(history_file, index=False)
        logger.info(f"Saved to {daily_file} and {history_file}")
        return daily_file

    def get_history(self) -> pd.DataFrame:
        """Load historical ATLAS results from Parquet."""
        history_file = self.output_dir / "atlas_history.parquet"
        if not history_file.exists():
            return pd.DataFrame()
        df = pd.read_parquet(history_file)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df.sort_values("date")


def run_sync(as_of_date: date | None = None) -> MacroResult:
    """Synchronous convenience wrapper for CLI usage."""
    pipeline = DailyPipeline()
    return asyncio.run(pipeline.run(as_of_date))
