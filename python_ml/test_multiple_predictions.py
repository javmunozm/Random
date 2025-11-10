"""
Test Impact of Generating Multiple Predictions

Question: If we generate 3 predictions instead of 1, how does it impact results?

Strategy:
- Generate top 3 candidates (scored independently)
- Evaluate: Does the BEST of 3 perform better than just top 1?
- Coverage: How much solution space do we cover with 3 predictions?
"""

import sys
import json
import random
from typing import List, Dict, Tuple

sys.path.append('/home/user/Random/python_ml')

from true_learning_model import TrueLearningModel
from mandel_pool_generator import MandelPoolGenerator


class MandelModelFixed(TrueLearningModel):
    """FIXED Mandel model with cold/hot boost"""
    def __init__(self):
        super().__init__()
        self.mandel_generator = None

    def _generate_candidates(self, target_series_id: int):
        self.mandel_generator = MandelPoolGenerator(
            frequency_weights=self.number_frequency_weights,
            pair_affinities=self.pair_affinities,
            hybrid_cold_numbers=self.hybrid_cold_numbers,
            hybrid_hot_numbers=self.hybrid_hot_numbers
        )
        return self.mandel_generator.generate_pool(size=self.CANDIDATES_TO_SCORE, seed=999)

    def predict_top_n_combinations(self, target_series_id: int, n: int = 3) -> List[List[int]]:
        """Generate top N predictions"""
        candidates = self._generate_candidates(target_series_id)
        scored = [(c, self._calculate_score(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top N unique combinations
        return [combo for combo, score in scored[:n]]


def load_data():
    """Load expanded dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def evaluate_predictions(predictions: List[List[int]], actual_events: List[List[int]]) -> Dict:
    """
    Evaluate multiple predictions
    Returns best match across all predictions
    """
    all_results = []

    for i, pred in enumerate(predictions, 1):
        matches = []
        for event in actual_events:
            match_count = len(set(pred) & set(event))
            match_pct = match_count / 14.0
            matches.append(match_pct)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        all_results.append({
            "prediction_num": i,
            "best_match": best_match,
            "avg_match": avg_match,
            "matches": matches
        })

    # Find best across all predictions
    best_overall = max(all_results, key=lambda x: x['best_match'])

    return {
        "individual_results": all_results,
        "best_prediction_num": best_overall['prediction_num'],
        "best_match": best_overall['best_match'],
        "best_avg_match": best_overall['avg_match'],
        "top1_best": all_results[0]['best_match'],  # For comparison
        "improvement_over_top1": best_overall['best_match'] - all_results[0]['best_match']
    }


def test_multiple_predictions():
    """
    Test generating 3 predictions vs 1 prediction
    """
    print("="*70)
    print("MULTIPLE PREDICTIONS TEST (1 vs 3)")
    print("="*70)
    print()

    # Load data
    SERIES_DATA = load_data()
    all_series = sorted(SERIES_DATA.keys())

    print(f"📊 Dataset: {len(SERIES_DATA)} series")
    print()

    # Validation window
    validation_window = all_series[-6:]
    print(f"🎯 Testing on: {validation_window}")
    print()

    print("Strategy:")
    print("  - Generate top 3 predictions for each series")
    print("  - Evaluate if ANY of the 3 matches better than top 1")
    print("  - Measure improvement in coverage")
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

        # Training
        training_series = [s for s in all_series if s < series_id]

        random.seed(SEED)
        model = MandelModelFixed()
        model.CANDIDATES_TO_SCORE = 2000

        for train_id in training_series:
            model.learn_from_series(train_id, SERIES_DATA[train_id])

        # Generate TOP 3 predictions
        top3_predictions = model.predict_top_n_combinations(series_id, n=3)

        # Evaluate
        actual_events = SERIES_DATA[series_id]
        eval_result = evaluate_predictions(top3_predictions, actual_events)

        results.append({
            "series_id": series_id,
            "predictions": [sorted(p) for p in top3_predictions],
            **eval_result
        })

        # Display
        print(f"   Top 1 only: {eval_result['top1_best']:.1%}")
        print(f"   Best of 3:  {eval_result['best_match']:.1%} (prediction #{eval_result['best_prediction_num']})")

        if eval_result['improvement_over_top1'] > 0:
            print(f"   ✅ Improvement: +{eval_result['improvement_over_top1']:.1%}")
        elif eval_result['improvement_over_top1'] == 0:
            print(f"   ➖ Same (top 1 was already best)")
        else:
            print(f"   ⚠️  Worse (shouldn't happen)")

        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()

    # Calculate averages
    avg_top1 = sum(r['top1_best'] for r in results) / len(results)
    avg_best_of_3 = sum(r['best_match'] for r in results) / len(results)
    avg_improvement = avg_best_of_3 - avg_top1

    print(f"Strategy 1 (Top 1 only):  {avg_top1:.1%} average")
    print(f"Strategy 2 (Best of 3):   {avg_best_of_3:.1%} average")
    print()
    print(f"Improvement: {avg_improvement:+.1%}")
    print()

    # Count how many times each prediction rank won
    prediction_wins = {1: 0, 2: 0, 3: 0}
    for r in results:
        prediction_wins[r['best_prediction_num']] += 1

    print("Which prediction was best?")
    print(f"  Prediction #1 (top scored): {prediction_wins[1]}/6 times")
    print(f"  Prediction #2 (2nd best):   {prediction_wins[2]}/6 times")
    print(f"  Prediction #3 (3rd best):   {prediction_wins[3]}/6 times")
    print()

    # Overlap analysis
    print("="*70)
    print("COVERAGE ANALYSIS")
    print("="*70)
    print()

    for result in results:
        series_id = result['series_id']
        preds = result['predictions']

        # Calculate unique numbers across all 3 predictions
        all_numbers = set()
        for pred in preds:
            all_numbers.update(pred)

        # Calculate overlap
        overlap_12 = len(set(preds[0]) & set(preds[1]))
        overlap_13 = len(set(preds[0]) & set(preds[2]))
        overlap_23 = len(set(preds[1]) & set(preds[2]))

        print(f"Series {series_id}:")
        print(f"  Unique numbers covered: {len(all_numbers)}/25 ({len(all_numbers)/25*100:.0f}%)")
        print(f"  Overlap 1-2: {overlap_12}/14, 1-3: {overlap_13}/14, 2-3: {overlap_23}/14")
        print()

    # Verdict
    print("="*70)
    print("VERDICT")
    print("="*70)
    print()

    if avg_improvement > 0.02:  # More than 2% improvement
        print(f"✅ SIGNIFICANT IMPROVEMENT!")
        print(f"   Generating 3 predictions improves results by {avg_improvement:.1%}")
        print()
        print("Recommendation: Generate 3 predictions for Series 3147")
    elif avg_improvement > 0:
        print(f"⚠️  MODEST IMPROVEMENT")
        print(f"   Generating 3 predictions improves results by {avg_improvement:.1%}")
        print()
        print("Recommendation: Consider generating 3 predictions (small benefit)")
    else:
        print(f"➖ NO IMPROVEMENT")
        print(f"   Top 1 prediction is already optimal")
        print()
        print("Recommendation: Stick with single prediction")

    # Save results
    output = {
        "validation_window": validation_window,
        "results": results,
        "summary": {
            "avg_top1": avg_top1,
            "avg_best_of_3": avg_best_of_3,
            "improvement": avg_improvement,
            "prediction_wins": prediction_wins
        }
    }

    with open('multiple_predictions_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("💾 Saved to: multiple_predictions_results.json")
    print("="*70)


if __name__ == "__main__":
    test_multiple_predictions()
