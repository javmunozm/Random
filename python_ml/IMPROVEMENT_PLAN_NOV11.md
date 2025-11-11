# Python ML Improvement Plan - November 11, 2025

**Current Performance**: 71.4% average (8-series lookback, 30x boost, seed 999)
**Historical Ceiling**: 70-72% (from walk-forward validation)
**Status**: Currently ABOVE ceiling (95.8th percentile performance)

---

## Executive Summary

After comprehensive testing (6 improvement attempts, 0 succeeded), we've identified **6 unexplored opportunities** for further optimization. Current performance (71.4%) is already above the historical ceiling (70-72%), so improvements must be approached cautiously with realistic expectations.

**Realistic Goals**:
- Fine-tuning: +0.5-1.5% possible
- New features: +1-3% if lucky
- Total potential: +2-4% at absolute best
- More likely: +0.5-2% or regression to mean

---

## Current Baseline

### Validated Configuration (Nov 10, 2025)
```python
RECENT_SERIES_LOOKBACK = 8      # Lookback window
COLD_NUMBER_COUNT = 7            # Cold numbers
HOT_NUMBER_COUNT = 7             # Hot numbers
cold_hot_boost = 30.0            # Boost multiplier
CANDIDATE_POOL_SIZE = 10000      # Pool size
seed = 999                       # Random seed
```

### Performance Metrics
- **Average Best Match**: 71.4% (10.0/14 numbers)
- **Peak Performance**: 78.6% (11/14 numbers)
- **Validation**: 7 series (3140-3147)
- **Improvement vs C# baseline**: +4.7%

---

## Rejected Approaches (Do NOT Retry)

| Approach | Impact | Reason |
|----------|--------|--------|
| Adaptive Learning Rate | -3.6% | Feedback loops cause instability |
| Position-Based Learning | +0.0% | Redundant information |
| Confidence-Based Selection | -4.5% | Dilutes best predictions |
| Temporal Decay Weighting | -7.1% | Deweights valuable historical data |
| Cross-Series Momentum | -9.8% | No momentum in random data |
| Ensemble Voting | -1.5% | Averages dilute quality |

**Success Rate**: 0/6 (0%)

---

## Improvement Opportunities (Prioritized)

### 🔥 HIGH PRIORITY - Quick Wins (Low Effort, Low Risk)

#### 1. Fine-Tune Lookback Window
**Current**: 8 series
**Test**: 6, 7, 9, 10 series
**Expected Gain**: +0.5% to +1.5%
**Effort**: LOW
**Risk**: LOW

**Rationale**: We found 8-series is optimal vs 12/16/20, but haven't tested immediate neighbors (6, 7, 9, 10).

**Test Plan**:
```python
# Test each lookback with 30x boost
lookback_tests = [6, 7, 9, 10]
validation_series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

for lookback in lookback_tests:
    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = lookback
    # Validate on 7 series...
```

**Success Criteria**: Must beat 71.4% by ≥0.5% on average

---

#### 2. Fine-Tune Cold/Hot Boost
**Current**: 30x
**Test**: 27x, 28x, 29x, 31x, 32x
**Expected Gain**: +0.3% to +1.0%
**Effort**: LOW
**Risk**: LOW

**Rationale**: We tested 10x, 25x, 50x, 75x, 100x but not fine increments around optimal 30x.

**Test Plan**:
```python
# Test each boost with 8-series lookback
boost_tests = [27.0, 28.0, 29.0, 31.0, 32.0]
validation_series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

for boost in boost_tests:
    model = TrueLearningModel(seed=999, cold_hot_boost=boost)
    model.RECENT_SERIES_LOOKBACK = 8
    # Validate on 7 series...
```

**Success Criteria**: Must beat 71.4% by ≥0.3% on average

---

#### 3. Different Cold/Hot Counts
**Current**: 7 cold + 7 hot
**Test**: 5+5, 6+6, 8+8, 9+9, 10+10
**Expected Gain**: +0.5% to +1.5%
**Effort**: LOW
**Risk**: LOW

**Rationale**: Currently hardcoded at 7+7, but haven't tested if different counts work better.

**Test Plan**:
```python
# Test each cold/hot count combination
count_tests = [5, 6, 8, 9, 10]
validation_series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

for count in count_tests:
    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = 8
    model.COLD_NUMBER_COUNT = count
    model.HOT_NUMBER_COUNT = count
    # Validate on 7 series...
```

**Success Criteria**: Must beat 71.4% by ≥0.5% on average

