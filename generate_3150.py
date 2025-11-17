#!/usr/bin/env python3
"""
Generate Series 3150 predictions using two methods:
1. ML-based weighted prediction (frequency-based)
2. Random prediction at seed 636,771 (theoretical average attempts for jackpot)

Updated to include Series 3149 training data
"""

import random
from collections import Counter
from typing import List, Dict

# Actual results for Series 3141-3149 (training data - NOW INCLUDES 3149)
ACTUAL_RESULTS = {
    3141: [
        [1, 2, 3, 4, 5, 7, 9, 10, 13, 15, 16, 18, 21, 25],
        [1, 4, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 21, 24],
        [1, 3, 6, 7, 8, 10, 13, 14, 15, 17, 19, 20, 22, 25],
        [2, 3, 5, 6, 7, 9, 10, 11, 12, 14, 17, 19, 23, 24],
        [1, 3, 4, 6, 8, 9, 10, 11, 14, 15, 19, 21, 22, 24],
        [2, 4, 5, 6, 9, 11, 12, 13, 15, 17, 19, 20, 22, 24],
        [2, 3, 4, 5, 7, 8, 10, 11, 13, 15, 18, 22, 23, 25]
    ],
    3142: [
        [1, 3, 4, 5, 8, 9, 10, 12, 13, 14, 17, 21, 22, 24],
        [1, 2, 5, 7, 8, 11, 12, 13, 15, 16, 17, 19, 21, 25],
        [2, 3, 6, 7, 10, 11, 13, 14, 15, 16, 18, 19, 22, 24],
        [1, 2, 6, 7, 8, 11, 13, 14, 15, 17, 19, 20, 21, 22],
        [1, 2, 5, 6, 8, 9, 11, 13, 14, 16, 18, 20, 24, 25],
        [2, 3, 4, 6, 7, 8, 9, 12, 13, 16, 20, 21, 22, 25],
        [2, 3, 4, 8, 10, 11, 12, 14, 16, 17, 18, 19, 24, 25]
    ],
    3143: [
        [1, 2, 5, 6, 7, 9, 11, 13, 14, 16, 18, 21, 23, 24],
        [1, 2, 5, 7, 8, 9, 10, 13, 14, 15, 18, 19, 20, 24],
        [3, 5, 7, 8, 9, 11, 12, 15, 17, 18, 19, 21, 23, 25],
        [2, 4, 5, 6, 8, 10, 11, 12, 13, 15, 18, 20, 21, 23],
        [1, 2, 4, 5, 7, 8, 9, 11, 13, 15, 17, 21, 23, 24],
        [2, 4, 5, 6, 7, 9, 11, 12, 14, 16, 17, 19, 20, 25],
        [2, 6, 7, 8, 9, 10, 12, 13, 15, 16, 18, 19, 21, 25]
    ],
    3144: [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25]
    ],
    3145: [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21]
    ],
    3146: [
        [2, 3, 4, 6, 7, 10, 11, 12, 15, 16, 18, 20, 21, 22],
        [2, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 18, 19, 25],
        [1, 2, 3, 4, 5, 6, 10, 13, 14, 16, 17, 18, 21, 25],
        [1, 2, 3, 6, 7, 8, 9, 11, 15, 17, 18, 19, 20, 25],
        [1, 3, 4, 5, 7, 9, 12, 13, 14, 15, 18, 21, 22, 25],
        [1, 2, 5, 6, 7, 8, 9, 11, 13, 15, 16, 18, 19, 21],
        [2, 6, 7, 8, 9, 10, 12, 13, 15, 16, 18, 19, 22, 25]
    ],
    3147: [
        [3, 4, 5, 6, 8, 10, 11, 13, 14, 15, 18, 19, 22, 24],
        [1, 4, 5, 6, 7, 8, 10, 11, 12, 14, 16, 17, 22, 24],
        [1, 2, 3, 7, 8, 9, 11, 12, 14, 16, 17, 19, 21, 23],
        [2, 3, 5, 7, 8, 12, 13, 14, 15, 17, 18, 19, 21, 23],
        [2, 3, 4, 5, 7, 9, 10, 11, 12, 14, 16, 19, 21, 22],
        [4, 5, 7, 8, 11, 12, 13, 14, 15, 16, 18, 21, 23, 24],
        [1, 3, 4, 5, 6, 9, 10, 12, 13, 15, 17, 19, 20, 22]
    ],
    3148: [
        [2, 3, 4, 5, 7, 8, 11, 13, 15, 17, 18, 19, 21, 23],
        [1, 2, 5, 6, 8, 9, 12, 13, 14, 15, 17, 20, 23, 25],
        [1, 2, 3, 5, 6, 8, 9, 10, 14, 16, 17, 19, 24, 25],
        [1, 3, 4, 7, 9, 10, 11, 12, 15, 17, 18, 22, 23, 25],
        [1, 2, 4, 6, 7, 10, 11, 12, 13, 15, 18, 19, 22, 25],
        [4, 5, 6, 8, 10, 11, 12, 14, 15, 16, 17, 19, 22, 25],
        [2, 6, 7, 8, 9, 10, 12, 13, 15, 16, 18, 19, 22, 25]
    ],
    3149: [
        [2, 3, 5, 6, 7, 8, 10, 12, 17, 19, 20, 22, 23, 25],
        [2, 3, 5, 6, 8, 10, 14, 15, 16, 17, 18, 23, 24, 25],
        [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 18, 19, 21, 22],
        [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 23, 24],
        [3, 4, 5, 6, 8, 9, 11, 12, 16, 17, 20, 21, 22, 24],
        [1, 2, 3, 5, 6, 8, 11, 13, 14, 19, 20, 21, 24, 25],
        [3, 4, 7, 9, 10, 11, 13, 15, 18, 19, 20, 21, 22, 25]
    ]
}


