#!/usr/bin/env python3
"""
Test IMPROVED Model: Ensemble Predictions

Strategy: Generate 5 predictions with different seeds, use voting
Expected: Reduce variance, more stable and potentially better results
"""

import json
from pathlib import Path
from true_learning_model_improved import TrueLearningModelImproved

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
    """Run IMPROVED model test"""

    print("=" * 80)
    print("IMPROVED MODEL TEST: Ensemble Predictions (5 runs with voting)")
    print("=" * 80)
    print()
    print("Strategy:")
    print("  1. Generate 5 predictions with different random seeds")
    print("  2. Count frequency of each number across all 5 predictions")
    print("  3. Select top 14 most frequent numbers")
    print()
    print("Expected: Reduce variance from random number generation")
    print("          More stable results, potentially beat 71.4%")
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

    # Initialize IMPROVED model with ensemble size 5
    model = TrueLearningModelImproved(ensemble_size=5)

    # Phase 1: Bulk training
    training_data = [s for s in all_series_data if s['series_id'] < validation_start]
    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    print(f"✅ Trained on {len(training_data)} historical series")
    print()

    # Phase 2: Iterative validation
    validation_series = [s for s in all_series_data if validation_start <= s['series_id'] <= latest_series]

    print(f"Iterative validation on {len(validation_series)} series")
    print(f"Using ensemble prediction (5 runs per series)")
    print("=" * 80)
    print()

    results = []

    for series_data in validation_series:
        series_id = series_data['series_id']
        actual_results = series_data['events']

        print(f"Series {series_id}", end=" ")

        # Generate ENSEMBLE prediction
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
    baseline_run1 = 0.714
    baseline_run2 = 0.688
    baseline_avg = (baseline_run1 + baseline_run2) / 2
    improvement_vs_best = avg_best - baseline_run1
    improvement_vs_avg = avg_best - baseline_avg

    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print()
    print(f"Phase 1 Pure (Run 1):       {baseline_run1:.1%}")
    print(f"Phase 1 Pure (Run 2):       {baseline_run2:.1%}")
    print(f"Phase 1 Pure (Average):     {baseline_avg:.1%}")
    print(f"IMPROVED (Ensemble):        {avg_best:.1%}")
    print()
    print(f"vs Best Baseline:           {improvement_vs_best:+.1%}")
    print(f"vs Average Baseline:        {improvement_vs_avg:+.1%}")
    print()

    if avg_best > baseline_run1:
        print("🎉 SUCCESS: IMPROVED model beats best baseline!")
        print(f"   Ensemble predictions work - variance reduced!")
    elif avg_best > baseline_avg:
        print("✅ GOOD: IMPROVED model beats average baseline")
        print(f"   More stable than single-run baseline")
    elif avg_best >= baseline_run2:
        print("⚠️  ACCEPTABLE: IMPROVED model matches worst baseline")
        print(f"   Ensemble didn't hurt, but no clear improvement")
    else:
        print("❌ REGRESSION: IMPROVED model worse than baseline")
        print(f"   Ensemble strategy didn't work")

    return avg_best


if __name__ == "__main__":
    run_test()
