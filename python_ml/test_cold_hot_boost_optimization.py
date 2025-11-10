#!/usr/bin/env python3
"""
Test cold/hot boost optimization: 25x, 50x, 75x, 100x
Uses walk-forward validation on Series 3140-3145
"""

import json
from true_learning_model import TrueLearningModel

# Validation window
VALIDATION_SERIES = list(range(3140, 3146))  # 3140-3145 (6 series)

# Series data
SERIES_DATA = {
    3140: [
        [1, 2, 3, 6, 7, 8, 11, 12, 13, 16, 18, 21, 22, 25],
        [1, 2, 4, 7, 8, 11, 12, 13, 14, 15, 18, 23, 24, 25],
        [1, 2, 3, 5, 6, 7, 8, 10, 14, 15, 16, 17, 21, 24],
        [1, 2, 3, 6, 7, 10, 11, 12, 15, 18, 19, 21, 24, 25],
        [1, 3, 4, 5, 12, 13, 14, 15, 16, 19, 20, 21, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 14, 17, 18, 21, 22, 23],
        [2, 4, 7, 9, 10, 11, 14, 15, 17, 18, 19, 22, 23, 25]
    ],
    3141: [
        [1, 2, 3, 4, 5, 6, 8, 11, 13, 14, 15, 18, 21, 24],
        [1, 2, 3, 4, 5, 6, 9, 11, 13, 16, 17, 19, 20, 24],
        [2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 16, 20, 24],
        [1, 2, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 19, 24],
        [1, 2, 3, 5, 7, 9, 10, 11, 12, 13, 15, 16, 19, 21],
        [1, 2, 5, 6, 9, 10, 11, 13, 15, 16, 17, 19, 22, 24],
        [1, 2, 4, 5, 7, 8, 9, 11, 13, 15, 16, 17, 20, 24]
    ],
    3142: [
        [2, 3, 5, 6, 7, 9, 11, 12, 13, 14, 18, 21, 22, 23],
        [1, 2, 3, 5, 6, 7, 8, 9, 11, 13, 18, 20, 22, 23],
        [1, 2, 5, 6, 7, 8, 9, 10, 13, 16, 17, 21, 23, 24],
        [1, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 18, 22, 24],
        [1, 3, 4, 5, 6, 7, 9, 10, 12, 13, 17, 18, 19, 23],
        [1, 2, 3, 4, 5, 7, 11, 14, 16, 17, 18, 19, 21, 22],
        [2, 3, 4, 5, 7, 8, 9, 12, 14, 16, 17, 19, 21, 24]
    ],
    3143: [
        [1, 2, 3, 6, 7, 8, 9, 11, 12, 13, 14, 17, 23, 24],
        [1, 2, 3, 6, 7, 8, 9, 11, 12, 13, 14, 19, 22, 24],
        [1, 2, 3, 5, 6, 7, 9, 11, 13, 14, 16, 17, 19, 22],
        [1, 2, 5, 6, 7, 9, 12, 13, 14, 17, 19, 22, 23, 24],
        [1, 2, 3, 6, 7, 8, 9, 11, 13, 14, 16, 18, 19, 23],
        [2, 3, 4, 5, 6, 7, 9, 12, 13, 14, 16, 19, 22, 24],
        [1, 2, 3, 5, 6, 7, 9, 12, 13, 14, 16, 19, 22, 23]
    ],
    3144: [
        [1, 3, 4, 5, 7, 8, 9, 11, 13, 15, 17, 18, 19, 23],
        [1, 3, 4, 5, 7, 9, 11, 12, 14, 15, 17, 18, 19, 23],
        [1, 3, 4, 5, 7, 9, 10, 12, 14, 15, 18, 19, 21, 23],
        [1, 4, 5, 6, 7, 9, 10, 14, 15, 17, 18, 20, 21, 23],
        [1, 3, 4, 6, 7, 8, 9, 10, 12, 14, 15, 17, 18, 20],
        [2, 4, 5, 6, 7, 8, 9, 10, 12, 13, 16, 18, 20, 21],
        [1, 4, 5, 6, 7, 9, 10, 12, 14, 15, 17, 18, 20, 21]
    ],
    3145: [
        [1, 2, 3, 5, 6, 7, 8, 11, 14, 15, 17, 20, 21, 24],
        [1, 2, 3, 4, 5, 6, 10, 11, 13, 14, 16, 19, 22, 23],
        [1, 2, 3, 6, 7, 9, 10, 11, 12, 15, 17, 21, 22, 23],
        [1, 3, 4, 5, 7, 9, 10, 11, 13, 14, 16, 18, 19, 20],
        [1, 3, 5, 6, 7, 8, 9, 13, 15, 17, 19, 20, 21, 23],
        [1, 2, 3, 5, 6, 7, 9, 11, 13, 14, 16, 19, 22, 23],
        [1, 2, 3, 5, 6, 7, 9, 11, 13, 14, 16, 17, 22, 23]
    ]
}


