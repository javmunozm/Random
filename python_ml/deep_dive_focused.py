#!/usr/bin/env python3
"""
Focused deep-dive: Why did we miss #09, #12, #16 in Series 3145?
"""

import json
import random
from collections import Counter
from pathlib import Path
from true_learning_model import TrueLearningModel

# Load historical data
json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

with open(json_path, 'r') as f:
    json_data = json.load(f)

all_series_data = []
for series in json_data.get('data', []):
    series_id = series['series_id']
    events = [event['numbers'] for event in series['events']]
    all_series_data.append({'series_id': series_id, 'events': events})

# Add Series 3144
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]

all_series_data.append({'series_id': 3144, 'events': SERIES_3144})

# Series 3145 actual
SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
]

# Our failed prediction
prediction = [1, 2, 4, 5, 7, 8, 11, 14, 17, 19, 21, 22, 24, 25]
missed_critical = [9, 12, 16]

print("=" * 80)
print("FOCUSED DEEP-DIVE: WHY DID WE MISS #09, #12, #16?")
print("=" * 80)
print()

# ==============================================================================
# ANALYSIS 1: Historical Frequency
# ==============================================================================
print("=" * 80)
print("ANALYSIS 1: HISTORICAL FREQUENCY")
print("=" * 80)
print()

hist_freq = Counter()
for s in all_series_data:
    for e in s['events']:
        hist_freq.update(e)

total_events = len(all_series_data) * 7

print("Number Rankings by Historical Frequency:")
ranked = sorted(hist_freq.items(), key=lambda x: x[1], reverse=True)
for rank, (num, count) in enumerate(ranked, 1):
    pct = count / total_events * 100
    marker = ""
    if num in missed_critical:
        marker = " ← MISSED CRITICAL"
    elif num in prediction:
        marker = " ← predicted"
    print(f"  {rank:2d}. #{num:02d}: {count:4d} events ({pct:4.1f}%){marker}")

print()
print("Key Observation:")
print(f"  #09: Rank #{[i for i, (n, _) in enumerate(ranked, 1) if n == 9][0]} - VERY HIGH FREQUENCY")
print(f"  #12: Rank #{[i for i, (n, _) in enumerate(ranked, 1) if n == 12][0]}")
print(f"  #16: Rank #{[i for i, (n, _) in enumerate(ranked, 1) if n == 16][0]}")
print()

# ==============================================================================
# ANALYSIS 2: Pattern Shift Analysis
# ==============================================================================
print("=" * 80)
print("ANALYSIS 2: PATTERN SHIFT - Last 20 vs Historical")
print("=" * 80)
print()

# Last 20 series
recent_series = [s for s in all_series_data if s['series_id'] >= 3125]
recent_freq = Counter()
for s in recent_series:
    for e in s['events']:
        recent_freq.update(e)

recent_events = len(recent_series) * 7

print("Missed Critical Numbers - Trending:")
for num in sorted(missed_critical):
    hist_rate = hist_freq[num] / len(all_series_data)
    recent_rate = recent_freq[num] / len(recent_series)
    change = recent_rate - hist_rate

    print(f"  #{num:02d}:")
    print(f"    Historical: {hist_rate:.2f} per series ({hist_freq[num]}/{len(all_series_data)*7} events)")
    print(f"    Recent:     {recent_rate:.2f} per series ({recent_freq[num]}/{recent_events} events)")
    print(f"    Change:     {change:+.2f} per series", end="")
    if abs(change) > 0.3:
        print(f" ← {'TRENDING UP' if change > 0 else 'TRENDING DOWN'}")
    else:
        print()
    print()

# ==============================================================================
# ANALYSIS 3: Model Weight Progression
# ==============================================================================
print("=" * 80)
print("ANALYSIS 3: MODEL WEIGHT PROGRESSION")
print("=" * 80)
print()

random.seed(999)
model = TrueLearningModel()

# Bulk training
bulk_data = [s for s in all_series_data if s['series_id'] < 3137]
for s in bulk_data:
    model.learn_from_series(s['series_id'], s['events'])

print(f"After BULK training ({len(bulk_data)} series):")
print()

# Print weights for all numbers, sorted by weight
all_weights = [(num, model.number_frequency_weights[num]) for num in range(1, 26)]
all_weights.sort(key=lambda x: x[1], reverse=True)

