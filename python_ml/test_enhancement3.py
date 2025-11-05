#!/usr/bin/env python3
"""
Test Enhancement 3: Larger Candidate Pool

Tests if increasing candidate pool improves exploration and performance.
"""

import json
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


def load_database_export():
    """Load data from JSON export"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found: {json_path}")
        return []

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    series_list = []
    for series in json_data.get('data', []):
        series_id = series['series_id']
        events = []
        for event in series['events']:
            numbers = event['numbers']
            events.append(numbers)

        series_list.append({
            'series_id': series_id,
            'events': events
        })

    print(f"✅ Loaded {len(series_list)} series from JSON export (2898-3143)")
    return series_list


def run_test():
    """Run Enhancement 3 test"""

    print("=" * 80)
    print("ENHANCEMENT 3 TEST: Larger Candidate Pool")
    print("=" * 80)
    print()
    print("Changes from Phase 1 Pure:")
    print("  - Candidate pool: 10,000 → 20,000 (+100%)")
    print("  - Candidates scored: 1,000 → 2,000 (+100%)")
    print()
    print("Rationale: More exploration might find better combinations")
    print("           Random component may need larger pool")
    print()
    print("Expected: Better exploration of solution space")
    print("Target: >71.4% (beat Phase 1 Pure baseline)")
    print()
    print("=" * 80)
    print()

    # Load data
    all_series_data = load_database_export()
    if not all_series_data:
        return

    # Add Series 3144
    all_series_data.append({
        'series_id': 3144,
        'events': SERIES_3144
    })

    latest_series = 3144
    validation_window_size = 8
    validation_start = latest_series - validation_window_size + 1
    training_end = validation_start - 1

    print(f"Training on all historical data up to series {training_end}")
    print(f"Validating on {validation_window_size} series ({validation_start}-{latest_series})")
    print("=" * 80)
    print()

    # Initialize model with LARGER candidate pool
    model = TrueLearningModel()
    model.CANDIDATE_POOL_SIZE = 20000  # Was 10000
    model.CANDIDATES_TO_SCORE = 2000   # Was 1000

    # Phase 1: Bulk training
    training_data = [s for s in all_series_data if s['series_id'] < validation_start]
    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    print(f"✅ Trained on {len(training_data)} historical series")
    print()

    # Phase 2: Iterative validation
    validation_series = [s for s in all_series_data if validation_start <= s['series_id'] <= latest_series]

    print(f"Iterative validation on {len(validation_series)} series")
    print("=" * 80)
    print()

    results = []

    for series_data in validation_series:
        series_id = series_data['series_id']
        actual_results = series_data['events']

        print(f"Series {series_id}", end=" ")

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Calculate accuracy
        accuracies = []
        for actual in actual_results:
            matches = len(set(prediction) & set(actual))
            accuracy = matches / 14.0
            accuracies.append(accuracy)

        best_accuracy = max(accuracies)
        avg_accuracy = sum(accuracies) / len(accuracies)

        print(f"→ Best: {best_accuracy:.1%} | Avg: {avg_accuracy:.1%}")

        # Learn from results
        model.validate_and_learn(series_id, prediction, actual_results)
        print()

        results.append({
            'series_id': series_id,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy
        })

    # Summary
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()

    avg_best = sum(r['best_accuracy'] for r in results) / len(results)
    avg_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print("Series | Best Match")
    print("-------|----------")
    for r in results:
        print(f" {r['series_id']} | {r['best_accuracy']:10.1%}")
    print()

    print(f"📈 Overall Best Average: {avg_best:.1%}")
    print(f"📊 Overall Average: {avg_avg:.1%}")
    print()

    # Comparison
    baseline_best = 0.714
    improvement = avg_best - baseline_best

    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print()
    print(f"Phase 1 Pure Baseline (10k pool):  {baseline_best:.1%}")
    print(f"Enhancement 3 (20k pool):          {avg_best:.1%}")
    print(f"Improvement:                       {improvement:+.1%}")
    print()

    if improvement > 0.01:  # >1% improvement
        print("✅ SUCCESS: Larger candidate pool works!")
        print(f"   More exploration = better results")
    elif improvement > 0:
        print("⚠️  MARGINAL: Small improvement, may be noise")
    else:
        print("❌ NO IMPROVEMENT: Larger pool doesn't help")
        print("   10k candidates was already sufficient")

    return avg_best, baseline_best


if __name__ == "__main__":
    run_test()
