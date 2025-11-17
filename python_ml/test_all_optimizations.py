#!/usr/bin/env python3
"""
Comprehensive Optimization Testing
Tests weighted lookback and triplet optimization on Series 3146-3150
"""

import json
import sys
from collections import defaultdict
from typing import List, Dict, Tuple
from true_learning_model import TrueLearningModel

def load_data(filepath='full_series_data.json'):
    """Load series data"""
    with open(filepath, 'r') as f:
        return json.load(f)

def test_configuration(config_name: str, model_config: dict, data: dict,
                      train_until: int = 3145, test_series: list = None) -> dict:
    """
    Test a specific configuration

    Args:
        config_name: Name of configuration
        model_config: Model parameters
        data: Series data
        train_until: Train on all series up to this ID
        test_series: List of series to test on

    Returns:
        dict with results
    """
    if test_series is None:
        test_series = ['3146', '3147', '3148', '3149', '3150']

    # Initialize model with configuration
    model = TrueLearningModel(**model_config)

    # Apply weighted lookback if specified
    if 'weighted_lookback' in model_config:
        model._use_weighted_lookback = True
        model._lookback_weight_type = model_config['weighted_lookback']

    # Train on bulk data
    for series_id_str in sorted(data.keys()):
        series_id = int(series_id_str)
        if series_id <= train_until:
            model.learn_from_series(series_id, data[series_id_str])

    # Test on validation series
    accuracies = []
    for series_id_str in test_series:
        if series_id_str not in data:
            continue

        series_id = int(series_id_str)
        actual = data[series_id_str]

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Calculate accuracy
        best_match = max(actual, key=lambda a: len(set(prediction) & set(a)))
        accuracy = len(set(prediction) & set(best_match)) / 14.0

        accuracies.append(accuracy)

        # Learn from results (for next iteration)
        model.validate_and_learn(series_id, prediction, actual)

    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    peak_accuracy = max(accuracies) if accuracies else 0

    return {
        'config_name': config_name,
        'avg_accuracy': avg_accuracy,
        'peak_accuracy': peak_accuracy,
        'accuracies': accuracies,
        'config': model_config
    }

def test_weighted_lookback():
    """Test different weighted lookback strategies"""

    print("=" * 80)
    print("WEIGHTED LOOKBACK WINDOW OPTIMIZATION")
    print("=" * 80)
    print()

    data = load_data()

    # Configurations to test
    configs = [
        # Baseline (no weighting)
        {
            'name': 'Baseline (Equal Weights)',
            'config': {'seed': 999, 'cold_hot_boost': 30.0}
        },
        # Exponential decay (gentle)
        {
            'name': 'Exponential Decay (Gentle)',
            'config': {'seed': 999, 'cold_hot_boost': 30.0, 'weighted_lookback': 'exponential'}
        },
        # Last-4 heavy
        {
            'name': 'Last-4 Heavy (2x weight)',
            'config': {'seed': 999, 'cold_hot_boost': 30.0, 'weighted_lookback': 'last4_heavy'}
        },
        # Linear decay
        {
            'name': 'Linear Decay',
            'config': {'seed': 999, 'cold_hot_boost': 30.0, 'weighted_lookback': 'linear'}
        }
    ]

    results = []
    baseline_avg = None

    for cfg in configs:
        print(f"\nTesting: {cfg['name']}")
        print(f"{'-' * 80}")

        result = test_configuration(cfg['name'], cfg['config'], data)

        if 'Baseline' in cfg['name']:
            baseline_avg = result['avg_accuracy']

        improvement = (result['avg_accuracy'] - baseline_avg) * 100 if baseline_avg else 0

        print(f"Average: {result['avg_accuracy']:.1%} ({result['avg_accuracy'] * 14:.1f}/14)")
        print(f"Peak: {result['peak_accuracy']:.1%}")
        if baseline_avg:
            print(f"vs Baseline: {improvement:+.1f}%")

        results.append(result)

    # Summary
    print("\n" + "=" * 80)
    print("WEIGHTED LOOKBACK SUMMARY")
    print("=" * 80)
    print()

    for r in results:
        improvement = (r['avg_accuracy'] - baseline_avg) * 100 if baseline_avg else 0
        status = "✅" if improvement > 0.5 else ("❌" if improvement < -0.5 else "➖")
        print(f"{status} {r['config_name']:30s}: {r['avg_accuracy']:.1%} ({improvement:+.1f}%)")

    # Find best
    best = max(results, key=lambda x: x['avg_accuracy'])
    print(f"\n🏆 Best: {best['config_name']} at {best['avg_accuracy']:.1%}")

    return results