def calculate_frequency_weights(data: Dict[int, List[List[int]]]) -> Dict[int, float]:
    """Calculate frequency-based weights for each number."""
    frequency = Counter()
    for series_data in data.values():
        for event in series_data:
            for num in event:
                frequency[num] += 1

    total = sum(frequency.values())
    weights = {num: (frequency.get(num, 0) / total) for num in range(1, 26)}
    return weights


def generate_weighted_prediction(weights: Dict[int, float], seed: int = 888) -> List[int]:
    """Generate prediction using weighted random selection."""
    random.seed(seed)
    numbers = list(range(1, 26))
    number_weights = [weights[num] for num in numbers]

    prediction = []
    available = numbers.copy()
    available_weights = number_weights.copy()

    for _ in range(14):
        chosen = random.choices(available, weights=available_weights, k=1)[0]
        prediction.append(chosen)

        idx = available.index(chosen)
        available.pop(idx)
        available_weights.pop(idx)

    return sorted(prediction)


def generate_random_prediction(seed: int) -> List[int]:
    """Generate prediction using pure random selection."""
    random.seed(seed)
    numbers = list(range(1, 26))
    prediction = random.sample(numbers, 14)
    return sorted(prediction)


def main():
    print("=" * 80)
    print("SERIES 3150 PREDICTIONS")
    print("Training data: Series 3141-3149 (9 series)")
    print("=" * 80)
    print()

    # Calculate weights from training data
    weights = calculate_frequency_weights(ACTUAL_RESULTS)

    # Method 1: ML-based weighted prediction
    ml_prediction = generate_weighted_prediction(weights, seed=888)

    # Method 2: Random prediction at seed 636771
    random_prediction = generate_random_prediction(636771)

    print("Method 1: ML-based Weighted Prediction (Frequency-based)")
    print(f"Prediction: {' '.join(f'{num:02d}' for num in ml_prediction)}")
    print()

    print("Method 2: Random Prediction at Seed #636,771")
    print(f"Prediction: {' '.join(f'{num:02d}' for num in random_prediction)}")
    print()

    # Compare predictions
    overlap = set(ml_prediction) & set(random_prediction)
    print("=" * 80)
    print(f"Overlap: {len(overlap)}/14 numbers in common")
    print(f"Common numbers: {' '.join(f'{num:02d}' for num in sorted(overlap))}")
    print("=" * 80)
    print()

    # Show frequency weights (top 10)
    print("Top 10 Most Frequent Numbers in Training Data:")
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    for i, (num, weight) in enumerate(sorted_weights[:10], 1):
        print(f"  {i:2d}. Number {num:02d}: {weight:.4f}")
    print()

    # Save results
    import json
    results = {
        "series_id": 3150,
        "training_series": list(ACTUAL_RESULTS.keys()),
        "training_count": len(ACTUAL_RESULTS),
        "predictions": {
            "ml_weighted": ml_prediction,
            "random_636771": random_prediction
        },
        "overlap": len(overlap),
        "common_numbers": sorted(list(overlap)),
        "top_weights": {num: weight for num, weight in sorted_weights[:10]}
    }

    with open("Results/predictions_3150.json", "w") as f:
        json.dump(results, f, indent=2)

    print("📁 Saved to: Results/predictions_3150.json")


if __name__ == "__main__":
    main()
