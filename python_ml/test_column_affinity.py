"""
Test: Column Affinity Tracking

Hypothesis: Numbers in the same column tend to appear together
- Column 0 (X=0): 01-09
- Column 1 (X=1): 10-19
- Column 2 (X=2): 20-25

Enhancement: Track how often numbers from same column appear together,
and boost combinations that respect column affinity patterns.
"""

import sys
import json
import random
from typing import List, Dict, Tuple, Set
from collections import defaultdict

# Add parent directory to path
sys.path.append('/home/user/Random/python_ml')
from true_learning_model import TrueLearningModel

# Series data
SERIES_DATA = {
    3137: [[1,2,3,4,8,9,10,11,13,14,17,19,23,24],[1,2,5,8,9,10,11,13,14,17,19,22,23,25],[1,4,5,6,8,10,12,14,17,18,19,22,23,24],[1,3,4,5,8,9,11,14,15,18,19,22,23,24],[1,2,3,5,9,11,12,14,15,17,18,19,22,23],[2,4,6,8,9,10,12,14,16,18,19,22,23,24],[1,3,4,5,8,9,12,14,16,17,18,19,23,25]],
    3138: [[2,3,4,6,7,8,9,10,13,14,17,18,19,25],[1,2,5,6,7,10,11,12,13,14,16,20,23,24],[1,2,3,4,5,7,9,11,13,16,18,19,20,24],[2,5,6,7,8,9,10,11,13,15,16,17,18,25],[1,3,4,6,7,9,11,12,13,15,17,21,22,24],[1,2,3,4,6,7,9,12,14,15,18,19,21,23],[1,3,5,6,8,9,10,14,17,18,19,21,22,24]],
    3139: [[1,3,4,5,6,7,9,11,12,14,18,21,23,24],[1,3,4,6,8,9,11,13,14,17,19,20,22,24],[1,3,5,6,7,9,10,11,12,14,18,19,21,24],[3,4,5,6,7,10,11,12,13,15,17,18,19,24],[1,4,5,7,9,12,13,15,16,17,19,20,21,23],[2,3,4,6,7,9,10,11,12,14,17,18,21,23],[2,3,4,5,6,7,9,11,12,16,17,18,19,21]],
    3140: [[1,2,3,6,7,8,11,12,13,16,18,21,22,25],[1,2,4,7,8,11,12,13,14,15,18,23,24,25],[1,2,3,5,6,7,8,10,14,15,16,17,21,24],[1,2,3,6,7,10,11,12,15,18,19,21,24,25],[1,3,4,5,12,13,14,15,16,19,20,21,23,25],[1,2,4,5,6,7,9,12,14,17,18,21,22,23],[2,4,7,9,10,11,14,15,17,18,19,22,23,25]],
    3141: [[2,4,5,6,7,9,10,11,12,13,15,18,21,24],[2,3,4,5,7,9,11,12,13,15,16,19,21,24],[1,2,4,5,6,7,8,10,13,14,15,18,19,23],[1,3,5,6,7,8,9,10,11,14,15,17,20,24],[1,2,4,5,6,9,10,11,12,15,19,21,23,24],[1,3,4,6,7,8,10,11,13,15,16,18,21,24],[2,3,4,5,6,8,10,13,16,17,19,20,22,25]],
    3142: [[1,2,4,7,8,10,11,13,14,16,18,19,21,22],[3,4,5,6,7,10,11,12,14,15,16,18,20,22],[1,3,5,6,7,9,11,13,15,17,18,19,20,25],[1,2,4,5,6,7,10,12,15,16,18,21,22,24],[1,2,4,5,6,7,8,10,11,13,16,18,21,24],[1,2,3,5,7,9,10,11,13,14,15,18,20,24],[2,3,5,6,7,8,9,10,14,16,17,19,22,25]],
    3143: [[1,2,4,6,7,9,11,12,13,14,16,18,21,25],[1,2,3,5,7,9,11,12,13,14,16,18,21,25],[2,3,4,5,6,7,9,11,12,14,15,16,18,21],[1,2,3,4,5,7,9,11,12,14,16,18,21,25],[1,2,4,5,6,7,9,11,12,14,16,18,21,25],[1,2,3,4,6,7,9,11,12,14,16,18,21,25],[1,2,4,5,6,7,9,11,12,14,16,18,21,25]],
    3144: [[2,3,5,6,7,9,10,11,12,14,16,21,22,24],[1,3,5,6,7,8,9,10,11,14,16,18,19,21],[1,2,3,4,6,7,9,10,12,14,16,18,21,24],[2,3,5,6,7,9,10,11,12,14,16,17,18,21],[1,2,3,5,6,7,9,10,11,14,15,16,18,21],[1,2,3,5,6,7,9,10,11,14,16,18,21,24],[2,5,6,7,9,10,11,12,14,15,16,18,21,24]],
    3145: [[1,3,4,6,7,8,9,12,13,16,18,19,21,23],[1,2,3,4,6,9,13,14,15,16,17,19,22,24],[1,2,4,5,7,9,10,12,13,14,15,17,22,25],[1,2,3,5,6,7,9,10,11,13,14,17,18,22],[1,3,4,5,6,7,8,9,10,11,14,16,17,20],[1,2,4,5,6,7,8,9,10,14,15,16,17,24],[2,3,4,5,6,8,9,11,13,15,16,17,18,25]]
}

def get_column(num: int) -> int:
    """Get column index for a number"""
    if 1 <= num <= 9:
        return 0
    elif 10 <= num <= 19:
        return 1
    else:  # 20-25
        return 2