def test_boost_value(boost: float, seed: int = 999):
    """Test a specific cold/hot boost value"""
    print(f"\n{'='*60}")
    print(f"Testing Cold/Hot Boost: {boost}x")
    print(f"{'='*60}")

    results = []

    for series_id in VALIDATION_SERIES:
        # Create model with custom boost
        model = TrueLearningModel(seed=seed, cold_hot_boost=boost)

        # Train on all previous series
        for train_id in range(2898, series_id):
            if train_id in SERIES_DATA:
                model.learn_from_series(train_id, SERIES_DATA[train_id])

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

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
            "prediction": prediction,
            "best_match": best_match,
            "avg_match": avg_match
        })

        print(f"  Series {series_id}: Best={best_match:.1%}, Avg={avg_match:.1%}")

    avg_best = sum(r["best_match"] for r in results) / len(results)
    peak_best = max(r["best_match"] for r in results)

    print(f"\n  Average Best Match: {avg_best:.3%}")
    print(f"  Peak Performance:   {peak_best:.1%}")

    return {
        "cold_hot_boost": boost,
        "avg_best_match": avg_best,
        "peak_performance": peak_best,
        "results": results
    }


def main():
    print("="*70)
    print("COLD/HOT BOOST OPTIMIZATION TEST")
    print("="*70)
    print("\nValidation: Series 3140-3145 (6 series)")
    print("Seed: 999 (reproducible)")
    print("Pool Size: 10000 (default)")

    # Test different boost values
    boost_values = [25.0, 50.0, 75.0, 100.0, 150.0]
    all_results = []

    for boost in boost_values:
        result = test_boost_value(boost)
        all_results.append(result)

    # Summary
    print(f"\n{'='*70}")
    print("RESULTS SUMMARY")
    print(f"{'='*70}")

    # Sort by performance
    all_results.sort(key=lambda x: x["avg_best_match"], reverse=True)

    print(f"\n{'Boost':<10} {'Avg Best':<12} {'Peak':<10} {'vs 50x':<15} {'Status':<10}")
    print("-"*65)

    baseline = next(r for r in all_results if r["cold_hot_boost"] == 50.0)

    for result in all_results:
        boost = result["cold_hot_boost"]
        avg = result["avg_best_match"]
        peak = result["peak_performance"]
        diff = avg - baseline["avg_best_match"]

        if diff > 0.01:  # >1% improvement
            status = "✅ BETTER"
        elif diff > 0.005:  # >0.5% improvement
            status = "⚠️ MARGINAL"
        elif diff < -0.005:  # >0.5% worse
            status = "❌ WORSE"
        else:
            status = "➖ SAME"

        print(f"{boost:<10.1f}x {avg:<12.3%} {peak:<10.1%} {diff:+.3%} {' '*7} {status}")

    # Recommendation
    print(f"\n{'='*70}")
    print("RECOMMENDATION")
    print(f"{'='*70}")

    best = all_results[0]
    improvement = best["avg_best_match"] - baseline["avg_best_match"]

    if best["cold_hot_boost"] == 50.0:
        print(f"\n✅ KEEP baseline 50x boost - already optimal")
        print(f"   Current performance: {baseline['avg_best_match']:.3%}")
    elif improvement > 0.01:
        print(f"\n✅ ADOPT {best['cold_hot_boost']:.1f}x boost - significant improvement!")
        print(f"   Improvement: {improvement:+.3%} ({improvement*100:+.2f} percentage points)")
        print(f"   New performance: {best['avg_best_match']:.3%} (was {baseline['avg_best_match']:.3%})")
    elif improvement > 0.005:
        print(f"\n⚠️  CONSIDER {best['cold_hot_boost']:.1f}x boost - marginal improvement")
        print(f"   Improvement: {improvement:+.3%}")
    else:
        print(f"\n❌ KEEP baseline 50x boost - no better alternative found")

    # Save results
    output_file = "cold_hot_boost_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_name": "Cold/Hot Boost Optimization",
            "validation_window": VALIDATION_SERIES,
            "seed": 999,
            "results": all_results,
            "baseline": baseline,
            "best": best,
            "improvement": improvement
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
