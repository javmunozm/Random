#!/usr/bin/env python3
"""
Insert Series 3151 actual results and evaluate prediction performance
"""

import json

# Series 3151 actual results (7 events)
series_3151_actual = [
    [1, 2, 3, 4, 7, 8, 11, 13, 15, 16, 19, 20, 23, 24],
    [2, 4, 7, 13, 14, 15, 16, 17, 18, 20, 21, 23, 24, 25],
    [2, 4, 6, 7, 11, 12, 13, 17, 19, 20, 21, 22, 23, 24],
    [1, 2, 4, 5, 6, 8, 9, 11, 13, 14, 15, 20, 21, 25],
    [1, 4, 6, 8, 9, 13, 14, 15, 16, 19, 20, 21, 22, 24],
    [1, 3, 4, 6, 8, 9, 10, 16, 18, 20, 22, 23, 24, 25],
    [2, 3, 4, 5, 7, 9, 10, 11, 12, 19, 21, 23, 24, 25]
]

# My ML-guided Mandel prediction
ml_guided_prediction = [1, 2, 3, 4, 5, 8, 10, 11, 15, 16, 18, 20, 22, 23]

# Load existing data
with open('full_series_data.json', 'r') as f:
    all_data = json.load(f)

# Add Series 3151
all_data['3151'] = series_3151_actual

# Save updated data
with open('full_series_data.json', 'w') as f:
    json.dump(all_data, f, indent=2)

print("✅ Series 3151 added to full_series_data.json")
print()

# Evaluate prediction performance
print("=" * 80)
print("PREDICTION PERFORMANCE ANALYSIS - SERIES 3151")
print("=" * 80)
print()

print("ML-Guided Mandel Prediction:")
pred_str = ' '.join(f"{n:02d}" for n in ml_guided_prediction)
print(f"  {pred_str}")
print()

print("Actual Results (7 events):")
for i, event in enumerate(series_3151_actual, 1):
    event_str = ' '.join(f"{n:02d}" for n in event)
    print(f"  Event {i}: {event_str}")
print()

print("=" * 80)
print("MATCH ANALYSIS")
print("=" * 80)
print()

matches_per_event = []
for i, event in enumerate(series_3151_actual, 1):
    matches = len(set(ml_guided_prediction) & set(event))
    match_pct = (matches / 14) * 100
    matches_per_event.append(matches)

    event_str = ' '.join(f"{n:02d}" for n in event)
    matched_nums = sorted(set(ml_guided_prediction) & set(event))
    matched_str = ' '.join(f"{n:02d}" for n in matched_nums)

    print(f"Event {i}: {matches:2d}/14 ({match_pct:5.1f}%)")
    print(f"  Actual:  {event_str}")
    print(f"  Matched: {matched_str}")
    print()

best_match = max(matches_per_event)
best_match_pct = (best_match / 14) * 100
avg_match = sum(matches_per_event) / len(matches_per_event)
avg_match_pct = (avg_match / 14) * 100

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"Best match: {best_match}/14 ({best_match_pct:.1f}%)")
print(f"Average match: {avg_match:.2f}/14 ({avg_match_pct:.1f}%)")
print(f"Worst match: {min(matches_per_event)}/14 ({(min(matches_per_event)/14)*100:.1f}%)")
print()

# Compare to training score
print("Comparison to Training:")
print(f"  Training score: 69.74% (on historical data)")
print(f"  Actual score: {best_match_pct:.1f}% (on Series 3151)")
print(f"  Difference: {best_match_pct - 69.74:+.1f}%")
print()

# Critical numbers analysis
from collections import Counter
all_numbers = []
for event in series_3151_actual:
    all_numbers.extend(event)
number_freq = Counter(all_numbers)

print("Critical Numbers in Series 3151 (appeared in 5+ events):")
critical_numbers = {num: count for num, count in number_freq.items() if count >= 5}
for num, count in sorted(critical_numbers.items(), key=lambda x: x[1], reverse=True):
    in_pred = "✅" if num in ml_guided_prediction else "❌"
    print(f"  Number {num:2d}: {count}/7 events {in_pred}")
print()

critical_hit_rate = sum(1 for num in critical_numbers if num in ml_guided_prediction) / len(critical_numbers) if critical_numbers else 0
print(f"Critical number hit rate: {critical_hit_rate*100:.1f}% ({sum(1 for num in critical_numbers if num in ml_guided_prediction)}/{len(critical_numbers)})")
print()

print("=" * 80)
print("✅ ANALYSIS COMPLETE")
print("=" * 80)
