# Priority 3: Potential Improvements - COMPREHENSIVE STUDY

**Date**: November 17, 2025
**Status**: Analysis Phase
**Branch**: `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`

---

## 🎯 Executive Summary

Priority 3 focuses on **potential improvements** that could yield +0.5% to +3.0% gains, but require careful testing due to:

1. **Historical failure rate**: 0/39 improvement attempts succeeded
2. **Performance ceiling**: 70-72% is the realistic maximum
3. **Seed robustness required**: Must work across multiple seeds
4. **Statistical significance**: Need p<0.05 AND CI not including zero

**Key Principle**: Test conservatively, validate rigorously, reject quickly if no improvement.

---

## 📊 Current Baseline

### Model Configuration (After Priority 1 Fixes)
```python
RECENT_SERIES_LOOKBACK = 8 (or 10)  # Needs verification
COLD_NUMBER_COUNT = 7
HOT_NUMBER_COUNT = 7
cold_hot_boost = 30.0               # Seed-robust
CANDIDATE_POOL_SIZE = 10000
seed = 999                          # Or multi-seed ensemble
```

### Performance (Series 3146-3150)
```
Average: 64.3% (9.0/14 numbers)
Range: 57.1% - 71.4%
Peak: 71.4% (Series 3148)
```

### Expected Long-term Performance
- **Historical average**: 67.9% ± 2.04% (24 windows)
- **Typical range**: 64-72% per series
- **True ceiling**: 70-72%

---

## 🔵 PRIORITY 3 IMPROVEMENTS

### 3.1 Weighted Lookback Window 💡

**Status**: Not implemented
**Priority**: MEDIUM-HIGH
**Expected Impact**: +0.5% to +2.0%
**Effort**: Medium (2-3 hours)
**Risk**: Medium

---

#### Hypothesis

Recent series are MORE predictive than older series because:
1. **Pattern drift**: Lottery patterns may shift over time
2. **Recency bias**: More recent data reflects current state
3. **Temporal correlation**: Adjacent series may share patterns

**Counter-argument**: From CEILING_STUDY_RESULTS.md:
- "Temporal Decay Weighting: -7.143%" (FAILED)
- "Deweights historical patterns too aggressively"
- "Old patterns still matter for lottery data"

**Resolution**: Use LIGHT weighting, not aggressive decay

---

#### Implementation Options

**Option 1: Exponential Decay (Recommended)**
```python
def _get_weighted_cold_hot_numbers(self, target_series_id: int):
    """
    Calculate cold/hot numbers with exponential recency weighting

    More recent series get higher weight:
    - Series at t-1: weight = 2^(0/4) = 1.00x
    - Series at t-2: weight = 2^(-1/4) = 0.84x
    - Series at t-3: weight = 2^(-2/4) = 0.71x
    - Series at t-4: weight = 2^(-3/4) = 0.59x
    - Series at t-5: weight = 2^(-4/4) = 0.50x
    - ...
    - Series at t-8: weight = 2^(-7/4) = 0.30x
    """
    if len(self.training_data) < self.RECENT_SERIES_LOOKBACK:
        # Fall back to unweighted if not enough data
        return self._get_unweighted_cold_hot_numbers(target_series_id)

    freq = defaultdict(float)
    recent_series = sorted(self.training_data, key=lambda x: x['series_id'], reverse=True)[:self.RECENT_SERIES_LOOKBACK]

    for i, series in enumerate(recent_series):
        # Exponential decay: more recent = higher weight
        weight = 2 ** (-(i) / 4)  # i=0 (most recent) -> 1.0x, i=7 (oldest) -> 0.30x

        for combo in series['combinations']:
            for num in combo:
                freq[num] += weight

    # Select cold and hot based on weighted frequency
    sorted_freq = sorted(freq.items(), key=lambda x: x[1])
    cold_numbers = set([num for num, _ in sorted_freq[:self.COLD_NUMBER_COUNT]])
    hot_numbers = set([num for num, _ in sorted_freq[-self.HOT_NUMBER_COUNT:]])

    return cold_numbers, hot_numbers
```

