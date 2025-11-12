#!/usr/bin/env python3
"""
EXHAUSTIVE MANDEL vs RANDOM SAMPLING - Performance Comparison
=============================================================

Compare two pool generation strategies:
1. Random Sampling: Generate 10,000 random candidates, pick best
2. Exhaustive Mandel: Score ALL 4,457,400 combinations, pick best

Both use the same trained ML model. Only difference is candidate pool.

Hypothesis: Exhaustive search should find equal or better combinations
since it has access to ALL possibilities, not just a sample.
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from true_learning_model import TrueLearningModel
from true_mandel_exhaustive import TrueMandel


def load_all_series_data():
    """Load all series data from JSON export + hardcoded recent series"""
    # Load from JSON export
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    series_dict = {}

    if json_path.exists():
        with open(json_path, 'r') as f:
            json_data = json.load(f)

        for series in json_data.get('data', []):
            series_id = series['series_id']
            events = [event['numbers'] for event in series['events']]
            series_dict[series_id] = events

    # Add hardcoded recent series
    series_dict[3144] = [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
    ]

    series_dict[3145] = [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
    ]

    series_dict[3147] = [
        [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
        [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
        [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
        [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
        [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
        [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
        [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
    ]

    return series_dict


def calculate_match_percentage(prediction: List[int], actual_events: List[List[int]]) -> Dict[str, Any]:
    """Calculate match statistics for a prediction"""
    prediction_set = set(prediction)

    matches_per_event = []
    for event in actual_events:
        event_set = set(event)
        matches = len(prediction_set & event_set)
        matches_per_event.append(matches)

    best_match = max(matches_per_event)
    avg_match = sum(matches_per_event) / len(matches_per_event)

    return {
        'best_match': best_match,
        'best_match_pct': (best_match / 14) * 100,
        'avg_match': avg_match,
        'avg_match_pct': (avg_match / 14) * 100,
        'matches_per_event': matches_per_event
    }


def test_series_with_random(series_id: int, series_data: dict, seed: int = 999) -> dict:
    """
    Test a series using Random Sampling method (current production)
    """
    # Create and train model
    model = TrueLearningModel(seed=seed, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = 8

    # Train on all data before target series
    for sid in sorted(series_data.keys()):
        if sid < series_id:
            model.learn_from_series(sid, series_data[sid])

    # Generate prediction using random sampling (default method)
    start = time.time()
    prediction = model.predict_best_combination(series_id)
    elapsed = time.time() - start

    # Calculate match statistics
    actual_events = series_data[series_id]
    match_stats = calculate_match_percentage(prediction, actual_events)

    return {
        'series_id': series_id,
        'method': 'random_sampling',
        'prediction': prediction,
        'match_stats': match_stats,
        'time_seconds': elapsed
    }


def test_series_with_exhaustive(series_id: int, series_data: dict, seed: int = 999) -> dict:
    """
    Test a series using Exhaustive Mandel method (all 4.4M combinations)
    """
    # Create and train model
    model = TrueLearningModel(seed=seed, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = 8

    # Train on all data before target series
    for sid in sorted(series_data.keys()):
        if sid < series_id:
            model.learn_from_series(sid, series_data[sid])

    # Generate prediction using exhaustive search
    mandel = TrueMandel(model)
    result = mandel.find_best_combination(show_progress=True)

    prediction = result['best_combination']
    elapsed = result['time_taken']

    # Calculate match statistics
    actual_events = series_data[series_id]
    match_stats = calculate_match_percentage(prediction, actual_events)

    return {
        'series_id': series_id,
        'method': 'exhaustive_mandel',
        'prediction': prediction,
        'ml_score': result['best_score'],
        'match_stats': match_stats,
        'time_seconds': elapsed,
        'combinations_scored': result['total_scored']
    }


def run_comparison_test():
    """
    Run comparison test on validation series
    """
    print("=" * 80)
    print("EXHAUSTIVE MANDEL vs RANDOM SAMPLING - COMPARISON TEST")
    print("=" * 80)
    print()

    # Load data
    series_data = load_all_series_data()

    # Test on recent series
    test_series = [3147]  # Start with one series, can expand later

    print(f"Testing on {len(test_series)} series: {test_series}")
    print(f"Total historical data: {len(series_data)} series")
    print()

    results = {}

    for series_id in test_series:
        print("\n" + "=" * 80)
        print(f"TESTING SERIES {series_id}")
        print("=" * 80)

        # Test with Random Sampling
        print("\n--- Method 1: Random Sampling (10K candidates) ---")
        result_random = test_series_with_random(series_id, series_data, seed=999)
        print(f"✅ Random Sampling: {result_random['match_stats']['best_match_pct']:.1f}% best match")
        print(f"   Prediction: {result_random['prediction']}")
        print(f"   Time: {result_random['time_seconds']:.2f} seconds")

        # Test with Exhaustive Mandel
        print("\n--- Method 2: Exhaustive Mandel (4.4M combinations) ---")
        result_exhaustive = test_series_with_exhaustive(series_id, series_data, seed=999)
        print(f"✅ Exhaustive Mandel: {result_exhaustive['match_stats']['best_match_pct']:.1f}% best match")
        print(f"   Prediction: {result_exhaustive['prediction']}")
        print(f"   Time: {result_exhaustive['time_seconds']:.2f} seconds")
        print(f"   ML Score: {result_exhaustive['ml_score']:.4f}")

        # Comparison
        print("\n" + "-" * 80)
        print("COMPARISON:")
        print("-" * 80)

        diff = result_exhaustive['match_stats']['best_match_pct'] - result_random['match_stats']['best_match_pct']
        time_ratio = result_exhaustive['time_seconds'] / result_random['time_seconds']

        print(f"Performance difference: {diff:+.1f}% (Exhaustive vs Random)")
        print(f"Time ratio: {time_ratio:.1f}x (Exhaustive takes {time_ratio:.1f}x longer)")

        if diff > 0:
            print(f"✅ WINNER: Exhaustive Mandel (+{diff:.1f}% accuracy)")
        elif diff < 0:
            print(f"✅ WINNER: Random Sampling (+{abs(diff):.1f}% accuracy)")
        else:
            print("➖ TIE: Both methods equal")

        # Check if predictions are identical
        if result_random['prediction'] == result_exhaustive['prediction']:
            print("\n🎯 IDENTICAL PREDICTIONS: Both methods found the same combination!")
        else:
            # Count differences
            set_random = set(result_random['prediction'])
            set_exhaustive = set(result_exhaustive['prediction'])
            common = set_random & set_exhaustive
            print(f"\n🔄 DIFFERENT PREDICTIONS: {len(common)}/14 numbers in common")
            print(f"   Random only: {sorted(set_random - set_exhaustive)}")
            print(f"   Exhaustive only: {sorted(set_exhaustive - set_random)}")

        results[series_id] = {
            'random': result_random,
            'exhaustive': result_exhaustive,
            'difference': diff,
            'time_ratio': time_ratio
        }

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    avg_diff = sum(r['difference'] for r in results.values()) / len(results)
    avg_time_ratio = sum(r['time_ratio'] for r in results.values()) / len(results)

    exhaustive_wins = sum(1 for r in results.values() if r['difference'] > 0.1)
    random_wins = sum(1 for r in results.values() if r['difference'] < -0.1)
    ties = len(results) - exhaustive_wins - random_wins

    print(f"\nTested {len(results)} series")
    print(f"Average performance difference: {avg_diff:+.1f}% (Exhaustive vs Random)")
    print(f"Average time ratio: {avg_time_ratio:.1f}x (Exhaustive / Random)")
    print()
    print(f"Exhaustive wins: {exhaustive_wins}/{len(results)}")
    print(f"Random wins: {random_wins}/{len(results)}")
    print(f"Ties: {ties}/{len(results)}")
    print()

    if avg_diff > 0.5:
        print("✅ RECOMMENDATION: ADOPT EXHAUSTIVE MANDEL")
        print(f"   - Better accuracy: +{avg_diff:.1f}%")
        print(f"   - Time cost: {avg_time_ratio:.1f}x longer (~{avg_time_ratio * 0.1:.0f} seconds vs ~0.1 seconds)")
        print(f"   - Trade-off: Worth it for {avg_diff:.1f}% improvement")
    elif avg_diff < -0.5:
        print("✅ RECOMMENDATION: KEEP RANDOM SAMPLING")
        print(f"   - Random is better: +{abs(avg_diff):.1f}%")
        print(f"   - Exhaustive is {avg_time_ratio:.1f}x slower for worse results")
    else:
        print("➖ RECOMMENDATION: KEEP RANDOM SAMPLING")
        print(f"   - Negligible difference: {avg_diff:+.1f}%")
        print(f"   - Exhaustive is {avg_time_ratio:.1f}x slower for no benefit")
        print(f"   - Random sampling is sufficient")

    # Save results
    output_file = Path(__file__).parent / 'exhaustive_vs_random_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("=" * 80)

    return results


if __name__ == '__main__':
    results = run_comparison_test()