---

### 🟡 MEDIUM PRIORITY - Potential Wins (Medium Effort, Medium Risk)

#### 4. Weighted Lookback Window
**Current**: All 8 series weighted equally
**Test**: Recent series weighted higher
**Expected Gain**: +0.5% to +2.0%
**Effort**: MEDIUM
**Risk**: MEDIUM

**Rationale**: Most recent series might be MORE predictive than older ones. Use exponential or linear decay weighting.

**Approaches to Test**:
1. **Last 4 series 2x weight**: Recent 4 get 2x, older 4 get 1x
2. **Exponential decay**: weight = 2^(-(lookback-position)/4)
3. **Linear decay**: weight = 1.0 - (lookback-position)/lookback

**Test Plan**:
```python
# Implement weighted cold/hot frequency calculation
def get_weighted_cold_hot(data, target_series, lookback=8, decay='exponential'):
    freq = defaultdict(float)
    for i, sid in enumerate(range(target_series-lookback, target_series)):
        if decay == 'exponential':
            weight = 2 ** (-(lookback - i) / 4)
        elif decay == 'linear':
            weight = (i + 1) / lookback
        else:  # last_4_heavy
            weight = 2.0 if i >= 4 else 1.0

        for event in data[sid]:
            for num in event:
                freq[num] += weight
    # Select cold/hot based on weighted frequency...
```

**Success Criteria**: Must beat 71.4% by ≥1.0% on average

---

#### 5. Triplet Affinity Tracking
**Current**: Pair affinity only (2-number combinations)
**Test**: Add triplet affinity (3-number combinations)
**Expected Gain**: +1.0% to +3.0%
**Effort**: HIGH
**Risk**: MEDIUM

**Rationale**: Some 3-number combinations might appear together more than expected by chance.

**Implementation**:
```python
# In TrueLearningModel.__init__:
self.triplet_affinities: Dict[Tuple[int, int, int], float] = {}

# During learning:
def _learn_from_event(self, numbers):
    # Existing pair learning...

    # NEW: Triplet learning
    for i in range(len(numbers)):
        for j in range(i+1, len(numbers)):
            for k in range(j+1, len(numbers)):
                triplet = tuple(sorted([numbers[i], numbers[j], numbers[k]]))
                self.triplet_affinities[triplet] = self.triplet_affinities.get(triplet, 0) + 1

# During scoring:
def _score_candidate(self, candidate):
    score = existing_score

    # NEW: Triplet bonus
    for i in range(len(candidate)):
        for j in range(i+1, len(candidate)):
            for k in range(j+1, len(candidate)):
                triplet = tuple(sorted([candidate[i], candidate[j], candidate[k]]))
                if triplet in self.triplet_affinities:
                    score += self.triplet_affinities[triplet] * 5.0  # Test 5x-15x multiplier
```

**Test Plan**:
- Test triplet boost multipliers: 5x, 10x, 15x
- Validate on 7 series
- Compare to baseline (pairs only)

**Success Criteria**: Must beat 71.4% by ≥1.5% on average

---

### 🔵 LOW PRIORITY - Risky Bets (High Effort, High Risk)

#### 6. Flexible Gap/Cluster Detection
**Previous Attempt**: Hard constraints failed (-3.1%)
**New Approach**: Soft constraints (bonus/penalty)
**Expected Gain**: -2.0% to +2.0%
**Effort**: HIGH
**Risk**: HIGH

**Rationale**: Hard constraints (exclusion) failed, but soft constraints (scoring adjustment) might work.

**Implementation**:
```python
def _apply_soft_constraints(self, candidate, score):
    # Gap penalty: Penalize large gaps between consecutive numbers
    gaps = [candidate[i+1] - candidate[i] for i in range(len(candidate)-1)]
    avg_gap = sum(gaps) / len(gaps)

    # Soft penalty for large gaps (not exclusion)
    for gap in gaps:
        if gap > avg_gap * 2:  # Large gap
            score *= 0.95  # Small penalty

    # Cluster bonus: Reward clusters of 2-3 consecutive numbers
    for gap in gaps:
        if gap == 1:  # Consecutive
            score *= 1.05  # Small bonus

    return score
```

**Test Plan**:
- Test different penalty/bonus values: 0.90-0.98 / 1.02-1.10
- Validate on 7 series
- Compare to baseline (no constraints)

**Success Criteria**: Must beat 71.4% by ≥1.0% on average

