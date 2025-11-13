#!/usr/bin/env python3
"""
Debug: Check model weights before and after training on Series 3147
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from generate_from_segment1_pool import load_all_series_data
from true_learning_model import TrueLearningModel

# Load data
series_data = load_all_series_data()

# Create model
model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
model.RECENT_SERIES_LOOKBACK = 8

print("=" * 80)
print("DEBUGGING: Model Weights Before/After Series 3147")
print("=" * 80)
print()

# Train on all series BEFORE 3147
for sid in sorted(series_data.keys()):
    if sid < 3147:
        model.learn_from_series(sid, series_data[sid])

print("✅ Trained on all series up to 3146")
print()

# Get weights BEFORE 3147
weights_before = dict(model.number_frequency_weights)
print("Top 10 weights BEFORE learning from 3147:")
sorted_before = sorted(weights_before.items(), key=lambda x: -x[1])[:10]
for num, weight in sorted_before:
    print(f"  #{num:02d}: {weight:.2f}")
print()

# Now learn from Series 3147
print("Learning from Series 3147...")
print()
print("Series 3147 actual results:")
for i, event in enumerate(series_data[3147], 1):
    print(f"  Event {i}: {event}")
print()

model.learn_from_series(3147, series_data[3147])

# Get weights AFTER 3147
weights_after = dict(model.number_frequency_weights)
print("Top 10 weights AFTER learning from 3147:")
sorted_after = sorted(weights_after.items(), key=lambda x: -x[1])[:10]
for num, weight in sorted_after:
    print(f"  #{num:02d}: {weight:.2f}")
print()

# Check critical numbers from 3147
from collections import Counter
all_numbers = []
for event in series_data[3147]:
    all_numbers.extend(event)
number_freq = Counter(all_numbers)

critical = {num: count for num, count in number_freq.items() if count >= 5}
print("Critical numbers in Series 3147 (appeared 5+ times):")
for num, count in sorted(critical.items(), key=lambda x: -x[1]):
    before_w = weights_before.get(num, 0)
    after_w = weights_after.get(num, 0)
    change = after_w - before_w
    print(f"  #{num:02d}: {count}/7 events | Weight: {before_w:.2f} -> {after_w:.2f} (Δ{change:+.2f})")
print()

# Compare weight changes
print("=" * 80)
print("WEIGHT CHANGES SUMMARY")
print("=" * 80)
print()

changes = []
for num in range(1, 26):
    before = weights_before.get(num, 0)
    after = weights_after.get(num, 0)
    change = after - before
    if abs(change) > 0.01:  # Only show significant changes
        changes.append((num, before, after, change))

changes.sort(key=lambda x: -abs(x[3]))  # Sort by magnitude of change

print("Top 10 weight changes:")
for num, before, after, change in changes[:10]:
    print(f"  #{num:02d}: {before:.2f} -> {after:.2f} (Δ{change:+.2f})")
print()

# Test scoring a combination
test_combo = [1, 2, 3, 8, 9, 10, 13, 19, 20, 21, 22, 23, 24, 25]

# Score with BEFORE weights
model.number_frequency_weights = weights_before
score_before = model._calculate_score(test_combo)

# Score with AFTER weights
model.number_frequency_weights = weights_after
score_after = model._calculate_score(test_combo)

print("=" * 80)
print("SCORING TEST: [1, 2, 3, 8, 9, 10, 13, 19, 20, 21, 22, 23, 24, 25]")
print("=" * 80)
print(f"Score with weights BEFORE 3147: {score_before:.2f}")
print(f"Score with weights AFTER 3147:  {score_after:.2f}")
print(f"Difference: {score_after - score_before:+.2f}")
print()

if abs(score_after - score_before) < 0.01:
    print("⚠️  WARNING: Scores are nearly identical!")
    print("   This suggests weights didn't change significantly.")
else:
    print("✅ Scores are different - weights did change.")
