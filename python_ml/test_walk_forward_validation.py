#!/usr/bin/env python3
"""
Phase 2 Test 6: Walk-Forward Validation (CRITICAL)

NOT an improvement test - this validates performance consistency!

Hypothesis: 73.2% might be specific to recent validation window (3137-3144)
- Test on ALL possible 8-series windows, not just the most recent
- Walk forward through time: test window 1, then 2, then 3, etc.
- Reveals if performance is consistent or if we got lucky with recent window

Purpose: Validate that 73.2% is robust across different time periods
Baseline: 73.214% (seed 999 on window 3137-3144)
Question: Is 73.2% consistent across ALL 8-series windows?
"""

import json
import random
from pathlib import Path
from typing import List, Dict
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


def test_single_window(all_series_data, window_start, window_size=8):
    """Test performance on a single 8-series validation window"""
    random.seed(999)  # Same seed for all windows

    window_end = window_start + window_size - 1
    training_end = window_start - 1

    # Initialize model
    model = TrueLearningModel()

    # Bulk training (all series before window)
    for series in all_series_data:
        if series['series_id'] < window_start:
            model.learn_from_series(series['series_id'], series['events'])

    # Iterative validation on this window
    accuracies = []
    series_details = []

    for series_data in all_series_data:
        if window_start <= series_data['series_id'] <= window_end:
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

            # Learn
            model.validate_and_learn(series_id, prediction, actual_results)

    if not accuracies:
        return None

    avg_accuracy = sum(accuracies) / len(accuracies)
    peak_accuracy = max(accuracies)
    min_accuracy = min(accuracies)

    return {
        'window_start': window_start,
        'window_end': window_end,
        'training_end': training_end,
        'training_series_count': training_end - 2898 + 1,
        'average': avg_accuracy,
        'peak': peak_accuracy,
        'min': min_accuracy,
        'series_details': series_details
    }


def run_walk_forward_validation(all_series_data, window_size=8, step_size=8):
    """
    Run walk-forward validation across all possible windows

    Args:
        window_size: Size of validation window (default: 8)
        step_size: How many series to step forward (default: 8, no overlap)
    """

    # Find range of available series
    min_series = min(s['series_id'] for s in all_series_data)
    max_series = max(s['series_id'] for s in all_series_data)

    # Calculate all possible windows
    # Need at least some training data, so start reasonably late
    min_window_start = min_series + 50  # At least 50 series for training

    windows = []
    current_start = min_window_start

    while current_start + window_size - 1 <= max_series:
        windows.append(current_start)
        current_start += step_size

    print(f"📊 Walk-Forward Validation Setup:")
    print(f"   Total series available: {max_series - min_series + 1} ({min_series}-{max_series})")
    print(f"   Window size: {window_size} series")
    print(f"   Step size: {step_size} series")
    print(f"   Total windows to test: {len(windows)}")
    print(f"   Window range: {windows[0]}-{windows[0]+window_size-1} to {windows[-1]}-{windows[-1]+window_size-1}")
    print()

    # Test each window
    results = []
    for i, window_start in enumerate(windows, 1):
        print(f"Testing window {i}/{len(windows)}: Series {window_start}-{window_start+window_size-1}...")
        result = test_single_window(all_series_data, window_start, window_size)
        if result:
            results.append(result)
            print(f"  Average: {result['average']:.1%}, Peak: {result['peak']:.1%}")

    return results


