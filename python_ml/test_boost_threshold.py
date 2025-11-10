#!/usr/bin/env python3
"""
Test cold/hot boost threshold: Find minimum effective boost
Tests: 1x (no boost), 2x, 5x, 10x, 15x, 25x, 50x
"""

import json
from true_learning_model import TrueLearningModel

# Validation window - just use 3 series for faster testing
VALIDATION_SERIES = [3143, 3144, 3145]

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
    results = []

    for series_id in VALIDATION_SERIES:
        # Create model with custom boost
        model = TrueLearningModel(seed=seed, cold_hot_boost=boost)

        # Train on all previous series
        for train_id in range(3140, series_id):
            if train_id in SERIES_DATA:
                model.learn_from_series(train_id, SERIES_DATA[train_id])

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Count how many cold/hot numbers in prediction
        cold_hot_count = sum(1 for n in prediction if n in model.hybrid_cold_numbers or n in model.hybrid_hot_numbers)

        # Evaluate
        actual = SERIES_DATA[series_id]
        matches = []
        for event in actual:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)

        results.append({
            "series_id": series_id,
            "best_match": best_match,
            "cold_hot_in_prediction": cold_hot_count,
            "total_cold_hot": len(model.hybrid_cold_numbers) + len(model.hybrid_hot_numbers)
        })

    avg_best = sum(r["best_match"] for r in results) / len(results)
    avg_cold_hot = sum(r["cold_hot_in_prediction"] for r in results) / len(results)

    return {
        "cold_hot_boost": boost,
        "avg_best_match": avg_best,
        "avg_cold_hot_in_prediction": avg_cold_hot,
        "results": results
    }


def main():
    print("="*70)
    print("COLD/HOT BOOST THRESHOLD TEST")
    print("="*70)
    print("\nObjective: Find minimum effective boost value")
    print("Validation: Series 3143-3145 (3 series for speed)")
    print("Seed: 999")

    # Test boost values from low to high
    boost_values = [1.0, 2.0, 5.0, 10.0, 15.0, 25.0, 50.0, 100.0]
    all_results = []

    print(f"\n{'Boost':<10} {'Avg Best':<12} {'Cold/Hot Usage':<18}")
    print("-"*45)

    for boost in boost_values:
        result = test_boost_value(boost)
        all_results.append(result)

        print(f"{boost:<10.1f}x {result['avg_best_match']:<12.3%} {result['avg_cold_hot_in_prediction']:<18.1f}/14")

    # Find threshold
    print(f"\n{'='*70}")
    print("ANALYSIS")
    print(f"{'='*70}")

    # Sort by performance
    all_results.sort(key=lambda x: x["avg_best_match"], reverse=True)
    best = all_results[0]

    print(f"\nBest Performance: {best['cold_hot_boost']:.1f}x boost → {best['avg_best_match']:.3%}")

    # Find point of diminishing returns
    sorted_by_boost = sorted(all_results, key=lambda x: x["cold_hot_boost"])

    print(f"\nPerformance vs Boost:")
    prev_perf = 0
    for r in sorted_by_boost:
        diff = r["avg_best_match"] - prev_perf
        marker = "📈" if diff > 0.01 else "➖" if abs(diff) < 0.001 else ""
        print(f"  {r['cold_hot_boost']:>6.1f}x → {r['avg_best_match']:.3%} ({diff:+.3%}) {marker}")
        prev_perf = r["avg_best_match"]

    # Recommendation
    print(f"\n{'='*70}")
    print("RECOMMENDATION")
    print(f"{'='*70}")

    # Find lowest boost with best performance
    best_perf = best["avg_best_match"]
    candidates = [r for r in all_results if abs(r["avg_best_match"] - best_perf) < 0.001]
    min_boost = min(c["cold_hot_boost"] for c in candidates)

    print(f"\n✅ Optimal boost: {min_boost:.1f}x")
    print(f"   Performance: {best_perf:.3%}")
    print(f"   Reasoning: Minimum boost achieving peak performance")

    if min_boost < 50.0:
        print(f"\n💡 Current 50x boost is OVERKILL - can reduce to {min_boost:.1f}x")
    elif min_boost == 50.0:
        print(f"\n✅ Current 50x boost is OPTIMAL")
    else:
        print(f"\n⚠️  Current 50x boost is TOO LOW - increase to {min_boost:.1f}x")

    # Save results
    output_file = "boost_threshold_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_name": "Cold/Hot Boost Threshold",
            "validation_window": VALIDATION_SERIES,
            "results": all_results,
            "optimal_boost": min_boost,
            "optimal_performance": best_perf
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
