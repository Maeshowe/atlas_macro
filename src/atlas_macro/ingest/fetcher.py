"""
ATLAS MACRO - Async Data Fetcher

Only module in atlas_macro that contains async code.
Uses Nexus_Core DataLoader for Polygon and FRED data.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import aiohttp

# Wire Nexus_Core dependency — vendored submodule at <project_root>/vendor/Nexus_Core/src
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/atlas_macro/ingest -> project root
_NEXUS_CORE_SRC = _PROJECT_ROOT / "vendor" / "Nexus_Core" / "src"

if not (_NEXUS_CORE_SRC / "data_loader").is_dir():
    raise ImportError(
        f"Nexus_Core not found at {_NEXUS_CORE_SRC}. "
        "Run: git submodule update --init --recursive"
    )

if str(_NEXUS_CORE_SRC) not in sys.path:
    sys.path.insert(0, str(_NEXUS_CORE_SRC))

from data_loader import DataLoader  # noqa: E402

from atlas_macro.config import AtlasConfig
from atlas_macro.types import RawMarketData

logger = logging.getLogger(__name__)


class MacroDataFetcher:
    """
    Async fetcher for all ATLAS MACRO data sources.

    Uses Nexus_Core DataLoader for FRED and Polygon data.
    This is the ONLY class in atlas_macro that contains async code.
    """

    def __init__(self, config: AtlasConfig | None = None) -> None:
        self.config = config or AtlasConfig()
        self.loader = DataLoader()

    async def fetch(self, as_of_date: date | None = None) -> RawMarketData:
        """
        Fetch all raw data for a given date.

        Fetches VIX, TNX, T10Y2Y, HY spread, and index prices concurrently.

        Args:
            as_of_date: Target date (default: today).

        Returns:
            RawMarketData with all available fields populated.
        """
        as_of_date = as_of_date or date.today()
        lookback_start = (
            as_of_date - timedelta(days=self.config.lookback_calendar_days)
        ).isoformat()
        as_of_str = as_of_date.isoformat()

        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                self._fetch_vix(session, lookback_start, as_of_str),
                self._fetch_tnx(session, lookback_start, as_of_str),
                self._fetch_t10y2y(session, as_of_str),
                self._fetch_hy_spread(session, lookback_start, as_of_str),
                self._fetch_index_prices(session, lookback_start, as_of_str),
                return_exceptions=True,
            )

            vix_data, tnx_data, t10y2y_data, hy_data, index_data = results

            vix = _safe(vix_data, {})
            tnx = _safe(tnx_data, {})
            t10y2y = _safe(t10y2y_data, {})
            hy = _safe(hy_data, {})
            idx = _safe(index_data, {})

            return RawMarketData(
                as_of_date=as_of_date,
                vix_current=vix.get("current"),
                vix_history_63d=vix.get("history", []),
                tnx_current=tnx.get("current"),
                tnx_history_20d=tnx.get("history_20d", []),
                t10y2y_current=t10y2y.get("current"),
                hy_spread_current=hy.get("current"),
                hy_spread_history_63d=hy.get("history", []),
                spy_prices=idx.get("SPY", []),
                qqq_prices=idx.get("QQQ", []),
                iwm_prices=idx.get("IWM", []),
                dia_prices=idx.get("DIA", []),
            )

    async def _fetch_vix(self, session: aiohttp.ClientSession, start: str, end: str) -> dict:
        """Fetch VIX from Polygon (I:VIX via aggs_daily), fallback to FRED (VIXCLS)."""
        # Primary: Polygon — I:VIX uses the same aggs path as equities
        response = await self.loader.get_polygon_data(
            session,
            "aggs_daily",
            symbol="I:VIX",
            start=start,
            end=end,
            sort="asc",
        )
        if response.success and response.data:
            results = response.data.get("results", [])
            if results:
                values = [r["c"] for r in results if "c" in r]
                if values:
                    return {
                        "current": values[-1],
                        "history": values[-64:-1],  # exclude current day
                    }

        logger.warning("Polygon VIX fetch failed, falling back to FRED VIXCLS")

        # Fallback: FRED VIXCLS
        response = await self.loader.get_fred_data(
            session,
            "series",
            series_id="VIXCLS",
            observation_start=start,
            observation_end=end,
            sort_order="asc",
        )
        if response.success and response.data:
            values = _parse_fred_observations(response.data)
            if values:
                return {
                    "current": values[-1],
                    "history": values[-64:-1],  # exclude current day
                }

        logger.error("VIX fetch failed from both Polygon and FRED")
        return {}

    async def _fetch_tnx(self, session: aiohttp.ClientSession, start: str, end: str) -> dict:
        """Fetch 10-Year Treasury (DGS10) from FRED."""
        response = await self.loader.get_fred_data(
            session,
            "series",
            series_id="DGS10",
            observation_start=start,
            observation_end=end,
            sort_order="asc",
        )
        if response.success and response.data:
            values = _parse_fred_observations(response.data)
            if values:
                return {
                    "current": values[-1],
                    "history_20d": values[-21:-1],  # exclude current day
                }

        logger.error("TNX (DGS10) fetch failed")
        return {}

    async def _fetch_t10y2y(self, session: aiohttp.ClientSession, end: str) -> dict:
        """Fetch 10Y-2Y spread from FRED as of the given date."""
        response = await self.loader.get_fred_data(
            session,
            "series",
            series_id="T10Y2Y",
            observation_end=end,
            sort_order="desc",
            limit=5,
        )
        if response.success and response.data:
            obs = response.data.get("observations", [])
            for o in obs:
                val = o.get("value", ".")
                if val != ".":
                    try:
                        return {"current": float(val)}
                    except (ValueError, TypeError):
                        continue

        logger.error("T10Y2Y fetch failed")
        return {}

    async def _fetch_hy_spread(
        self, session: aiohttp.ClientSession, start: str, end: str
    ) -> dict:
        """Fetch High Yield spread (BAMLH0A0HYM2) from FRED."""
        response = await self.loader.get_fred_data(
            session,
            "series",
            series_id="BAMLH0A0HYM2",
            observation_start=start,
            observation_end=end,
            sort_order="asc",
        )
        if response.success and response.data:
            values = _parse_fred_observations(response.data)
            if values:
                return {
                    "current": values[-1],
                    "history": values[-64:-1],  # exclude current day
                }

        logger.error("HY spread (BAMLH0A0HYM2) fetch failed")
        return {}

    async def _fetch_index_prices(
        self, session: aiohttp.ClientSession, start: str, end: str
    ) -> dict:
        """Fetch daily close prices for SPY, QQQ, IWM, DIA from Polygon."""
        tickers = ["SPY", "QQQ", "IWM", "DIA"]
        tasks = [
            self.loader.get_polygon_data(
                session,
                "aggs_daily",
                symbol=t,
                start=start,
                end=end,
                sort="asc",
            )
            for t in tickers
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        result: dict[str, list[float]] = {}
        for ticker, resp in zip(tickers, responses):
            if isinstance(resp, Exception):
                logger.warning(f"Failed to fetch {ticker}: {resp}")
                result[ticker] = []
                continue
            if not resp.success:
                logger.warning(f"Failed to fetch {ticker}: {resp.error}")
                result[ticker] = []
                continue
            bars = resp.data.get("results", []) if resp.data else []
            result[ticker] = [b["c"] for b in bars if "c" in b][-63:]

        return result


def _safe(val: Any, default: Any) -> Any:
    """Return default if val is an exception."""
    return default if isinstance(val, Exception) else val


def _parse_fred_observations(data: dict) -> list[float]:
    """Parse FRED observations into a list of floats, skipping missing values."""
    obs = data.get("observations", [])
    values = []
    for o in obs:
        val = o.get("value", ".")
        if val != ".":
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                continue
    return values
