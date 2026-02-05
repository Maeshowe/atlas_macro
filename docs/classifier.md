# ATLAS MACRO — Classifier Logic

## Overview

The classifier is purely deterministic. No weights, no scores, no soft boundaries.
Each day is classified independently — no hysteresis, no smoothing, no memory.

## Threshold Table

### Volatility (VIX)

| Level | Condition |
|-------|-----------|
| **Calm** (0) | VIX percentile < 80th AND VIX < 35 |
| **Stressed** (1) | VIX percentile >= 80th |
| **Crisis** (2) | VIX percentile >= 95th **OR** VIX >= 35.0 |

Percentile is computed over 63 trading days (~3 months).
The absolute floor (VIX >= 35) prevents desensitization during prolonged high-vol regimes.

### Rate Stress (TNX)

| Level | Condition |
|-------|-----------|
| **Calm** (0) | TNX <= SMA_20(TNX) |
| **Stressed** (1) | TNX > SMA_20(TNX) |

Binary indicator only. No crisis level — rising rates are directional pressure, not a shock.

### Yield Curve (T10Y2Y)

| Level | Condition |
|-------|-----------|
| **Normal** (0) | 10Y-2Y spread >= 0 |
| **Inverted** (1) | 10Y-2Y spread < 0 |

Binary indicator. Yield curve inversion is a structural warning, not an acute crisis.

### Credit Spread (BAMLH0A0HYM2)

| Level | Condition |
|-------|-----------|
| **Calm** (0) | Percentile < 80th AND spread < 6.0% |
| **Stressed** (1) | Percentile >= 80th |
| **Crisis** (2) | Percentile >= 95th **OR** spread >= 6.0% |

Percentile is computed over 63 trading days.
The absolute floor (spread >= 600bps) catches extreme credit events.

### Cross-Asset Correlation

| Level | Condition |
|-------|-----------|
| **Calm** (0) | Percentile < 80th AND mean corr < 0.85 |
| **Stressed** (1) | Percentile >= 80th |
| **Crisis** (2) | Percentile >= 95th **OR** mean corr >= 0.85 |

Mean pairwise Pearson correlation across SPY/QQQ/IWM/DIA.
Computed over 21-day rolling window, percentile over 63-day history.

## State Classification Rules

Evaluated in strict order:

```
Rule 1: IF any signal == 2  →  CRISIS
Rule 2: IF count(signal >= 1) >= 2  →  STRESSED
Rule 3: OTHERWISE  →  CALM
```

### Truth Table (representative examples)

| Vol | Rate | YC | Credit | Corr | Stressed Count | Crisis Count | **State** |
|-----|------|----|--------|------|----------------|--------------|-----------|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | **CALM** |
| 1 | 0 | 0 | 0 | 0 | 1 | 0 | **CALM** |
| 0 | 1 | 0 | 0 | 0 | 1 | 0 | **CALM** |
| 1 | 1 | 0 | 0 | 0 | 2 | 0 | **STRESSED** |
| 1 | 0 | 1 | 0 | 0 | 2 | 0 | **STRESSED** |
| 0 | 1 | 0 | 1 | 0 | 2 | 0 | **STRESSED** |
| 1 | 1 | 1 | 0 | 0 | 3 | 0 | **STRESSED** |
| 1 | 1 | 1 | 1 | 0 | 4 | 0 | **STRESSED** |
| 2 | 0 | 0 | 0 | 0 | 1 | 1 | **CRISIS** |
| 0 | 0 | 0 | 2 | 0 | 1 | 1 | **CRISIS** |
| 0 | 0 | 0 | 0 | 2 | 1 | 1 | **CRISIS** |
| 2 | 1 | 0 | 0 | 0 | 2 | 1 | **CRISIS** |
| 2 | 1 | 1 | 2 | 1 | 5 | 2 | **CRISIS** |

Key insight: A single crisis-level signal **always** overrides any number of calm signals.

## Confidence Levels

| Level | Condition |
|-------|-----------|
| **LOW** | Data quality < 60% (fewer than 3 of 5 metrics available) |
| **MEDIUM** | Data quality >= 60% but state is borderline |
| **HIGH** | Data quality >= 80% AND signals strongly agree |

### Signal Agreement (for HIGH confidence)

- **CALM**: HIGH if 4+ signals are at 0
- **STRESSED**: HIGH if 3+ signals are >= 1
- **CRISIS**: HIGH if 2+ signals are at crisis level (2)

## Configuration

All thresholds are defined in `src/atlas_macro/config.py`:

```python
@dataclass(frozen=True)
class AtlasConfig:
    volatility: VolatilityThresholds    # stressed=80, crisis=95, absolute=35.0
    rates: RateThresholds               # sma_window=20
    yield_curve: YieldCurveThresholds   # inversion_threshold=0.0
    credit: CreditThresholds            # stressed=80, crisis=95, absolute=6.0
    correlation: CorrelationThresholds  # window=21, stressed=80, crisis=95, absolute=0.85
    classifier: ClassifierConfig        # crisis_required=1, stressed_required=2
```

To modify thresholds, instantiate `AtlasConfig` with custom sub-configs:

```python
from atlas_macro.config import AtlasConfig, VolatilityThresholds

custom = AtlasConfig(
    volatility=VolatilityThresholds(crisis_absolute=30.0),  # Lower VIX crisis threshold
)
pipeline = DailyPipeline(config=custom)
```

## Design Rationale

### Why no hysteresis?
Hysteresis (e.g., "stay STRESSED for 3 days after signals clear") introduces state memory,
which makes the output non-deterministic from current inputs. ATLAS is designed so that
given the same `RawMarketData`, it always produces the same `MacroState`.

### Why absolute crisis floors?
During prolonged high-volatility regimes, the 63-day rolling window normalizes extreme values.
A VIX of 35 during a month of 30+ VIX might only be at the 70th percentile.
The absolute floor prevents this desensitization.

### Why are Rate Stress and Yield Curve binary only?
Rising rates and yield curve inversion are directional/structural signals, not acute shocks.
They don't have "crisis" equivalents — a 50bps rate move is not comparable to VIX spiking to 40.
They contribute to STRESSED (via signal count) but cannot independently trigger CRISIS.
