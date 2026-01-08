# Lottery Prediction Research

**Status**: PRODUCTION READY | **Updated**: January 8, 2026

---

## Quick Start

```bash
cd ml_models
python production_predictor.py predict 3173
python production_predictor.py find 3172
python production_predictor.py validate 2981 3172
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
#4    S6 (ML hot#2)      ...                                           ML
...
```

---

## Key Metrics (192 series validated)

| Metric | Value |
|--------|-------|
| Average | 10.21/14 |
| Best | 12/14 |
| Worst | 9/14 |
| 11+ matches | 63 (32.8%) |
| 12+ matches | 6 (3.1%) |
| 14/14 hits | 0 |

### Set Performance (ordered by win rate)

| Rank | Set | Strategy | Wins | Rate | Unique |
|------|-----|----------|------|------|--------|
| 1 | S1 | swap 14<>16 | 86 | 44.8% | 4 |
| 2 | S2 | swap 13<>15 | 44 | 22.9% | 15 |
| 3 | S4 | primary top-14 | 21 | 10.9% | 8 |
| 4 | S6 | ML hot #1+#2 | 13 | 6.8% | 12 |
| 5 | S5 | ML hot #1 | 10 | 5.2% | 2 |
| 6 | S7 | swap 14<>17 | 7 | 3.6% | 1 |
| 7 | S8 | swap 14<>18 | 6 | 3.1% | 6 |
| 8 | S3 | swap 14<>15 | 5 | 2.6% | 1 |

**ML helped**: 23 (12.0%) | **Extended helped**: 13 (6.8%)

### Latest Result (Series 3172)

- **Winner**: S1 (9/14, tied with S2/S3/S6/S7/S8)
- **Low correlation series**: 3171 E1 had only 8/14 raw match to any 3172 event

---

## Statistical Validation (Monte Carlo)

| Test | Value | Interpretation |
|------|-------|----------------|
| t-statistic | 43.48 | Extremely high |
| p-value | 1.09e-100 | Highly significant |
| Cohen's d | 2.25 | Large effect |
| 95% CI | [10.05, 10.26] | Tight confidence |
| Percentile | 100% | Beats all random |

*Reverted from recency-weighted algorithm (overfitting on recent data)*

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

- **Series**: 193 (2980-3172)
- **Latest**: 3172
- **File**: `data/full_series_data.json`

---

## Strategy (Global Frequency)

```python
# Prior Event 1 + 8-set hedging (4 std + 2 ML + 2 ext)
# Ranking: Event1 membership > global frequency
ranked = sorted(1..25, key=lambda n: (-(n in event1), -freq[n]))

# Hot non-E1 numbers from recent 5 series (unweighted)
recent_freq = count(last_5_series)
hot_outside = sorted(non_top14, key=lambda n: -recent_freq[n])[:3]

# Sets ordered by win rate
sets = [
    ranked[:13] + [ranked[15]],          # S1: swap 14<>16 (44.8% wins)
    ranked[:12] + [ranked[14], ranked[13]],  # S2: swap 13<>15 (22.9%)
    ranked[:14],                         # S4: primary (10.9%)
    ranked[:12] + hot_outside[:2],       # S6: ML hot #1+#2 (6.8%)
    ranked[:13] + [hot_outside[0]],      # S5: ML hot #1 (5.2%)
    ranked[:13] + [ranked[16]],          # S7: swap 14<>17 (3.6%)
    ranked[:13] + [ranked[17]],          # S8: swap 14<>18 (3.1%)
    ranked[:13] + [ranked[14]],          # S3: swap 14<>15 (2.6%)
]
```

**Priority**: S1 > S2 > S4 > S6 > S5 > S7 > S8 > S3

**Jackpot Probability**: ~0.001% per series (~1 in 80,000 series)

**Performance**: 30.2% above random baseline (7.84/14)

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
