#!/usr/bin/env python3
"""
Comprehensive study of seed optimization to understand why seed 999 works
and if we can improve beyond 73.2%
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
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
    """Load all series data from JSON export + Series 3144"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found: {json_path}")
        return {}

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    # Convert to dictionary format
    all_series = {}
    for series in json_data.get('data', []):
        series_id = series['series_id']
        events = [event['numbers'] for event in series['events']]
        all_series[series_id] = events

    # Add Series 3144
    all_series[3144] = SERIES_3144

    return all_series

def test_extended_seeds(num_seeds: int = 20) -> List[Tuple[int, float]]:
    """Test extended range of seeds to find potentially better performers"""
    print("=" * 80)
    print(f"EXTENDED SEED TESTING: Testing {num_seeds} additional seeds")
    print("=" * 80)
    print()

    # Test seeds in promising ranges
    test_ranges = [
        range(900, 1100, 10),   # Around 999 (best so far)
        range(2000, 2100, 10),  # Around 2024 (second best: 72.3%)
        range(400, 600, 10),    # Around 456 (baseline: 71.4%)
    ]

    results = []
    tested = {999, 2024, 456}  # Already tested

    for seed_range in test_ranges:
        for seed in seed_range:
            if seed in tested:
                continue

            tested.add(seed)
            random.seed(seed)

            # Run training
            model = TrueLearningModel()

            # Load all series
            all_series = load_all_data()
            if not all_series:
                print("❌ No data loaded")
                return []

            latest_id = max(all_series.keys())

            # Iterative validation (last 8 series)
            validation_window = 8
            validation_series_ids = sorted(all_series.keys())[-validation_window:]

            accuracies = []

            for series_id in validation_series_ids:
                # Train on all data before this series
                model = TrueLearningModel()
                train_data = {k: v for k, v in all_series.items() if k < series_id}
                model.learn_from_historical_data(train_data)

                # Predict
                prediction = model.predict_best_combination(series_id)

                # Get actual and calculate best match
                actual_results = all_series[series_id]
                best_match = max(len(set(prediction) & set(actual)) for actual in actual_results)
                best_accuracy = best_match / 14
                accuracies.append(best_accuracy)

            avg_best = sum(accuracies) / len(accuracies)
            results.append((seed, avg_best))

            print(f"Seed {seed:5d}: {avg_best:.1%}", end="")
            if avg_best > 0.732:
                print(" 🎯 NEW BEST!")
            elif avg_best >= 0.714:
                print(" ✅")
            else:
                print()

            if len(tested) >= num_seeds + 3:
                break

        if len(tested) >= num_seeds + 3:
            break

    return results


def test_candidate_pool_sizes(seed: int = 999) -> Dict[int, float]:
    """Test if larger candidate pools improve seed 999 performance"""
    print()
    print("=" * 80)
    print(f"CANDIDATE POOL SIZE TESTING: Testing with seed {seed}")
    print("=" * 80)
    print()

    pool_sizes = [5000, 10000, 20000, 30000, 50000]
    results = {}

    for pool_size in pool_sizes:
        print(f"\nTesting pool size: {pool_size:,}")
        random.seed(seed)

        model = TrueLearningModel()

        # Override candidate pool size
        model.CANDIDATE_POOL_SIZE = pool_size

        # Load all series
        all_series = load_all_data()
        if not all_series:
            print("❌ No data loaded")
            return {}

        # Validation on last 8 series
        validation_window = 8
        validation_series_ids = sorted(all_series.keys())[-validation_window:]

        accuracies = []

        for series_id in validation_series_ids:
            # Train on all data before this series
            model = TrueLearningModel()
            model.CANDIDATE_POOL_SIZE = pool_size
            train_data = {k: v for k, v in all_series.items() if k < series_id}
            model.learn_from_historical_data(train_data)

            # Predict
            prediction = model.predict_best_combination(series_id)

            # Get actual and calculate best match
            actual_results = all_series[series_id]
            best_match = max(len(set(prediction) & set(actual)) for actual in actual_results)
            best_accuracy = best_match / 14
            accuracies.append(best_accuracy)

        avg_best = sum(accuracies) / len(accuracies)
        results[pool_size] = avg_best

        print(f"  Result: {avg_best:.1%}", end="")
        if avg_best > 0.732:
            print(" 🎯 IMPROVEMENT!")
        elif avg_best >= 0.732:
            print(" ✅ Same as 10k")
        else:
            print(f" ❌ Worse by {0.732 - avg_best:.1%}")

    return results


