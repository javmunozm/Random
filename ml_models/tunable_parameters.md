# Tunable Parameters Specification

**Author**: model-analysis-expert
**Date**: 2026-01-26
**Purpose**: Define all tunable parameters for evolutionary algorithm implementation

---

## Executive Summary

Analysis of `production_predictor.py` identifies **8 tunable parameter categories**. Based on L30 performance analysis, **3 parameters show measurable variance** that could benefit from adaptive tuning:

1. **DIRECT_EVENTS** - Which events to copy directly (highest impact)
2. **FUSION_PAIRS** - Which event pairs to fuse (moderate impact)
3. **BOUNDARY_RANK** - Which rank positions to include (low-moderate impact)

Other parameters (window size, anti-E1 weighting, top-N) show minimal variance and are not recommended for initial tuning.

---

## Parameter Categories

### 1. DIRECT_EVENTS - Direct Event Copy Selection

**Current Setting**: E3, E4, E6, E7 (sets S3, S5, S7, S8)

**Possible Values**: Any subset of {E1, E2, E3, E4, E5, E6, E7}

**L30 Performance Analysis**:
| Event | Avg Score | 11+ Rate | 12+ Rate |
|-------|-----------|----------|----------|
| E4    | 9.63/14   | 13%      | 0%       |
| E6    | 9.60/14   | 13%      | 0%       |
| E7    | 9.60/14   | 13%      | 3%       |
| E5    | 9.50/14   | 10%      | 0%       |
| E2    | 9.43/14   | 10%      | 0%       |
| E1    | 9.40/14   | 7%       | 0%       |
| E3    | 9.37/14   | 3%       | 0%       |

**Tuning Strategy**:
- Track which direct event copy wins each L10 window
- Promote top 3-4 performers to active set
- Demote consistently underperforming events
- Swap cold events (E3) for potentially warmer ones (E5)

**Expected Impact**: HIGH - E4 vs E3 is 0.26 point difference (2.8% improvement potential)

**Implementation**:
```python
# Instead of fixed:
sets[2] = sorted(event4)  # S3: E4 directly
sets[4] = sorted(event6)  # S5: E6 directly
sets[6] = sorted(event3)  # S7: E3 directly
sets[7] = sorted(event7)  # S8: E7 directly

# Adaptive:
active_direct_events = select_top_n_events(performance_history, n=4)
for i, event_idx in enumerate(active_direct_events):
    sets[direct_slots[i]] = sorted(data[prior][event_idx])
```

---

### 2. FUSION_PAIRS - Event Fusion Combinations

**Current Setting**: E1&E6, E3&E7, E6&E7 (sets S6, S11, S12)

**Possible Values**: Any of 21 unique pairs from {E1-E7}

**L30 Performance Analysis (Top 10)**:
| Fusion  | Avg Score | 11+ Rate | 12+ Rate |
|---------|-----------|----------|----------|
| E3&E6   | 9.93/14   | 23%      | 3%       |
| E4&E6   | 9.87/14   | 20%      | 3%       |
| E3&E5   | 9.73/14   | 10%      | 3%       |
| E6&E7   | 9.73/14   | 20%      | 0%       |
| E2&E5   | 9.70/14   | 10%      | 0%       |
| E3&E7   | 9.70/14   | 13%      | 7%       |
| E5&E7   | 9.70/14   | 20%      | 0%       |
| E2&E6   | 9.67/14   | 23%      | 3%       |
| E4&E5   | 9.67/14   | 7%       | 0%       |
| E5&E6   | 9.67/14   | 13%      | 0%       |

**Key Finding**: E3&E6 (9.93) outperforms current E1&E6 (9.57) by 0.36 points!

**Tuning Strategy**:
- Track fusion pair wins over L10 window
- Replace underperforming fusions with top performers
- Current E1&E6 should be swapped for E3&E6

**Expected Impact**: MODERATE-HIGH - 0.36 point improvement potential (3.8%)

**Implementation**:
```python
# Current (static):
fusion_slots = [(0, 5), (2, 6), (5, 6)]  # E1&E6, E3&E7, E6&E7

# Adaptive:
top_fusions = select_top_n_fusions(performance_history, n=3)
for i, (e1, e2) in enumerate(top_fusions):
    sets[fusion_slots[i]] = create_fusion(events[e1], events[e2], freq)
```

---

