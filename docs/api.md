# ATLAS MACRO — Data Sources Reference

## Overview

ATLAS uses two data providers, both accessed through the Nexus_Core `DataLoader`:

| Provider | Purpose | API Key Env Var |
|----------|---------|-----------------|
| **Polygon** | VIX index, equity index prices | `POLYGON_KEY` |
| **FRED** | Treasury yields, yield curve, credit spreads, VIX fallback | `FRED_KEY` |

## Polygon Endpoints

### VIX Index (`indices-aggs`)

Fetches CBOE Volatility Index (VIX) daily bars.

```python
response = await loader.get_polygon_data(
    session,
    "indices-aggs",
    indexTicker="I:VIX",     # NOT aliased — must use exact param name
    multiplier=1,
    timespan="day",
    start="2025-10-01",      # aliased from "from"
    end="2026-02-05",        # aliased from "to"
    sort="asc",
)
```

**Response structure:**
```json
{
  "results": [
    {"t": 1696118400000, "o": 17.5, "h": 18.2, "l": 17.1, "c": 17.8, "v": 0, "n": 0}
  ]
}
```

ATLAS uses the `c` (close) field.

### Equity Index Prices (`aggs_daily`)

Fetches daily OHLCV bars for SPY, QQQ, IWM, DIA.

```python
response = await loader.get_polygon_data(
    session,
    "aggs_daily",
    ticker="SPY",            # aliased from "symbol"
    from_date="2025-10-01",  # aliased from "from"
    to_date="2026-02-05",    # aliased from "to"
    sort="asc",
)
```

**Response structure:** Same as indices-aggs. ATLAS uses the `c` (close) field.

**Tickers used:**

| Ticker | Index | Purpose |
|--------|-------|---------|
| `SPY` | S&P 500 | Large-cap benchmark |
| `QQQ` | Nasdaq 100 | Tech/growth benchmark |
| `IWM` | Russell 2000 | Small-cap benchmark |
| `DIA` | Dow Jones 30 | Blue-chip benchmark |

## FRED Endpoints

All FRED data is fetched via the `series` endpoint (observations).

### 10-Year Treasury Yield (`DGS10`)

```python
response = await loader.get_fred_data(
    session,
    "series",
    series_id="DGS10",
    observation_start="2025-10-01",
    observation_end="2026-02-05",
    sort_order="asc",
)
```

**Response structure:**
```json
{
  "observations": [
    {"date": "2025-10-01", "value": "4.25"},
    {"date": "2025-10-02", "value": "."}
  ]
}
```

Note: FRED uses `"."` for missing values. The fetcher filters these out.

**Usage in ATLAS:** Current value + 20-day history for SMA calculation.

### 10Y-2Y Treasury Spread (`T10Y2Y`)

```python
response = await loader.get_fred_data(
    session,
    "series",
    series_id="T10Y2Y",
    sort_order="desc",
    limit=5,
)
```

**Usage in ATLAS:** Latest value only. Negative = inverted yield curve.

### ICE BofA US High Yield Spread (`BAMLH0A0HYM2`)

```python
response = await loader.get_fred_data(
    session,
    "series",
    series_id="BAMLH0A0HYM2",
    observation_start="2025-10-01",
    observation_end="2026-02-05",
    sort_order="asc",
)
```

**Usage in ATLAS:** Current value + 63-day history for percentile calculation.

**Note:** This series is option-adjusted spread (OAS) in percentage points.
A value of 4.5 means 450 basis points.

### VIX Fallback (`VIXCLS`)

Used only when Polygon VIX fetch fails.

```python
response = await loader.get_fred_data(
    session,
    "series",
    series_id="VIXCLS",
    observation_start="2025-10-01",
    observation_end="2026-02-05",
    sort_order="asc",
)
```

**Note:** FRED VIX data (VIXCLS) has a 1-day lag compared to Polygon. Polygon is the primary source.

## Nexus_Core Parameter Aliases

The Nexus_Core `DataLoader` supports automatic parameter aliasing:

| Path Param | Accepted Aliases |
|------------|-----------------|
| `ticker` | `symbol`, `ticker`, `stocksTicker` |
| `from` | `start`, `from`, `from_date` |
| `to` | `end`, `to`, `to_date` |
| `indexTicker` | **NOT aliased** (must use exact name) |

## Caching

Nexus_Core provides built-in filesystem caching:

- **Location:** `data/cache/` (relative to project root)
- **TTL:** Configurable via `CACHE_TTL_DAYS` env var (default: 7)
- **Format:** JSON files with atomic writes (temp file + rename)
- **Behavior:** Cache is checked before any API call. In `READ_ONLY` mode, only cached data is served.

## Rate Limits

| Provider | Concurrency | Notes |
|----------|-------------|-------|
| Polygon | 10 concurrent | QoS semaphore in Nexus_Core |
| FRED | 1 concurrent | FRED is slow; sequential access |

The fetcher runs all 5 data fetches concurrently via `asyncio.gather()`,
but Nexus_Core's QoS router ensures provider-specific limits are respected.

## Error Handling

- Individual fetch failures are logged but don't crash the pipeline
- Failed fetches return empty `dict`, which propagates as `None` in `RawMarketData`
- `None` values result in `data_quality < 1.0` and `Confidence.LOW` or `MEDIUM`
- Circuit breaker in Nexus_Core prevents cascading failures (20% error rate threshold)

## Lookback Period

The fetcher requests `lookback_calendar_days` (default: 120) of history for each data source.
This ensures approximately 63 trading days of data are available for percentile calculations,
accounting for weekends and holidays.
