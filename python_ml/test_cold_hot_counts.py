#!/usr/bin/env python3
"""
Test Different Cold/Hot Number Counts
Test counts: 5, 6, 7, 8, 9, 10 (vs current 7+7)
Expected improvement: +0.5% to +1.5%
"""

import json
from collections import defaultdict
from true_learning_model import TrueLearningModel

# Load data
with open('full_series_data_expanded.json', 'r') as f:
    data = json.load(f)
SERIES_DATA = {int(k): v for k, v in data.items()}

# Validation series
VALIDATION_SERIES = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

# Cold/Hot counts to test
COUNTS = [5, 6, 7, 8, 9, 10]  # Include 7 as baseline

# Lookback window (keep constant at optimal 8)
LOOKBACK = 8

# Boost value (use NEW optimal 29x from previous test)
BOOST = 29.0

# Seed for reproducibility
SEED = 999


def test_count_on_series(count: int, target_series: int):
    """Test a specific cold/hot count on a target series"""
    model = TrueLearningModel(seed=SEED, cold_hot_boost=BOOST)
    model.RECENT_SERIES_LOOKBACK = LOOKBACK
    model.COLD_NUMBER_COUNT = count
    model.HOT_NUMBER_COUNT = count

    # Train on all data before target
    for sid in sorted(SERIES_DATA.keys()):
        if sid < target_series:
            model.learn_from_series(sid, SERIES_DATA[sid])

    # Generate prediction
    prediction = model.predict_best_combination(target_series)

    # Evaluate against actual
    actual_events = SERIES_DATA[target_series]
    pred_set = set(prediction)

    matches_per_event = []
    for event in actual_events:
        event_set = set(event)
        matches = len(pred_set & event_set)
        matches_per_event.append(matches)

    best_match = max(matches_per_event)
    avg_match = sum(matches_per_event) / len(matches_per_event)

    return {
        'series': target_series,
        'count': count,
        'best_match': best_match / 14,
        'avg_match': avg_match / 14,
        'matches_per_event': matches_per_event,
        'prediction': prediction
    }


def main():
    print("=" * 70)
    print("COLD/HOT COUNT FINE-TUNING TEST")
    print("=" * 70)
    print(f"\nTesting cold/hot counts: {COUNTS}")
    print(f"Lookback: {LOOKBACK} series (constant)")
    print(f"Boost: {BOOST}x (NEW optimal from previous test)")
    print(f"Validation series: {VALIDATION_SERIES}")
    print(f"Seed: {SEED}")
    print()

    # Store all results
    results = {}

    # Test each count
    for count in COUNTS:
        print(f"\n{'=' * 70}")
        print(f"Testing Count: {count} cold + {count} hot")
        print(f"{'=' * 70}")

        series_results = []

        for target_series in VALIDATION_SERIES:
            print(f"\nSeries {target_series}...", end=" ")
            result = test_count_on_series(count, target_series)
            series_results.append(result)
            print(f"Best: {result['best_match']*100:.1f}%, Avg: {result['avg_match']*100:.1f}%")

        # Calculate aggregate metrics
        avg_best_match = sum(r['best_match'] for r in series_results) / len(series_results)
        peak_best_match = max(r['best_match'] for r in series_results)

        results[f"count_{count}"] = {
            'cold_count': count,
            'hot_count': count,
            'lookback': LOOKBACK,
            'boost': BOOST,
            'avg_best_match': avg_best_match,
            'peak_best_match': peak_best_match,
            'series_results': series_results
        }

        print(f"\n{count}+{count} Count Summary:")
        print(f"  Average Best Match: {avg_best_match*100:.3f}%")
        print(f"  Peak Best Match: {peak_best_match*100:.1f}%")

    # Compare to baseline (7+7)
    print("\n" + "=" * 70)
    print("COMPARISON TO BASELINE (7+7)")
    print("=" * 70)

    baseline = results['count_7']
    baseline_avg = baseline['avg_best_match']

    print(f"\nBaseline (7+7): {baseline_avg*100:.3f}%\n")

    comparison = []
    for count in COUNTS:
        key = f"count_{count}"
        avg = results[key]['avg_best_match']
        diff = avg - baseline_avg
        comparison.append((count, avg, diff))

        status = "✅ IMPROVED" if diff > 0.005 else "⚠️ SIMILAR" if abs(diff) <= 0.005 else "❌ WORSE"
        print(f"{count:2d}+{count:2d}: {avg*100:6.3f}% ({diff*100:+.3f}%) {status}")

    # Find best
    best_count, best_avg, best_diff = max(comparison, key=lambda x: x[1])

    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)

    if abs(best_diff) <= 0.005:  # Within 0.5%
        print(f"\n✅ KEEP CURRENT: 7+7 count remains optimal")
        print(f"   Performance: {baseline_avg*100:.3f}%")
        print(f"   No meaningful improvement found in fine-tuning")
    else:
        print(f"\n🎯 NEW OPTIMAL: {best_count}+{best_count} count")
        print(f"   Performance: {best_avg*100:.3f}%")
        print(f"   Improvement: {best_diff*100:+.3f}% vs 7+7")
        print(f"   Expected correct: {best_avg*14:.1f}/14 numbers")

    # Save results
    output = {
        'test_name': 'Cold/Hot Count Fine-Tuning',
        'test_date': '2025-11-11',
        'lookback': LOOKBACK,
        'boost': BOOST,
        'seed': SEED,
        'validation_series': VALIDATION_SERIES,
        'counts_tested': COUNTS,
        'results': results,
        'baseline': {
            'count': 7,
            'avg_best_match': baseline_avg,
        },
        'best_configuration': {
            'count': best_count,
            'avg_best_match': best_avg,
            'improvement_vs_baseline': best_diff
        },
        'recommendation': 'KEEP 7+7' if abs(best_diff) <= 0.005 else f'SWITCH to {best_count}+{best_count}'
    }

    with open('test_cold_hot_counts_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n✅ Results saved to: test_cold_hot_counts_results.json")


if __name__ == '__main__':
    main()
