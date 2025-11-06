#!/usr/bin/env python3
"""
Deep-dive analysis: Why did the model miss #09, #12, #16 in Series 3145?
These numbers appeared 6/7 times but weren't in our prediction.
"""

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from true_learning_model import TrueLearningModel

# Series 3144 actual results
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]

# Series 3145 actual results
SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
]

# Load all historical data
json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

if not json_path.exists():
    print(f"❌ JSON export not found: {json_path}")
    exit(1)

with open(json_path, 'r') as f:
    json_data = json.load(f)

# Extract series data from JSON structure
all_series_data = []
for series in json_data.get('data', []):
    series_id = series['series_id']
    events = []
    for event in series['events']:
        numbers = event['numbers']
        events.append(numbers)

    all_series_data.append({
        'series_id': series_id,
        'events': events
    })

# Add Series 3144 and 3145
all_series_data.append({
    'series_id': 3144,
    'events': SERIES_3144
})

all_series_data.append({
    'series_id': 3145,
    'events': SERIES_3145
})

# Our prediction that failed
prediction = [1, 2, 4, 5, 7, 8, 11, 14, 17, 19, 21, 22, 24, 25]

# Critical numbers we missed
missed_critical = [9, 12, 16]

print("=" * 80)
print("DEEP-DIVE ANALYSIS: WHY DID WE MISS #09, #12, #16?")
print("=" * 80)
print()

# ============================================================================
# PART 1: Historical Frequency Analysis
# ============================================================================
print("=" * 80)
print("PART 1: HISTORICAL FREQUENCY ANALYSIS")
print("=" * 80)
print()

# Calculate frequency of missed numbers in historical data (before 3145)
historical_freq = Counter()
for series_data in all_series_data:
    if series_data['series_id'] < 3145:
        for event in series_data['events']:
            historical_freq.update(event)

total_series = sum(1 for s in all_series_data if s['series_id'] < 3145)
total_events = total_series * 7

print(f"Historical data: {total_series} series, {total_events} events")
print()

print("Missed Critical Numbers - Historical Frequency:")
for num in sorted(missed_critical):
    count = historical_freq[num]
    avg_per_series = count / total_series
    print(f"  #{num:02d}: {count}/{total_events} events ({count/total_events*100:.1f}%) - {avg_per_series:.2f} per series")

print()
print("Predicted Numbers - Historical Frequency (for comparison):")
for num in sorted(prediction):
    count = historical_freq[num]
    avg_per_series = count / total_series
    print(f"  #{num:02d}: {count}/{total_events} events ({count/total_events*100:.1f}%) - {avg_per_series:.2f} per series")

print()

# Rank all numbers by historical frequency
ranked_by_freq = sorted(historical_freq.items(), key=lambda x: x[1], reverse=True)
print("ALL NUMBERS ranked by historical frequency (top 25):")
for i, (num, count) in enumerate(ranked_by_freq, 1):
    in_pred = "✓" if num in prediction else "✗"
    missed = "← MISSED CRITICAL" if num in missed_critical else ""
    print(f"  {i:2d}. #{num:02d}: {count:4d} events ({count/total_events*100:.1f}%) {in_pred} {missed}")
print()

# ============================================================================
# PART 2: Recent Pattern Analysis (Last 20 series)
# ============================================================================
print("=" * 80)
print("PART 2: RECENT PATTERN ANALYSIS (Last 20 series)")
print("=" * 80)
print()

recent_series = [s for s in all_series_data if s['series_id'] >= 3125 and s['series_id'] < 3145]
recent_freq = Counter()
for series_data in recent_series:
    for event in series_data['events']:
        recent_freq.update(event)

recent_count = len(recent_series)
recent_events = recent_count * 7

print(f"Recent data: {recent_count} series (3125-3144), {recent_events} events")
print()

print("Missed Critical Numbers - Recent Frequency:")
for num in sorted(missed_critical):
    hist_count = historical_freq[num]
    hist_avg = hist_count / total_series
    recent_count_num = recent_freq[num]
    recent_avg = recent_count_num / recent_count if recent_count > 0 else 0
    diff = recent_avg - hist_avg
    print(f"  #{num:02d}: {recent_count_num}/{recent_events} events ({recent_count_num/recent_events*100:.1f}%)")
    print(f"        Historical avg: {hist_avg:.2f} per series")
    print(f"        Recent avg:     {recent_avg:.2f} per series")
    print(f"        Change:         {diff:+.2f} per series {'↑ TRENDING UP' if diff > 0.5 else ''}")
    print()

# ============================================================================
# PART 3: Model Weight Analysis
# ============================================================================
print("=" * 80)
print("PART 3: MODEL WEIGHT ANALYSIS")
print("=" * 80)
print()

# Train model exactly as we did for Series 3145 prediction
random.seed(999)
model = TrueLearningModel()

# Bulk training (all series before 3137)
bulk_series = [s for s in all_series_data if s['series_id'] < 3137]
for series_data in bulk_series:
    model.learn_from_series(series_data['series_id'], series_data['events'])

print(f"After bulk training ({len(bulk_series)} series):")
print()

# Check weights for missed numbers
print("Missed Critical Numbers - Model Weights BEFORE iterative validation:")
for num in sorted(missed_critical):
    weight = model.number_frequency_weights.get(num, 1.0)
    pos_weight = model.position_weights.get(num, 0.0)
    print(f"  #{num:02d}: freq_weight={weight:.4f}, pos_weight={pos_weight:.4f}")

