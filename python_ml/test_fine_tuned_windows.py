#!/usr/bin/env python3
"""
Fine-tune the recent data window size.

Previous test showed 50 series was best (+1.4%).
Now testing more granularly: 30, 35, 40, 45, 55, 60, 65, 70

Looking for sweet spot between:
- Too little data: High variance, insufficient patterns
- Too much data: Old noise dilutes recent patterns

Current best: 50 series → 57.7% actual average
"""

import json
import sys
import random
from pathlib import Path
from true_learning_model import TrueLearningModel

# Series data
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]

SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
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

    return series_list


def test_recent_count(recent_count, seed=999):
    """Test specific recent series count"""
    print(f"Testing {recent_count} recent series... ", end='', flush=True)

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Fixed validation window (8 series)
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1  # 3138
    training_start = validation_start - recent_count

    # Initialize model
    random.seed(seed)
    model = TrueLearningModel()

    # Phase 1: Bulk training (ONLY recent series)
    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]

    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    # Phase 2: Iterative validation
    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    results = []
    for series in validation_series:
        series_id = series['series_id']
        actual_events = series['events']

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Calculate accuracy for each event
        event_accuracies = []
        for actual in actual_events:
            matches = len(set(prediction) & set(actual))
            accuracy = matches / 14
            event_accuracies.append(accuracy)

        best_accuracy = max(event_accuracies)
        avg_accuracy = sum(event_accuracies) / len(event_accuracies)

        results.append({
            'series_id': series_id,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy
        })

        # Learn from this series
        model.learn_from_series(series_id, actual_events)

    # Calculate overall metrics
    overall_best_avg = sum(r['best_accuracy'] for r in results) / len(results)
    overall_actual_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print(f"Actual: {overall_actual_avg*100:.1f}%")

    return {
        'recent_count': recent_count,
        'actual_avg': overall_actual_avg,
        'best_match_avg': overall_best_avg,
        'results': results
    }


def main():
    """Fine-tune recent data window"""
    print("="*80)
    print("FINE-TUNED RECENT DATA WINDOW OPTIMIZATION")
    print("="*80)
    print()
    print("Current best: 50 series → 57.7% actual average")
    print("Testing: 30, 35, 40, 45, 55, 60, 65, 70 series")
    print("="*80)
    print()

    # Test various window sizes around 50
    window_sizes = [30, 35, 40, 45, 50, 55, 60, 65, 70]
    all_results = []

    for size in window_sizes:
        result = test_recent_count(size)
        all_results.append(result)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - RANKED BY ACTUAL AVERAGE")
    print("="*80)
    print()
    print("Recent Series | ACTUAL Avg | vs Best (57.7%)")
    print("--------------|------------|----------------")

    # Sort by actual average (descending)
    sorted_results = sorted(all_results, key=lambda x: x['actual_avg'], reverse=True)
    baseline_actual = 0.577  # Current best (50 series)

    for result in sorted_results:
        size = result['recent_count']
        actual = result['actual_avg'] * 100
        vs_baseline = result['actual_avg'] - baseline_actual

        if vs_baseline > 0.01:
            verdict = f"+{vs_baseline*100:.1f}% ✅"
        elif vs_baseline > -0.01:
            verdict = "~same ➖"
        else:
            verdict = f"{vs_baseline*100:.1f}% ❌"

        marker = " ← CURRENT" if size == 50 else ""
        print(f"    {size:3d} series |     {actual:5.1f}% | {verdict}{marker}")

    print()
    print("="*80)
    print("CONCLUSION:")
    print("="*80)

    best = sorted_results[0]
    if best['actual_avg'] > baseline_actual + 0.01:
        print(f"✅ IMPROVEMENT FOUND: {best['recent_count']} series")
        print(f"   Actual average: {best['actual_avg']*100:.1f}% (vs {baseline_actual*100:.1f}% baseline)")
        print(f"   Improvement: +{(best['actual_avg'] - baseline_actual)*100:.1f}%")
        print(f"   RECOMMENDATION: Update to {best['recent_count']} series")
    elif best['recent_count'] == 50:
        print(f"✅ CURRENT IS OPTIMAL: 50 series")
        print(f"   Performance: {best['actual_avg']*100:.1f}%")
        print(f"   No better window size found")
    else:
        print(f"➖ MARGINAL DIFFERENCE")
        print(f"   Best: {best['recent_count']} series at {best['actual_avg']*100:.1f}%")
        print(f"   Current: 50 series at {baseline_actual*100:.1f}%")
        print(f"   Difference within noise")

    # Save results
    output_file = "test_fine_tuned_windows_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'baseline': baseline_actual,
            'results': all_results,
            'best': {
                'recent_count': best['recent_count'],
                'actual_avg': best['actual_avg'],
                'improvement': best['actual_avg'] - baseline_actual
            }
        }, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
