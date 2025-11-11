#!/usr/bin/env python3
"""
Test Fine-Tuning of Lookback Window
Test lookback windows: 6, 7, 9, 10 (vs current optimal 8)
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

# Lookback windows to test
LOOKBACK_WINDOWS = [6, 7, 8, 9, 10]  # Include 8 as baseline

# Boost value (keep constant at optimal 30x)
BOOST = 30.0

# Seed for reproducibility
SEED = 999


def test_lookback_on_series(lookback: int, target_series: int):
    """Test a specific lookback window on a target series"""
    model = TrueLearningModel(seed=SEED, cold_hot_boost=BOOST)
    model.RECENT_SERIES_LOOKBACK = lookback

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

    # Get cold/hot numbers used
    start_series = target_series - lookback
    freq = defaultdict(int)
    for sid in range(start_series, target_series):
        if sid in SERIES_DATA:
            for event in SERIES_DATA[sid]:
                for num in event:
                    freq[num] += 1

    sorted_freq = sorted(freq.items(), key=lambda x: x[1])
    cold_numbers = [num for num, _ in sorted_freq[:7]]
    hot_numbers = [num for num, _ in sorted_freq[-7:]]

    return {
        'series': target_series,
        'lookback': lookback,
        'best_match': best_match / 14,
        'avg_match': avg_match / 14,
        'matches_per_event': matches_per_event,
        'prediction': prediction,
        'cold_numbers': cold_numbers,
        'hot_numbers': hot_numbers
    }


def main():
    print("=" * 70)
    print("LOOKBACK WINDOW FINE-TUNING TEST")
    print("=" * 70)
    print(f"\nTesting lookback windows: {LOOKBACK_WINDOWS}")
    print(f"Boost: {BOOST}x (constant)")
    print(f"Validation series: {VALIDATION_SERIES}")
    print(f"Seed: {SEED}")
    print()

    # Store all results
    results = {}

    # Test each lookback window
    for lookback in LOOKBACK_WINDOWS:
        print(f"\n{'=' * 70}")
        print(f"Testing Lookback: {lookback} series")
        print(f"{'=' * 70}")

        series_results = []

        for target_series in VALIDATION_SERIES:
            print(f"\nSeries {target_series}...", end=" ")
            result = test_lookback_on_series(lookback, target_series)
            series_results.append(result)
            print(f"Best: {result['best_match']*100:.1f}%, Avg: {result['avg_match']*100:.1f}%")

        # Calculate aggregate metrics
        avg_best_match = sum(r['best_match'] for r in series_results) / len(series_results)
        peak_best_match = max(r['best_match'] for r in series_results)

        results[f"{lookback}_series"] = {
            'lookback': lookback,
            'boost': BOOST,
            'avg_best_match': avg_best_match,
            'peak_best_match': peak_best_match,
            'series_results': series_results
        }

        print(f"\n{lookback}-series Summary:")
        print(f"  Average Best Match: {avg_best_match*100:.3f}%")
        print(f"  Peak Best Match: {peak_best_match*100:.1f}%")

    # Compare to baseline (8-series)
    print("\n" + "=" * 70)
    print("COMPARISON TO BASELINE (8-series)")
    print("=" * 70)

    baseline = results['8_series']
    baseline_avg = baseline['avg_best_match']

    print(f"\nBaseline (8-series): {baseline_avg*100:.3f}%\n")

    comparison = []
    for lookback in LOOKBACK_WINDOWS:
        key = f"{lookback}_series"
        avg = results[key]['avg_best_match']
        diff = avg - baseline_avg
        comparison.append((lookback, avg, diff))

        status = "✅ IMPROVED" if diff > 0.005 else "⚠️ SIMILAR" if abs(diff) <= 0.005 else "❌ WORSE"
        print(f"{lookback:2d}-series: {avg*100:6.3f}% ({diff*100:+.3f}%) {status}")

    # Find best
    best_lookback, best_avg, best_diff = max(comparison, key=lambda x: x[1])

    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)

    if best_lookback == 8:
        print(f"\n✅ KEEP CURRENT: 8-series lookback remains optimal")
        print(f"   Performance: {best_avg*100:.3f}%")
        print(f"   No improvement found in fine-tuning")
    else:
        print(f"\n🎯 NEW OPTIMAL: {best_lookback}-series lookback")
        print(f"   Performance: {best_avg*100:.3f}%")
        print(f"   Improvement: {best_diff*100:+.3f}% vs 8-series")
        print(f"   Expected correct: {best_avg*14:.1f}/14 numbers")

    # Save results
    output = {
        'test_name': 'Lookback Fine-Tuning',
        'test_date': '2025-11-11',
        'boost': BOOST,
        'seed': SEED,
        'validation_series': VALIDATION_SERIES,
        'lookback_windows_tested': LOOKBACK_WINDOWS,
        'results': results,
        'baseline': {
            'lookback': 8,
            'avg_best_match': baseline_avg,
        },
        'best_configuration': {
            'lookback': best_lookback,
            'avg_best_match': best_avg,
            'improvement_vs_baseline': best_diff
        },
        'recommendation': 'KEEP 8-series' if best_lookback == 8 else f'SWITCH to {best_lookback}-series'
    }

    with open('test_lookback_fine_tune_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n✅ Results saved to: test_lookback_fine_tune_results.json")


if __name__ == '__main__':
    main()