def test_triplet_multipliers():
    """Test different triplet affinity multipliers"""

    print("\n" + "=" * 80)
    print("TRIPLET AFFINITY MULTIPLIER OPTIMIZATION")
    print("=" * 80)
    print()

    data = load_data()

    # Test different multipliers
    multipliers = [20.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0]

    results = []
    baseline_avg = None

    for mult in multipliers:
        print(f"\nTesting Multiplier: {mult}x")
        print(f"{'-' * 80}")

        # Create model with this multiplier
        model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
        model.TRIPLET_AFFINITY_MULTIPLIER = mult

        # Train
        for series_id_str in sorted(data.keys()):
            series_id = int(series_id_str)
            if series_id <= 3145:
                model.learn_from_series(series_id, data[series_id_str])

        # Test
        accuracies = []
        for series_id_str in ['3146', '3147', '3148', '3149', '3150']:
            if series_id_str not in data:
                continue

            series_id = int(series_id_str)
            actual = data[series_id_str]

            prediction = model.predict_best_combination(series_id)
            best_match = max(actual, key=lambda a: len(set(prediction) & set(a)))
            accuracy = len(set(prediction) & set(best_match)) / 14.0

            accuracies.append(accuracy)
            model.validate_and_learn(series_id, prediction, actual)

        avg_accuracy = sum(accuracies) / len(accuracies)
        peak_accuracy = max(accuracies)

        if mult == 35.0:  # Current default
            baseline_avg = avg_accuracy

        improvement = (avg_accuracy - baseline_avg) * 100 if baseline_avg else 0

        print(f"Average: {avg_accuracy:.1%}")
        print(f"Peak: {peak_accuracy:.1%}")
        if baseline_avg:
            print(f"vs Baseline (35x): {improvement:+.1f}%")

        results.append({
            'multiplier': mult,
            'avg_accuracy': avg_accuracy,
            'peak_accuracy': peak_accuracy,
            'accuracies': accuracies
        })

    # Summary
    print("\n" + "=" * 80)
    print("TRIPLET MULTIPLIER SUMMARY")
    print("=" * 80)
    print()

    for r in results:
        improvement = (r['avg_accuracy'] - baseline_avg) * 100 if baseline_avg else 0
        status = "✅" if improvement > 0.5 else ("❌" if improvement < -0.5 else "➖")
        marker = " ← CURRENT" if r['multiplier'] == 35.0 else ""
        print(f"{status} {r['multiplier']:4.0f}x: {r['avg_accuracy']:.1%} ({improvement:+.1f}%){marker}")

    # Find best
    best = max(results, key=lambda x: x['avg_accuracy'])
    print(f"\n🏆 Best: {best['multiplier']:.0f}x at {best['avg_accuracy']:.1%}")

    return results