**Expected behavior**:
- Most recent series: 1.00x weight
- 4 series ago: 0.71x weight
- 8 series ago: 0.30x weight
- **Gentle** decay, not aggressive

---

**Option 2: Last-4 Heavy**
```python
# Simpler approach: Recent half gets 2x weight
for i, series in enumerate(recent_series):
    weight = 2.0 if i < 4 else 1.0  # Recent 4 get 2x, older 4 get 1x
    # ... rest of logic
```

**Expected behavior**:
- Recent 4 series: 2.0x weight
- Older 4 series: 1.0x weight
- **Step function** instead of smooth decay

---

**Option 3: Linear Decay**
```python
# Linearly increasing weights from oldest to newest
for i, series in enumerate(recent_series):
    weight = (self.RECENT_SERIES_LOOKBACK - i) / self.RECENT_SERIES_LOOKBACK
    # i=0 (most recent) -> 8/8 = 1.00x
    # i=7 (oldest) -> 1/8 = 0.125x
```

**Expected behavior**:
- Most recent: 1.00x weight
- 4 series ago: 0.50x weight
- 8 series ago: 0.125x weight
- **More aggressive** decay than exponential

---

#### Testing Plan

**Phase 1: Implementation**
- [ ] Implement all 3 weighting schemes
- [ ] Create `_get_weighted_cold_hot_numbers()` method
- [ ] Add configuration option: `USE_WEIGHTED_LOOKBACK = True/False`
- [ ] Preserve unweighted as fallback

**Phase 2: Validation (Single Seed)**
- [ ] Test on Series 3140-3150 (11 series) with seed 999
- [ ] Compare each approach vs baseline (unweighted)
- [ ] Measure average accuracy, peak, and consistency
- [ ] Identify best-performing approach

**Phase 3: Seed Robustness**
- [ ] Test winner with seeds: 42, 123, 456, 789, 999
- [ ] Calculate average performance across all seeds
- [ ] Verify improvement is NOT seed-specific
- [ ] Require consistent gains across ≥3 seeds

**Phase 4: Statistical Validation**
- [ ] Paired t-test: p-value < 0.05 required
- [ ] Bootstrap 95% CI: Must not include zero
- [ ] Cohen's d effect size: ≥ 0.3 (medium effect)
- [ ] Reject if any test fails

**Adoption Criteria**:
- ✅ Average improvement ≥ +0.5% on validation set
- ✅ Seed-robust (works with ≥3 different seeds)
- ✅ Statistically significant (p < 0.05)
- ✅ Confidence interval does not include zero
- ✅ No performance degradation on any seed

**Files to Create**:
- `test_weighted_lookback.py` (test script)
- `WEIGHTED_LOOKBACK_RESULTS.md` (results documentation)

---

#### Risk Assessment

**Why It Might Work**:
- ✅ Gentle weighting preserves historical patterns
- ✅ Emphasizes recent trends without discarding old data
- ✅ Aligns with intuition about temporal correlation
- ✅ Low implementation complexity

**Why It Might Fail**:
- ❌ Previous temporal decay test failed (-7.1%)
- ❌ Lottery data may have NO temporal correlation
- ❌ Could reduce effective training data
- ❌ May be overfitting to recent anomalies

**Probability of Success**: **30-40%**

**Recommendation**: Test exponential decay first (gentlest approach)

---

### 3.2 Triplet Affinity Tracking 💡

**Status**: ⚠️ **ALREADY IMPLEMENTED** (Basic version)
**Priority**: MEDIUM
**Expected Impact**: +1.0% to +3.0% if enhanced
**Effort**: High (4-6 hours for enhancements)
**Risk**: Medium

---

#### Current Implementation

