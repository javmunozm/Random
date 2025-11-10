"""
FIXED Mandel Validation Test

Test the Mandel pool generator WITH cold/hot boost (matching C# strategy)

Comparison:
1. Original (base model with weighted generation)
2. Mandel WITHOUT cold/hot boost (old - should be worse)
3. Mandel WITH cold/hot boost (new - should be best)
"""

import sys
import json
import random
from typing import List, Dict

sys.path.append('/home/user/Random/python_ml')

from true_learning_model import TrueLearningModel
from mandel_pool_generator import MandelPoolGenerator


class OriginalModel(TrueLearningModel):
    """Base model - uses weighted generation (no Mandel pool)"""
    pass  # No override - use base implementation


class MandelModelOld(TrueLearningModel):
    """Mandel WITHOUT cold/hot boost (old implementation)"""
    def __init__(self):
        super().__init__()
        self.mandel_generator = None

    def _generate_candidates(self, target_series_id: int):
        self.mandel_generator = MandelPoolGenerator(
            frequency_weights=self.number_frequency_weights,
            pair_affinities=self.pair_affinities
            # NO cold/hot numbers passed!
        )
        return self.mandel_generator.generate_pool(size=self.CANDIDATES_TO_SCORE, seed=999)


class MandelModelFixed(TrueLearningModel):
    """Mandel WITH cold/hot boost (FIXED implementation)"""
    def __init__(self):
        super().__init__()
        self.mandel_generator = None

    def _generate_candidates(self, target_series_id: int):
        self.mandel_generator = MandelPoolGenerator(
            frequency_weights=self.number_frequency_weights,
            pair_affinities=self.pair_affinities,
            hybrid_cold_numbers=self.hybrid_cold_numbers,  # CRITICAL FIX!
            hybrid_hot_numbers=self.hybrid_hot_numbers      # CRITICAL FIX!
        )
        return self.mandel_generator.generate_pool(size=self.CANDIDATES_TO_SCORE, seed=999)


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


