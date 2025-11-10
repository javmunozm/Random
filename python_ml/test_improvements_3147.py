#!/usr/bin/env python3
"""
Test Improvements Based on Series 3147 Analysis

Key insight: We missed 07 and 18. Number 18 should have been HOT
but somehow wasn't in our prediction. Let's test:

1. Different lookback windows (8, 12, 20 vs current 16)
2. Different boost values (15x, 20x, 30x vs current 25x)
3. Combined optimizations

Use Series 3147 as validation to see which config would have performed best.
"""

import json
from true_learning_model import TrueLearningModel


def load_data():
    """Load full historical dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def test_configuration(lookback: int, boost: float, seed: int = 999):
    """
    Test a specific configuration on Series 3147

    Note: We need to temporarily modify the model's lookback constant
    """
    data = load_data()

    # Create model
    model = TrueLearningModel(seed=seed, cold_hot_boost=boost)

    # HACK: Temporarily change the lookback window
    original_lookback = model.RECENT_SERIES_LOOKBACK
    model.RECENT_SERIES_LOOKBACK = lookback

    # Train on all data up to 3146 (before 3147)
    for sid in sorted(data.keys()):
        if sid < 3147:
            model.learn_from_series(sid, data[sid])

    # Generate prediction for 3147
    prediction = model.predict_best_combination(3147)

    # Restore original lookback
    model.RECENT_SERIES_LOOKBACK = original_lookback

    # Evaluate against actual 3147
    actual_3147 = data[3147]
    matches = []
    for event in actual_3147:
        match_count = len(set(prediction) & set(event))
        matches.append(match_count / 14)

    best_match = max(matches)
    avg_match = sum(matches) / len(matches)

    # Count cold/hot in prediction
    cold_hot_count = sum(1 for n in prediction
                         if n in model.hybrid_cold_numbers or n in model.hybrid_hot_numbers)

    # Check if we caught the critical numbers
    critical_3147 = [1, 7, 10, 15, 16, 18, 21, 22, 23, 25]  # 5+ events
    critical_caught = sum(1 for n in critical_3147 if n in prediction)

    # Check specifically for 07, 18
    has_07 = 7 in prediction
    has_18 = 18 in prediction

    return {
        "lookback": lookback,
        "boost": boost,
        "best_match": best_match,
        "avg_match": avg_match,
        "cold_hot_count": cold_hot_count,
        "cold_numbers": sorted(model.hybrid_cold_numbers),
        "hot_numbers": sorted(model.hybrid_hot_numbers),
        "prediction": prediction,
        "critical_caught": f"{critical_caught}/10",
        "has_07": has_07,
        "has_18": has_18
    }


def main():
    print("="*70)
    print("IMPROVEMENT TESTING - Based on Series 3147 Analysis")
    print("="*70)
    print()
    print("Goal: Find configuration that would have performed better on 3147")
    print("Current config (baseline): 16 lookback, 25x boost = 64.3%")
    print()

    configurations = [
        # Baseline
        (16, 25.0, "Baseline"),

        # Test different lookbacks with current 25x boost
        (8, 25.0, "8-series lookback"),
        (12, 25.0, "12-series lookback"),
        (20, 25.0, "20-series lookback"),
        (24, 25.0, "24-series lookback"),

        # Test different boosts with 8-series lookback (caught 18 in analysis)
        (8, 15.0, "8-series + 15x boost"),
        (8, 20.0, "8-series + 20x boost"),
        (8, 30.0, "8-series + 30x boost"),

        # Test different boosts with 12-series lookback
        (12, 20.0, "12-series + 20x boost"),
        (12, 30.0, "12-series + 30x boost"),
    ]

    results = []

    print(f"{'Config':<25} {'Lookback':<10} {'Boost':<10} {'Best':<10} {'07?':<6} {'18?':<6} {'Critical'}")
    print("-"*85)

    for lookback, boost, label in configurations:
        result = test_configuration(lookback, boost)
        result["label"] = label
        results.append(result)

        marker_07 = "✓" if result["has_07"] else "✗"
        marker_18 = "✓" if result["has_18"] else "✗"

        print(f"{label:<25} {lookback:<10} {boost:<10.1f}x {result['best_match']:<10.1%} "
              f"{marker_07:<6} {marker_18:<6} {result['critical_caught']}")

    print()
    print("="*70)
    print("DETAILED ANALYSIS")
    print("="*70)
    print()

    # Sort by best match
    results.sort(key=lambda x: x["best_match"], reverse=True)

    print("Top 5 Configurations for Series 3147:")
    print()

    baseline = next(r for r in results if r["label"] == "Baseline")

    for i, result in enumerate(results[:5], 1):
        diff = result["best_match"] - baseline["best_match"]
        marker = "✅" if diff > 0 else "➖"

        print(f"{i}. {result['label']}")
        print(f"   Performance: {result['best_match']:.1%} ({diff:+.1%} vs baseline) {marker}")
        print(f"   Lookback: {result['lookback']} series, Boost: {result['boost']:.1f}x")
        print(f"   Cold numbers: {result['cold_numbers']}")
        print(f"   Hot numbers: {result['hot_numbers']}")
        print(f"   Has 07: {'Yes ✓' if result['has_07'] else 'No ✗'}")
        print(f"   Has 18: {'Yes ✓' if result['has_18'] else 'No ✗'}")
        print(f"   Critical caught: {result['critical_caught']}")
        print()

    # Check which configs caught both 07 and 18
    print()
    print("="*70)
    print("Configurations that caught BOTH 07 and 18:")
    print("="*70)
    print()

    both_caught = [r for r in results if r["has_07"] and r["has_18"]]

    if both_caught:
        for result in both_caught:
            print(f"  • {result['label']}: {result['best_match']:.1%}")
            print(f"    Lookback: {result['lookback']}, Boost: {result['boost']:.1f}x")
    else:
        print("  None! Even with different configurations, we can't catch both.")
        print("  This confirms the randomness of lottery data.")

    # Recommendation
    print()
    print("="*70)
    print("RECOMMENDATION")
    print("="*70)
    print()

    best = results[0]
    improvement = best["best_match"] - baseline["best_match"]

    if improvement > 0.05:  # 5% improvement
        print(f"✅ SIGNIFICANT IMPROVEMENT FOUND")
        print(f"   Config: {best['label']}")
        print(f"   Improvement: {improvement:+.1%}")
        print(f"   Recommend adopting this configuration")
    elif improvement > 0.02:  # 2% improvement
        print(f"⚠️  MARGINAL IMPROVEMENT FOUND")
        print(f"   Config: {best['label']}")
        print(f"   Improvement: {improvement:+.1%}")
        print(f"   Consider adopting if consistent across more series")
    else:
        print(f"❌ NO MEANINGFUL IMPROVEMENT")
        print(f"   Best alternative: {best['label']} ({improvement:+.1%})")
        print(f"   Current configuration (16 lookback, 25x boost) is already optimal")
        print()
        print(f"   This single-series result (3147) was just statistical variance.")
        print(f"   The optimization study (6-series validation) is more reliable.")

    # Save results
    output_file = "improvement_test_3147_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_name": "Series 3147 Improvement Testing",
            "baseline": baseline,
            "all_results": results,
            "best": best,
            "improvement": improvement
        }, f, indent=2)

    print()
    print(f"✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
