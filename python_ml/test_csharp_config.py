"""
Test with EXACT C# configuration

C# config:
- CANDIDATE_POOL_SIZE = 10,000 (generation attempts)
- CANDIDATES_TO_SCORE = 1,000 (take first 1000 valid)
- Uses weighted generation with 50x cold/hot boost
- No Mandel pool - just weighted selection

This test will:
1. Use base Python model (no Mandel override)
2. Use C# pool sizes (10k generation, 1k scoring)
3. Compare against C# reported 71.4% baseline
"""

import sys
import json
import random
from typing import List, Dict

sys.path.append('/home/user/Random/python_ml')

from true_learning_model import TrueLearningModel


def load_data():
    """Load expanded dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def evaluate_prediction(prediction: List[int], actual_events: List[List[int]]) -> Dict:
    """Evaluate prediction"""
    matches = []
    for event in actual_events:
        match_count = len(set(prediction) & set(event))
        match_pct = match_count / 14.0
        matches.append(match_pct)

    return {
        "best_match": max(matches),
        "avg_match": sum(matches) / len(matches),
        "matches": matches
    }


def test_with_csharp_config():
    """
    Test Python model with exact C# configuration
    """
    print("="*70)
    print("TESTING WITH C# CONFIGURATION")
    print("="*70)
    print()

    # Load data
    SERIES_DATA = load_data()
    all_series = sorted(SERIES_DATA.keys())

    print(f"📊 Dataset: {len(SERIES_DATA)} series ({all_series[0]}-{all_series[-1]})")
    print()

    # C# Configuration
    print("⚙️  C# Configuration:")
    print("   CANDIDATE_POOL_SIZE: 10,000")
    print("   CANDIDATES_TO_SCORE: 1,000")
    print("   Method: Weighted generation with 50x cold/hot boost")
    print("   C# Reported Performance: 71.4% baseline")
    print()

    # Validation window: last 6 series
    validation_window = all_series[-6:]
    print(f"🎯 Validation Window: {validation_window}")
    print()

    results = []
    SEED = 999

    print("="*70)
    print("TESTING")
    print("="*70)
    print()

    for series_id in validation_window:
        print(f"📍 Series {series_id}")
        print("-" * 50)

        # Training data
        training_series = [s for s in all_series if s < series_id]
        print(f"   Training on {len(training_series)} series")

        # Initialize model with C# config
        random.seed(SEED)
        model = TrueLearningModel()

        # Use C# pool sizes (these are already the defaults in the class)
        print(f"   Pool config: {model.CANDIDATE_POOL_SIZE} generation, {model.CANDIDATES_TO_SCORE} scoring")

        # Train
        for train_id in training_series:
            model.learn_from_series(train_id, SERIES_DATA[train_id])

        # Predict
        prediction = model.predict_best_combination(series_id)

        # Evaluate
        actual_events = SERIES_DATA[series_id]
        eval_result = evaluate_prediction(prediction, actual_events)

        results.append({
            "series_id": series_id,
            **eval_result
        })

        print(f"   Result: {eval_result['best_match']:.1%} best, {eval_result['avg_match']:.1%} avg")
        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()

    avg_best = sum(r['best_match'] for r in results) / len(results)
    avg_avg = sum(r['avg_match'] for r in results) / len(results)

    print(f"Python with C# config:")
    print(f"  Average Best Match: {avg_best:.1%}")
    print(f"  Average Avg Match:  {avg_avg:.1%}")
    print()

    print(f"C# Reported Baseline:")
    print(f"  Average Best Match: 71.4%")
    print()

    # Comparison
    diff = avg_best - 0.714

    print("="*70)
    print("VERDICT")
    print("="*70)
    print()

    if avg_best >= 0.714:
        print(f"✅ MATCH or BETTER! Python: {avg_best:.1%} vs C#: 71.4%")
        print(f"   Difference: {diff:+.1%}")
    elif avg_best >= 0.70:
        print(f"⚠️  CLOSE but slightly below")
        print(f"   Python: {avg_best:.1%} vs C#: 71.4%")
        print(f"   Difference: {diff:+.1%}")
        print()
        print("Possible reasons:")
        print("- Random seed differences between C# and Python")
        print("- Validation window differences")
        print("- Small sample size (6 series)")
    else:
        print(f"❌ BELOW C# baseline")
        print(f"   Python: {avg_best:.1%} vs C#: 71.4%")
        print(f"   Difference: {diff:+.1%}")
        print()
        print("Need to investigate:")
        print("- Weighted selection logic differences")
        print("- Scoring algorithm differences")
        print("- Other implementation differences")

    # Save results
    output = {
        "validation_window": validation_window,
        "results": results,
        "summary": {
            "python_avg_best": avg_best,
            "python_avg_avg": avg_avg,
            "csharp_baseline": 0.714,
            "difference": diff
        },
        "config": {
            "candidate_pool_size": 10000,
            "candidates_to_score": 1000,
            "seed": 999
        }
    }

    with open('csharp_config_test_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("💾 Saved to: csharp_config_test_results.json")
    print("="*70)


if __name__ == "__main__":
    test_with_csharp_config()