def walk_forward_test():
    """
    Walk-forward validation comparing all three approaches
    """
    print("="*70)
    print("FIXED MANDEL VALIDATION - 3-WAY COMPARISON")
    print("="*70)
    print()

    # Load data
    SERIES_DATA = load_data()
    all_series = sorted(SERIES_DATA.keys())

    print(f"📊 Dataset: {len(SERIES_DATA)} series ({all_series[0]}-{all_series[-1]})")
    print()

    # Validation window: last 6 series
    validation_window = all_series[-6:]
    print(f"🎯 Validation Window: {validation_window}")
    print()

    # Results storage
    original_results = []
    mandel_old_results = []
    mandel_fixed_results = []

    CANDIDATES = 2000
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

        # 1. Original Model (base weighted generation)
        print("   [1/3] Testing Original (weighted generation)...")
        random.seed(SEED)
        original_model = OriginalModel()
        original_model.CANDIDATES_TO_SCORE = CANDIDATES

        for train_id in training_series:
            original_model.learn_from_series(train_id, SERIES_DATA[train_id])

        original_pred = original_model.predict_best_combination(series_id)

        # 2. Mandel OLD (no cold/hot boost)
        print("   [2/3] Testing Mandel OLD (no cold/hot boost)...")
        random.seed(SEED)
        mandel_old_model = MandelModelOld()
        mandel_old_model.CANDIDATES_TO_SCORE = CANDIDATES

        for train_id in training_series:
            mandel_old_model.learn_from_series(train_id, SERIES_DATA[train_id])

        mandel_old_pred = mandel_old_model.predict_best_combination(series_id)

        # 3. Mandel FIXED (with cold/hot boost)
        print("   [3/3] Testing Mandel FIXED (WITH cold/hot boost)...")
        random.seed(SEED)
        mandel_fixed_model = MandelModelFixed()
        mandel_fixed_model.CANDIDATES_TO_SCORE = CANDIDATES

        for train_id in training_series:
            mandel_fixed_model.learn_from_series(train_id, SERIES_DATA[train_id])

        mandel_fixed_pred = mandel_fixed_model.predict_best_combination(series_id)

        # Evaluate all
        actual_events = SERIES_DATA[series_id]
        original_eval = evaluate_prediction(original_pred, actual_events)
        mandel_old_eval = evaluate_prediction(mandel_old_pred, actual_events)
        mandel_fixed_eval = evaluate_prediction(mandel_fixed_pred, actual_events)

        # Store
        original_results.append({"series_id": series_id, **original_eval})
        mandel_old_results.append({"series_id": series_id, **mandel_old_eval})
        mandel_fixed_results.append({"series_id": series_id, **mandel_fixed_eval})

        # Display
        print(f"   Original:     {original_eval['best_match']:.1%} best, {original_eval['avg_match']:.1%} avg")
        print(f"   Mandel OLD:   {mandel_old_eval['best_match']:.1%} best, {mandel_old_eval['avg_match']:.1%} avg")
        print(f"   Mandel FIXED: {mandel_fixed_eval['best_match']:.1%} best, {mandel_fixed_eval['avg_match']:.1%} avg")

        best_score = max(original_eval['best_match'], mandel_old_eval['best_match'], mandel_fixed_eval['best_match'])
        if mandel_fixed_eval['best_match'] == best_score:
            print(f"   🏆 FIXED WINS!")
        elif original_eval['best_match'] == best_score:
            print(f"   ⚠️  Original wins")
        else:
            print(f"   ⚠️  Old wins")

        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()

    original_avg = sum(r['best_match'] for r in original_results) / len(original_results)
    mandel_old_avg = sum(r['best_match'] for r in mandel_old_results) / len(mandel_old_results)
    mandel_fixed_avg = sum(r['best_match'] for r in mandel_fixed_results) / len(mandel_fixed_results)

    print(f"Original (weighted):         {original_avg:.1%} average best match")
    print(f"Mandel OLD (no cold/hot):    {mandel_old_avg:.1%} average best match")
    print(f"Mandel FIXED (WITH cold/hot): {mandel_fixed_avg:.1%} average best match")
    print()

    # Improvement
    improvement_vs_original = mandel_fixed_avg - original_avg
    improvement_vs_old = mandel_fixed_avg - mandel_old_avg

    print("="*70)
    print("VERDICT")
    print("="*70)
    print()

    if mandel_fixed_avg > original_avg and mandel_fixed_avg > mandel_old_avg:
        print("🏆 MANDEL FIXED is the WINNER!")
        print(f"   Improvement vs Original: {improvement_vs_original:+.1%}")
        print(f"   Improvement vs Old: {improvement_vs_old:+.1%}")
        print()
        print("✅ Cold/hot boost in Mandel pool WORKS!")
        print("✅ Mandel balanced distribution + cold/hot = optimal")
    elif original_avg >= mandel_fixed_avg:
        print("⚠️  Original weighted generation still wins")
        print(f"   Mandel FIXED is {improvement_vs_original:.1%} vs Original")
        print()
        print("❌ Mandel pool needs more tuning")
    else:
        print("🤔 Mixed results - need more testing")

    # Save results
    output = {
        "validation_window": validation_window,
        "original_results": original_results,
        "mandel_old_results": mandel_old_results,
        "mandel_fixed_results": mandel_fixed_results,
        "summary": {
            "original_avg": original_avg,
            "mandel_old_avg": mandel_old_avg,
            "mandel_fixed_avg": mandel_fixed_avg,
            "improvement_vs_original": improvement_vs_original,
            "improvement_vs_old": improvement_vs_old
        }
    }

    with open('fixed_mandel_validation_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("💾 Saved to: fixed_mandel_validation_results.json")
    print("="*70)


if __name__ == "__main__":
    walk_forward_test()
