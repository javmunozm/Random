#!/usr/bin/env python3
"""
Comprehensive System Test - Complete Performance Evaluation

This script:
1. Tests current baseline configuration
2. Tests all optimization candidates
3. Compares results
4. Recommends: keep current or apply improvements
"""

import json
import sys
from pathlib import Path
from datetime import datetime
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

# Series 3145 actual results
SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
]

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
    """Load full historical dataset + Series 3144, 3145, 3147, 3148"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)

    series_data = {int(k): v for k, v in data.items()}

    # Add recent series
    series_data[3144] = SERIES_3144
    series_data[3145] = SERIES_3145
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
    avg_avg = sum(r["avg_match"] for r in results) / len(results)
    peak_best = max(r["best_match"] for r in results)

    return {
        "lookback": lookback,
        "boost": boost,
        "avg_best_match": avg_best,
        "avg_avg_match": avg_avg,
        "peak_performance": peak_best,
        "results": results
    }


def main():
    print("="*80)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    data = load_data()
    validation_series = [3141, 3142, 3143, 3144, 3145, 3147, 3148]

    print(f"Dataset: {len(data)} series total")
    print(f"Validation window: {validation_series[0]}-{validation_series[-1]} ({len(validation_series)} series)")
    print()

    # STEP 1: Test current baseline
    print("="*80)
    print("STEP 1: TESTING CURRENT BASELINE")
    print("="*80)
    print()
    print("Configuration: Lookback 8, Boost 30x, Candidates 10k, Seed 999")
    print()

    baseline = test_configuration(8, 30.0, validation_series, data)

    print(f"✅ Baseline Results:")
    print(f"   Average Best Match: {baseline['avg_best_match']*100:.1f}%")
    print(f"   Average Avg Match: {baseline['avg_avg_match']*100:.1f}%")
    print(f"   Peak Performance: {baseline['peak_performance']*100:.1f}%")
    print()

    # STEP 2: Test optimization candidates
    print("="*80)
    print("STEP 2: TESTING OPTIMIZATION CANDIDATES")
    print("="*80)
    print()

    # Test a focused set of configurations around baseline
    configs_to_test = [
        # Current baseline
        (8, 30.0, "Current Baseline"),

        # Lookback variations
        (6, 30.0, "Shorter lookback (6)"),
        (10, 30.0, "Longer lookback (10)"),
        (12, 30.0, "Longer lookback (12)"),
        (16, 30.0, "Much longer lookback (16)"),

        # Boost variations with 8-series lookback
        (8, 20.0, "Lower boost (20x)"),
        (8, 25.0, "Lower boost (25x)"),
        (8, 35.0, "Higher boost (35x)"),
        (8, 40.0, "Higher boost (40x)"),
        (8, 50.0, "Much higher boost (50x)"),

        # Combination optimizations
        (6, 35.0, "Shorter lookback + higher boost"),
        (10, 25.0, "Longer lookback + lower boost"),
        (12, 25.0, "Much longer lookback + lower boost"),
        (16, 25.0, "Original optimized config"),
    ]

    all_results = [baseline]  # Include baseline

    for i, (lookback, boost, label) in enumerate(configs_to_test[1:], 1):  # Skip baseline (already tested)
        print(f"[{i}/{len(configs_to_test)-1}] Testing: {label}...", end=" ", flush=True)

        result = test_configuration(lookback, boost, validation_series, data)
        result["label"] = label
        all_results.append(result)

        avg = result["avg_best_match"] * 100
        peak = result["peak_performance"] * 100
        print(f"Avg {avg:.1f}%, Peak {peak:.1f}%")

    baseline["label"] = "Current Baseline"

    print()

    # STEP 3: Compare results
    print("="*80)
    print("STEP 3: RESULTS COMPARISON")
    print("="*80)
    print()

    # Sort by avg_best_match (primary) and peak (secondary)
    all_results.sort(key=lambda x: (x["avg_best_match"], x["peak_performance"]), reverse=True)

    print("Rank   Configuration                       Avg Best   Peak      vs Baseline")
    print("-" * 85)

    best_config = all_results[0]
    baseline_avg = baseline["avg_best_match"]

    for i, result in enumerate(all_results, 1):
        label = result.get("label", f"L{result['lookback']} B{result['boost']}x")
        avg = result["avg_best_match"] * 100
        peak = result["peak_performance"] * 100
        diff = (result["avg_best_match"] - baseline_avg) * 100

        marker = "🏆" if i == 1 else "  "
        status = "BASELINE" if result is baseline else (f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%")

        print(f"{marker} {i:2d}   {label:35s}   {avg:5.1f}%   {peak:5.1f}%   {status}")

    print()

    # STEP 4: Decision
    print("="*80)
    print("STEP 4: DECISION")
    print("="*80)
    print()

    improvement = best_config["avg_best_match"] - baseline["avg_best_match"]
    improvement_pct = improvement * 100

    if best_config is baseline:
        print("✅ RECOMMENDATION: KEEP CURRENT CONFIGURATION")
        print()
        print("   Current baseline is already optimal.")
        print(f"   Performance: {baseline['avg_best_match']*100:.1f}% avg, {baseline['peak_performance']*100:.1f}% peak")
        decision = "KEEP"
    elif improvement_pct >= 1.0:
        print("✅ RECOMMENDATION: APPLY IMPROVEMENT")
        print()
        print(f"   Best configuration: {best_config.get('label', 'Unknown')}")
        print(f"   Lookback: {best_config['lookback']} series")
        print(f"   Boost: {best_config['boost']}x")
        print(f"   Performance: {best_config['avg_best_match']*100:.1f}% avg, {best_config['peak_performance']*100:.1f}% peak")
        print(f"   Improvement: +{improvement_pct:.1f}% (significant)")
        decision = "IMPROVE"
    else:
        print("⚠️  RECOMMENDATION: KEEP CURRENT CONFIGURATION")
        print()
        print(f"   Best alternative: {best_config.get('label', 'Unknown')}")
        print(f"   Performance: {best_config['avg_best_match']*100:.1f}% avg, {best_config['peak_performance']*100:.1f}% peak")
        print(f"   Improvement: +{improvement_pct:.1f}% (too small, not significant)")
        print()
        print("   Current baseline is good enough.")
        decision = "KEEP"

    print()

    # Save results
    output = {
        "test_name": "Comprehensive System Test",
        "timestamp": datetime.now().isoformat(),
        "validation_series": validation_series,
        "baseline_config": {
            "lookback": baseline["lookback"],
            "boost": baseline["boost"],
            "avg_best_match": baseline["avg_best_match"],
            "peak_performance": baseline["peak_performance"]
        },
        "best_config": {
            "lookback": best_config["lookback"],
            "boost": best_config["boost"],
            "label": best_config.get("label", "Unknown"),
            "avg_best_match": best_config["avg_best_match"],
            "peak_performance": best_config["peak_performance"]
        },
        "improvement": improvement,
        "improvement_pct": improvement_pct,
        "decision": decision,
        "all_results": all_results
    }

    output_path = Path(__file__).parent / "comprehensive_system_test_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📁 Full results saved to: {output_path}")
    print()

    # Return decision code
    return 0 if decision == "KEEP" else 1


if __name__ == "__main__":
    sys.exit(main())
