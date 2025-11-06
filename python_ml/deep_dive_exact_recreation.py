#!/usr/bin/env python3
"""
Exact recreation of the prediction process to understand Series 3145 failure
"""

import json
import random
from collections import Counter
from pathlib import Path
from true_learning_model import TrueLearningModel

# Load data exactly as run_phase1_test.py does
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

# ==================================================================================
# EXACT RECREATION OF run_phase1_test.py TRAINING PROCESS
# ==================================================================================

print("=" * 80)
print("EXACT RECREATION: Series 3145 Prediction Process")
print("=" * 80)
print()

random.seed(999)
model = TrueLearningModel()

# Phase 1: Bulk training (exactly as run_phase1_test.py)
validation_window_size = 8
latest_series = 3144
validation_start = latest_series - validation_window_size + 1  # 3137

training_data = [s for s in all_series_data if s['series_id'] < validation_start]
for series in training_data:
    model.learn_from_series(series['series_id'], series['events'])

print(f"Phase 1: Bulk training on {len(training_data)} series (up to {validation_start-1})")
print()

# Phase 2: Iterative validation (exactly as run_phase1_test.py)
validation_series = [s for s in all_series_data if validation_start <= s['series_id'] <= latest_series]

print(f"Phase 2: Iterative validation on {len(validation_series)} series ({validation_start}-{latest_series})")
print("=" * 80)
print()

for series_data in validation_series:
    series_id = series_data['series_id']
    actual_results = series_data['events']

    print(f"Series {series_id}:")

    # Generate prediction
    prediction = model.predict_best_combination(series_id)
    print(f"  Prediction: {' '.join(f'{n:02d}' for n in prediction)}")

    # Calculate accuracy
    accuracies = []
    for actual in actual_results:
        matches = len(set(prediction) & set(actual))
        accuracy = matches / 14.0
        accuracies.append(accuracy)

    best_accuracy = max(accuracies)
    avg_accuracy = sum(accuracies) / len(accuracies)
    print(f"  Best: {best_accuracy:.1%}, Avg: {avg_accuracy:.1%}")

    # LEARN (exactly as run_phase1_test.py uses validate_and_learn)
    model.validate_and_learn(series_id, prediction, actual_results)
    print()

# Now generate Series 3145 prediction
print("=" * 80)
print("FINAL PREDICTION: Series 3145")
print("=" * 80)
print()

final_prediction = model.predict_best_combination(3145)
print(f"🎯 Prediction: {' '.join(f'{n:02d}' for n in final_prediction)}")
print()

# Load the recorded prediction
with open('prediction_3145.json', 'r') as f:
    recorded_prediction = json.load(f)['prediction']

print(f"📄 Recorded:   {' '.join(f'{n:02d}' for n in recorded_prediction)}")
print()

if final_prediction == recorded_prediction:
    print("✅ Predictions MATCH - exact recreation successful")
else:
    print("❌ Predictions DON'T MATCH")
    print(f"   Numbers in final but not recorded: {set(final_prediction) - set(recorded_prediction)}")
    print(f"   Numbers in recorded but not final: {set(recorded_prediction) - set(final_prediction)}")
print()

# Now test against actual Series 3145
print("=" * 80)
print("PERFORMANCE ON SERIES 3145")
print("=" * 80)
print()

print("Using FINAL prediction (just generated):")
print(f"  {' '.join(f'{n:02d}' for n in final_prediction)}")
print()

matches_per_event = []
for i, actual in enumerate(SERIES_3145, 1):
    matches = set(final_prediction) & set(actual)
    match_count = len(matches)
    accuracy = match_count / 14.0
    matches_per_event.append(match_count)
    print(f"Event {i}: {match_count}/14 ({accuracy:.1%})")

best = max(matches_per_event)
avg = sum(matches_per_event) / len(matches_per_event)
print()
print(f"Best Match: {best}/14 ({best/14:.1%})")
print(f"Average: {avg:.2f}/14 ({avg/14:.1%})")
print()

# Critical numbers analysis
number_freq_3145 = Counter()
for event in SERIES_3145:
    number_freq_3145.update(event)

critical = {num: count for num, count in number_freq_3145.items() if count >= 5}
print(f"Critical numbers in Series 3145 (5+ events): {len(critical)}")
for num in sorted(critical.keys()):
    in_pred = "✓" if num in final_prediction else "✗"
    print(f"  #{num:02d}: {critical[num]}/7 events {in_pred}")

critical_hit = sum(1 for num in critical if num in final_prediction)
print(f"\nCritical hit rate: {critical_hit}/{len(critical)} ({critical_hit/len(critical)*100:.1f}%)")
print()

# Compare with recorded prediction
print("=" * 80)
print("Using RECORDED prediction (from prediction_3145.json):")
print(f"  {' '.join(f'{n:02d}' for n in recorded_prediction)}")
print()

matches_per_event = []
for i, actual in enumerate(SERIES_3145, 1):
    matches = set(recorded_prediction) & set(actual)
    match_count = len(matches)
    accuracy = match_count / 14.0
    matches_per_event.append(match_count)
    print(f"Event {i}: {match_count}/14 ({accuracy:.1%})")

best = max(matches_per_event)
avg = sum(matches_per_event) / len(matches_per_event)
print()
print(f"Best Match: {best}/14 ({best/14:.1%})")
print(f"Average: {avg:.2f}/14 ({avg/14:.1%})")
print()

critical_hit = sum(1 for num in critical if num in recorded_prediction)
print(f"Critical hit rate: {critical_hit}/{len(critical)} ({critical_hit/len(critical)*100:.1f}%)")
print()
