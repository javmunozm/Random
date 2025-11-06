#!/usr/bin/env python3
"""
Analysis of Series 3145 performance
"""

# Our prediction
prediction = [1, 2, 4, 5, 7, 8, 11, 14, 17, 19, 21, 22, 24, 25]

# Actual results (7 events)
actual_events = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],  # Event 1
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],    # Event 2
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],   # Event 3
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],   # Event 4
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],      # Event 5
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],   # Event 6
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],      # Event 7
]

print("=" * 80)
print("SERIES 3145 PERFORMANCE ANALYSIS")
print("=" * 80)
print()

print(f"Prediction: {' '.join(f'{n:02d}' for n in prediction)}")
print()

# Calculate matches for each event
matches_per_event = []
for i, event in enumerate(actual_events, 1):
    matches = [n for n in prediction if n in event]
    match_count = len(matches)
    accuracy = (match_count / 14) * 100
    matches_per_event.append((match_count, accuracy))

    print(f"Event {i}: {' '.join(f'{n:02d}' for n in event)}")
    print(f"  Matches: {' '.join(f'{n:02d}' for n in matches)}")
    print(f"  Count: {match_count}/14 = {accuracy:.1f}%")
    print()

# Overall statistics
match_counts = [m[0] for m in matches_per_event]
accuracies = [m[1] for m in matches_per_event]
best_match = max(match_counts)
best_accuracy = max(accuracies)
avg_match = sum(match_counts) / len(match_counts)
avg_accuracy = sum(accuracies) / len(accuracies)

print("=" * 80)
print("PERFORMANCE SUMMARY")
print("=" * 80)
print(f"Best Match:     {best_match}/14 = {best_accuracy:.1f}%")
print(f"Average Match:  {avg_match:.2f}/14 = {avg_accuracy:.1f}%")
print(f"Worst Match:    {min(match_counts)}/14 = {min(accuracies):.1f}%")
print()

# Critical numbers analysis (appeared in 5+ events)
from collections import Counter
all_numbers = []
for event in actual_events:
    all_numbers.extend(event)

number_freq = Counter(all_numbers)
critical_numbers = {num: count for num, count in number_freq.items() if count >= 5}

print("=" * 80)
print("CRITICAL NUMBERS (appeared in 5+ events)")
print("=" * 80)
for num in sorted(critical_numbers.keys()):
    count = critical_numbers[num]
    in_prediction = "✓ HIT" if num in prediction else "✗ MISS"
    print(f"  #{num:02d}: {count}/7 events  {in_prediction}")

critical_hit = sum(1 for num in critical_numbers if num in prediction)
critical_total = len(critical_numbers)
critical_rate = (critical_hit / critical_total * 100) if critical_total > 0 else 0
print(f"\nCritical Hit Rate: {critical_hit}/{critical_total} = {critical_rate:.1f}%")
print()

# Most common numbers overall
print("=" * 80)
print("ALL NUMBERS FREQUENCY (top 20)")
print("=" * 80)
for num, count in number_freq.most_common(20):
    in_prediction = "✓" if num in prediction else "✗"
    print(f"  #{num:02d}: {count}/7 events  {in_prediction}")
print()

# What we predicted but didn't appear much
print("=" * 80)
print("PREDICTED NUMBERS - FREQUENCY IN ACTUAL RESULTS")
print("=" * 80)
for num in sorted(prediction):
    count = number_freq.get(num, 0)
    print(f"  #{num:02d}: {count}/7 events")
print()

# What we missed that appeared frequently
print("=" * 80)
print("MISSED NUMBERS (appeared 5+ times but not in prediction)")
print("=" * 80)
missed_critical = [num for num in critical_numbers if num not in prediction]
if missed_critical:
    for num in sorted(missed_critical):
        count = critical_numbers[num]
        print(f"  #{num:02d}: {count}/7 events - SHOULD HAVE PREDICTED")
else:
    print("  None! We caught all critical numbers.")
print()

# Context: Ceiling Study Expectations
print("=" * 80)
print("CONTEXT: CEILING STUDY EXPECTATIONS")
print("=" * 80)
print("Recent Window (3137-3144):    73.2% avg (95.8th percentile - exceptional)")
print("Historical Average:           67.9% ± 2.0%")
print("Typical Range:                65.9% - 69.9%")
print("Worst Window Ever:            63.39%")
print()
print(f"Series 3145 Performance:      {avg_accuracy:.1f}% avg (BELOW historical avg)")
print()
print("ANALYSIS:")
if avg_accuracy < 67.9:
    print("  • Performance BELOW historical average (67.9%)")
    print("  • Confirms regression to mean after lucky 73.2% period")
    print("  • Within expected variance range")
    if avg_accuracy < 65.9:
        print("  • Below typical range - this is a difficult series")
        print(f"  • Distance from worst: {avg_accuracy - 63.39:.1f}%")
else:
    print("  • Performance within historical average range")
    print("  • Normal variation expected")
print()
