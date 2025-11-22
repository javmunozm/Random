#!/usr/bin/env python3
"""
Validate Priority 1 improvements against Series 3151
Compare original vs improved performance
"""

import json

# Load actual results
with open('all_series_data.json', 'r') as f:
    data = json.load(f)

actual_3151 = data['3151']

# Original predictions (Multi-Signal from before)
original_prediction = [1, 3, 4, 6, 8, 9, 10, 16, 20, 21, 22, 23, 24, 25]  # Multi-Signal #1 from 3152

# Improved Priority 1 prediction
improved_prediction = [1, 2, 6, 8, 9, 10, 12, 13, 19, 20, 21, 23, 24, 25]

print("=" * 80)
print("PRIORITY 1 VALIDATION - Series 3151")
print("=" * 80)

def evaluate_prediction(prediction, actual_events, label):
    print(f"\n{label}")
    print("-" * 80)
    print(f"Prediction: {' '.join(f'{n:02d}' for n in sorted(prediction))}")
    print()

    matches = []
    for i, event in enumerate(actual_events, 1):
        match_count = len(set(prediction) & set(event))
        match_pct = (match_count / 14) * 100
        matches.append(match_count)
        status = "🎯" if match_count >= 11 else "✅" if match_count >= 10 else "🟡" if match_count >= 9 else "⚠️"
        print(f"Event {i}: {match_count:2d}/14 ({match_pct:5.1f}%) {status}")

    best_match = max(matches)
    avg_match = sum(matches) / len(matches)
    best_pct = (best_match / 14) * 100
    avg_pct = (avg_match / 14) * 100

    print("-" * 80)
    print(f"📈 PEAK: {best_match}/14 ({best_pct:.1f}%)")
    print(f"📊 AVG:  {avg_match:.2f}/14 ({avg_pct:.1f}%)")

    return {
        'peak': best_match,
        'avg': avg_match,
        'matches': matches
    }

# Evaluate both
results_original = evaluate_prediction(original_prediction, actual_3151, "🔴 ORIGINAL (Multi-Signal)")
results_improved = evaluate_prediction(improved_prediction, actual_3151, "🟢 IMPROVED (Priority 1)")

# Comparison
print("\n" + "=" * 80)
print("📊 COMPARISON")
print("=" * 80)

peak_diff = results_improved['peak'] - results_original['peak']
avg_diff = results_improved['avg'] - results_original['avg']

print(f"\nPeak Match:")
print(f"  Original:  {results_original['peak']}/14 ({results_original['peak']/14*100:.1f}%)")
print(f"  Improved:  {results_improved['peak']}/14 ({results_improved['peak']/14*100:.1f}%)")
print(f"  Difference: {peak_diff:+.0f} numbers ({peak_diff/14*100:+.1f}%)")

print(f"\nAverage Match:")
print(f"  Original:  {results_original['avg']:.2f}/14 ({results_original['avg']/14*100:.1f}%)")
print(f"  Improved:  {results_improved['avg']:.2f}/14 ({results_improved['avg']/14*100:.1f}%)")
print(f"  Difference: {avg_diff:+.2f} numbers ({avg_diff/14*100:+.1f}%)")

print("\n" + "=" * 80)
print("✅ VERDICT")
print("=" * 80)

if peak_diff > 0:
    print(f"✅ IMPROVEMENT: +{peak_diff} peak match improvement!")
    print(f"   Priority 1 changes are WORKING")
elif peak_diff == 0:
    if avg_diff > 0:
        print(f"🟡 SAME PEAK, BETTER AVG: +{avg_diff:.2f} average improvement")
        print(f"   Priority 1 changes show positive trend")
    else:
        print(f"⚠️  NO CHANGE: Same performance")
        print(f"   May need more testing or different series")
else:
    print(f"❌ REGRESSION: -{abs(peak_diff)} peak match decrease")
    print(f"   Priority 1 changes may need adjustment")

print("\n💡 INSIGHT:")
if results_improved['peak'] >= 12:
    print(f"   ✅ Target achieved! {results_improved['peak']}/14 meets 12-13/14 goal")
elif results_improved['peak'] >= 11:
    print(f"   🟡 Close to target: {results_improved['peak']}/14 (goal: 12-13/14)")
    print(f"   Priority 2 improvements may close the gap")
else:
    print(f"   ⚠️  Below target: {results_improved['peak']}/14 (goal: 12-13/14)")
    print(f"   Further tuning needed")

print("=" * 80)
