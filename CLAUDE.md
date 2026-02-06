# ATLAS MACRO — Project Guide

## Philosophy
"Macro is a constraint, not a driver." ATLAS is a deterministic, rule-based macro stress diagnostic. No forecasting, no soft data, no narratives, no single macro score. Binary classification into discrete states.

## Architecture

### 8-Module Pipeline
```
ingest (async) → features → normalization → classifier → explain → pipeline → dashboard
```

- **Async boundary**: Only `ingest/fetcher.py` is async. Everything else is synchronous.
- **Nexus_Core**: Git submodule at `vendor/Nexus_Core/`. Imported via `sys.path` in `ingest/fetcher.py` only. Provides Polygon + FRED API access with caching, circuit breaker, retry.
- **Immutability**: All intermediate types are `@dataclass(frozen=True)` in `types.py`.
- **Config**: Single source of truth in `config.py`. All thresholds are named and centralized.

### Key Source Paths
| Module | Path | Role |
|--------|------|------|
| Types | `src/atlas_macro/types.py` | Frozen dataclasses, enums |
| Config | `src/atlas_macro/config.py` | All thresholds |
| Ingest | `src/atlas_macro/ingest/fetcher.py` | Async data fetcher (Nexus_Core) |
| Features | `src/atlas_macro/features/` | Pure functions: volatility, rates, credit, correlation |
| Normalization | `src/atlas_macro/normalization/normalizer.py` | Features → 0/1/2 signals |
| Classifier | `src/atlas_macro/classifier/engine.py` | Signals → CALM/STRESSED/CRISIS |
| Explain | `src/atlas_macro/explain/generator.py` | Driver list + confidence |
| Pipeline | `src/atlas_macro/pipeline/daily.py` | Orchestration, persistence |
| Dashboard | `src/atlas_macro/dashboard/app.py` | Streamlit + Plotly components |

### Classifier Rules
- **CRISIS**: Any signal == 2 (VIX pctl >= 95 or VIX >= 35, credit pctl >= 95 or spread >= 6.0, corr pctl >= 95 or corr >= 0.85)
- **STRESSED**: 2+ signals >= 1
- **CALM**: Otherwise
- No hysteresis. Each day is independent.

## Nexus_Core API Notes
- **Polygon `aggs_daily`**: Required params: `symbol`, `start`, `end`. Optional: `adjusted`, `sort`, `limit`
- **Polygon has NO `indices-aggs` endpoint** — VIX is fetched from FRED instead
- **FRED `series`**: Required: `series_id`. Optional: `observation_start`, `observation_end`, `sort_order`, `limit`
- Polygon index prices: `get_polygon_data(session, "aggs_daily", symbol="SPY", start=..., end=...)`
- FRED series: `get_fred_data(session, "series", series_id="DGS10", observation_start=..., observation_end=...)`

## Data Sources
| Data | Source | Endpoint |
|------|--------|----------|
| VIX | Polygon (primary), FRED (fallback) | `aggs_daily` symbol=`I:VIX` / `VIXCLS` |
| SPY/QQQ/IWM/DIA prices | Polygon | `aggs_daily` (param: `symbol`) |
| 10Y Treasury (TNX) | FRED | `DGS10` |
| Yield curve | FRED | `T10Y2Y` |
| HY credit spread | FRED | `BAMLH0A0HYM2` |

## Running

```bash
# Tests (56 passing)
PYTHONPATH=src python -m pytest tests/ -v

# Daily diagnostic
PYTHONPATH=src python scripts/run_daily.py -v

# Specific date
PYTHONPATH=src python scripts/run_daily.py --date 2026-02-05

# JSON output
PYTHONPATH=src python scripts/run_daily.py --json

# Dashboard (port 8505 in production)
PYTHONPATH=src streamlit run src/atlas_macro/dashboard/app.py
```

## Deployment
- Server: Linux at `/home/safrtam/atlas_macro`
- Dashboard: Streamlit on port 8505 behind nginx at `atlas.ssh.services`
- Daily run: systemd timer Mon-Fri 21:30 UTC (30 min after OBSIDIAN to avoid API contention)
- See `DEPLOY_LINUX.md` for full setup instructions

## Testing Notes
- Synthetic test data uses sin/cos offsets with different frequencies per ticker to avoid perfect correlation (which would falsely trigger CRISIS)
- Pipeline `process()` method is synchronous and testable without API calls
- 56 unit tests covering features, normalization, classifier, explain, pipeline

## SSH-Services Ecosystem
| Service | Port | Domain |
|---------|------|--------|
| moneyflows | 8501 | moneyflows.ssh.services |
| obsidian | 8502 | obsidian.ssh.services |
| aurora | 8503 | aurora.ssh.services |
| **atlas** | **8505** | **atlas.ssh.services** |

## Dependencies
Runtime: `aiohttp`, `pandas`, `pyarrow`, `python-dotenv`, `streamlit`, `plotly`
Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`