**Already in `true_learning_model.py`**:
```python
# Line 110: Initialization
self.triplet_affinities = {}

# Lines 257-263: Learning
def _learn_triplet_affinities(self, combination: List[int]):
    """Learn 3-number patterns"""
    for i in range(len(combination)):
        for j in range(i + 1, len(combination)):
            for k in range(j + 1, len(combination)):
                triplet = tuple(sorted([combination[i], combination[j], combination[k]]))
                self.triplet_affinities[triplet] = self.triplet_affinities.get(triplet, 0.0) + self.learning_rate

# Lines 378-391: Scoring
def _calculate_triplet_affinity_score(self, combination: List[int]) -> float:
    """Calculate triplet affinity score"""
    if not self.triplet_affinities:
        return 0.0

    affinity_score = 0.0
    for i in range(len(combination)):
        for j in range(i + 1, len(combination)):
            for k in range(j + 1, len(combination)):
                triplet = tuple(sorted([combination[i], combination[j], combination[k]]))
                if triplet in self.triplet_affinities:
                    affinity_score += self.triplet_affinities[triplet]

    return affinity_score * self.TRIPLET_AFFINITY_MULTIPLIER  # Currently 35.0x
```

**Current Configuration**:
- Multiplier: 35.0x (line 58: `TRIPLET_AFFINITY_MULTIPLIER = 35.0`)
- Learning: Active (called in `_learn_triplet_affinities`)
- Scoring: Active (called in `_calculate_score`)

---

#### Analysis: Why Not Showing Improvement?

**Potential Issues**:

1. **Multiplier Too Low/High**
   - Current: 35.0x
   - Pair affinity: 25.0x
   - Ratio: 35/25 = 1.4x
   - **May need tuning**: Test 20x, 30x, 40x, 50x

2. **Sparse Data Problem**
   - C(25,3) = 2,300 possible triplets
   - C(14,3) = 364 triplets per event
   - 171 series × 7 events = 1,197 events
   - Each triplet appears ~0.5-1 times on average
   - **Too sparse to learn meaningful patterns?**

3. **Computational Overhead**
   - 364 triplets × 10,000 candidates = 3.64M lookups
   - May slow down without caching
   - **Current implementation: No caching**

4. **No Pruning**
   - Tracks ALL triplets (unbounded dictionary)
   - Many triplets appear only once (noise)
   - **Should prune triplets with frequency < 3?**

---

#### Proposed Enhancements

**Enhancement 1: Optimize Multiplier** (Low effort, high impact)
```python
# Test different multipliers
TRIPLET_MULTIPLIERS_TO_TEST = [20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0]

# Current baseline: 35.0x
# Test if different value improves performance
```

**Enhancement 2: Top-K Pruning** (Medium effort, medium impact)
```python
def _prune_triplet_affinities(self, top_k=200):
    """Keep only top K most frequent triplets to reduce noise"""
    if len(self.triplet_affinities) <= top_k:
        return

    # Sort by frequency, keep top K
    sorted_triplets = sorted(self.triplet_affinities.items(), key=lambda x: x[1], reverse=True)
    self.triplet_affinities = dict(sorted_triplets[:top_k])
```

**Enhancement 3: Minimum Frequency Threshold** (Low effort, medium impact)
```python
def _calculate_triplet_affinity_score(self, combination: List[int]) -> float:
    """Calculate triplet affinity score (only count frequent triplets)"""
    if not self.triplet_affinities:
        return 0.0

    affinity_score = 0.0
    MIN_FREQUENCY = 3  # Only count triplets seen ≥3 times

    for i in range(len(combination)):
        for j in range(i + 1, len(combination)):
            for k in range(j + 1, len(combination)):
                triplet = tuple(sorted([combination[i], combination[j], combination[k]]))
                if triplet in self.triplet_affinities:
                    freq = self.triplet_affinities[triplet]
                    if freq >= MIN_FREQUENCY:  # Filter noise
                        affinity_score += freq

    return affinity_score * self.TRIPLET_AFFINITY_MULTIPLIER
```

**Enhancement 4: Caching (Performance)** (High effort, low impact on accuracy)
```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def _get_triplets_from_candidate(self, candidate_tuple):
    """Cache triplet generation (candidate must be tuple for hashing)"""
    triplets = []
    candidate = list(candidate_tuple)
    for i in range(len(candidate)):
        for j in range(i + 1, len(candidate)):
            for k in range(j + 1, len(candidate)):
                triplets.append(tuple(sorted([candidate[i], candidate[j], candidate[k]])))
    return triplets
```