### 3. BOUNDARY_RANK - E1 Boundary Position Selection

**Current Setting**: rank15, rank16 (sets S1, S2, S4)

**Possible Values**: rank14, rank15, rank16, rank17, rank18

**L30 Performance Analysis**:
| Position | Avg Score | 11+ Rate | 12+ Rate |
|----------|-----------|----------|----------|
| rank18   | 9.67/14   | 13%      | 0%       |
| rank15   | 9.60/14   | 20%      | 0%       |
| rank16   | 9.60/14   | 13%      | 0%       |
| rank17   | 9.60/14   | 17%      | 0%       |
| rank14   | 9.40/14   | 7%       | 0%       |

**Tuning Strategy**:
- Track which boundary position wins in L10
- Rotate underperforming positions
- rank14 consistently underperforms - never use

**Expected Impact**: LOW-MODERATE - 0.07-0.27 point variance

**Implementation**:
```python
# Current (static):
boundary_positions = [15, 16]  # For S1, S2

# Adaptive:
active_boundaries = select_top_n_boundaries(performance_history, n=2)
sets[0] = sorted(ranked[:13] + [ranked[active_boundaries[0] - 1]])
sets[1] = sorted(ranked[:13] + [ranked[active_boundaries[1] - 1]])
```

---

### 4. RECENT_WINDOW - Hot Number Calculation Window

**Current Setting**: 3 series

**Possible Values**: 1, 2, 3, 5, 7, 10

**L30 Performance Analysis**:
| Window | Avg Score | 11+ Rate | 12+ Rate |
|--------|-----------|----------|----------|
| 1      | 9.57/14   | 13%      | 0%       |
| 3      | 9.57/14   | 20%      | 3%       |
| 2      | 9.50/14   | 17%      | 3%       |
| 10     | 9.50/14   | 17%      | 0%       |
| 7      | 9.47/14   | 17%      | 3%       |
| 5      | 9.43/14   | 17%      | 3%       |

**Tuning Strategy**: Minimal variance (0.14 points max). Current value of 3 is optimal.

**Expected Impact**: VERY LOW - Not recommended for initial tuning

---

### 5. ANTI_E1_BONUS - Anti-E1 Weighting Factor

**Current Setting**: 2 (bonus for numbers NOT in E1)

**Possible Values**: 1, 1.5, 2, 2.5, 3, 4

**L30 Performance Analysis**:
| Bonus | Avg Score | 11+ Rate | 12+ Rate |
|-------|-----------|----------|----------|
| 4     | 9.67/14   | 13%      | 0%       |
| 2.5   | 9.63/14   | 10%      | 0%       |
| 3     | 9.63/14   | 10%      | 0%       |
| 1     | 9.60/14   | 7%       | 3%       |
| 2     | 9.57/14   | 3%       | 0%       |
| 1.5   | 9.47/14   | 3%       | 3%       |

**Tuning Strategy**: Higher weights (4) perform slightly better but minimal variance.

**Expected Impact**: VERY LOW - Not recommended for initial tuning

---

### 6. TOP_N - E1-Based Core Selection

**Current Setting**: top-13 (then fill with boundary ranks)

**Possible Values**: top-11, top-12, top-13

**L30 Performance Analysis**:
| Top-N  | Avg Score | 11+ Rate | 12+ Rate |
|--------|-----------|----------|----------|
| top-11 | 9.73/14   | 17%      | 0%       |
| top-12 | 9.67/14   | 17%      | 3%       |
| top-13 | 9.60/14   | 20%      | 0%       |

**Key Finding**: Smaller top-N allows more boundary diversity but minimal impact.

**Expected Impact**: LOW - 0.13 point variance

---

### 7. SET_ALLOCATION - Which Strategy Types to Include

**Current Setting**: 3 E1-based, 4 direct, 5 fusion/hybrid

**Possible Values**: Various allocations of 12 slots

**Analysis**: The current split emerged from L30 optimization. However, win distribution suggests:
- E1-based: 78 wins (39%)
- Direct: 36 wins (18%)
- Fusion: 86 wins (43%)

**Tuning Strategy**: Could shift 1-2 slots from direct to fusion based on recent performance.

**Expected Impact**: MODERATE - But high complexity

---

### 8. PERF_RANK - Performance-Based Ranking

**Current Setting**: Static ranking from L30 snapshot (updated manually)

**Possible Values**: Dynamic ranking updated after each series

