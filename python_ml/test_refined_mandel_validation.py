"""
Walk-Forward Validation Test: Refined Mandel vs Original

Test methodology:
1. Select validation window (e.g., last 6 series: 3141-3146)
2. For each series in window:
   - Train model on ALL data BEFORE that series
   - Generate prediction with:
     a) Original Mandel method
     b) Refined Mandel method
   - Compare accuracy against actual results
3. Report comparative performance
"""

import sys
import json
import random
from typing import List, Dict

sys.path.append('/home/user/Random/python_ml')

from true_learning_model import TrueLearningModel
from mandel_pool_generator import MandelPoolGenerator
from mandel_pool_refined import RefinedMandelPoolGenerator


class OriginalMandelModel(TrueLearningModel):
    """Model using original Mandel pool"""
    def __init__(self):
        super().__init__()
        self.mandel_generator = None

    def _generate_candidates(self, target_series_id: int):
        self.mandel_generator = MandelPoolGenerator(
            frequency_weights=self.number_frequency_weights,
            pair_affinities=self.pair_affinities
        )
        return self.mandel_generator.generate_pool(
            size=self.CANDIDATES_TO_SCORE,
            seed=999
        )


class RefinedMandelModel(TrueLearningModel):
    """Model using refined Mandel pool"""
    def __init__(self, historical_data: Dict[int, List[List[int]]]):
        super().__init__()
        self.historical_data = historical_data
        self.refined_generator = None

    def _generate_candidates(self, target_series_id: int):
        # Only use data before target for pattern analysis
        training_data = {
            k: v for k, v in self.historical_data.items()
            if k < target_series_id
        }

        self.refined_generator = RefinedMandelPoolGenerator(
            frequency_weights=self.number_frequency_weights,
            pair_affinities=self.pair_affinities,
            historical_data=training_data
        )
        return self.refined_generator.generate_pool(
            size=self.CANDIDATES_TO_SCORE,
            seed=999
        )