---

#### Testing Plan

**Phase 1: Multiplier Tuning**
- [ ] Test multipliers: 20x, 25x, 30x, 35x, 40x, 50x
- [ ] Validate on Series 3146-3150
- [ ] Keep current implementation, just change multiplier
- [ ] Find optimal value

**Phase 2: Pruning Tests**
- [ ] Implement Top-K pruning (K=100, 200, 500)
- [ ] Implement minimum frequency threshold (min=2, 3, 5)
- [ ] Test combinations
- [ ] Measure impact on performance and memory

**Phase 3: Seed Robustness**
- [ ] Test winner with seeds: 42, 123, 456, 789, 999
- [ ] Verify improvement across ≥3 seeds
- [ ] Statistical validation (p<0.05)

**Adoption Criteria**:
- ✅ Average improvement ≥ +1.0% (higher bar than weighted lookback)
- ✅ Seed-robust (works with ≥3 different seeds)
- ✅ Statistically significant (p < 0.05)
- ✅ No significant runtime increase (< 2x slower)

**Files to Create**:
- `test_triplet_optimization.py` (test script)
- `TRIPLET_OPTIMIZATION_RESULTS.md` (results)

---

#### Risk Assessment

**Why It Might Work**:
- ✅ Already implemented (just needs tuning)
- ✅ Captures 3-way correlations (beyond pairs)
- ✅ More specific patterns than pairs
- ✅ Low implementation risk (already tested)

**Why It Might Fail**:
- ❌ Data too sparse (2,300 possible triplets, 1,197 events)
- ❌ Most triplets appear only once (noise)
- ❌ Current 35x multiplier may already be optimal
- ❌ Lottery data may have no 3-way correlations

**Probability of Success**: **20-30%**

**Recommendation**: Start with multiplier tuning (lowest effort)

---

### 3.3 Fine-Tune Lookback Window (9 vs 8) 💡

**Status**: Tied in previous tests
**Priority**: LOW
**Expected Impact**: 0% to +0.5%
**Effort**: Trivial (10 minutes)
**Risk**: Very Low

---

#### Current Status

**From COMPLETE_TESTING_SUMMARY_NOV11.md**:
```
Lookback Window Test Results:
 6-series: 66.327% (-5.102%) ❌ WORSE
 7-series: 66.327% (-5.102%) ❌ WORSE
 8-series: 71.429% (BASELINE) ✅
 9-series: 71.429% (+0.000%) ⚠️ TIE
10-series: 68.367% (-3.061%) ❌ WORSE
```

**Observation**: 8 and 9 are EXACTLY tied at 71.429%

---

#### Question

Which performs better on NEW data (Series 3146-3150)?

**Hypothesis 1**: 8-series is optimal (simpler, less noise)
**Hypothesis 2**: 9-series is optimal (more context)
**Hypothesis 3**: Still tied (no difference)

---

#### Implementation

**Currently**:
```python
RECENT_SERIES_LOOKBACK = 10  # Line 36 in true_learning_model.py
```

**Wait, the model shows 10, not 8!** This is inconsistent with test results.

**Need to verify**: What is the ACTUAL current lookback value?

---

#### Testing Plan

**Simple Test**:
```python
# Test both configurations
for lookback in [8, 9, 10]:
    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = lookback

    # Test on Series 3146-3150
    # Record average accuracy

    # Test with seeds 42, 123, 999
    # Check for seed-robustness
```

**Adoption Criteria**:
- Winner must beat others by ≥0.5%
- Must be seed-robust
- If still tied: Keep 8 (simpler)

**Files to Create**:
- `test_lookback_8_vs_9_vs_10.py`
- `LOOKBACK_COMPARISON_RESULTS.md`

---

#### Risk Assessment

**Probability of Success**: **10-20%** (likely still tied)

