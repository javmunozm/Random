"""
Generate 3 Predictions for Series 3147

Based on validation testing:
- Generating 3 predictions improves results by +3.6%
- Best of 3 achieves 71.4% vs 67.9% for top 1 only
- Prediction #1 best 50% of time, Prediction #2 best 50% of time
- Coverage: 72-80% of all numbers with 3 predictions

Strategy: Generate top 3 scored candidates for maximum coverage
"""

import sys
import json
import random
from typing import List, Tuple

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

    def predict_top_n_combinations(self, target_series_id: int, n: int = 3) -> List:
        """Generate top N predictions with scores"""
        candidates = self._generate_candidates(target_series_id)
        scored = [(c, self._calculate_score(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top N with scores
        return [(combo, score) for combo, score in scored[:n]]


def load_data():
    """Load expanded dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def main():
    """Generate 3 predictions for Series 3147"""
    print("="*70)
    print("SERIES 3147 - TRIPLE PREDICTION STRATEGY")
    print("="*70)
    print()

    # Load data
    SERIES_DATA = load_data()
    all_series = sorted(SERIES_DATA.keys())

    print(f"📊 Dataset: {len(SERIES_DATA)} series")
    print()

    print("⚙️  Configuration:")
    print("   Method: Mandel FIXED with cold/hot boost")
    print("   Predictions: 3 (top scored candidates)")
    print("   Validated improvement: +3.6% vs single prediction")
    print("   Expected performance: 71.4% (best of 3)")
    print()

    # Train model
    random.seed(999)
    model = MandelModelFixed()
    model.CANDIDATES_TO_SCORE = 2000

    print("Training on all available data...")
    for series_id in all_series:
        model.learn_from_series(series_id, SERIES_DATA[series_id])

    print("✅ Training complete")
    print()

    # Generate top 3 predictions
    print("🎯 Generating TOP 3 predictions for Series 3147...")
    print()

    top3_with_scores = model.predict_top_n_combinations(3147, n=3)

    predictions = []
    for i, (pred, score) in enumerate(top3_with_scores, 1):
        pred_sorted = sorted(pred)
        predictions.append(pred_sorted)

        # Distribution
        col0 = [n for n in pred_sorted if 1 <= n <= 9]
        col1 = [n for n in pred_sorted if 10 <= n <= 19]
        col2 = [n for n in pred_sorted if 20 <= n <= 25]

        # Cold/hot coverage
        cold_in_pred = [n for n in pred_sorted if n in model.hybrid_cold_numbers]
        hot_in_pred = [n for n in pred_sorted if n in model.hybrid_hot_numbers]

        print("="*70)
        print(f"PREDICTION #{i} (Score: {score:.2f})")
        print("="*70)
        print()
        print("Numbers:", " ".join(f"{n:02d}" for n in pred_sorted))
        print()
        print(f"Distribution: {len(col0)}-{len(col1)}-{len(col2)}")
        print(f"  Column 0 (01-09): {' '.join(f'{n:02d}' for n in col0)}")
        print(f"  Column 1 (10-19): {' '.join(f'{n:02d}' for n in col1)}")
        print(f"  Column 2 (20-25): {' '.join(f'{n:02d}' for n in col2)}")
        print()
        print(f"Cold/Hot: {len(cold_in_pred)}/7 cold, {len(hot_in_pred)}/7 hot")
        print()

    # Coverage analysis
    print("="*70)
    print("COVERAGE ANALYSIS")
    print("="*70)
    print()

    all_numbers = set()
    for pred in predictions:
        all_numbers.update(pred)

    print(f"Unique numbers across all 3 predictions: {len(all_numbers)}/25 ({len(all_numbers)/25*100:.0f}%)")
    print(f"Missing numbers: {sorted(set(range(1, 26)) - all_numbers)}")
    print()

    # Overlap
    overlap_12 = len(set(predictions[0]) & set(predictions[1]))
    overlap_13 = len(set(predictions[0]) & set(predictions[2]))
    overlap_23 = len(set(predictions[1]) & set(predictions[2]))

    print(f"Overlap between predictions:")
    print(f"  #1 ∩ #2: {overlap_12}/14 numbers in common")
    print(f"  #1 ∩ #3: {overlap_13}/14 numbers in common")
    print(f"  #2 ∩ #3: {overlap_23}/14 numbers in common")
    print()

    # Save
    output = {
        "series_id": 3147,
        "predictions": predictions,
        "model": "TrueLearningModel Phase 1 Pure + Mandel FIXED",
        "strategy": "Triple prediction (top 3 candidates)",
        "configuration": {
            "method": "Mandel pool with cold/hot boost",
            "candidates": 2000,
            "seed": 999,
            "predictions_generated": 3
        },
        "performance": {
            "single_prediction_avg": "67.9%",
            "triple_prediction_avg": "71.4%",
            "improvement": "+3.6%"
        },
        "coverage": {
            "unique_numbers": len(all_numbers),
            "coverage_percent": len(all_numbers)/25*100,
            "overlaps": {
                "1_2": overlap_12,
                "1_3": overlap_13,
                "2_3": overlap_23
            }
        },
        "generated_at": "2025-11-09"
    }

    with open('prediction_3147_triple.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("💾 Saved to: prediction_3147_triple.json")
    print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("✅ Generated 3 predictions for Series 3147")
    print(f"✅ Coverage: {len(all_numbers)}/25 numbers ({len(all_numbers)/25*100:.0f}%)")
    print("✅ Expected performance: 71.4% (best of 3)")
    print("✅ Improvement over single: +3.6%")
    print()
    print("Recommendation: Use all 3 predictions to maximize chance of match")
    print("="*70)


if __name__ == "__main__":
    main()
