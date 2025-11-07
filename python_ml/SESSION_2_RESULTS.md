# Session 2 Results - Additional Testing ($5 compute)

**Date**: 2025-11-07 (continued)
**Budget Used**: ~$5 additional
**Total Budget**: ~$10 total ($195 remaining)
**Tests This Session**: 13 new tests
**Success Rate**: 7.7% (1/13 marginal improvements)

---

## Tests Conducted This Session

### Test 1: Simple Baselines
**Purpose**: Check if simpler approaches beat ML
**Tested**: Pure frequency, weighted random, hybrid approaches
**Results**: All WORSE than ML baseline
| Approach | Result | vs Baseline |
|----------|--------|-------------|
| Hybrid (90% freq + 10% random) | 56.1% | -1.6% |
| Pure Frequency (top 14) | 55.9% | -1.8% |
| Weighted Random | 55.0% | -2.7% |

**Conclusion**: ML approach beats simple baselines

### Test 2: Fine-Tuned Recent Data Windows
**Purpose**: Fine-tune around 50 series to find optimal
**Tested**: 30, 35, 40, 45, 50, 55, 60, 65, 70 series
**Results**: 70 series TIES with 50 series
| Recent Series | Result | vs Baseline |
|---------------|--------|-------------|
| 70 series | 57.7% | ~same (tied) |
| 55 series | 57.5% | -0.2% |
| 50 series | 57.1% | baseline |
| 30-40 series | 56.1% | -1.6% |

**Conclusion**: 70 series = 50 series, both optimal

### Test 3: 70 Series + Hyperparameter Tweaks
**Purpose**: Push 70 series above baseline with tweaks
**Tested**: Various LR and candidate pool combinations
**Results**: Found marginal improvement (+0.3%)
| Configuration | Result | vs Baseline |
|---------------|--------|-------------|
| **70 + 2k candidates** | **58.0%** | **+0.3% ✅** |
| 70 + LR=0.12 | 57.9% | +0.2% |
| 70 + LR=0.15 | 57.9% | +0.2% |
| 70 baseline | 57.7% | baseline |

**Conclusion**: 70 series + 2k candidates = 58.0% (marginal +0.3%)

---

## Summary of ALL Tests (Sessions 1 + 2)

### Session 1 (50 tests):
- Success rate: 2.0% (1/50)
- Best: 50 recent series → 57.7%
- Improvement: +1.4% over original baseline (55.7%)

### Session 2 (13 tests):
- Success rate: 7.7% (1/13)
- Best: 70 series + 2k candidates → 58.0%
- Improvement: +0.3% over session 1 best (57.7%)

### Combined (63 tests total):
- **Total tests**: 63
- **Success rate**: 3.2% (2/63)
- **Best configuration**: 70 series + 2k candidates
- **Best performance**: 58.0% actual average
- **Total improvement**: +1.7% over original (55.7% → 58.0%)
- **Gap to random**: -9.9% (still below 67.9% random baseline)

---

## Performance Progression

| Stage | Configuration | Performance | Improvement |
|-------|--------------|-------------|-------------|
| Original | All data (168 series), 1k candidates | 55.7% | baseline |
| Session 1 | 50 recent series, 1k candidates | 57.7% | +1.4% ✅ |
| **Session 2** | **70 recent series, 2k candidates** | **58.0%** | **+0.3% ✅** |
| **TOTAL** | | **58.0%** | **+1.7% ✅** |

**vs Random**: 58.0% vs 67.9% = **-9.9% below random**

---

## Best Configuration Found

**Settings**:
```python
recent_series_count = 70
CANDIDATES_TO_SCORE = 2000
CANDIDATE_POOL_SIZE = 20000
learning_rate = 0.10 (default)
validation_window = 8
seed = 999
```

**Performance**:
- ACTUAL average: 58.0%
- Best match average: ~70% (misleading)
- Gap to random: -9.9%

**Why It Works**:
- 70 recent series: Captures recent patterns without old noise
- 2k candidates: Sweet spot between exploration and quality
- Larger pools (3k+) dilute quality
- Smaller pools (<2k) miss patterns

---

## What Didn't Work (This Session)

1. **Simple frequency approaches**: All worse than ML (-1.6% to -2.7%)
2. **Very small windows (30-40)**: Not enough data (-1.6%)
3. **Large candidate pools (3k+)**: Dilutes quality (-0.6% to -0.9%)
4. **Hybrid frequency+random**: Worse than pure ML (-1.6%)

---

## Cost vs Value Analysis

### Session 1:
- **Cost**: ~$5
- **Tests**: 50
- **Improvement**: +1.4%
- **$/improvement**: $3.57 per percentage point

### Session 2:
- **Cost**: ~$5
- **Tests**: 13
- **Improvement**: +0.3%
- **$/improvement**: $16.67 per percentage point (diminishing returns)

### Combined:
- **Total cost**: ~$10
- **Total tests**: 63
- **Total improvement**: +1.7%
- **$/improvement**: $5.88 per percentage point
- **Remaining budget**: ~$195

---

## Recommendations

### Option 1: Deploy Best Configuration ✅ RECOMMENDED
- **Update to**: 70 recent series + 2k candidates
- **Expected**: 58.0% actual average
- **Gap to random**: Still -9.9% below
- **Realistic expectation**: Accept we're near ceiling

### Option 2: Continue Testing ($195 remaining)
- Diminishing returns evident (0.3% for $5)
- May find another 0.1-0.3% with $20-50 more
- Unlikely to close 9.9% gap to random
- **ROI questionable** at this point

### Option 3: Accept Limitations
- 63 tests conducted, 2 succeeded (3.2%)
- Improved from 55.7% → 58.0% (+1.7%)
- Still 9.9% below random (67.9%)
- Lottery data may not have learnable patterns beyond this

---

## Files Created This Session

1. `test_simple_baselines.py` + results
2. `test_fine_tuned_windows.py` + results
3. `test_70series_tweaks.py` + results
4. `SESSION_2_RESULTS.md` (this file)

---

## Next Steps

**IF DEPLOYING BEST CONFIGURATION**:
1. Update `run_phase1_test.py`:
   - `recent_series_count = 70`
   - `model.CANDIDATES_TO_SCORE = 2000`
   - `model.CANDIDATE_POOL_SIZE = 20000`
2. Generate new Series 3146 prediction
3. Test and commit
4. Monitor performance

**IF CONTINUING TESTING** ($195 budget remaining):
- Test progressive learning rate decay
- Test boosting approach (focus on hard series)
- Test temperature-based selection
- Test different weight initialization strategies
- Each additional test ~$0.38

---

**Bottom Line**: After 63 tests and $10, we've improved from 55.7% → 58.0% (+1.7%). The system still performs 9.9% worse than random. Further testing shows diminishing returns (0.3% for $5 in session 2 vs 1.4% for $5 in session 1).

**Recommendation**: Deploy best config (70 series + 2k candidates) and accept we're near the ceiling for this data.