**Recommendation**: Test quickly, low priority

---

### 3.4 Flexible Gap/Cluster Detection ⚠️

**Status**: Hard constraints FAILED (-3.1%)
**Priority**: LOW (Only if 3.1-3.2 fail)
**Expected Impact**: -2.0% to +2.0% (HIGH VARIANCE)
**Effort**: High (6-8 hours)
**Risk**: HIGH

---

#### Previous Failure

**From documentation**:
- "Gap/Cluster Detection: -3.1%" (FAILED)
- "Hard constraints (exclusion) failed"
- "Rigid patterns hurt performance"

**Why it failed**:
- Excluded valid candidates based on gaps
- Assumed lottery follows distribution patterns
- Too restrictive

---

#### New Approach: Soft Constraints

Instead of **excluding** candidates with bad gaps, **penalize** them slightly.

**Implementation**:
```python
def _apply_soft_gap_cluster_constraints(self, candidate: List[int], score: float) -> float:
    """
    Apply SOFT penalties/bonuses based on gaps and clusters
    Does NOT exclude candidates, just adjusts scores
    """
    # Calculate gaps between consecutive numbers
    gaps = [candidate[i+1] - candidate[i] for i in range(len(candidate)-1)]
    avg_gap = sum(gaps) / len(gaps)  # Should be ~1.8 for 14 numbers in range 1-25

    # SOFT penalty for very large gaps (not exclusion!)
    for gap in gaps:
        if gap > avg_gap * 2.5:  # Large gap (>4.5)
            score *= 0.98  # Small 2% penalty

    # SOFT bonus for clusters (consecutive numbers)
    consecutive_count = sum(1 for gap in gaps if gap == 1)
    if consecutive_count >= 2:  # At least 2 pairs of consecutive numbers
        score *= 1.02  # Small 2% bonus

    return score
```

**Key Differences from Hard Constraints**:
- ✅ Does NOT exclude candidates
- ✅ Only adjusts scores (98% or 102%)
- ✅ Very gentle penalties/bonuses
- ✅ Can be overridden by other strong signals

---

#### Testing Plan

**Phase 1: Implementation**
- [ ] Implement soft constraint function
- [ ] Add to `_calculate_score()` method
- [ ] Test penalty/bonus values: (0.95, 1.05), (0.98, 1.02), (0.99, 1.01)

**Phase 2: Validation**
- [ ] Test on Series 3146-3150
- [ ] Compare vs baseline (no constraints)
- [ ] Measure impact

**Phase 3: Decision**
- [ ] **ONLY proceed if 3.1 and 3.2 showed NO improvement**
- [ ] This is a last resort approach
- [ ] Reject immediately if performance drops

**Adoption Criteria**:
- ✅ Must improve by ≥+1.0% (high bar)
- ✅ Seed-robust
- ✅ Statistically significant
- ⚠️ **HIGH RISK** - Likely to fail based on history

---

#### Risk Assessment

**Probability of Success**: **5-10%** (very low)

**Recommendation**: **DO NOT PURSUE** unless desperate

Previous hard constraint approach failed. Soft constraints unlikely to succeed where hard constraints failed.

---

## 📋 Recommended Testing Order

### Week 1: Low-Hanging Fruit
1. **Day 1-2**: Test Lookback 8 vs 9 vs 10 (30 min implementation, 1 hour testing)
   - Simplest test
   - Verify current configuration
   - Low risk

2. **Day 3-4**: Triplet Multiplier Tuning (2 hours)
   - Already implemented
   - Just test different multipliers
   - Medium chance of improvement

3. **Day 5**: Analyze results, decide next steps

### Week 2: Higher Effort Tests
4. **Day 1-3**: Weighted Lookback Window (2-3 hours implementation, 2 hours testing)
   - Highest expected impact (+0.5-2.0%)
   - Medium implementation effort
   - Test all 3 approaches

5. **Day 4-5**: Triplet Pruning/Filtering (if multiplier tuning showed promise)
   - Implement Top-K pruning
   - Test minimum frequency thresholds

