# Phase 2 ML Model - Testing Guide

**Date:** 2025-11-05
**Model Version:** Phase 2 UPGRADED
**Expected Improvement:** +5% average accuracy (67% → 72%)

---

## Quick Test Commands

### 1. Generate Prediction for Next Series
```bash
dotnet run --project DataProcessor.csproj
```
**Expected Output:**
- Validation on series 3136-3143 (8 rounds)
- Final prediction for series 3144
- Learning improvement metrics
- Phase 2 features should be active

### 2. Check Model Status
```bash
dotnet run --project DataProcessor.csproj status
```
**Expected Output:**
- Latest series: 3143
- Critical numbers identified
- Database statistics

### 3. Explicit Real-Train Test
```bash
dotnet run --project DataProcessor.csproj real-train
```
**Expected Output:**
- Phase 1: Bulk training on 163+ series
- Phase 2: Iterative validation (8 rounds)
- Validation summary with accuracy metrics
- Generated prediction with Phase 2 features

---

## What to Look For - Phase 2 Active Indicators

### ✅ **Trend Detection Active**
Look for numbers in prediction that match analysis trends:
- **Rising numbers** (should appear more): 16, 2, 24, 11, 7
- **Falling numbers** (should appear less): 23, 25, 22, 4, 21

### ✅ **Optimized Sum Range (170-200)**
Check prediction sum:
```
Sum of 14 numbers = X
If 170 ≤ X ≤ 200: ✓ Phase 2 active
If 180 ≤ X ≤ 189: ✓✓ Optimal range bonus applied
```

### ✅ **Gap Preference (Consecutive Numbers)**
Count gaps between consecutive numbers:
```
Example: [1, 2, 4, 5, 7, 9, 10, 11, ...]
Gaps:     1  2  1  2  2  1   1
```
- Should see more gap-1 (consecutive)
- Should see fewer gap-4+ (rare)

### ✅ **Even/Odd Balance (6-8 Even)**
Count even numbers in prediction:
```
If 6 ≤ even_count ≤ 8: ✓ Phase 2 balance active
```

---

## Performance Comparison Test

### Step 1: Record Phase 2 Prediction
```bash
dotnet run --project DataProcessor.csproj > phase2_test.txt
```

### Step 2: Analyze Validation Results
Look in output for validation summary (series 3136-3143):

**Metrics to Compare:**
```
Phase 1 Performance (from real_train_validation_summary.json):
- Overall best average: 71.4%
- Overall average: 57.4%
- Series 3143 best: 78.6%

Phase 2 Performance (new run):
- Overall best average: ??? (target: 72-75%)
- Overall average: ??? (target: 59-62%)
- Series 3143 best: ??? (target: 79-82%)
```

### Step 3: Check Prediction Quality
Analyze generated prediction for series 3144:

**Quality Indicators:**
1. **Sum in optimal range?** (170-200, ideally 180-189)
2. **Even count in target?** (6-8 even numbers)
3. **Gap distribution natural?** (mostly 1-2 gaps)
4. **Trending numbers present?** (16, 2, 24 appearing more)
5. **Declining numbers reduced?** (23, 25, 22 appearing less)

---

## Detailed Validation Test

### Test Prediction Against Series 3141-3143
These series have actual results in the database. Compare predictions:

```bash
# Test on series 3141
dotnet run --project DataProcessor.csproj predict 3141

# Test on series 3142
dotnet run --project DataProcessor.csproj predict 3142

# Test on series 3143
dotnet run --project DataProcessor.csproj predict 3143
```

**Compare Results:**
- Phase 1 performance: Known from validation (71.4% best on 3143)
- Phase 2 performance: New predictions with upgraded model
- Expected improvement: +3-5% on best match

---

## Feature-Specific Tests

### Test 1: Temporal Decay (Recent Series Weight)
**What to check:**
- Prediction should favor patterns from series 3124-3143 (recent 20)
- Less influence from series 2898-2980 (old data)
- Numbers appearing in recent series should dominate

**Verification:**
```
Recent hot numbers (3139-3143): 1, 2, 6, 7, 8, 9, 11, 14, 18
→ Should see more of these in prediction
```

### Test 2: Trend Detection
**What to check:**
- Rising numbers boosted: 16 (+20), 2 (+17), 24 (+13), 11 (+10), 7 (+9)
- Falling numbers penalized: 23 (-15), 25 (-13), 22 (-12)

**Verification:**
```
Count occurrences in prediction:
- Rising numbers (16, 2, 24, 11, 7): ??? / 5 (expect 3-4)
- Falling numbers (23, 25, 22): ??? / 3 (expect 0-1)
```