def main():
    print("=" * 80)
    print("PHASE 2 TEST 6: WALK-FORWARD VALIDATION (CRITICAL)")
    print("=" * 80)
    print()
    print("⚠️  NOT AN IMPROVEMENT TEST - THIS IS VALIDATION!")
    print()
    print("Purpose: Validate that 73.2% is consistent across time, not just lucky")
    print("  - Test on ALL possible 8-series windows")
    print("  - Walk forward through entire dataset")
    print("  - Check if performance is consistent or varies by time period")
    print()
    print("Baseline: 73.214% (seed 999 on window 3137-3144)")
    print("Question: Is 73.2% typical or exceptional?")
    print()

    # Load data
    print("Loading data...")
    all_series_data = load_all_data()
    if not all_series_data:
        print("❌ Failed to load data")
        return
    print(f"✅ Loaded {len(all_series_data)} series")
    print()

    # Run walk-forward validation
    results = run_walk_forward_validation(all_series_data, window_size=8, step_size=8)

    print()
    print("=" * 80)
    print("WALK-FORWARD VALIDATION RESULTS")
    print("=" * 80)
    print()

    if not results:
        print("❌ No results generated")
        return

    # Summary statistics
    all_averages = [r['average'] for r in results]
    all_peaks = [r['peak'] for r in results]

    mean_avg = sum(all_averages) / len(all_averages)
    min_avg = min(all_averages)
    max_avg = max(all_averages)

    import statistics
    stdev_avg = statistics.stdev(all_averages) if len(all_averages) > 1 else 0

    print(f"Performance Across {len(results)} Windows:")
    print(f"  Average Performance: {mean_avg:.3%} ± {stdev_avg:.3%}")
    print(f"  Best Window:         {max_avg:.3%}")
    print(f"  Worst Window:        {min_avg:.3%}")
    print(f"  Range:               {max_avg - min_avg:.3%}")
    print()

    # Find best and worst windows
    best_window = max(results, key=lambda r: r['average'])
    worst_window = min(results, key=lambda r: r['average'])

    print(f"Best Window:  Series {best_window['window_start']}-{best_window['window_end']} → {best_window['average']:.1%}")
    print(f"Worst Window: Series {worst_window['window_start']}-{worst_window['window_end']} → {worst_window['average']:.1%}")
    print()

    # Check if recent window (3137-3144) is special
    recent_window = next((r for r in results if r['window_start'] == 3137), None)
    if recent_window:
        print(f"Recent Window (3137-3144): {recent_window['average']:.3%}")
        print(f"  vs Average of all windows: {mean_avg:.3%}")
        diff = recent_window['average'] - mean_avg
        print(f"  Difference: {diff:+.3%} ({'above' if diff > 0 else 'below'} average)")
        print()

        if diff > stdev_avg:
            print("  ⚠️  Recent window performs ABOVE AVERAGE (lucky period!)")
        elif diff < -stdev_avg:
            print("  ⚠️  Recent window performs BELOW AVERAGE (unlucky period)")
        else:
            print("  ✅ Recent window is TYPICAL (representative performance)")
    print()

    # Detailed window breakdown
    print("=" * 80)
    print("DETAILED BREAKDOWN BY WINDOW")
    print("=" * 80)
    print()
    print("Window Range          | Training | Average | Peak   | Status")
    print("----------------------|----------|---------|--------|--------")
    for r in results:
        status = ""
        if r['average'] == max_avg:
            status = "⭐ BEST"
        elif r['average'] == min_avg:
            status = "❌ WORST"
        elif r['window_start'] == 3137:
            status = "📍 RECENT"

        print(f"{r['window_start']:4d}-{r['window_end']:4d} ({r['window_end']-r['window_start']+1} series) | {r['training_series_count']:4d}     | {r['average']:6.1%}  | {r['peak']:6.1%} | {status}")
    print()

    # Save results
    output = {
        'test_name': 'walk_forward_validation',
        'purpose': 'Validate performance consistency across time periods',
        'baseline_window': '3137-3144',
        'baseline_performance': 0.73214,
        'num_windows_tested': len(results),
        'summary': {
            'mean_average': mean_avg,
            'stdev_average': stdev_avg,
            'best_average': max_avg,
            'worst_average': min_avg,
            'range': max_avg - min_avg
        },
        'best_window': {
            'start': best_window['window_start'],
            'end': best_window['window_end'],
            'average': best_window['average']
        },
        'worst_window': {
            'start': worst_window['window_start'],
            'end': worst_window['window_end'],
            'average': worst_window['average']
        },
        'recent_window_analysis': {
            'performance': recent_window['average'] if recent_window else None,
            'vs_mean': recent_window['average'] - mean_avg if recent_window else None,
            'is_typical': abs(recent_window['average'] - mean_avg) <= stdev_avg if recent_window else None
        } if recent_window else None,
        'all_windows': results
    }

    output_file = Path(__file__).parent / 'test_walk_forward_validation_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print()
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()

    if recent_window:
        if abs(recent_window['average'] - mean_avg) <= stdev_avg:
            print("✅ VALIDATION PASSED: Recent window (73.2%) is TYPICAL performance")
            print("   → Seed 999 consistently delivers 73% across different time periods")
            print("   → Our baseline is robust and representative")
        else:
            if recent_window['average'] > mean_avg + stdev_avg:
                print("⚠️  WARNING: Recent window (73.2%) is ABOVE AVERAGE")
                print(f"   → Typical performance is closer to {mean_avg:.1%}")
                print("   → We may have been lucky with recent validation window")
            else:
                print("⚠️  WARNING: Recent window (73.2%) is BELOW AVERAGE")
                print(f"   → Typical performance is closer to {mean_avg:.1%}")
                print("   → Recent window is an unlucky period")
    print()


if __name__ == "__main__":
    main()