### Week 3: Decision & Documentation
6. **Day 1-2**: Statistical validation of any promising approaches
   - Multi-seed testing
   - p-value calculations
   - Confidence intervals

7. **Day 3-4**: Documentation and code cleanup

8. **Day 5**: Final recommendation

**SKIP**: Gap/cluster detection (too risky, low success probability)

---

## ✅ Success Criteria Summary

For ANY improvement to be adopted:

1. **Performance**:
   - ✅ Average improvement ≥ +0.5% (or +1.0% for high-risk)
   - ✅ Tested on ≥10 validation series
   - ✅ No degradation on any seed

2. **Seed Robustness**:
   - ✅ Works with seeds: 42, 123, 456, 789, 999
   - ✅ Average across seeds must be positive
   - ✅ No seed shows >5% degradation

3. **Statistical Significance**:
   - ✅ p-value < 0.05 (paired t-test)
   - ✅ 95% Confidence interval does not include zero
   - ✅ Cohen's d ≥ 0.3 (medium effect size)

4. **Implementation Quality**:
   - ✅ No significant runtime increase (<2x slower)
   - ✅ Code documented and tested
   - ✅ Backward compatible

---

## 🎯 Expected Outcomes

### Optimistic Scenario (20% probability)
- Weighted lookback: +1.0%
- Triplet tuning: +0.5%
- **Total: +1.5%**
- **New average: 65.8%** (was 64.3%)

### Realistic Scenario (50% probability)
- Weighted lookback: +0.3%
- Triplet tuning: +0.0%
- Lookback 8vs9: +0.0%
- **Total: +0.3%**
- **New average: 64.6%** (marginal)

### Pessimistic Scenario (30% probability)
- All tests: +0.0% or negative
- **No adoption**
- **Average remains: 64.3%**

**Most Likely**: Marginal or no improvement

**Reason**: 39 previous attempts failed, ceiling is real

---

## ⚠️ Warnings & Lessons

### From Previous Failures

1. **Don't overfit to validation set**
   - Test on UNSEEN data (Series 3151+)
   - Reserve 20% holdout set

2. **Reject quickly**
   - If first test shows no improvement, STOP
   - Don't waste time on failed approaches

3. **Seed robustness is critical**
   - Single-seed success = likely overfitting
   - Always test with 5 seeds minimum

4. **Statistical significance required**
   - p-value > 0.05 = NOT significant
   - Don't deploy based on luck

5. **Simpler is often better**
   - Complex features often hurt more than help
   - Phase 1 Pure beat all 9 alternatives

---

## 📁 Files to Create

### Test Scripts
- `test_lookback_8_vs_9_vs_10.py`
- `test_weighted_lookback.py`
- `test_triplet_optimization.py`
- `test_soft_constraints.py` (optional, low priority)

### Results Documentation
- `LOOKBACK_COMPARISON_RESULTS.md`
- `WEIGHTED_LOOKBACK_RESULTS.md`
- `TRIPLET_OPTIMIZATION_RESULTS.md`
- `PRIORITY_3_FINAL_REPORT.md` (summary)

### Code Enhancements (if adopted)
- Modify `true_learning_model.py` with successful improvements
- Add configuration flags for each feature
- Update documentation

---

## 🏁 Conclusion

Priority 3 improvements have **low to medium probability of success** based on:
- Historical 0/39 success rate
- Performance ceiling (70-72%)
- Data randomness limitations

**Recommended approach**:
1. Test low-effort improvements first (lookback, multiplier)
2. Validate rigorously (seeds, statistics)
3. Reject quickly if no improvement
4. Accept that ceiling may be reached
5. Focus on stability and documentation if no gains found

**Realistic expectation**: 0-1.5% improvement at best, more likely 0%

**Time budget**: 2-3 weeks maximum, then move to Priority 4 (documentation)

---

**Study Completed**: November 17, 2025
**Next Action**: Implement test scripts for Priority 3.1-3.3
**Skip**: Priority 3.4 (gap/cluster detection - too risky)