def test_lookback_window_size():
    """Test lookback window 8 vs 9 vs 10"""

    print("\n" + "=" * 80)
    print("LOOKBACK WINDOW SIZE OPTIMIZATION (8 vs 9 vs 10)")
    print("=" * 80)
    print()

    data = load_data()

    lookback_sizes = [8, 9, 10]
    results = []
    baseline_avg = None

    for lookback in lookback_sizes:
        print(f"\nTesting Lookback: {lookback} series")
        print(f"{'-' * 80}")

        model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
        model.RECENT_SERIES_LOOKBACK = lookback

        # Train
        for series_id_str in sorted(data.keys()):
            series_id = int(series_id_str)
            if series_id <= 3145:
                model.learn_from_series(series_id, data[series_id_str])

        # Test
        accuracies = []
        for series_id_str in ['3146', '3147', '3148', '3149', '3150']:
            if series_id_str not in data:
                continue

            series_id = int(series_id_str)
            actual = data[series_id_str]

            prediction = model.predict_best_combination(series_id)
            best_match = max(actual, key=lambda a: len(set(prediction) & set(a)))
            accuracy = len(set(prediction) & set(best_match)) / 14.0

            accuracies.append(accuracy)
            model.validate_and_learn(series_id, prediction, actual)

        avg_accuracy = sum(accuracies) / len(accuracies)
        peak_accuracy = max(accuracies)

        if lookback == 10:  # Current default
            baseline_avg = avg_accuracy

        improvement = (avg_accuracy - baseline_avg) * 100 if baseline_avg else 0

        print(f"Average: {avg_accuracy:.1%}")
        print(f"Peak: {peak_accuracy:.1%}")
        if baseline_avg:
            print(f"vs Baseline (10): {improvement:+.1f}%")

        results.append({
            'lookback': lookback,
            'avg_accuracy': avg_accuracy,
            'peak_accuracy': peak_accuracy,
            'accuracies': accuracies
        })

    # Summary
    print("\n" + "=" * 80)
    print("LOOKBACK WINDOW SUMMARY")
    print("=" * 80)
    print()

    for r in results:
        improvement = (r['avg_accuracy'] - baseline_avg) * 100 if baseline_avg else 0
        status = "✅" if improvement > 0.5 else ("❌" if improvement < -0.5 else "➖")
        marker = " ← CURRENT" if r['lookback'] == 10 else ""
        print(f"{status} {r['lookback']:2d}-series: {r['avg_accuracy']:.1%} ({improvement:+.1f}%){marker}")

    # Find best
    best = max(results, key=lambda x: x['avg_accuracy'])
    print(f"\n🏆 Best: {best['lookback']}-series at {best['avg_accuracy']:.1%}")

    return results

def main():
    """Run all optimization tests"""

    print("=" * 80)
    print("COMPREHENSIVE OPTIMIZATION TESTING")
    print("Testing on Series 3146-3150")
    print("=" * 80)
    print()

    # Test 1: Lookback window size (quick)
    print("\n📊 TEST 1: Lookback Window Size")
    lookback_results = test_lookback_window_size()

    # Test 2: Triplet multipliers
    print("\n📊 TEST 2: Triplet Multipliers")
    triplet_results = test_triplet_multipliers()

    # Test 3: Weighted lookback (only if time permits - this requires code changes)
    # print("\n📊 TEST 3: Weighted Lookback")
    # weighted_results = test_weighted_lookback()

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL RECOMMENDATIONS")
    print("=" * 80)
    print()

    best_lookback = max(lookback_results, key=lambda x: x['avg_accuracy'])
    best_triplet = max(triplet_results, key=lambda x: x['avg_accuracy'])

    print(f"Best Lookback: {best_lookback['lookback']}-series ({best_lookback['avg_accuracy']:.1%})")
    print(f"Best Triplet: {best_triplet['multiplier']:.0f}x ({best_triplet['avg_accuracy']:.1%})")
    print()

    # Check if improvements are significant
    lookback_default = [r for r in lookback_results if r['lookback'] == 10][0]
    triplet_default = [r for r in triplet_results if r['multiplier'] == 35.0][0]

    lookback_improvement = (best_lookback['avg_accuracy'] - lookback_default['avg_accuracy']) * 100
    triplet_improvement = (best_triplet['avg_accuracy'] - triplet_default['avg_accuracy']) * 100

    print("Improvements over current defaults:")
    print(f"  Lookback: {lookback_improvement:+.2f}%")
    print(f"  Triplet: {triplet_improvement:+.2f}%")
    print()

    if lookback_improvement > 0.5:
        print(f"✅ ADOPT: Change lookback to {best_lookback['lookback']}-series")
    else:
        print(f"➖ KEEP: Lookback at 10-series (improvement < 0.5%)")

    if triplet_improvement > 0.5:
        print(f"✅ ADOPT: Change triplet multiplier to {best_triplet['multiplier']:.0f}x")
    else:
        print(f"➖ KEEP: Triplet at 35x (improvement < 0.5%)")

if __name__ == "__main__":
    main()