**⚠️ WARNING**: This approach failed before. Only pursue if other improvements yield no results.

---

## Testing Methodology

### Standard Validation Protocol

**Validation Series**: 7 series (3140, 3141, 3142, 3143, 3144, 3145, 3147)

**Process**:
1. For each validation series:
   - Train on all data BEFORE target series
   - Generate prediction for target series
   - Compare to actual results
   - Calculate best match % (max across 7 events)
2. Calculate average best match across all 7 series
3. Compare to baseline (71.4%)

**Adoption Criteria**:
- Must improve by ≥0.5% on average
- Must be reproducible (seed 999)
- Must not degrade peak performance (<78.6%)

---

## Execution Plan

### Phase 1: Quick Wins (Est. 2-3 hours)
1. ✅ Review baseline and identify opportunities (DONE)
2. ⏳ Fine-tune lookback window (6, 7, 9, 10)
3. ⏳ Fine-tune boost values (27-32x)
4. ⏳ Test cold/hot counts (5-10)

**Expected Outcome**: +0.5-2.0% improvement

---

### Phase 2: Medium Efforts (Est. 4-6 hours)
1. ⏳ Implement weighted lookback
2. ⏳ Add triplet affinity tracking
3. ⏳ Validate on Series 3148 (when available)

**Expected Outcome**: +1.0-3.0% improvement (if successful)

---

### Phase 3: Deep Research (Est. 8-12 hours)
1. ⏳ Analyze learned vs missed patterns
2. ⏳ Test flexible gap/cluster detection
3. ⏳ Document all findings
4. ⏳ Update CLAUDE.md with results

**Expected Outcome**: Understanding WHY the model works, potential +1-2% if lucky

---

## Success Metrics

### Minimum Success
- Achieve 72.0% average (+0.6% improvement)
- Maintain 78.6% peak performance
- Reproducible with seed 999

### Good Success
- Achieve 72.5-73.0% average (+1.1-1.6% improvement)
- Peak ≥78.6%
- Validated on 10+ series

### Exceptional Success
- Achieve 73.5%+ average (+2.1%+ improvement)
- Peak ≥85.7% (12/14)
- Sustained over 15+ series

**Reality Check**: Given ceiling study findings (67.9% historical avg, 70-72% ceiling), exceptional success is statistically improbable. Focus on minimum/good success.

---

## Risk Management

### Known Risks
1. **Regression to Mean**: Current 71.4% might be lucky period (95.8th percentile)
2. **Overfitting**: Fine-tuning on same 7 series might not generalize
3. **Complexity Cost**: Adding features might add noise, not signal
4. **Time Cost**: High-effort approaches might yield no improvement

### Mitigation Strategies
1. **Always validate on multiple series** (minimum 5)
2. **Test on Series 3148+ when available** (unseen data)
3. **Start with low-effort, low-risk improvements**
4. **Stop if 3 consecutive attempts fail** (likely at ceiling)

---

## Timeline

### Week 1 (Nov 11-17)
- Complete Phase 1 quick wins
- Analyze results
- Decide on Phase 2 go/no-go

### Week 2 (Nov 18-24)
- Implement Phase 2 if Phase 1 shows promise
- Otherwise, focus on analysis and documentation

### Week 3 (Nov 25-30)
- Validate on Series 3148+ actual results
- Deep research if needed
- Finalize documentation

---

## Documentation Requirements

### For Each Test
- Configuration tested
- Validation series used
- Performance metrics (avg, peak, by series)
- Comparison to baseline
- Decision (adopt/reject)
- Rationale

### Files to Create
- `test_lookback_fine_tune.py`
- `test_boost_fine_tune.py`
- `test_cold_hot_counts.py`
- `test_weighted_lookback.py`
- `test_triplet_affinity.py`
- `test_flexible_constraints.py`

### Files to Update
- `CLAUDE.md` - Add "November 11+ Improvements" section
- `PYTHON_ML_SCOPE.md` - Update with new results
- `IMPROVEMENT_SUMMARY_NOV11.md` - This file (ongoing updates)

---

## Next Steps

1. **Start with lookback fine-tuning** (Test 6, 7, 9, 10 series)
2. **If improvement found**: Test boost fine-tuning
3. **If no improvement**: Skip to weighted lookback or triplet affinity
4. **Document everything**: All tests, even failures

---

**Created**: November 11, 2025
**Status**: Phase 0 Complete (Analysis), Phase 1 Ready
**Next Action**: Implement `test_lookback_fine_tune.py`
