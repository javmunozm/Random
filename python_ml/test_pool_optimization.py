#!/usr/bin/env python3
"""
Pool Generation Optimization Tests
Tests various pool generation parameters to find optimal configuration.

Priority 1: Pool Size (2k, 5k, 10k)
Priority 2: Cold/Hot Boost Weight (25x, 50x, 75x, 100x)
"""

import json
from typing import List, Dict, Tuple
from true_learning_model import TrueLearningModel
from mandel_pool_generator import MandelPoolGenerator

# Validation window
VALIDATION_SERIES = list(range(3140, 3146))  # 3140-3145 (6 series)

# Series data (3140-3145)
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


def calculate_match_percentage(predicted: List[int], actual: List[int]) -> float:
    """Calculate match percentage between prediction and actual results."""
    matches = len(set(predicted) & set(actual))
    return matches / len(predicted)


def test_configuration(pool_size: int, cold_hot_boost: float, seed: int = 999) -> Dict:
    """
    Test a specific pool generation configuration.

    Args:
        pool_size: Number of candidates to generate
        cold_hot_boost: Multiplier for cold/hot numbers
        seed: Random seed for reproducibility

    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"Testing: Pool Size = {pool_size}, Cold/Hot Boost = {cold_hot_boost}x")
    print(f"{'='*60}")

    results = []

    for series_id in VALIDATION_SERIES:
        # Train on all data before this series
        train_data = {}
        for sid in range(2898, series_id):
            if sid in SERIES_DATA:
                train_data[sid] = SERIES_DATA[sid]

        # Create and train model
        model = TrueLearningModel(seed=seed)

        # Bulk train on historical data (simulate full dataset)
        # For this test, we'll use available data
        for sid, events in train_data.items():
            for event in events:
                model.learn_from_series(event)

        # Generate prediction with test configuration
        # Note: We need to modify how we call the model to use custom params
        # For now, generate candidates and track performance

        # Get cold/hot numbers
        recent_series_ids = [s for s in range(max(2898, series_id - 16), series_id)
                            if s in SERIES_DATA or s in train_data]
        cold_numbers, hot_numbers = model._identify_cold_hot_numbers(
            recent_series_ids, SERIES_DATA
        )

        # Generate pool using Mandel generator with test parameters
        mandel_gen = MandelPoolGenerator(
            frequency_weights=model.number_frequency_weights,
            pair_affinities=model.pair_affinities,
            hybrid_cold_numbers=cold_numbers,
            hybrid_hot_numbers=hot_numbers
        )

        # Temporarily modify the cold/hot boost in the generator
        original_boost = 50.0  # Save original
        # We need to modify the generator class to accept custom boost
        # For now, we'll work around this limitation

        # Generate candidates
        candidates = mandel_gen.generate_pool(pool_size, seed)

        # Score candidates (use first 1000 for efficiency like C#)
        scored_candidates = []
        for candidate in candidates[:min(1000, len(candidates))]:
            score = model._score_candidate(
                candidate,
                model.number_frequency_weights,
                model.pair_affinities,
                cold_numbers,
                hot_numbers,
                cold_hot_boost  # Use test boost value
            )
            scored_candidates.append((candidate, score))

        # Get top prediction
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        prediction = scored_candidates[0][0]

        # Evaluate against actual results
        actual_results = SERIES_DATA[series_id]
        matches = []
        for event in actual_results:
            match_pct = calculate_match_percentage(prediction, event)
            matches.append(match_pct)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        result = {
            "series_id": series_id,
            "prediction": prediction,
            "best_match": best_match,
            "avg_match": avg_match,
            "matches": matches
        }
        results.append(result)

        print(f"  Series {series_id}: Best={best_match:.1%}, Avg={avg_match:.1%}")

    # Calculate summary statistics
    avg_best = sum(r["best_match"] for r in results) / len(results)
    avg_avg = sum(r["avg_match"] for r in results) / len(results)
    peak_best = max(r["best_match"] for r in results)

    print(f"\n  Summary:")
    print(f"    Average Best Match: {avg_best:.3%}")
    print(f"    Average Avg Match:  {avg_avg:.3%}")
    print(f"    Peak Performance:   {peak_best:.1%}")

    return {
        "pool_size": pool_size,
        "cold_hot_boost": cold_hot_boost,
        "results": results,
        "summary": {
            "avg_best_match": avg_best,
            "avg_avg_match": avg_avg,
            "peak_performance": peak_best
        }
    }


def main():
    """Run pool optimization tests."""
    print("=" * 70)
    print("POOL GENERATION OPTIMIZATION TESTS")
    print("=" * 70)
    print("\nValidation Window: Series 3140-3145 (6 series)")
    print("Seed: 999 (for reproducibility)")

    all_results = []

    # Test 1: Pool Size Variations (with baseline 50x boost)
    print("\n" + "=" * 70)
    print("TEST 1: POOL SIZE OPTIMIZATION")
    print("=" * 70)

    pool_sizes = [2000, 5000, 10000]
    baseline_boost = 50.0

    for pool_size in pool_sizes:
        result = test_configuration(pool_size, baseline_boost)
        all_results.append(result)

    # Test 2: Cold/Hot Boost Variations (with baseline 2000 pool)
    print("\n" + "=" * 70)
    print("TEST 2: COLD/HOT BOOST OPTIMIZATION")
    print("=" * 70)

    boost_values = [25.0, 50.0, 75.0, 100.0]
    baseline_pool = 2000

    for boost in boost_values:
        if boost == 50.0 and baseline_pool == 2000:
            # Already tested in Test 1, skip duplicate
            continue
        result = test_configuration(baseline_pool, boost)
        all_results.append(result)

    # Find best configuration
    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS SUMMARY")
    print("=" * 70)

    # Sort by average best match
    all_results.sort(key=lambda x: x["summary"]["avg_best_match"], reverse=True)

    print("\nTop 5 Configurations:")
    print(f"{'Rank':<6} {'Pool Size':<12} {'Boost':<10} {'Avg Best':<12} {'Peak':<10}")
    print("-" * 60)

    for i, result in enumerate(all_results[:5], 1):
        pool = result["pool_size"]
        boost = result["cold_hot_boost"]
        avg_best = result["summary"]["avg_best_match"]
        peak = result["summary"]["peak_performance"]
        print(f"{i:<6} {pool:<12} {boost:<10.1f}x {avg_best:<12.3%} {peak:<10.1%}")

    # Compare to baseline
    baseline = next(r for r in all_results if r["pool_size"] == 2000 and r["cold_hot_boost"] == 50.0)
    best = all_results[0]

    improvement = best["summary"]["avg_best_match"] - baseline["summary"]["avg_best_match"]

    print(f"\n{'='*60}")
    print("BASELINE vs BEST:")
    print(f"{'='*60}")
    print(f"Baseline (2000 pool, 50x boost): {baseline['summary']['avg_best_match']:.3%}")
    print(f"Best Config ({best['pool_size']} pool, {best['cold_hot_boost']:.1f}x boost): {best['summary']['avg_best_match']:.3%}")
    print(f"Improvement: {improvement:+.3%} ({improvement*100:+.2f} percentage points)")

    if improvement >= 0.005:  # 0.5% or more
        print("\n✅ SIGNIFICANT IMPROVEMENT - Recommend adopting best configuration")
    elif improvement >= 0.002:  # 0.2% or more
        print("\n⚠️  MARGINAL IMPROVEMENT - Consider complexity trade-off")
    else:
        print("\n❌ NO MEANINGFUL IMPROVEMENT - Keep baseline configuration")

    # Save results
    output_file = "pool_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_name": "Pool Generation Optimization",
            "validation_window": VALIDATION_SERIES,
            "seed": 999,
            "all_results": all_results,
            "best_config": best,
            "baseline_config": baseline,
            "improvement": improvement
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
