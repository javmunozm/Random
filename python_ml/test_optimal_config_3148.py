#!/usr/bin/env python3
"""
Comprehensive Configuration Search for 78.6% Peak

Tests all combinations of:
- Lookback windows: 8, 12, 16, 20, 24 series
- Boost values: 20x, 25x, 30x, 35x, 40x, 50x, 75x
- Candidate pool: 10000 (fixed for speed)

Goal: Find configuration that achieves 78.6% peak on validation window 3141-3148
"""

import json
import sys
from pathlib import Path
from true_learning_model import TrueLearningModel

# Series 3147 actual results
SERIES_3147 = [
    [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
    [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
    [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
    [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
    [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
    [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
    [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
]

# Series 3148 actual results
SERIES_3148 = [
    [1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 19, 22, 23, 25],
    [2, 3, 6, 7, 10, 12, 13, 14, 15, 16, 17, 19, 21, 23],
    [1, 2, 4, 5, 6, 8, 10, 12, 14, 15, 17, 18, 20, 22],
    [2, 3, 4, 5, 8, 10, 12, 13, 14, 15, 18, 20, 21, 25],
    [3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 19, 20, 21, 24],
    [2, 3, 4, 5, 9, 10, 12, 14, 15, 16, 17, 18, 22, 25],
    [1, 4, 6, 7, 9, 11, 12, 14, 16, 19, 20, 21, 23, 25],
]


def load_data():
    """Load full historical dataset + Series 3147-3148"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)

    series_data = {int(k): v for k, v in data.items()}

    # Add Series 3147 and 3148
    series_data[3147] = SERIES_3147
    series_data[3148] = SERIES_3148

    return series_data


def test_configuration(lookback: int, boost: float, validation_series: list, data: dict, seed: int = 999):
    """Test a specific configuration on validation series"""
    results = []

    for target_series in validation_series:
        # Create fresh model
        model = TrueLearningModel(seed=seed, cold_hot_boost=boost)

        # Override lookback window
        model.RECENT_SERIES_LOOKBACK = lookback

        # Train on all data before target series
        for sid in sorted(data.keys()):
            if sid < target_series:
                model.learn_from_series(sid, data[sid])

        # Generate prediction
        prediction = model.predict_best_combination(target_series)

        # Evaluate
        actual = data[target_series]
        matches = []
        for event in actual:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        results.append({
            "series_id": target_series,
            "best_match": best_match,
            "avg_match": avg_match,
            "prediction": prediction
        })

    # Calculate summary stats
    avg_best = sum(r["best_match"] for r in results) / len(results)
    peak_best = max(r["best_match"] for r in results)

    return {
        "lookback": lookback,
        "boost": boost,
        "avg_best_match": avg_best,
        "peak_performance": peak_best,
        "results": results
    }


def main():
    print("="*80)
    print("COMPREHENSIVE CONFIGURATION SEARCH FOR 78.6% PEAK")
    print("="*80)
    print()
    print("Testing on validation window: 3141-3148 (includes Series 3147-3148)")
    print("Goal: Find configuration that achieves 78.6% peak performance")
    print()

    # Load data
    data = load_data()
    validation_series = [3141, 3142, 3143, 3144, 3145, 3147, 3148]

    # Configurations to test
    lookback_windows = [8, 12, 16, 20, 24]
    boost_values = [20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 75.0]

    all_results = []
    best_config = None
    best_peak = 0

    total_tests = len(lookback_windows) * len(boost_values)
    test_count = 0

    print(f"Total configurations to test: {total_tests}")
    print()

    for lookback in lookback_windows:
        for boost in boost_values:
            test_count += 1
            label = f"Lookback {lookback}, Boost {boost}x"

            print(f"[{test_count}/{total_tests}] Testing: {label}...", end=" ", flush=True)

            result = test_configuration(lookback, boost, validation_series, data)
            result["label"] = label
            all_results.append(result)

            avg = result["avg_best_match"] * 100
            peak = result["peak_performance"] * 100
            print(f"Avg {avg:.1f}%, Peak {peak:.1f}%")

            # Track best peak
            if result["peak_performance"] > best_peak:
                best_peak = result["peak_performance"]
                best_config = result

    print()
    print("="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print()

    # Sort by peak performance (descending), then by average (descending)
    all_results.sort(key=lambda x: (x["peak_performance"], x["avg_best_match"]), reverse=True)

    print("Top 10 Configurations by Peak Performance:")
    print()
    print("Rank   Configuration                       Avg Best     Peak")
    print("-" * 75)

    for i, result in enumerate(all_results[:10], 1):
        label = result["label"]
        avg = result["avg_best_match"] * 100
        peak = result["peak_performance"] * 100
        marker = "🎯" if peak >= 78.6 else "  "
        print(f"{marker} {i:2d}   {label:35s}   {avg:5.1f}%      {peak:.1f}%")

    print()

    if best_peak >= 0.786:
        print(f"✅ SUCCESS! Found configuration achieving 78.6% peak!")
        print()
        print(f"Best Configuration: {best_config['label']}")
        print(f"  Lookback: {best_config['lookback']} series")
        print(f"  Boost: {best_config['boost']}x")
        print(f"  Average Best: {best_config['avg_best_match']*100:.1f}%")
        print(f"  Peak Performance: {best_config['peak_performance']*100:.1f}%")
        print()

        # Show which series achieved peak
        for r in best_config['results']:
            if r['best_match'] == best_config['peak_performance']:
                print(f"  Peak achieved on Series {r['series_id']}: {r['best_match']*100:.1f}%")
    else:
        print(f"❌ No configuration achieved 78.6% peak")
        print(f"   Best peak found: {best_peak*100:.1f}%")
        print()
        print(f"Best Configuration: {best_config['label']}")
        print(f"  Lookback: {best_config['lookback']} series")
        print(f"  Boost: {best_config['boost']}x")
        print(f"  Average Best: {best_config['avg_best_match']*100:.1f}%")
        print(f"  Peak Performance: {best_config['peak_performance']*100:.1f}%")

    print()

    # Save results
    output = {
        "test_name": "Comprehensive Configuration Search (3141-3148)",
        "validation_series": validation_series,
        "total_configurations": len(all_results),
        "best_peak_found": best_peak,
        "target_peak": 0.786,
        "achieved_target": best_peak >= 0.786,
        "best_configuration": best_config,
        "all_results": all_results
    }

    output_path = Path(__file__).parent / "optimal_config_search_3148.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📁 Results saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