**Implementation**:
```python
# Current (static):
PERF_RANK = [3, 4, 1, 5, 7, 8, 11, 9, 12, 10, 2, 6]

# Adaptive:
def update_perf_rank(results, window=10):
    wins = count_wins_per_set(results[-window:])
    return sorted(range(12), key=lambda i: -wins[i])
```

**Expected Impact**: LOW - Ranking affects display order, not prediction quality

---

## Recommended Tuning Priority

### Phase 1: FUSION_PAIRS (Immediate Impact)

**Rationale**:
- E3&E6 outperforms current E1&E6 by 0.36 points
- Clear signal from L30 data
- Simple swap, measurable improvement

**Action**:
```python
# Replace E1&E6 with E3&E6
sets[5] = sorted(e3_e6_fusion)  # Was E1&E6
```

**Expected Improvement**: +0.3 to +0.4 per prediction

---

### Phase 2: DIRECT_EVENTS (Medium-Term)

**Rationale**:
- E3 (currently included) scores 9.37/14
- E5 (not included) scores 9.50/14
- Potential +0.13 points from swap

**Action**: Replace E3 direct with E5 direct in L10 adaptive mode

---

### Phase 3: BOUNDARY_RANK (Long-Term Adaptive)

**Rationale**:
- Variance is small (0.07-0.27 points)
- But could adapt to local patterns
- Low risk, potential marginal gains

---

## Parameters NOT Recommended for Tuning

| Parameter | Reason |
|-----------|--------|
| RECENT_WINDOW | Variance too small (0.14 max) |
| ANTI_E1_BONUS | Variance too small (0.20 max) |
| TOP_N | Variance too small (0.13 max) |
| PERF_RANK | Affects display only |

---

## Evolutionary Tuning Framework

### Sliding Window Approach

```python
def evolve_parameters(data, start_series, window=10):
    """
    Evolve parameters using L10 sliding window.
    """
    params = {
        'direct_events': [3, 5, 6],      # E3, E5, E6 indices (0-based)
        'fusion_pairs': [(2, 5), (2, 6), (5, 6)],  # E3&E6, E3&E7, E6&E7
        'boundaries': [15, 16],
    }

    for series in range(start_series, latest):
        # 1. Make prediction with current params
        prediction = predict_with_params(data, series, params)

        # 2. Compare to actual result
        result = evaluate(data, series, prediction)

        # 3. Update performance history
        history.append({
            'series': series,
            'result': result,
            'params': params.copy()
        })

        # 4. Every 10 series, re-tune parameters
        if len(history) >= window and len(history) % window == 0:
            params = tune_parameters(history[-window:])

    return history
```

### Tuning Functions

```python
def tune_parameters(recent_history):
    """
    Adjust parameters based on recent performance.
    """
    # Count wins per direct event
    direct_wins = count_wins_by_type(recent_history, 'direct')
    top_direct = sorted(direct_wins.items(), key=lambda x: -x[1])[:4]

    # Count wins per fusion pair
    fusion_wins = count_wins_by_type(recent_history, 'fusion')
    top_fusions = sorted(fusion_wins.items(), key=lambda x: -x[1])[:3]

    # Count wins per boundary
    boundary_wins = count_wins_by_type(recent_history, 'boundary')
    top_boundaries = sorted(boundary_wins.items(), key=lambda x: -x[1])[:2]

    return {
        'direct_events': [e for e, _ in top_direct],
        'fusion_pairs': [f for f, _ in top_fusions],
        'boundaries': [b for b, _ in top_boundaries],
    }
```

---

## Summary

| Parameter | Current | Best Alternative | Delta | Priority |
|-----------|---------|------------------|-------|----------|
| FUSION_PAIRS | E1&E6 | E3&E6 | +0.36 | **1st** |
| DIRECT_EVENTS | E3 | E5 | +0.13 | **2nd** |
| BOUNDARY_RANK | r15,r16 | r17,r18 | +0.07 | **3rd** |
| RECENT_WINDOW | 3 | 3 (optimal) | 0 | Skip |
| ANTI_E1_BONUS | 2 | 4 | +0.10 | Skip |
| TOP_N | 13 | 11 | +0.13 | Skip |

**Total potential improvement from Phase 1-3**: +0.56/14 (from 10.74 to ~11.30)

---

*Generated by model-analysis-expert on 2026-01-26*