def load_data():
    """Load expanded dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def evaluate_prediction(prediction: List[int], actual_events: List[List[int]]) -> Dict:
    """Evaluate prediction against actual events"""
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
    Walk-forward validation on last 6 series
    """
    print("="*70)
    print("WALK-FORWARD VALIDATION: ORIGINAL vs REFINED MANDEL")
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
    print(f"   Testing on: {validation_window[0]} to {validation_window[-1]}")
    print()

    # Results storage
    original_results = []
    refined_results = []

    # Configuration
    CANDIDATES = 2000
    SEED = 999

    print("="*70)
    print("STARTING VALIDATION")
    print("="*70)
    print()

    for series_id in validation_window:
        print(f"📍 Testing Series {series_id}")
        print("-" * 50)

        # Get training data (everything before this series)
        training_series = [s for s in all_series if s < series_id]

        print(f"   Training on {len(training_series)} series ({training_series[0]}-{training_series[-1]})")

        # Train Original Mandel model
        print("   Training Original Mandel model...")
        random.seed(SEED)
        original_model = OriginalMandelModel()
        original_model.CANDIDATES_TO_SCORE = CANDIDATES

        for train_id in training_series:
            original_model.learn_from_series(train_id, SERIES_DATA[train_id])

        # Predict
        original_pred = original_model.predict_best_combination(series_id)

        # Train Refined Mandel model
        print("   Training Refined Mandel model...")
        random.seed(SEED)
        refined_model = RefinedMandelModel(SERIES_DATA)
        refined_model.CANDIDATES_TO_SCORE = CANDIDATES

        for train_id in training_series:
            refined_model.learn_from_series(train_id, SERIES_DATA[train_id])

        # Predict
        refined_pred = refined_model.predict_best_combination(series_id)

        # Evaluate both
        actual_events = SERIES_DATA[series_id]
        original_eval = evaluate_prediction(original_pred, actual_events)
        refined_eval = evaluate_prediction(refined_pred, actual_events)

        # Store results
        original_results.append({
            "series_id": series_id,
            "prediction": sorted(original_pred),
            **original_eval
        })
        refined_results.append({
            "series_id": series_id,
            "prediction": sorted(refined_pred),
            **refined_eval
        })

        # Display
        print(f"   Original: {original_eval['best_match']:.1%} best, {original_eval['avg_match']:.1%} avg")
        print(f"   Refined:  {refined_eval['best_match']:.1%} best, {refined_eval['avg_match']:.1%} avg")

        diff = refined_eval['best_match'] - original_eval['best_match']
        if diff > 0:
            print(f"   ✅ Refined BETTER by {diff:.1%}")
        elif diff < 0:
            print(f"   ❌ Original better by {abs(diff):.1%}")
        else:
            print(f"   ➖ TIE")

        print()

    # Summary
    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print()

    original_avg_best = sum(r['best_match'] for r in original_results) / len(original_results)
    original_avg_avg = sum(r['avg_match'] for r in original_results) / len(original_results)

    refined_avg_best = sum(r['best_match'] for r in refined_results) / len(refined_results)
    refined_avg_avg = sum(r['avg_match'] for r in refined_results) / len(refined_results)

    print(f"Original Mandel:")
    print(f"  Average Best Match: {original_avg_best:.1%}")
    print(f"  Average Avg Match:  {original_avg_avg:.1%}")
    print()

    print(f"Refined Mandel:")
    print(f"  Average Best Match: {refined_avg_best:.1%}")
    print(f"  Average Avg Match:  {refined_avg_avg:.1%}")
    print()

    # Improvement
    improvement_best = refined_avg_best - original_avg_best
    improvement_avg = refined_avg_avg - original_avg_avg

    print("="*70)
    print("PERFORMANCE COMPARISON")
    print("="*70)
    print()

    if improvement_best > 0:
        print(f"✅ Refined is BETTER by {improvement_best:.1%} (best match)")
    elif improvement_best < 0:
        print(f"❌ Original is better by {abs(improvement_best):.1%} (best match)")
    else:
        print(f"➖ TIE on best match")

    if improvement_avg > 0:
        print(f"✅ Refined is BETTER by {improvement_avg:.1%} (average match)")
    elif improvement_avg < 0:
        print(f"❌ Original is better by {abs(improvement_avg):.1%} (average match)")
    else:
        print(f"➖ TIE on average match")

    print()

    # Series-by-series comparison
    print("="*70)
    print("SERIES-BY-SERIES BREAKDOWN")
    print("="*70)
    print()
    print(f"{'Series':<10} {'Original':<15} {'Refined':<15} {'Winner':<10}")
    print("-" * 60)

    refined_wins = 0
    original_wins = 0
    ties = 0

    for orig, ref in zip(original_results, refined_results):
        orig_score = orig['best_match']
        ref_score = ref['best_match']

        if ref_score > orig_score:
            winner = "Refined ✅"
            refined_wins += 1
        elif orig_score > ref_score:
            winner = "Original ✅"
            original_wins += 1
        else:
            winner = "Tie ➖"
            ties += 1

        print(f"{orig['series_id']:<10} {orig_score:.1%} ({orig['avg_match']:.1%})  "
              f"{ref_score:.1%} ({ref['avg_match']:.1%})  {winner:<10}")

    print()
    print(f"Final Tally: Original {original_wins} | Refined {refined_wins} | Ties {ties}")
    print()

    # Save results
    output = {
        "validation_window": validation_window,
        "original_results": original_results,
        "refined_results": refined_results,
        "summary": {
            "original_avg_best": original_avg_best,
            "original_avg_avg": original_avg_avg,
            "refined_avg_best": refined_avg_best,
            "refined_avg_avg": refined_avg_avg,
            "improvement_best": improvement_best,
            "improvement_avg": improvement_avg,
            "refined_wins": refined_wins,
            "original_wins": original_wins,
            "ties": ties
        }
    }

    with open('refined_mandel_validation_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("💾 Saved to: refined_mandel_validation_results.json")
    print()

    # Verdict
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()

    if refined_wins > original_wins:
        print("🏆 REFINED MANDEL is the WINNER!")
        print(f"   Won {refined_wins}/{len(validation_window)} series")
        print(f"   Performance gain: +{improvement_best:.1%}")
    elif original_wins > refined_wins:
        print("🏆 ORIGINAL MANDEL is the WINNER!")
        print(f"   Won {original_wins}/{len(validation_window)} series")
        print(f"   Performance gap: -{improvement_best:.1%}")
    else:
        print("➖ IT'S A TIE!")
        print(f"   Both methods performed equally")

    print()
    print("="*70)


if __name__ == "__main__":
    walk_forward_test()