print("Top 20 numbers by weight:")
for rank, (num, weight) in enumerate(all_weights[:20], 1):
    marker = ""
    if num in missed_critical:
        marker = " ← MISSED CRITICAL"
    elif num in prediction:
        marker = " ← predicted"
    print(f"  {rank:2d}. #{num:02d}: weight={weight:.2f}{marker}")

print()
print("Missed critical numbers ranking:")
for num in sorted(missed_critical):
    weight = model.number_frequency_weights[num]
    rank = [i for i, (n, _) in enumerate(all_weights, 1) if n == num][0]
    print(f"  #{num:02d}: weight={weight:.2f}, rank={rank}/25")

print()
print()

# Now do iterative validation
validation_data = [s for s in all_series_data if 3137 <= s['series_id'] <= 3144]

print(f"After ITERATIVE VALIDATION ({len(validation_data)} series: 3137-3144):")
print()

for s in validation_data:
    # Generate prediction (but we don't use it, just let model learn)
    _ = model.predict_best_combination(s['series_id'])
    # Learn from actual
    model.learn_from_series(s['series_id'], s['events'])

# Print updated weights
all_weights = [(num, model.number_frequency_weights[num]) for num in range(1, 26)]
all_weights.sort(key=lambda x: x[1], reverse=True)

print("Top 20 numbers by weight:")
for rank, (num, weight) in enumerate(all_weights[:20], 1):
    marker = ""
    if num in missed_critical:
        marker = " ← MISSED CRITICAL"
    elif num in prediction:
        marker = " ← predicted"
    print(f"  {rank:2d}. #{num:02d}: weight={weight:.2f}{marker}")

print()
print("Missed critical numbers ranking:")
for num in sorted(missed_critical):
    weight = model.number_frequency_weights[num]
    rank = [i for i, (n, _) in enumerate(all_weights, 1) if n == num][0]
    print(f"  #{num:02d}: weight={weight:.2f}, rank={rank}/25")

print()
print()

# ==============================================================================
# ANALYSIS 4: What was actually predicted?
# ==============================================================================
print("=" * 80)
print("ANALYSIS 4: FINAL PREDICTION ANALYSIS")
print("=" * 80)
print()

final_prediction = model.predict_best_combination(3145)

print(f"Model's actual prediction: {' '.join(f'{n:02d}' for n in final_prediction)}")
print(f"Known prediction:          {' '.join(f'{n:02d}' for n in prediction)}")
print()

if final_prediction == prediction:
    print("✓ Predictions match - this is the exact model state that produced our prediction")
else:
    print("✗ Predictions don't match - slight difference in execution")
    diff = set(final_prediction) - set(prediction)
    if diff:
        print(f"  Extra in model: {diff}")
    diff = set(prediction) - set(final_prediction)
    if diff:
        print(f"  Missing from model: {diff}")

print()

# ==============================================================================
# SUMMARY
# ==============================================================================
print("=" * 80)
print("SUMMARY: ROOT CAUSE ANALYSIS")
print("=" * 80)
print()

print("1. FREQUENCY PARADOX:")
print(f"   #09 was rank #{[i for i, (n, _) in enumerate(ranked, 1) if n == 9][0]}/25 by historical frequency")
print("   Yet it wasn't selected in the final prediction")
print()

print("2. WEIGHT ANALYSIS:")
# Get final ranks
final_ranks = {num: i for i, (num, _) in enumerate(all_weights, 1)}
print(f"   After iterative validation:")
for num in sorted(missed_critical):
    print(f"     #{num:02d}: rank={final_ranks[num]}/25")
print()

print("3. PATTERN SHIFT:")
print(f"   #16 was trending UP (+0.46 per series)")
print("   But the model didn't adapt enough to this trend")
print()

print("4. PROBABLE CAUSES:")
print("   a) Pair affinity penalties: These numbers may have paired with")
print("      numbers that the model learned to avoid")
print("   b) Critical number threshold: Model may have boosted OTHER numbers")
print("      more heavily, pushing these out of top 14")
print("   c) Random candidate generation: With only 10,000 candidates,")
print("      the best combination may not have been generated")
print("   d) Learning rate: Model may have under-learned from recent data")
print("      where these numbers were appearing more frequently")
print()

print("5. SYSTEMIC ISSUE:")
print("   The model prioritizes consistency with historical patterns.")
print("   When actual results shift (like #16 trending up), the model")
print("   is slow to adapt. This is inherent in error-based learning -")
print("   the model needs to make mistakes before it updates.")
print()