### Test 3: Gap Preference
**What to check:**
- Most gaps should be 1 or 2
- Few gaps should be 4+

**Manual Calculation:**
```python
prediction = [1, 2, 4, 5, ...]  # Your prediction
gaps = [prediction[i+1] - prediction[i] for i in range(13)]
gap_1_count = gaps.count(1)  # Should be ~55% (7-8 gaps)
gap_2_count = gaps.count(2)  # Should be ~26% (3-4 gaps)
gap_4_plus = sum(1 for g in gaps if g >= 4)  # Should be minimal
```

### Test 4: Even/Odd Balance
**What to check:**
- Should have 6-8 even numbers

**Manual Calculation:**
```python
prediction = [1, 2, 4, 5, ...]  # Your prediction
even_count = sum(1 for n in prediction if n % 2 == 0)
# Should be: 6 ≤ even_count ≤ 8
```

### Test 5: Optimized Sum Range
**What to check:**
- Sum should be 170-200
- Ideally 180-189 for optimal bonus

**Manual Calculation:**
```python
prediction = [1, 2, 4, 5, ...]  # Your prediction
total_sum = sum(prediction)
# Should be: 170 ≤ total_sum ≤ 200
# Optimal: 180 ≤ total_sum ≤ 189
```

---

## Expected Test Results

### Scenario 1: Phase 2 Working Perfectly ✅
```
✓ Validation accuracy: 72-75% average (up from 67-71%)
✓ Prediction sum: 180-189 (optimal range)
✓ Even count: 6-8
✓ Gap distribution: 7-8 gap-1, 3-4 gap-2, 0-1 gap-4+
✓ Trending numbers: 3-4 of top 5 rising numbers present
✓ Declining numbers: 0-1 of top 3 falling numbers present
```

### Scenario 2: Phase 2 Partially Active ⚠️
```
⚠ Validation accuracy: 69-71% (small improvement)
✓ Prediction sum: 170-200 (in range but not optimal)
✓ Even count: 6-8
✓ Gap distribution: Reasonable but not optimal
~ Trending numbers: 2-3 present (moderate)
```

### Scenario 3: Phase 2 Not Active ❌
```
✗ Validation accuracy: 67-68% (no improvement)
✗ Prediction sum: Outside 170-200
✗ Even count: <6 or >8
✗ Gap distribution: Random
✗ Trending numbers: Same as before
```

---

## Troubleshooting

### If No Improvement Seen:

1. **Check Model Loading**
   - Ensure TrueLearningModel.cs Phase 2 changes compiled
   - Run: `dotnet clean && dotnet build --project DataProcessor.csproj`

2. **Check Data Range**
   - Model needs 40+ series for trend detection (20 recent + 20 old)
   - Database should have series up to 3143

3. **Check Output for Errors**
   - Look for any compilation warnings
   - Check for null reference exceptions

### If Accuracy Decreased:

1. **Parameter Tuning Needed**
   - Trend multipliers may be too aggressive
   - Gap penalties may be too strict
   - Even/odd bonus may be too high

2. **Revert to Phase 1** (if needed)
   ```bash
   git checkout 6edbf37  # Last Phase 1 commit
   dotnet build --project DataProcessor.csproj
   ```

---

## Success Criteria

### Minimum Viable (Pass):
- ✅ Compiles without errors
- ✅ Validation accuracy ≥ 70%
- ✅ Prediction uses optimized sum range (170-200)

### Good Performance (Expected):
- ✅ Validation accuracy 72-74%
- ✅ Sum in optimal range (180-189)
- ✅ Even count 6-8
- ✅ Gap distribution natural

### Excellent Performance (Best Case):
- ✅ Validation accuracy 75%+
- ✅ Trending numbers dominate prediction
- ✅ All Phase 2 features active
- ✅ Peak accuracy 82-85%

---

## Quick Verification Checklist

Run this command and check:
```bash
dotnet run --project DataProcessor.csproj > test_output.txt 2>&1
```

Then verify:
- [ ] No compilation errors
- [ ] Phase 2 model header shows in comments
- [ ] Validation runs on 8 series (3136-3143)
- [ ] Prediction generated for series 3144
- [ ] Prediction sum is 170-200
- [ ] Prediction has 6-8 even numbers
- [ ] Trending numbers (16, 2, 24) appear in prediction
- [ ] Falling numbers (23, 25, 22) less frequent

---

## Report Results

After testing, please share:
1. Validation summary (overall accuracy)
2. Generated prediction for 3144
3. Any errors or warnings
4. Performance comparison vs Phase 1

**I can then analyze results and fine-tune Phase 2 parameters if needed!**
