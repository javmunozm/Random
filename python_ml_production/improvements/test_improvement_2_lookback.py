#!/usr/bin/env python3
"""
Improvement 2: Dynamic Lookback Window

Tests different lookback window sizes to find optimal configuration
Budget: 400 simulations
Expected: +1-3% improvement

Current baseline: Lookback 10 (optimized Nov 14)
Will test: 6, 8, 10, 12, 14, 16, 18, 20
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'model'))
from true_learning_model import TrueLearningModel


# Series 3144-3148 actual results
SERIES_DATA = {
    3144: [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
    ],
    3145: [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
    ],
    3147: [
        [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
        [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
        [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
        [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
        [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
        [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
        [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
    ],
    3148: [
        [1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 19, 22, 23, 25],
        [2, 3, 6, 7, 10, 12, 13, 14, 15, 16, 17, 19, 21, 23],
        [1, 2, 4, 5, 6, 8, 10, 12, 14, 15, 17, 18, 20, 22],
        [2, 3, 4, 5, 8, 10, 12, 13, 14, 15, 18, 20, 21, 25],
        [3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 19, 20, 21, 24],
        [2, 3, 4, 5, 9, 10, 12, 14, 15, 16, 17, 18, 22, 25],
        [1, 4, 6, 7, 9, 11, 12, 14, 16, 19, 20, 21, 23, 25],
    ],
}


def load_historical_data():
    """Load all historical data"""
    data_path = Path(__file__).parent.parent / 'data' / 'full_series_data_expanded.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    series_data = {int(k): v for k, v in data.items()}

    # Add recent series
    for series_id, events in SERIES_DATA.items():
        if series_id not in series_data:
            series_data[series_id] = events

    return series_data


def test_lookback_config(lookback, validation_series, historical_data, seed=999):
    """
    Test a specific lookback window configuration

    Args:
        lookback: Lookback window size
        validation_series: Series to validate on
        historical_data: All historical data
        seed: Random seed

    Returns:
        dict with results
    """
    results = []

    for target_series in validation_series:
        # Create model with specific lookback
        model = TrueLearningModel(seed=seed, cold_hot_boost=30.0)

        # Override lookback window
        model.RECENT_SERIES_LOOKBACK = lookback

        # Train on all data before target
        for sid in sorted(historical_data.keys()):
            if sid < target_series:
                model.learn_from_series(sid, historical_data[sid])

        # Generate prediction
        prediction = model.predict_best_combination(target_series)

        # Evaluate
        actual = historical_data[target_series]
        matches = []
        for event in actual:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        results.append({
            'series_id': target_series,
            'best_match': best_match,
            'avg_match': avg_match
        })

    # Calculate summary
    avg_best = sum(r['best_match'] for r in results) / len(results)
    peak = max(r['best_match'] for r in results)

    return {
        'lookback': lookback,
        'avg_best_match': avg_best,
        'peak_performance': peak,
        'results': results
    }


def main():
    print("\n")
    print("="*80)
    print("IMPROVEMENT 2: DYNAMIC LOOKBACK WINDOW OPTIMIZATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Testing different lookback window sizes")
    print("Budget: 400 simulations")
    print("Expected: +1-3% improvement")
    print()

    # Load data
    historical_data = load_historical_data()

    # Validation window: Last 10 series
    all_series = sorted(historical_data.keys())
    validation_series = all_series[-10:]  # 3139-3148

    print(f"Validation Series: {validation_series[0]}-{validation_series[-1]} ({len(validation_series)} series)")
    print()

    # Test configurations
    lookback_values = [6, 8, 10, 12, 14, 16, 18, 20]

    print(f"Testing {len(lookback_values)} lookback configurations:")
    print(f"  {lookback_values}")
    print()

    all_results = []
    baseline = None

    for i, lookback in enumerate(lookback_values, 1):
        print(f"[{i}/{len(lookback_values)}] Testing lookback={lookback:2d}...", end=" ", flush=True)

        result = test_lookback_config(lookback, validation_series, historical_data)
        all_results.append(result)

        avg = result['avg_best_match'] * 100
        peak = result['peak_performance'] * 100

        print(f"Avg {avg:5.1f}%, Peak {peak:5.1f}%")

        # Mark baseline (lookback=10)
        if lookback == 10:
            baseline = result

    print()
    print("="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print()

    # Sort by average performance
    all_results.sort(key=lambda x: x['avg_best_match'], reverse=True)

    print("Rank   Lookback   Avg Best   Peak      vs Baseline")
    print("-" * 65)

    baseline_avg = baseline['avg_best_match']
    best_config = all_results[0]

    for i, result in enumerate(all_results, 1):
        lookback = result['lookback']
        avg = result['avg_best_match'] * 100
        peak = result['peak_performance'] * 100
        diff = (result['avg_best_match'] - baseline_avg) * 100

        marker = "🏆" if i == 1 else "  "
        status = "BASELINE" if lookback == 10 else (f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%")

        print(f"{marker} {i:2d}   {lookback:8d}   {avg:7.1f}%   {peak:6.1f}%   {status}")

    print()

    # Decision
    improvement = (best_config['avg_best_match'] - baseline_avg) * 100

    print("="*80)
    print("DECISION")
    print("="*80)
    print()

    if improvement >= 0.5:  # Min 0.5% improvement
        print(f"✅ PASS: Improvement found (+{improvement:.1f}%)")
        print(f"   Best lookback: {best_config['lookback']} series")
        print(f"   Performance: {best_config['avg_best_match']*100:.1f}% avg, {best_config['peak_performance']*100:.1f}% peak")
        print(f"   vs Baseline (lookback=10): {baseline_avg*100:.1f}% avg, {baseline['peak_performance']*100:.1f}% peak")
        decision = "PASS"

        if best_config['lookback'] != 10:
            print()
            print(f"   RECOMMENDATION: Change lookback from 10 to {best_config['lookback']}")
    else:
        print(f"❌ FAIL: No significant improvement ({improvement:+.1f}%)")
        print(f"   Best alternative: Lookback {best_config['lookback']} ({best_config['avg_best_match']*100:.1f}%)")
        print(f"   Current (lookback=10): {baseline_avg*100:.1f}%")
        print(f"   Recommendation: Keep lookback=10 (already optimal)")
        decision = "FAIL"

    print()

    # Save results
    output = {
        'improvement_name': 'Dynamic Lookback Window',
        'timestamp': datetime.now().isoformat(),
        'validation_series': validation_series,
        'lookback_values_tested': lookback_values,
        'simulations_used': len(lookback_values) * len(validation_series),  # 8 lookbacks × 10 series = 80 sims
        'baseline_lookback': 10,
        'baseline_performance': baseline_avg,
        'best_lookback': best_config['lookback'],
        'best_performance': best_config['avg_best_match'],
        'improvement_pct': improvement,
        'decision': decision,
        'all_results': all_results
    }

    output_path = Path(__file__).parent.parent / 'results' / 'improvement_2_dynamic_lookback.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"📁 Results saved to: {output_path}")
    print()

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    if decision == "PASS":
        print(f"✅ Dynamic lookback optimization successful")
        print(f"   Optimal lookback: {best_config['lookback']} series")
        print(f"   Improvement: +{improvement:.1f}%")
    else:
        print(f"⚠️  Dynamic lookback showed no improvement")
        print(f"   Lookback=10 already optimal")

    print()
    print(f"Simulations used: 80/400 budgeted")
    print(f"Remaining budget: 320 simulations")
    print()
    print("NEXT: Test Improvement 3 (Event-Level Weighting)")
    print()

    return 0 if decision == "PASS" else 1


if __name__ == '__main__':
    sys.exit(main())
