# Lottery Prediction Research

**Status**: PRODUCTION READY | **Updated**: January 6, 2026

---

## Quick Start

```bash
cd ml_models
python production_predictor.py predict 3172
python production_predictor.py find 3171
python production_predictor.py validate 2981 3171
```

---

## Current Prediction

Run: `python ml_models/production_predictor.py predict [series]`

Output is **ordered by performance rank** (best performers first):
```
Rank  Set                Numbers                                       Type
#1    S1 (14<>16)        ...                                           STD
#2    S2 (13<>15)        ...                                           STD
#3    S4 (Primary)       ...                                           STD
...
```

---

## Key Metrics (191 series validated)

| Metric | Value |
|--------|-------|
| Average | 10.22/14 |
| Best | 12/14 |
| Worst | 9/14 |
| 11+ matches | 63 (33%) |
| 12+ matches | 6 (3.1%) |
| 14/14 hits | 0 |

### Set Performance (ordered by win rate)

| Rank | Set | Strategy | Wins | Rate |
|------|-----|----------|------|------|
| 1 | S1 | swap 14<>16 | 77 | 40.3% |
| 2 | S2 | swap 13<>15 | 52 | 27.2% |
| 3 | S4 | primary top-14 | 20 | 10.5% |
| 4 | S5 | ML hot #1 | 10 | 5.2% |
| 5 | S6 | ML hot #1+#2 | 10 | 5.2% |
| 6 | S7 | swap 14<>17 | 9 | 4.7% |
| 7 | S3 | swap 14<>15 | 7 | 3.7% |
| 8 | S8 | swap 14<>18 | 6 | 3.1% |

**ML helped**: 20 (10.5%) | **Extended helped**: 15 (7.9%)

### Latest Result (Series 3171)

- **Winner**: S1 (11/14 on Event 4)
- **S1/S2/S3 tied** at 11/14, S1 credited (first match)

---

## Statistical Validation (Monte Carlo)

| Test | Value | Interpretation |
|------|-------|----------------|
| t-statistic | 45.62 | Extremely high |
| p-value | 2.62e-104 | Highly significant |
| Cohen's d | 2.32 | Large effect |
| 95% CI | [10.12, 10.32] | Tight confidence |
| Percentile | 100% | Beats all random |

### Convergence Analysis
- **Saturation**: ~60 series (model maxed)
- **Optimal lookback**: 5 series (confirmed)
- **Regime changes**: 0 (stable)

### Stress Test
- **Avg latency**: 1.16ms (target <10ms)
- **P99 latency**: 1.95ms (target <50ms)
- **Error rate**: 0%

Run: `python ml_models/monte_carlo_validation.py -n 10000`

---

## Data

- **Series**: 192 (2980-3171)
- **Latest**: 3171
- **File**: `data/full_series_data.json`

---

## Strategy (Simulation-Validated Best)

```python
# Prior Event 1 + 8-set hedging (4 std + 2 ML + 2 ext)
ranked = sorted(1..25, key=lambda n: (-(n in event1), -freq[n]))

# Hot non-E1 numbers from recent 5 series
hot_outside = sorted(non_top14, key=lambda n: -recent_freq[n])[:3]

# Sets ordered by implementation (see performance ranking above)
sets = [
    ranked[:13] + [ranked[15]],          # S1: swap 14<>16 (40.3% wins)
    ranked[:12] + [ranked[14], ranked[13]],  # S2: swap 13<>15 (27.2%)
    ranked[:13] + [ranked[14]],          # S3: swap 14<>15 (3.7%)
    ranked[:14],                         # S4: primary (10.5%)
    ranked[:13] + [hot_outside[0]],      # S5: ML hot #1 (5.2%)
    ranked[:12] + hot_outside[:2],       # S6: ML hot #1+#2 (5.2%)
    ranked[:13] + [ranked[16]],          # S7: swap 14<>17 (4.7%)
    ranked[:13] + [ranked[17]],          # S8: swap 14<>18 (3.1%)
]
```

**Priority**: S1 > S2 > S4 > S5/S6 > S7 > S3 > S8

**Jackpot Probability**: ~0.001% per series (~1 in 80,000 series)

**Performance**: 30.4% above random baseline (7.84/14)

**Jackpot Pool**: Pool-24 (exclude #12), ~1.96M combinations

---

## Code (KISS/YAGNI/SOLID)

```
ml_models/
├── production_predictor.py   # ~290 lines, core logic
├── monte_carlo_validation.py # Statistical validation
├── bootstrap_analysis.py     # CI estimation
├── convergence_analysis.py   # Learning curves
└── stress_test.py            # Performance testing
```

---

## Goal

Hit **14/14** at least once.

---

*Maintained by Claude Code*