print()
print("Predicted Numbers - Model Weights BEFORE iterative validation:")
for num in sorted(prediction):
    weight = model.number_frequency_weights.get(num, 1.0)
    pos_weight = model.position_weights.get(num, 0.0)
    print(f"  #{num:02d}: freq_weight={weight:.4f}, pos_weight={pos_weight:.4f}")

print()

# Iterative validation (3137-3144)
validation_series = [s for s in all_series_data if 3137 <= s['series_id'] <= 3144]
print(f"Performing iterative validation ({len(validation_series)} series: 3137-3144)...")
print()

for series_data in validation_series:
    # Predict (we don't need the actual prediction, just the learning)
    candidates = model._generate_candidates(num_candidates=10000)
    scored = model._score_candidates(candidates)

    # Learn from actual
    model.learn_from_series(series_data['series_id'], series_data['events'])

print("Missed Critical Numbers - Model Weights AFTER iterative validation:")
for num in sorted(missed_critical):
    weight = model.number_frequency_weights.get(num, 1.0)
    pos_weight = model.position_weights.get(num, 0.0)
    print(f"  #{num:02d}: freq_weight={weight:.4f}, pos_weight={pos_weight:.4f}")

print()
print("Predicted Numbers - Model Weights AFTER iterative validation:")
for num in sorted(prediction):
    weight = model.number_frequency_weights.get(num, 1.0)
    pos_weight = model.position_weights.get(num, 0.0)
    print(f"  #{num:02d}: freq_weight={weight:.4f}, pos_weight={pos_weight:.4f}")

print()

# ============================================================================
# PART 4: Candidate Scoring Analysis
# ============================================================================
print("=" * 80)
print("PART 4: CANDIDATE SCORING ANALYSIS")
print("=" * 80)
print()

# Generate candidates and see where numbers rank
candidates = model._generate_candidates(num_candidates=10000)
scored_candidates = model._score_candidates(candidates)

print("Analyzing 10,000 candidates...")
print()

# Count how often each number appears in top 100 candidates
top_100 = scored_candidates[:100]
number_frequency_top100 = Counter()
for cand, score in top_100:
    number_frequency_top100.update(cand)

print("Missed Critical Numbers - Frequency in TOP 100 candidates:")
for num in sorted(missed_critical):
    count = number_frequency_top100[num]
    print(f"  #{num:02d}: {count}/100 candidates ({count}%)")

print()
print("Predicted Numbers - Frequency in TOP 100 candidates:")
for num in sorted(prediction):
    count = number_frequency_top100[num]
    print(f"  #{num:02d}: {count}/100 candidates ({count}%)")

print()

# Find where the "ideal" prediction would rank
ideal_prediction = sorted(set([n for event in SERIES_3145 for n in event if
                               sum(1 for e in SERIES_3145 if n in e) >= 5]))[:14]
if len(ideal_prediction) < 14:
    # Add more numbers
    all_3145_nums = sorted(set([n for event in SERIES_3145 for n in event]))
    for num in all_3145_nums:
        if num not in ideal_prediction:
            ideal_prediction.append(num)
            if len(ideal_prediction) == 14:
                break

ideal_tuple = tuple(sorted(ideal_prediction))

# Score the ideal prediction
ideal_score = model._score_candidates([ideal_tuple])[0][1]

# Find rank of ideal prediction
found_rank = None
for i, (cand, score) in enumerate(scored_candidates, 1):
    if set(cand) == set(ideal_tuple):
        found_rank = i
        break

print(f"Ideal prediction for Series 3145: {' '.join(f'{n:02d}' for n in ideal_tuple)}")
print(f"Ideal prediction score: {ideal_score:.2f}")
if found_rank:
    print(f"Ideal prediction rank: {found_rank}/{len(scored_candidates)}")
else:
    print(f"Ideal prediction not found in candidates (not generated)")

print()

# What was our actual prediction score?
our_prediction_tuple = tuple(sorted(prediction))
our_score = model._score_candidates([our_prediction_tuple])[0][1]
print(f"Our prediction: {' '.join(f'{n:02d}' for n in prediction)}")
print(f"Our prediction score: {our_score:.2f}")
print(f"Our prediction rank: 1/{len(scored_candidates)} (selected as best)")

print()

# ============================================================================
# PART 5: Pair Affinity Analysis
# ============================================================================
print("=" * 80)
print("PART 5: PAIR AFFINITY ANALYSIS")
print("=" * 80)
print()

print("Did missed critical numbers have strong pair affinities?")
print()

for num in sorted(missed_critical):
    # Find pairs with this number
    pairs_with_num = [(pair, aff) for pair, aff in model.pair_affinities.items()
                      if num in pair and aff > 0]
    pairs_with_num.sort(key=lambda x: x[1], reverse=True)

    print(f"#{num:02d} - Top 10 pair affinities:")
    if pairs_with_num:
        for (n1, n2), aff in pairs_with_num[:10]:
            partner = n2 if n1 == num else n1
            in_pred = "✓" if partner in prediction else "✗"
            print(f"  #{num:02d}+#{partner:02d}: {aff:.2f} {in_pred}")
    else:
        print(f"  No pair affinities recorded")
    print()

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("Why did the model miss #09, #12, #16?")
print()
