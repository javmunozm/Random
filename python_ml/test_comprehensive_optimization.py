#!/usr/bin/env python3
"""
Comprehensive Pool Optimization Test
Tests pool size AND cold/hot boost with FULL historical data (176 series)
"""

import json
from true_learning_model import TrueLearningModel

# Validation window - last 6 series
VALIDATION_SERIES = [3140, 3141, 3142, 3143, 3144, 3145]


def load_data():
    """Load full historical dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def test_configuration(pool_size: int, cold_hot_boost: float, seed: int = 999):
    """Test a specific configuration"""
    # Load all data
    SERIES_DATA = load_data()

    results = []

    for series_id in VALIDATION_SERIES:
        # Create model with test configuration
        model = TrueLearningModel(seed=seed, pool_size=pool_size, cold_hot_boost=cold_hot_boost)

        # Train on ALL data before this series
        for train_id in sorted(SERIES_DATA.keys()):
            if train_id < series_id:
                model.learn_from_series(train_id, SERIES_DATA[train_id])

        # Check cold/hot activation
        cold_hot_count = len(model.hybrid_cold_numbers) + len(model.hybrid_hot_numbers)

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Count cold/hot in prediction
        cold_hot_in_pred = sum(1 for n in prediction
                               if n in model.hybrid_cold_numbers or n in model.hybrid_hot_numbers)

        # Evaluate
        actual = SERIES_DATA[series_id]
        matches = []
        for event in actual:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        results.append({
            "series_id": series_id,
            "best_match": best_match,
            "avg_match": avg_match,
            "cold_hot_total": cold_hot_count,
            "cold_hot_in_prediction": cold_hot_in_pred
        })

    avg_best = sum(r["best_match"] for r in results) / len(results)
    peak_best = max(r["best_match"] for r in results)
    avg_cold_hot_usage = sum(r["cold_hot_in_prediction"] for r in results) / len(results)

    return {
        "pool_size": pool_size,
        "cold_hot_boost": cold_hot_boost,
        "avg_best_match": avg_best,
        "peak_performance": peak_best,
        "avg_cold_hot_usage": avg_cold_hot_usage,
        "results": results
    }


def main():
    print("="*70)
    print("COMPREHENSIVE POOL OPTIMIZATION TEST")
    print("="*70)
    print("\nUsing FULL historical data (176 series: 2898-3145)")
    print("Validation: Series 3140-3145 (6 series)")
    print("Seed: 999 (reproducible)")
    print()

    # Test configurations
    configurations = [
        # Baseline
        (10000, 50.0, "Baseline"),

        # Pool size variations (with baseline 50x boost)
        (2000, 50.0, "Pool 2k"),
        (5000, 50.0, "Pool 5k"),
        (20000, 50.0, "Pool 20k"),

        # Boost variations (with baseline 10k pool)
        (10000, 10.0, "Boost 10x"),
        (10000, 25.0, "Boost 25x"),
        (10000, 75.0, "Boost 75x"),
        (10000, 100.0, "Boost 100x"),

        # Combined optimizations
        (20000, 75.0, "20k pool + 75x boost"),
        (5000, 75.0, "5k pool + 75x boost"),
    ]

    all_results = []

    print("Running tests...")
    print(f"\n{'Config':<25} {'Pool':<10} {'Boost':<10} {'Avg Best':<12} {'Peak':<10} {'C/H Usage'}")
    print("-"*85)

    for pool_size, boost, label in configurations:
        result = test_configuration(pool_size, boost)
        result["label"] = label
        all_results.append(result)

        print(f"{label:<25} {pool_size:<10} {boost:<10.1f}x {result['avg_best_match']:<12.3%} "
              f"{result['peak_performance']:<10.1%} {result['avg_cold_hot_usage']:.1f}/14")

    # Analysis
    print(f"\n{'='*70}")
    print("ANALYSIS")
    print(f"{'='*70}")

    # Sort by performance
    all_results.sort(key=lambda x: x["avg_best_match"], reverse=True)

    print("\nTop 5 Configurations:")
    print(f"{'Rank':<6} {'Config':<25} {'Avg Best':<12} {'Improvement':<15}")
    print("-"*60)

    baseline = next(r for r in all_results if r["label"] == "Baseline")

    for i, result in enumerate(all_results[:5], 1):
        diff = result["avg_best_match"] - baseline["avg_best_match"]
        marker = "✅" if diff > 0.005 else "⚠️" if diff > 0.002 else ""
        print(f"{i:<6} {result['label']:<25} {result['avg_best_match']:<12.3%} {diff:+.3%} {' '*8}{marker}")

    # Pool size analysis
    print(f"\n{'='*70}")
    print("POOL SIZE IMPACT (with 50x boost):")
    print(f"{'='*70}")

    pool_tests = [r for r in all_results if r["cold_hot_boost"] == 50.0]
    pool_tests.sort(key=lambda x: x["pool_size"])

    for r in pool_tests:
        diff = r["avg_best_match"] - baseline["avg_best_match"]
        print(f"  {r['pool_size']:>6} pool → {r['avg_best_match']:.3%} ({diff:+.3%})")

    # Boost analysis
    print(f"\n{'='*70}")
    print("BOOST IMPACT (with 10k pool):")
    print(f"{'='*70}")

    boost_tests = [r for r in all_results if r["pool_size"] == 10000]
    boost_tests.sort(key=lambda x: x["cold_hot_boost"])

    for r in boost_tests:
        diff = r["avg_best_match"] - baseline["avg_best_match"]
        print(f"  {r['cold_hot_boost']:>6.1f}x boost → {r['avg_best_match']:.3%} ({diff:+.3%}) "
              f"[{r['avg_cold_hot_usage']:.1f}/14 C/H usage]")

    # Recommendation
    print(f"\n{'='*70}")
    print("RECOMMENDATION")
    print(f"{'='*70}")

    best = all_results[0]
    improvement = best["avg_best_match"] - baseline["avg_best_match"]

    print(f"\nBest Configuration: {best['label']}")
    print(f"  Pool Size: {best['pool_size']}")
    print(f"  Cold/Hot Boost: {best['cold_hot_boost']:.1f}x")
    print(f"  Performance: {best['avg_best_match']:.3%}")
    print(f"  Peak: {best['peak_performance']:.1%}")
    print(f"  Improvement over baseline: {improvement:+.3%}")

    if improvement > 0.01:
        print(f"\n✅ SIGNIFICANT IMPROVEMENT - Recommend adopting best configuration")
    elif improvement > 0.005:
        print(f"\n⚠️  MARGINAL IMPROVEMENT - Consider trade-offs (complexity, computation time)")
    elif best["label"] == "Baseline":
        print(f"\n✅ BASELINE IS OPTIMAL - No changes needed")
    else:
        print(f"\n❌ NO MEANINGFUL IMPROVEMENT - Keep baseline configuration")

    # Save results
    output_file = "comprehensive_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_name": "Comprehensive Pool Optimization",
            "dataset_size": 176,
            "validation_window": VALIDATION_SERIES,
            "seed": 999,
            "configurations": all_results,
            "baseline": baseline,
            "best": best,
            "improvement": improvement
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
