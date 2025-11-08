"""
COMPREHENSIVE RE-TEST WITH FULL DATASET

Previous tests used only 9 series (3137-3145)
Now re-testing with FULL 166 series (2980-3145)

This will find the TRUE optimal configuration.
"""

import sys
import json
import random
from typing import List, Dict
from collections import defaultdict

sys.path.append('/home/user/Random/python_ml')
from true_learning_model import TrueLearningModel

def load_full_data():
    """Load all 166 series"""
    with open('full_series_data.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def test_configuration(SERIES_DATA, recent_series_count, candidates_to_score=1000, learning_rate=0.1, seed=999):
    """Test a specific configuration"""
    random.seed(seed)

    # Use last 8 series as validation
    all_series = sorted(SERIES_DATA.keys())
    val_start_idx = len(all_series) - 8
    training_series = all_series[:val_start_idx]
    validation_series = all_series[val_start_idx:]

    # Use recent N for training
    if len(training_series) > recent_series_count:
        training_series = training_series[-recent_series_count:]

    # Train model
    model = TrueLearningModel()
    model.learning_rate = learning_rate

    # Override CANDIDATES_TO_SCORE if model supports it
    if hasattr(model, 'CANDIDATES_TO_SCORE'):
        original_candidates = model.CANDIDATES_TO_SCORE
        model.CANDIDATES_TO_SCORE = candidates_to_score

    for series_id in training_series:
        if series_id in SERIES_DATA:
            model.learn_from_series(series_id, SERIES_DATA[series_id])

    # Validate
    results = []
    for series_id in validation_series:
        actual_events = SERIES_DATA[series_id]
        prediction = model.predict_best_combination(series_id)

        best_accuracy = max(len(set(prediction) & set(event)) / 14.0 for event in actual_events)
        avg_accuracy = sum(len(set(prediction) & set(event)) / 14.0 for event in actual_events) / 7.0

        results.append({
            "series_id": series_id,
            "best_accuracy": best_accuracy,
            "avg_accuracy": avg_accuracy
        })

        # Learn from actual
        model.learn_from_series(series_id, actual_events)

    # Restore original if changed
    if hasattr(model, 'CANDIDATES_TO_SCORE'):
        model.CANDIDATES_TO_SCORE = original_candidates

    overall_best_avg = sum(r["best_accuracy"] for r in results) / len(results)
    overall_avg = sum(r["avg_accuracy"] for r in results) / len(results)

    return {
        "overall_best_avg": overall_best_avg,
        "overall_avg": overall_avg,
        "results": results
    }

def main():
    """Run comprehensive re-test with full dataset"""
    print("="*70)
    print("COMPREHENSIVE RE-TEST WITH FULL DATASET")
    print("="*70)
    print()

    # Load full data
    print("Loading full dataset...")
    SERIES_DATA = load_full_data()
    print(f"✅ Loaded {len(SERIES_DATA)} series ({min(SERIES_DATA.keys())} to {max(SERIES_DATA.keys())})")
    print()

    all_results = {}

    # =====================================================================
    # TEST 1: Training Window Sizes
    # =====================================================================
    print("="*70)
    print("TEST 1: Training Window Sizes")
    print("="*70)

    baseline_window = 70
    print(f"\n1. Baseline: {baseline_window} series...")
    baseline_result = test_configuration(SERIES_DATA, baseline_window, seed=999)
    baseline_actual = baseline_result["overall_avg"]

    print(f"   Actual avg: {baseline_actual:.1%}")
    print(f"   Best match avg: {baseline_result['overall_best_avg']:.1%}")

    window_sizes = [30, 40, 50, 60, 70, 80, 90, 100, 120, 150]
    window_results = []

    for window in window_sizes:
        if window == baseline_window:
            result = baseline_result
        else:
            print(f"\n   Testing window={window}...")
            result = test_configuration(SERIES_DATA, window, seed=999)
            print(f"   Actual avg: {result['overall_avg']:.1%} ({result['overall_avg'] - baseline_actual:+.1%})")

        window_results.append({
            "window_size": window,
            "actual_avg": result["overall_avg"],
            "best_match_avg": result["overall_best_avg"],
            "vs_baseline": result["overall_avg"] - baseline_actual
        })

    all_results["window_sizes"] = {
        "baseline": baseline_actual,
        "results": window_results,
        "best": max(window_results, key=lambda x: x["actual_avg"])
    }

    print(f"\n   ✅ Best window: {all_results['window_sizes']['best']['window_size']} " +
          f"({all_results['window_sizes']['best']['actual_avg']:.1%}, " +
          f"{all_results['window_sizes']['best']['vs_baseline']:+.1%})")

    # Use best window for further tests
    best_window = all_results['window_sizes']['best']['window_size']

    # =====================================================================
    # TEST 2: Candidate Pool Sizes
    # =====================================================================
    print("\n" + "="*70)
    print("TEST 2: Candidate Pool Sizes")
    print("="*70)

    candidate_sizes = [500, 1000, 1500, 2000, 3000, 5000, 7000, 10000]
    candidate_results = []

    for cand_size in candidate_sizes:
        print(f"\n   Testing {cand_size} candidates...")
        result = test_configuration(SERIES_DATA, best_window, candidates_to_score=cand_size, seed=999)
        print(f"   Actual avg: {result['overall_avg']:.1%} ({result['overall_avg'] - baseline_actual:+.1%})")

        candidate_results.append({
            "candidate_size": cand_size,
            "actual_avg": result["overall_avg"],
            "best_match_avg": result["overall_best_avg"],
            "vs_baseline": result["overall_avg"] - baseline_actual
        })

    all_results["candidate_sizes"] = {
        "baseline": baseline_actual,
        "results": candidate_results,
        "best": max(candidate_results, key=lambda x: x["actual_avg"])
    }

    print(f"\n   ✅ Best candidates: {all_results['candidate_sizes']['best']['candidate_size']} " +
          f"({all_results['candidate_sizes']['best']['actual_avg']:.1%}, " +
          f"{all_results['candidate_sizes']['best']['vs_baseline']:+.1%})")

    best_candidates = all_results['candidate_sizes']['best']['candidate_size']

    # =====================================================================
    # TEST 3: Learning Rates
    # =====================================================================
    print("\n" + "="*70)
    print("TEST 3: Learning Rates")
    print("="*70)

    learning_rates = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]
    lr_results = []

    for lr in learning_rates:
        print(f"\n   Testing LR={lr}...")
        result = test_configuration(SERIES_DATA, best_window, candidates_to_score=best_candidates,
                                   learning_rate=lr, seed=999)
        print(f"   Actual avg: {result['overall_avg']:.1%} ({result['overall_avg'] - baseline_actual:+.1%})")

        lr_results.append({
            "learning_rate": lr,
            "actual_avg": result["overall_avg"],
            "best_match_avg": result["overall_best_avg"],
            "vs_baseline": result["overall_avg"] - baseline_actual
        })

    all_results["learning_rates"] = {
        "baseline": baseline_actual,
        "results": lr_results,
        "best": max(lr_results, key=lambda x: x["actual_avg"])
    }

    print(f"\n   ✅ Best LR: {all_results['learning_rates']['best']['learning_rate']} " +
          f"({all_results['learning_rates']['best']['actual_avg']:.1%}, " +
          f"{all_results['learning_rates']['best']['vs_baseline']:+.1%})")

    best_lr = all_results['learning_rates']['best']['learning_rate']

    # =====================================================================
    # FINAL TEST: Best Combined Configuration
    # =====================================================================
    print("\n" + "="*70)
    print("FINAL TEST: Best Combined Configuration")
    print("="*70)

    print(f"\nBest window: {best_window}")
    print(f"Best candidates: {best_candidates}")
    print(f"Best LR: {best_lr}")
    print()

    print("Testing combined configuration...")
    final_result = test_configuration(SERIES_DATA, best_window,
                                      candidates_to_score=best_candidates,
                                      learning_rate=best_lr, seed=999)

    all_results["final_best"] = {
        "config": {
            "window": best_window,
            "candidates": best_candidates,
            "learning_rate": best_lr,
            "seed": 999
        },
        "performance": {
            "actual_avg": final_result["overall_avg"],
            "best_match_avg": final_result["overall_best_avg"],
            "improvement": final_result["overall_avg"] - baseline_actual
        },
        "results": final_result["results"]
    }

    # =====================================================================
    # SUMMARY
    # =====================================================================
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)

    print(f"\nOriginal baseline (70 series): {baseline_actual:.1%}")
    print()
    print(f"Best window size: {best_window} series")
    print(f"  → Performance: {all_results['window_sizes']['best']['actual_avg']:.1%}")
    print(f"  → Improvement: {all_results['window_sizes']['best']['vs_baseline']:+.1%}")
    print()
    print(f"Best candidate pool: {best_candidates}")
    print(f"  → Performance: {all_results['candidate_sizes']['best']['actual_avg']:.1%}")
    print(f"  → Improvement: {all_results['candidate_sizes']['best']['vs_baseline']:+.1%}")
    print()
    print(f"Best learning rate: {best_lr}")
    print(f"  → Performance: {all_results['learning_rates']['best']['actual_avg']:.1%}")
    print(f"  → Improvement: {all_results['learning_rates']['best']['vs_baseline']:+.1%}")
    print()
    print("="*70)
    print("FINAL BEST CONFIGURATION:")
    print("="*70)
    print(f"Window: {best_window} series")
    print(f"Candidates: {best_candidates}")
    print(f"Learning Rate: {best_lr}")
    print(f"Seed: 999")
    print()
    print(f"Performance: {final_result['overall_avg']:.1%} actual avg")
    print(f"Best match avg: {final_result['overall_best_avg']:.1%}")
    print(f"Improvement over baseline: {final_result['overall_avg'] - baseline_actual:+.1%}")
    print()

    if final_result['overall_avg'] > baseline_actual + 0.001:
        print(f"✅ SUCCESS: Improved by {(final_result['overall_avg'] - baseline_actual)*100:+.1f}%!")
    elif final_result['overall_avg'] > baseline_actual - 0.001:
        print(f"➖ NEUTRAL: No significant change")
    else:
        print(f"❌ REGRESSION: Performance decreased")

    print("="*70)

    # Save results
    with open('full_data_retest_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print("\n💾 Results saved to: full_data_retest_results.json")

if __name__ == "__main__":
    main()
