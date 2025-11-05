#!/usr/bin/env python3
"""
Confidence Interval Testing - Phase 1 Critical

Tests seed 999 performance across multiple runs to establish:
1. Mean performance ± confidence interval
2. Performance stability
3. Statistical significance baseline
"""

import json
import random
from pathlib import Path
from typing import List, Dict
from true_learning_model import TrueLearningModel
import statistics

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


def load_all_data():
    """Load all series data"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found")
        return []

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    all_series = []
    for series in json_data.get('data', []):
        all_series.append({
            'series_id': series['series_id'],
            'events': [event['numbers'] for event in series['events']]
        })

    # Add Series 3144
    all_series.append({'series_id': 3144, 'events': SERIES_3144})

    return all_series


def run_single_test(all_series_data, test_num: int, verbose=False):
    """Run single test with seed 999"""
    random.seed(999)  # Fixed seed for consistency

    validation_window = 8
    latest_series = 3144
    validation_start = latest_series - validation_window + 1  # 3137

    # Initialize model
    model = TrueLearningModel()

    # Bulk training
    for series in all_series_data:
        if series['series_id'] < validation_start:
            model.learn_from_series(series['series_id'], series['events'])

    # Iterative validation
    accuracies = []
    series_details = []

    for series_data in all_series_data:
        if validation_start <= series_data['series_id'] <= latest_series:
            series_id = series_data['series_id']
            actual_results = series_data['events']

            # Predict
            prediction = model.predict_best_combination(series_id)

            # Calculate best match
            best_match = max(len(set(prediction) & set(actual)) for actual in actual_results)
            best_accuracy = best_match / 14.0
            accuracies.append(best_accuracy)

            series_details.append({
                'series_id': series_id,
                'best_match': best_match,
                'accuracy': best_accuracy
            })

            if verbose:
                print(f"  Series {series_id}: {best_accuracy:.1%} ({best_match}/14)")

            # Learn
            model.validate_and_learn(series_id, prediction, actual_results)

    avg_accuracy = sum(accuracies) / len(accuracies)
    peak_accuracy = max(accuracies)
    min_accuracy = min(accuracies)

    return {
        'test_num': test_num,
        'average': avg_accuracy,
        'peak': peak_accuracy,
        'min': min_accuracy,
        'series_details': series_details
    }


def main():
    print("=" * 80)
    print("CONFIDENCE INTERVAL TESTING - Seed 999")
    print("=" * 80)
    print()
    print("Research Question: How stable is 73.2% performance?")
    print("Method: Run 30 independent tests with seed 999")
    print()

    # Load data once
    print("Loading data...")
    all_series_data = load_all_data()
    if not all_series_data:
        print("❌ Failed to load data")
        return
    print(f"✅ Loaded {len(all_series_data)} series")
    print()

    # Run multiple tests
    num_tests = 30
    print(f"Running {num_tests} tests with seed 999...")
    print()

    results = []
    for i in range(num_tests):
        print(f"Test {i+1}/{num_tests}...", end=" ", flush=True)
        result = run_single_test(all_series_data, i+1)
        results.append(result)
        print(f"{result['average']:.1%}")

    print()
    print("=" * 80)
    print("STATISTICAL ANALYSIS")
    print("=" * 80)
    print()

    # Extract metrics
    averages = [r['average'] for r in results]
    peaks = [r['peak'] for r in results]
    mins = [r['min'] for r in results]

    # Calculate statistics
    mean_avg = statistics.mean(averages)
    stdev_avg = statistics.stdev(averages) if len(averages) > 1 else 0
    mean_peak = statistics.mean(peaks)
    stdev_peak = statistics.stdev(peaks) if len(peaks) > 1 else 0

    # 95% confidence interval (±1.96 * std error)
    std_error = stdev_avg / (len(averages) ** 0.5)
    ci_95_lower = mean_avg - (1.96 * std_error)
    ci_95_upper = mean_avg + (1.96 * std_error)

    print(f"Average Performance:")
    print(f"  Mean:    {mean_avg:.3%}")
    print(f"  Std Dev: {stdev_avg:.3%}")
    print(f"  Min:     {min(averages):.3%}")
    print(f"  Max:     {max(averages):.3%}")
    print(f"  Range:   {max(averages) - min(averages):.3%}")
    print()
    print(f"95% Confidence Interval: [{ci_95_lower:.3%}, {ci_95_upper:.3%}]")
    print()

    print(f"Peak Performance:")
    print(f"  Mean:    {mean_peak:.3%}")
    print(f"  Std Dev: {stdev_peak:.3%}")
    print(f"  Min:     {min(peaks):.3%}")
    print(f"  Max:     {max(peaks):.3%}")
    print()

    # Per-series variance
    print("Per-Series Consistency:")
    print()

    # Collect per-series accuracies across all tests
    series_performance = {}
    for result in results:
        for detail in result['series_details']:
            series_id = detail['series_id']
            if series_id not in series_performance:
                series_performance[series_id] = []
            series_performance[series_id].append(detail['accuracy'])

    for series_id in sorted(series_performance.keys()):
        accs = series_performance[series_id]
        mean_acc = statistics.mean(accs)
        stdev_acc = statistics.stdev(accs) if len(accs) > 1 else 0
        print(f"  Series {series_id}: {mean_acc:.3%} ± {stdev_acc:.3%}")

    print()
    print("=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print()

    if stdev_avg < 0.01:
        print(f"✅ HIGHLY STABLE: {stdev_avg:.3%} std dev (< 1%)")
        print(f"   Seed 999 produces consistent {mean_avg:.1%} performance")
    elif stdev_avg < 0.03:
        print(f"✅ STABLE: {stdev_avg:.3%} std dev (< 3%)")
        print(f"   Seed 999 produces reliable {mean_avg:.1%} ± {stdev_avg:.1%} performance")
    else:
        print(f"⚠️  VARIABLE: {stdev_avg:.3%} std dev (> 3%)")
        print(f"   Performance varies: {min(averages):.1%} - {max(averages):.1%}")

    print()
    print(f"Baseline for future tests: {mean_avg:.3%} ± {stdev_avg:.3%}")
    print(f"Improvement threshold: >{ci_95_upper:.3%} (95% confidence)")
    print()

    # Save results
    output = {
        'num_tests': num_tests,
        'seed': 999,
        'statistics': {
            'mean_average': mean_avg,
            'stdev_average': stdev_avg,
            'ci_95_lower': ci_95_lower,
            'ci_95_upper': ci_95_upper,
            'mean_peak': mean_peak,
            'stdev_peak': stdev_peak,
            'range': max(averages) - min(averages),
        },
        'all_results': results,
        'per_series_stats': {
            str(sid): {
                'mean': statistics.mean(series_performance[sid]),
                'stdev': statistics.stdev(series_performance[sid]) if len(series_performance[sid]) > 1 else 0,
            }
            for sid in sorted(series_performance.keys())
        }
    }

    output_file = Path(__file__).parent / 'confidence_intervals_seed999.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
