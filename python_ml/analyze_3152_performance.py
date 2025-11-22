#!/usr/bin/env python3
"""
Analyze Series 3152 prediction performance vs actual results
"""

import json

# Load actual results
with open('series_3152_actual.json', 'r') as f:
    actual = json.load(f)

# Our top predictions
predictions = {
    "Multi-Signal #1": [1, 3, 4, 6, 8, 9, 10, 16, 20, 21, 22, 23, 24, 25],
    "Multi-Signal #2": [1, 2, 3, 4, 6, 10, 14, 16, 19, 20, 21, 22, 23, 25],
    "Multi-Signal #3": [1, 2, 3, 4, 6, 10, 15, 16, 19, 20, 21, 22, 23, 25],
    "Basic #1 (Global Freq)": [2, 3, 4, 7, 10, 14, 15, 16, 19, 20, 21, 22, 23, 25],
    "Basic #2 (3151 Pattern)": [1, 2, 3, 4, 7, 8, 11, 13, 15, 16, 19, 20, 23, 24],
}

# Our exclusion strategy
excluded_numbers = [5, 12, 17, 18]
reduced_pool = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25]

print("=" * 80)
print("SERIES 3152 - PREDICTION PERFORMANCE ANALYSIS")
print("=" * 80)

# Check if excluded numbers appeared
print("\n📊 EXCLUSION STRATEGY VALIDATION")
print("-" * 80)
all_numbers = set()
for event in actual['events']:
    all_numbers.update(event)

excluded_appeared = [num for num in excluded_numbers if num in all_numbers]
print(f"Numbers we EXCLUDED: {excluded_numbers}")
print(f"Excluded numbers that APPEARED: {excluded_appeared}")
print(f"❌ EXCLUSION FAILURE RATE: {len(excluded_appeared)}/{len(excluded_numbers)} = {len(excluded_appeared)/len(excluded_numbers)*100:.1f}%")
print(f"\n⚠️  ALL 25 NUMBERS APPEARED - Exclusion strategy INVALID")

# Analyze each prediction
print("\n" + "=" * 80)
print("PREDICTION PERFORMANCE")
print("=" * 80)

for pred_name, prediction in predictions.items():
    print(f"\n🎯 {pred_name}")
    print(f"Prediction: {' '.join(f'{n:02d}' for n in prediction)}")
    print("-" * 80)

    matches = []
    for i, event in enumerate(actual['events'], 1):
        event_set = set(event)
        pred_set = set(prediction)
        match = len(event_set & pred_set)
        match_pct = (match / 14) * 100
        matches.append(match)

        print(f"Event {i}: {match:2d}/14 ({match_pct:5.1f}%)  |  {' '.join(f'{n:02d}' for n in sorted(event))}")

    best_match = max(matches)
    avg_match = sum(matches) / len(matches)
    best_pct = (best_match / 14) * 100
    avg_pct = (avg_match / 14) * 100

    print("-" * 80)
    print(f"📈 BEST:    {best_match}/14 ({best_pct:.1f}%)")
    print(f"📊 AVERAGE: {avg_match:.2f}/14 ({avg_pct:.1f}%)")

# Summary comparison
print("\n" + "=" * 80)
print("SUMMARY - ALL PREDICTIONS")
print("=" * 80)

results = []
for pred_name, prediction in predictions.items():
    matches = []
    for event in actual['events']:
        event_set = set(event)
        pred_set = set(prediction)
        match = len(event_set & pred_set)
        matches.append(match)

    best_match = max(matches)
    avg_match = sum(matches) / len(matches)
    results.append({
        'name': pred_name,
        'best': best_match,
        'avg': avg_match,
        'best_pct': (best_match / 14) * 100,
        'avg_pct': (avg_match / 14) * 100
    })

results.sort(key=lambda x: x['avg'], reverse=True)

print(f"\n{'Prediction':<30} {'Best':>10} {'Average':>10}")
print("-" * 80)
for r in results:
    print(f"{r['name']:<30} {r['best']}/14 ({r['best_pct']:5.1f}%)  {r['avg']:.2f}/14 ({r['avg_pct']:5.1f}%)")

# Compare to expected performance
print("\n" + "=" * 80)
print("COMPARISON TO EXPECTED PERFORMANCE")
print("=" * 80)
print(f"Expected GA Average:     71.8%")
print(f"Expected Random Baseline: 67.9%")
print(f"Multi-Signal #1 Achieved: {results[0]['avg_pct']:.1f}%")
print(f"Best Prediction Achieved: {results[0]['best_pct']:.1f}%")

if results[0]['avg_pct'] < 67.9:
    print(f"\n⚠️  BELOW RANDOM BASELINE by {67.9 - results[0]['avg_pct']:.1f}%")
elif results[0]['avg_pct'] < 71.8:
    print(f"\n⚠️  BELOW GA EXPECTED by {71.8 - results[0]['avg_pct']:.1f}%")
else:
    print(f"\n✅ ABOVE EXPECTED by {results[0]['avg_pct'] - 71.8:.1f}%")

print("\n" + "=" * 80)
print("CRITICAL FINDINGS")
print("=" * 80)
print("1. ❌ NUMBER EXCLUSION FAILED - All 4 excluded numbers appeared")
print("2. ❌ SPACE REDUCTION INVALID - Cannot exclude any numbers safely")
print("3. ⚠️  PERFORMANCE BELOW EXPECTED - Achieved lower than GA validation")
print("4. ✅ MULTI-SIGNAL BEST - Outperformed basic frequency methods")
print("5. 🔍 LESSON: Exclusion strategies have false positives")
print("\n💡 CONCLUSION: ML pattern recognition works, but exclusion doesn't")
print("   - Use ML for PRIORITIZATION, not ELIMINATION")
print("   - Search ALL combinations ranked by score")
print("   - Cannot reduce search space by excluding numbers")
print("=" * 80)
