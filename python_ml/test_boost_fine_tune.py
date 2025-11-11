#!/usr/bin/env python3
"""
Test Fine-Tuning of Cold/Hot Boost
Test boost values: 27x, 28x, 29x, 30x, 31x, 32x (vs current optimal 30x)
Expected improvement: +0.3% to +1.0%
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

# Boost values to test
BOOST_VALUES = [27.0, 28.0, 29.0, 30.0, 31.0, 32.0]  # Include 30.0 as baseline

# Lookback window (keep constant at optimal 8)
LOOKBACK = 8

# Seed for reproducibility
SEED = 999


def test_boost_on_series(boost: float, target_series: int):
    """Test a specific boost value on a target series"""
    model = TrueLearningModel(seed=SEED, cold_hot_boost=boost)
    model.RECENT_SERIES_LOOKBACK = LOOKBACK

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
        'boost': boost,
        'best_match': best_match / 14,
        'avg_match': avg_match / 14,
        'matches_per_event': matches_per_event,
        'prediction': prediction
    }


def main():
    print("=" * 70)
    print("COLD/HOT BOOST FINE-TUNING TEST")
    print("=" * 70)
    print(f"\nTesting boost values: {BOOST_VALUES}")
    print(f"Lookback: {LOOKBACK} series (constant)")
    print(f"Validation series: {VALIDATION_SERIES}")
    print(f"Seed: {SEED}")
    print()

    # Store all results
    results = {}

    # Test each boost value
    for boost in BOOST_VALUES:
        print(f"\n{'=' * 70}")
        print(f"Testing Boost: {boost}x")
        print(f"{'=' * 70}")

        series_results = []

        for target_series in VALIDATION_SERIES:
            print(f"\nSeries {target_series}...", end=" ")
            result = test_boost_on_series(boost, target_series)
            series_results.append(result)
            print(f"Best: {result['best_match']*100:.1f}%, Avg: {result['avg_match']*100:.1f}%")

        # Calculate aggregate metrics
        avg_best_match = sum(r['best_match'] for r in series_results) / len(series_results)
        peak_best_match = max(r['best_match'] for r in series_results)

        results[f"boost_{int(boost)}x"] = {
            'boost': boost,
            'lookback': LOOKBACK,
            'avg_best_match': avg_best_match,
            'peak_best_match': peak_best_match,
            'series_results': series_results
        }

        print(f"\n{boost}x Boost Summary:")
        print(f"  Average Best Match: {avg_best_match*100:.3f}%")
        print(f"  Peak Best Match: {peak_best_match*100:.1f}%")

    # Compare to baseline (30x)
    print("\n" + "=" * 70)
    print("COMPARISON TO BASELINE (30x)")
    print("=" * 70)

    baseline = results['boost_30x']
    baseline_avg = baseline['avg_best_match']

    print(f"\nBaseline (30x): {baseline_avg*100:.3f}%\n")

    comparison = []
    for boost in BOOST_VALUES:
        key = f"boost_{int(boost)}x"
        avg = results[key]['avg_best_match']
        diff = avg - baseline_avg
        comparison.append((boost, avg, diff))

        status = "✅ IMPROVED" if diff > 0.003 else "⚠️ SIMILAR" if abs(diff) <= 0.003 else "❌ WORSE"
        print(f"{boost:4.0f}x: {avg*100:6.3f}% ({diff*100:+.3f}%) {status}")

    # Find best
    best_boost, best_avg, best_diff = max(comparison, key=lambda x: x[1])

    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)

    if abs(best_diff) <= 0.003:  # Within 0.3%
        print(f"\n✅ KEEP CURRENT: 30x boost remains optimal")
        print(f"   Performance: {baseline_avg*100:.3f}%")
        print(f"   No meaningful improvement found in fine-tuning")
    else:
        print(f"\n🎯 NEW OPTIMAL: {best_boost:.0f}x boost")
        print(f"   Performance: {best_avg*100:.3f}%")
        print(f"   Improvement: {best_diff*100:+.3f}% vs 30x")
        print(f"   Expected correct: {best_avg*14:.1f}/14 numbers")

    # Save results
    output = {
        'test_name': 'Cold/Hot Boost Fine-Tuning',
        'test_date': '2025-11-11',
        'lookback': LOOKBACK,
        'seed': SEED,
        'validation_series': VALIDATION_SERIES,
        'boost_values_tested': BOOST_VALUES,
        'results': results,
        'baseline': {
            'boost': 30.0,
            'avg_best_match': baseline_avg,
        },
        'best_configuration': {
            'boost': best_boost,
            'avg_best_match': best_avg,
            'improvement_vs_baseline': best_diff
        },
        'recommendation': 'KEEP 30x' if abs(best_diff) <= 0.003 else f'SWITCH to {best_boost:.0f}x'
    }

    with open('test_boost_fine_tune_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n✅ Results saved to: test_boost_fine_tune_results.json")


if __name__ == '__main__':
    main()
