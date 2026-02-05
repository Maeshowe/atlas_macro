# ATLAS MACRO

**Macro-Level Market Constraint & Stress Diagnostic**

ATLAS answers one question only:

> *"Are there macro-level conditions that constrain or override otherwise valid market participation and allocation signals?"*

ATLAS is not a macro forecasting model and not an economic indicator suite.
It is a **ceiling**, not a steering wheel.

---

## Design Principles

- Macro is a **constraint**, not a driver
- No economic forecasting
- No soft data (PMI, CPI, NFP, speeches)
- No narratives
- Deterministic, rule-based
- Discrete states only

## Macro States

| State | Definition | Action |
|-------|-----------|--------|
| **CALM** | VIX low, rates stable, no stress signals | No constraint on downstream systems |
| **STRESSED** | Elevated VIX or rate pressure (2+ signals) | Downstream systems should reduce exposure |
| **CRISIS** | VIX shock, correlation spike, or credit blowout | Override: halt new positions |

## Output Format

```json
{
  "date": "2026-02-05",
  "macro_state": "STRESSED",
  "drivers": [
    "VIX elevated: 21.8 (percentile: 92 > 80)",
    "10Y yield above 20D SMA by +0.060%"
  ],
  "confidence": "MEDIUM"
}
```

## Quick Start

### 1. Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. API Keys

Copy `.env.example` to `.env` and add your keys:

```bash
cp .env.example .env
```

Required keys:
- `POLYGON_KEY` — [Polygon.io](https://polygon.io) API key
- `FRED_KEY` — [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) API key

### 3. Run Daily Diagnostic

```bash
# Human-readable output
PYTHONPATH=src python scripts/run_daily.py

# JSON output (for piping to other systems)
PYTHONPATH=src python scripts/run_daily.py --json

# Specific date
PYTHONPATH=src python scripts/run_daily.py --date 2026-01-15

# Verbose logging
PYTHONPATH=src python scripts/run_daily.py -v
```

### 4. Launch Dashboard

```bash
.venv/bin/streamlit run src/atlas_macro/dashboard/app.py
```

Opens at `http://localhost:8501`.

### 5. Run Scheduler

```bash
# Run daily at 4:30 PM (after market close)
PYTHONPATH=src python scripts/run_scheduler.py --time 16:30
```

### 6. Run Tests

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/ -v
```

## Core Metrics

### 1. Volatility Stress (VIX)
- **Source**: Polygon (`I:VIX`), FRED fallback (`VIXCLS`)
- **Feature**: VIX level + percentile rank (63-day baseline)
- **Thresholds**: Stressed >= 80th percentile, Crisis >= 95th OR VIX >= 35

### 2. Rate Stress (TNX)
- **Source**: FRED (`DGS10`)
- **Feature**: `RateStress_t = 1{TNX_t > SMA_20(TNX)}`
- **Binary**: Above SMA = stressed, below = calm

### 3. Yield Curve (T10Y2Y)
- **Source**: FRED (`T10Y2Y`)
- **Feature**: 10Y-2Y Treasury spread
- **Binary**: Inverted (< 0) = stressed, normal = calm

### 4. Credit Spread (HY)
- **Source**: FRED (`BAMLH0A0HYM2`)
- **Feature**: ICE BofA HY spread + percentile rank (63-day)
- **Thresholds**: Stressed >= 80th percentile, Crisis >= 95th OR spread >= 6.0%

### 5. Cross-Asset Correlation
- **Source**: Polygon (`SPY`, `QQQ`, `IWM`, `DIA`)
- **Feature**: Mean pairwise Pearson correlation (21-day rolling, log returns)
- **Thresholds**: Stressed >= 80th percentile, Crisis >= 95th OR corr >= 0.85

## Classifier Rules

```
1. CRISIS  — any single metric at crisis level (signal == 2)
2. STRESSED — 2 or more metrics at stressed-or-above (signal >= 1)
3. CALM     — otherwise
```

No hysteresis. No smoothing. Each day is classified independently.

## Architecture

```
Polygon (I:VIX, SPY/QQQ/IWM/DIA) ─┐
                                     ├─> RawMarketData
FRED (DGS10, T10Y2Y, BAMLH0A0HYM2) ┘
        │
        ▼
  FeatureVector (vix_pctl, rate_stress, corr, credit_pctl, yield_curve)
        │
        ▼
  NormalizedSignals (0/1/2 per metric)
        │
        ▼
  MacroState (CALM | STRESSED | CRISIS)
        │
        ▼
  MacroResult (state + drivers + confidence)
```

See [docs/architecture.md](docs/architecture.md) for detailed module design.

## Project Structure

```
atlas_macro/
  src/atlas_macro/
    types.py              # Frozen dataclasses, enums
    config.py             # All thresholds (single source of truth)
    ingest/fetcher.py     # Async data fetching (Nexus_Core DataLoader)
    features/             # Feature engineering (volatility, rates, credit, correlation)
    normalization/        # Features -> discrete stress signals
    classifier/engine.py  # Deterministic CALM/STRESSED/CRISIS
    explain/generator.py  # Driver list + confidence
    pipeline/daily.py     # Orchestration + persistence
    dashboard/            # Streamlit app + components
  scripts/
    run_daily.py          # CLI entry point
    run_scheduler.py      # Scheduled execution
  tests/                  # 56 unit tests
  data/
    output/               # Daily JSON + Parquet history
    cache/                # Nexus_Core API cache
```

## Guardrails

- No combining with AURORA, HELIOS, or OBSIDIAN internally
- No scoring into a single macro number
- No predictive statements
- If macro signals conflict with microstructure or breadth: **macro state wins**

## Dependencies

| Package | Purpose |
|---------|---------|
| `aiohttp` | Async HTTP for Nexus_Core DataLoader |
| `pandas` | Data processing |
| `pyarrow` | Parquet persistence |
| `python-dotenv` | `.env` configuration |
| `streamlit` | Dashboard |
| `plotly` | Dashboard charts |

External dependency: [Nexus_Core](../Nexus_Core/) DataLoader (imported via `sys.path`).
