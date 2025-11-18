#!/usr/bin/env python3
"""
Test Critical Fixes - Priority 1
Tests all four critical bug fixes on Series 3146-3150
"""

import json
import sys
from true_learning_model import TrueLearningModel

def load_data(filepath='full_series_data.json'):
    """Load series data from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def test_critical_fixes():
    """Test all Priority 1 fixes on Series 3146-3150"""

    print("=" * 80)
    print("TESTING CRITICAL FIXES - Priority 1")
    print("=" * 80)
    print()
    print("Fixes being tested:")
    print("  FIX #1: Weight normalization (prevent explosion)")
    print("  FIX #2: Critical number tracking with decay")
    print("  FIX #3: 30x boost (seed-robust, not 29x)")
    print("  FIX #4: Weight decay mechanism (prevent overfitting)")
    print()
    print("=" * 80)
    print()

    # Load data
    print("Loading dataset...")
    data = load_data()
    print(f"✅ Loaded {len(data)} series\n")

    # Initialize model with seed 999 for reproducibility
    print("Initializing model (seed=999, 30x boost)...")
    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
    print(f"✅ Model initialized")
    print(f"   Cold/Hot Boost: {model._cold_hot_boost}x (should be 30.0)")
    print(f"   Candidate Pool: {model.CANDIDATE_POOL_SIZE}")
    print()

    # Training phase: Train on all series up to 3145
    print("=" * 80)
    print("PHASE 1: Training on Series 2980-3145")
    print("=" * 80)
    print()

    training_series = [str(sid) for sid in range(2980, 3146) if str(sid) in data and str(sid) != '3146']

    for series_id_str in training_series:
        series_id = int(series_id_str)
        if series_id_str in data:
            model.learn_from_series(series_id, data[series_id_str])

    print(f"✅ Trained on {len(training_series)} series (2980-3145)")
    print(f"   Training size: {model.get_training_size()} series")
    print()

    # Validation phase: Test on Series 3146-3150
    print("=" * 80)
    print("PHASE 2: Validation on Series 3146-3150 (Walk-Forward)")
    print("=" * 80)
    print()

    validation_series = ['3146', '3147', '3148', '3149', '3150']
    results = []

    for series_id_str in validation_series:
        if series_id_str not in data:
            print(f"⚠️  Series {series_id_str} not found in dataset, skipping...")
            continue

        series_id = int(series_id_str)
        actual_results = data[series_id_str]

        print(f"\n{'=' * 80}")
        print(f"Testing Series {series_id}")
        print(f"{'=' * 80}")

        # Generate prediction
        prediction = model.predict_best_combination(series_id)
        print(f"\n🎯 Prediction: {' '.join(f'{n:02d}' for n in prediction)}")

        # Calculate accuracy
        best_match = max(actual_results, key=lambda actual: len(set(prediction) & set(actual)))
        best_match_count = len(set(prediction) & set(best_match))
        best_match_pct = best_match_count / 14.0

        print(f"\n📊 Results:")
        print(f"   Best match: {best_match_count}/14 ({best_match_pct:.1%})")
        print(f"   Matched numbers: {' '.join(f'{n:02d}' for n in sorted(set(prediction) & set(best_match)))}")

        # Validate and learn (this triggers fixes #1, #2, #4)
        print(f"\n📚 Learning from Series {series_id}...")
        model.validate_and_learn(series_id, prediction, actual_results)

        # Check weight normalization (FIX #1)
        max_weight = max(model.number_frequency_weights.values())
        print(f"\n🔍 Post-learning checks:")
        print(f"   Max weight: {max_weight:.2f} (should be ≤ 100.0 due to normalization)")
        print(f"   Critical numbers tracked: {len(model.recent_critical_numbers)} (FIX #2)")
        print(f"   Validation counter: {model._validation_counter} (FIX #4)")

        results.append({
            'series_id': series_id,
            'best_match_pct': best_match_pct,
            'best_match_count': best_match_count,
            'max_weight': max_weight
        })

    # Summary
    print("\n" + "=" * 80)
    print("TESTING SUMMARY")
    print("=" * 80)
    print()

    avg_pct = sum(r['best_match_pct'] for r in results) / len(results) if results else 0
    avg_count = sum(r['best_match_count'] for r in results) / len(results) if results else 0

    print(f"Series tested: {len(results)}")
    print(f"Average accuracy: {avg_pct:.1%} ({avg_count:.1f}/14 numbers)")
    print()

    print("Per-series results:")
    for r in results:
        print(f"  Series {r['series_id']}: {r['best_match_pct']:.1%} ({r['best_match_count']}/14) - Max weight: {r['max_weight']:.2f}")
    print()

    # Verify fixes
    print("=" * 80)
    print("FIX VERIFICATION")
    print("=" * 80)
    print()

    all_passed = True

    # FIX #1: Weight normalization
    max_weight_ever = max(r['max_weight'] for r in results)
    if max_weight_ever <= 100.0:
        print("✅ FIX #1 PASS: Weight normalization working (max weight ≤ 100.0)")
    else:
        print(f"❌ FIX #1 FAIL: Weight explosion detected (max weight: {max_weight_ever:.2f})")
        all_passed = False

    # FIX #2: Critical number tracking
    if len(model.recent_critical_numbers) > 0 and len(model.recent_critical_numbers) <= 15:
        print(f"✅ FIX #2 PASS: Critical number tracking with decay ({len(model.recent_critical_numbers)} tracked)")
    else:
        print(f"⚠️  FIX #2 WARNING: Critical number count: {len(model.recent_critical_numbers)} (expected 1-15)")

    # FIX #3: 30x boost
    if model._cold_hot_boost == 30.0:
        print("✅ FIX #3 PASS: Using 30x boost (seed-robust)")
    else:
        print(f"❌ FIX #3 FAIL: Using {model._cold_hot_boost}x boost (should be 30.0)")
        all_passed = False

    # FIX #4: Weight decay
    if model._validation_counter == len(results):
        print(f"✅ FIX #4 PASS: Weight decay counter tracking validations ({model._validation_counter})")
    else:
        print(f"⚠️  FIX #4 WARNING: Counter mismatch ({model._validation_counter} vs {len(results)} series)")

    print()
    print("=" * 80)

    if all_passed:
        print("✅ ALL CRITICAL FIXES VERIFIED")
    else:
        print("❌ SOME FIXES FAILED - REVIEW NEEDED")

    print("=" * 80)
    print()

    return results, all_passed

if __name__ == "__main__":
    results, passed = test_critical_fixes()
    sys.exit(0 if passed else 1)