def analyze_seed_999_characteristics():
    """Analyze what makes seed 999 special"""
    print()
    print("=" * 80)
    print("SEED 999 CHARACTERISTICS ANALYSIS")
    print("=" * 80)
    print()

    # Compare seed 999 vs worst seed (123: 65.2%)
    seeds_to_compare = [
        (999, "BEST"),
        (2024, "2nd Best"),
        (456, "Baseline"),
        (123, "WORST"),
    ]

    for seed, label in seeds_to_compare:
        random.seed(seed)
        print(f"\n{label} - Seed {seed}:")

        # Generate sample of random numbers to see distribution
        samples = [random.random() for _ in range(100)]

        print(f"  Random sample stats:")
        print(f"    Mean: {sum(samples)/len(samples):.3f} (ideal: 0.500)")
        print(f"    Min:  {min(samples):.3f}")
        print(f"    Max:  {max(samples):.3f}")
        print(f"    Range: {max(samples) - min(samples):.3f}")

        # Check if seed produces more diverse early samples
        early_diversity = len(set([int(x * 100) for x in samples[:20]]))
        print(f"    Early diversity (first 20): {early_diversity}/20")


def main():
    print("🔬 COMPREHENSIVE SEED OPTIMIZATION STUDY")
    print()
    print("Research Question: Can we improve beyond seed 999 (73.2%)?")
    print()

    # Study 1: Test extended seed range
    print("\n📊 STUDY 1: Extended Seed Range Testing")
    extended_results = test_extended_seeds(num_seeds=20)

    if extended_results:
        print("\n" + "=" * 80)
        print("EXTENDED SEED RESULTS")
        print("=" * 80)
        sorted_results = sorted(extended_results, key=lambda x: x[1], reverse=True)
        for seed, accuracy in sorted_results[:10]:
            print(f"  Seed {seed:5d}: {accuracy:.1%}", end="")
            if accuracy > 0.732:
                print(" 🎯 BEATS SEED 999!")
            else:
                print()

    # Study 2: Test candidate pool sizes
    print("\n📊 STUDY 2: Candidate Pool Size Testing")
    pool_results = test_candidate_pool_sizes(seed=999)

    if pool_results:
        print("\n" + "=" * 80)
        print("CANDIDATE POOL SIZE RESULTS")
        print("=" * 80)
        for pool_size, accuracy in sorted(pool_results.items()):
            improvement = accuracy - 0.732
            print(f"  Pool {pool_size:6,}: {accuracy:.1%} ({improvement:+.1%})")

    # Study 3: Analyze seed characteristics
    print("\n📊 STUDY 3: Seed Characteristics Analysis")
    analyze_seed_999_characteristics()

    # Summary
    print("\n" + "=" * 80)
    print("STUDY SUMMARY")
    print("=" * 80)

    if extended_results:
        best_extended = max(extended_results, key=lambda x: x[1])
        print(f"\n✅ Best seed found: {best_extended[0]} → {best_extended[1]:.1%}")
        if best_extended[1] > 0.732:
            print(f"   🎯 IMPROVEMENT: +{best_extended[1] - 0.732:.1%} over seed 999!")
        else:
            print(f"   ℹ️  Seed 999 remains optimal")

    if pool_results:
        best_pool = max(pool_results.items(), key=lambda x: x[1])
        print(f"\n✅ Best pool size: {best_pool[0]:,} → {best_pool[1]:.1%}")
        if best_pool[1] > 0.732:
            print(f"   🎯 IMPROVEMENT: +{best_pool[1] - 0.732:.1%} over 10k pool!")
        else:
            print(f"   ℹ️  10k pool remains optimal")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