class ColumnAffinityModel(TrueLearningModel):
    """Enhanced model with column affinity tracking"""

    def __init__(self):
        super().__init__()
        self.column_affinity = defaultdict(lambda: defaultdict(float))
        self.column_affinity_multiplier = 5.0  # Bonus multiplier for same-column pairs

    def learn_from_series(self, series_id: int, events: List[List[int]]):
        """Enhanced learning with column affinity tracking"""
        # Call parent learn
        super().learn_from_series(series_id, events)

        # Track column affinity
        for event in events:
            event_cols = [get_column(n) for n in event]
            # Count how many numbers from each column appear
            col_counts = defaultdict(int)
            for col in event_cols:
                col_counts[col] += 1

            # Strengthen affinity between numbers in same column
            for i, num1 in enumerate(event):
                col1 = get_column(num1)
                for num2 in event[i+1:]:
                    col2 = get_column(num2)
                    if col1 == col2:  # Same column
                        self.column_affinity[num1][num2] += 0.1
                        self.column_affinity[num2][num1] += 0.1

    def score_candidate(self, candidate: List[int]) -> float:
        """Enhanced scoring with column affinity bonus"""
        # Get base score from parent
        score = super().score_candidate(candidate)

        # Add column affinity bonus
        column_bonus = 0.0
        for i, num1 in enumerate(candidate):
            for num2 in candidate[i+1:]:
                affinity = self.column_affinity[num1].get(num2, 0.0)
                column_bonus += affinity

        return score + (column_bonus * self.column_affinity_multiplier)

def test_column_affinity(recent_series_count=70, seed=999):
    """Test column affinity tracking"""
    random.seed(seed)

    # Load training data (exclude validation window)
    all_series = sorted(SERIES_DATA.keys())
    val_start_idx = len(all_series) - 8
    training_series = all_series[:val_start_idx]
    validation_series = all_series[val_start_idx:]

    # Filter to recent N series for training
    if len(training_series) > recent_series_count:
        training_series = training_series[-recent_series_count:]

    # Train model
    model = ColumnAffinityModel()
    for series_id in training_series:
        if series_id in SERIES_DATA:
            model.learn_from_series(series_id, SERIES_DATA[series_id])

    # Validate
    results = []
    for series_id in validation_series:
        actual_events = SERIES_DATA[series_id]
        prediction = model.predict_best_combination(series_id)

        # Calculate accuracy
        best_accuracy = max(len(set(prediction) & set(event)) / 14.0 for event in actual_events)
        avg_accuracy = sum(len(set(prediction) & set(event)) / 14.0 for event in actual_events) / 7.0

        results.append({
            "series_id": series_id,
            "best_accuracy": best_accuracy,
            "avg_accuracy": avg_accuracy,
            "prediction": prediction
        })

        # Learn from actual results
        model.learn_from_series(series_id, actual_events)

    # Calculate overall metrics
    overall_best_avg = sum(r["best_accuracy"] for r in results) / len(results)
    overall_avg = sum(r["avg_accuracy"] for r in results) / len(results)

    return {
        "overall_best_avg": overall_best_avg,
        "overall_avg": overall_avg,
        "results": results
    }

def main():
    """Run column affinity tests"""
    baseline_config = {"recent_series_count": 70, "seed": 999}

    print("Testing Column Affinity Tracking...")
    print("="*60)

    # Test 1: Baseline (70 series, 2k candidates)
    print("\n1. Baseline (70 series)...")
    baseline_result = test_column_affinity(**baseline_config)
    baseline_actual = baseline_result["overall_avg"]

    print(f"   Actual avg: {baseline_actual:.1%}")
    print(f"   Best match avg: {baseline_result['overall_best_avg']:.1%}")

    # Test 2: With different affinity multipliers
    multipliers = [2.0, 5.0, 10.0, 15.0]

    test_results = []
    for mult in multipliers:
        print(f"\n2. Column affinity multiplier = {mult}...")

        # Need to modify model temporarily
        random.seed(999)
        all_series = sorted(SERIES_DATA.keys())
        val_start_idx = len(all_series) - 8
        training_series = all_series[:val_start_idx][-70:]
        validation_series = all_series[val_start_idx:]

        model = ColumnAffinityModel()
        model.column_affinity_multiplier = mult

        for series_id in training_series:
            if series_id in SERIES_DATA:
                model.learn_from_series(series_id, SERIES_DATA[series_id])

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

            model.learn_from_series(series_id, actual_events)

        overall_avg = sum(r["avg_accuracy"] for r in results) / len(results)
        overall_best_avg = sum(r["best_accuracy"] for r in results) / len(results)

        test_results.append({
            "multiplier": mult,
            "actual_avg": overall_avg,
            "best_match_avg": overall_best_avg,
            "vs_baseline": overall_avg - baseline_actual
        })

        print(f"   Actual avg: {overall_avg:.1%}")
        print(f"   vs Baseline: {overall_avg - baseline_actual:+.1%}")

    # Find best
    best = max(test_results, key=lambda x: x["actual_avg"])

    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"Baseline: {baseline_actual:.1%}")
    print(f"Best config: multiplier={best['multiplier']}")
    print(f"Best actual avg: {best['actual_avg']:.1%}")
    print(f"Improvement: {best['vs_baseline']:+.1%}")

    if best['vs_baseline'] > 0.001:
        print(f"\n✅ SUCCESS: +{best['vs_baseline']*100:.1f}% improvement!")
    elif best['vs_baseline'] > -0.001:
        print(f"\n➖ NEUTRAL: No significant change")
    else:
        print(f"\n❌ FAILED: {best['vs_baseline']*100:.1f}% regression")

    # Save results
    output = {
        "baseline": baseline_actual,
        "test_results": test_results,
        "best": best
    }

    with open('test_column_affinity_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\nResults saved to test_column_affinity_results.json")

if __name__ == "__main__":
    main()
