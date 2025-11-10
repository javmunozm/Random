#!/usr/bin/env python3
"""
Test pool size optimization: 2k vs 5k vs 10k
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


def test_pool_size(pool_size: int, seed: int = 999):
    """Test a specific pool size configuration"""
    print(f"\n{'='*60}")
    print(f"Testing Pool Size: {pool_size}")
    print(f"{'='*60}")

    results = []

    for series_id in VALIDATION_SERIES:
        # Create model with custom pool size
        model = TrueLearningModel(seed=seed, pool_size=pool_size)

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
            "best_match": best_match,
            "avg_match": avg_match
        })

        print(f"  Series {series_id}: Best={best_match:.1%}, Avg={avg_match:.1%}")

    avg_best = sum(r["best_match"] for r in results) / len(results)
    print(f"\n  Average Best Match: {avg_best:.3%}")

    return {
        "pool_size": pool_size,
        "avg_best_match": avg_best,
        "results": results
    }


def main():
    print("="*70)
    print("POOL SIZE OPTIMIZATION TEST")
    print("="*70)
    print("\nValidation: Series 3140-3145 (6 series)")
    print("Seed: 999 (reproducible)")
    print("Cold/Hot Boost: 50x (default)")

    # Test different pool sizes
    pool_sizes = [2000, 5000, 10000]
    all_results = []

    for pool_size in pool_sizes:
        result = test_pool_size(pool_size)
        all_results.append(result)

    # Summary
    print(f"\n{'='*70}")
    print("RESULTS SUMMARY")
    print(f"{'='*70}")

    # Sort by performance
    all_results.sort(key=lambda x: x["avg_best_match"], reverse=True)

    print(f"\n{'Pool Size':<12} {'Avg Best Match':<18} {'vs Baseline':<15}")
    print("-"*50)

    baseline = next(r for r in all_results if r["pool_size"] == 2000)

    for result in all_results:
        pool = result["pool_size"]
        avg = result["avg_best_match"]
        diff = avg - baseline["avg_best_match"]
        marker = "✅" if diff > 0.005 else "⚠️" if diff > 0.002 else ""

        print(f"{pool:<12} {avg:<18.3%} {diff:+.3%} {marker}")

    # Save results
    output_file = "pool_size_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_name": "Pool Size Optimization",
            "validation_window": VALIDATION_SERIES,
            "seed": 999,
            "results": all_results,
            "baseline": baseline
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
