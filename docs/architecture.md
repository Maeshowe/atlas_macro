# ATLAS MACRO — Architecture

## Module Pipeline

```
┌─────────┐    ┌──────────┐    ┌───────────────┐    ┌────────────┐    ┌─────────┐
│ INGEST  │───>│ FEATURES │───>│ NORMALIZATION │───>│ CLASSIFIER │───>│ EXPLAIN │
│ (async) │    │ (sync)   │    │ (sync)        │    │ (sync)     │    │ (sync)  │
└─────────┘    └──────────┘    └───────────────┘    └────────────┘    └─────────┘
     │                                                                      │
     │              ┌────────────┐                                          │
     └──────────────│  PIPELINE  │<─────────────────────────────────────────┘
                    │ (orchest.) │
                    └─────┬──────┘
                          │
                    ┌─────▼──────┐
                    │ DASHBOARD  │
                    │ (Streamlit)│
                    └────────────┘
```

## Data Flow

### Input Types

```
RawMarketData (frozen dataclass)
├── as_of_date: date
├── vix_current: float              ← Polygon I:VIX / FRED VIXCLS
├── vix_history_63d: list[float]    ← 63 trading days
├── tnx_current: float              ← FRED DGS10
├── tnx_history_20d: list[float]    ← 20 trading days
├── t10y2y_current: float           ← FRED T10Y2Y
├── hy_spread_current: float        ← FRED BAMLH0A0HYM2
├── hy_spread_history_63d: list     ← 63 trading days
├── spy_prices: list[float]         ← Polygon aggs_daily
├── qqq_prices: list[float]
├── iwm_prices: list[float]
└── dia_prices: list[float]
```

### Processing Types

```
FeatureVector (frozen dataclass)
├── vix_level: float
├── vix_percentile: float           ← rank within 63d history
├── rate_stress: int (0|1)          ← TNX vs SMA_20
├── tnx_vs_sma20: float             ← difference in yield points
├── yield_curve_spread: float       ← T10Y2Y value
├── yield_curve_inverted: bool
├── credit_spread: float
├── credit_spread_percentile: float ← rank within 63d history
├── mean_pairwise_correlation: float← mean of 6 pairwise correlations
└── correlation_percentile: float   ← rank within 63d rolling history
```

```
NormalizedSignals (frozen dataclass)
├── vol_stress: int (0|1|2)         ← calm / stressed / crisis
├── rate_stress: int (0|1)          ← calm / stressed
├── yield_curve_stress: int (0|1)   ← normal / inverted
├── credit_stress: int (0|1|2)      ← calm / stressed / crisis
├── correlation_stress: int (0|1|2) ← calm / stressed / crisis
└── data_quality: float (0-1)       ← fraction of 5 metrics available
```

### Output Type

```
MacroResult (frozen dataclass)
├── date: date
├── macro_state: MacroState         ← CALM | STRESSED | CRISIS
├── drivers: list[str]              ← human-readable explanations
├── confidence: Confidence          ← HIGH | MEDIUM | LOW
├── signals: NormalizedSignals
└── features: FeatureVector
```

## Module Details

### 1. Ingest (`ingest/fetcher.py`)

**Only async module.** Uses Nexus_Core `DataLoader` for all API access.

| Method | Source | Endpoint | Params |
|--------|--------|----------|--------|
| `_fetch_vix` | Polygon | `indices-aggs` | `indexTicker="I:VIX"` |
| `_fetch_vix` (fallback) | FRED | `series` | `series_id="VIXCLS"` |
| `_fetch_tnx` | FRED | `series` | `series_id="DGS10"` |
| `_fetch_t10y2y` | FRED | `series` | `series_id="T10Y2Y"` |
| `_fetch_hy_spread` | FRED | `series` | `series_id="BAMLH0A0HYM2"` |
| `_fetch_index_prices` | Polygon | `aggs_daily` | `ticker=SPY/QQQ/IWM/DIA` |

All fetches run concurrently via `asyncio.gather(return_exceptions=True)`.
Failures are logged but do not crash the pipeline — missing data propagates as `None`.

### 2. Features (`features/`)

Four pure-function modules, each taking `RawMarketData` and returning a `dict`:

| Module | Function | Inputs | Key Output |
|--------|----------|--------|------------|
| `volatility.py` | `compute_vix_features()` | VIX current + 63d history | `vix_level`, `vix_percentile` |
| `rates.py` | `compute_rate_features()` | TNX current + 20d history, T10Y2Y | `rate_stress` (0\|1), `yield_curve_inverted` |
| `credit.py` | `compute_credit_features()` | HY spread + 63d history | `credit_spread`, `credit_spread_percentile` |
| `correlation.py` | `compute_correlation_features()` | SPY/QQQ/IWM/DIA prices | `mean_pairwise_correlation`, `correlation_percentile` |

Correlation uses pure Python Pearson implementation (no numpy). Log returns over 21-day rolling window, percentile over 63-day history.

### 3. Normalization (`normalization/normalizer.py`)

Single function: `normalize_features(FeatureVector, AtlasConfig) -> NormalizedSignals`

Maps each feature to a discrete stress level using configured thresholds.
Also computes `data_quality` as the fraction of 5 metrics that are non-None.

### 4. Classifier (`classifier/engine.py`)

Single function: `classify_state(NormalizedSignals, ClassifierConfig) -> MacroState`

Three rules evaluated in order. See [docs/classifier.md](classifier.md) for the full truth table.

### 5. Explain (`explain/generator.py`)

Single function: `generate_explanation(MacroState, NormalizedSignals, FeatureVector) -> (list[str], Confidence)`

Generates factual driver strings (e.g., "VIX elevated: 21.8 (percentile: 92 > 80)").
Confidence is derived from data quality and signal agreement.

### 6. Pipeline (`pipeline/daily.py`)

`DailyPipeline` orchestrates the full flow:

```python
async def run(as_of_date):
    raw_data = await self.fetcher.fetch(as_of_date)   # async
    result = self.process(raw_data)                     # sync
    self._save_result(result)                           # persist
    return result

def process(raw_data):                                  # testable without API
    features = self._compute_features(raw_data)
    signals = normalize_features(features, config)
    state = classify_state(signals, config.classifier)
    drivers, confidence = generate_explanation(state, signals, features)
    return MacroResult(...)
```

Persistence: daily JSON + append to Parquet history file.

### 7. Dashboard (`dashboard/`)

Streamlit app with 4 reusable components:

| Component | File | Description |
|-----------|------|-------------|
| State Indicator | `state_indicator.py` | Plotly semicircular gauge (3-zone) |
| Metric Cards | `metric_cards.py` | 5 styled cards with stress level coloring |
| Driver Panel | `driver_panel.py` | Active drivers list |
| History Chart | `history_chart.py` | State timeline with colored markers |

## External Dependency: Nexus_Core

ATLAS imports the Nexus_Core `DataLoader` via `sys.path` insertion in `ingest/fetcher.py`.

```python
sys.path.insert(0, "/Users/safrtam/SSH-Services/Nexus_Core/src")
from data_loader import DataLoader
```

No other module in ATLAS has any Nexus_Core awareness. The DataLoader provides:
- Built-in caching (filesystem JSON, configurable TTL)
- Circuit breaker (20% error threshold)
- QoS semaphore routing (provider-specific concurrency)
- Retry with exponential backoff

## Immutability

All intermediate types (`RawMarketData`, `FeatureVector`, `NormalizedSignals`, `MacroResult`) are `@dataclass(frozen=True)`. Data flows in one direction only; no mutation occurs after construction.
