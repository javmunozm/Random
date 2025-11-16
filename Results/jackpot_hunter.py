#!/usr/bin/env python3
"""
Jackpot Hunter: Find perfect 14/14 matches for series 3141-3148

Strategy: Try different random seeds until hitting a perfect match
"""

import random
from typing import List, Tuple, Dict

# Actual results for series 3141-3148
ACTUAL_RESULTS: Dict[int, List[List[int]]] = {
    3141: [
        [1, 2, 3, 6, 7, 9, 10, 12, 13, 14, 16, 21, 24, 25],
        [1, 2, 4, 5, 8, 9, 11, 13, 14, 19, 22, 23, 24, 25],
        [1, 3, 4, 5, 6, 9, 10, 11, 12, 14, 15, 16, 21, 24],
        [2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 17, 18, 20, 21],
        [2, 5, 6, 7, 8, 10, 13, 14, 16, 18, 19, 20, 21, 25],
        [1, 2, 4, 5, 6, 7, 9, 11, 15, 16, 17, 19, 20, 23],
        [1, 2, 5, 6, 7, 11, 12, 15, 16, 18, 19, 20, 21, 23],
    ],
    3142: [
        [2, 3, 4, 6, 8, 9, 10, 11, 13, 15, 16, 17, 21, 23],
        [1, 2, 5, 6, 7, 8, 9, 11, 13, 17, 18, 19, 20, 24],
        [1, 3, 5, 6, 7, 9, 10, 12, 14, 16, 17, 18, 19, 24],
        [1, 3, 5, 6, 7, 8, 9, 10, 11, 13, 15, 16, 19, 23],
        [1, 2, 3, 4, 5, 8, 10, 13, 15, 17, 19, 21, 23, 24],
        [1, 3, 4, 5, 6, 8, 9, 10, 12, 13, 15, 16, 17, 19],
        [2, 4, 7, 8, 9, 10, 12, 15, 17, 19, 20, 21, 24, 25],
    ],
    3143: [
        [1, 2, 3, 4, 6, 7, 9, 11, 13, 14, 15, 19, 21, 23],
        [1, 3, 4, 5, 6, 8, 12, 13, 15, 16, 17, 18, 19, 21],
        [1, 2, 5, 6, 7, 8, 10, 13, 14, 16, 18, 19, 22, 25],
        [2, 3, 4, 6, 7, 8, 10, 11, 14, 15, 17, 20, 21, 25],
        [1, 3, 4, 6, 9, 10, 12, 13, 15, 16, 19, 22, 23, 25],
        [1, 2, 4, 5, 6, 8, 9, 12, 13, 15, 17, 21, 23, 25],
        [4, 5, 6, 7, 8, 10, 11, 13, 17, 19, 20, 22, 23, 24],
    ],
    3144: [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
    ],
    3145: [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
    ],
    3146: [
        [1, 2, 3, 7, 8, 10, 11, 12, 15, 16, 19, 21, 22, 23],
        [2, 4, 5, 6, 7, 8, 9, 13, 15, 17, 20, 21, 22, 24],
        [2, 3, 4, 5, 6, 8, 9, 10, 12, 14, 17, 18, 21, 25],
        [1, 2, 3, 4, 6, 7, 9, 10, 14, 15, 17, 19, 20, 25],
        [3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 19, 20, 21],
        [1, 2, 3, 5, 6, 9, 10, 11, 15, 18, 19, 20, 21, 24],
        [1, 2, 3, 5, 8, 10, 13, 14, 15, 16, 17, 18, 20, 25],
    ],
    3147: [
        [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
        [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
        [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
        [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
        [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
        [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
        [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
    ],
    3148: [
        [1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 19, 22, 23, 25],
        [2, 3, 6, 7, 10, 12, 13, 14, 15, 16, 17, 19, 21, 23],
        [1, 2, 4, 5, 6, 8, 10, 12, 14, 15, 17, 18, 20, 22],
        [2, 3, 4, 5, 8, 10, 12, 13, 14, 15, 18, 20, 21, 25],
        [3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 19, 20, 21, 24],
        [2, 3, 4, 5, 9, 10, 12, 14, 15, 16, 17, 18, 22, 25],
        [1, 4, 6, 7, 9, 11, 12, 14, 16, 19, 20, 21, 23, 25],
    ],
}


def generate_random_prediction(seed: int) -> List[int]:
    """Generate a random combination of 14 numbers from 1-25"""
    rnd = random.Random(seed)
    numbers = list(range(1, 26))
    selected = rnd.sample(numbers, 14)
    return sorted(selected)


def check_jackpot(prediction: List[int], actual_events: List[List[int]]) -> bool:
    """Check if prediction matches any event perfectly (14/14)"""
    for event in actual_events:
        if prediction == event:
            return True
    return False


def hunt_jackpot(series_id: int) -> Tuple[int, int, List[int]]:
    """Hunt for a perfect match using different seeds"""
    actual_events = ACTUAL_RESULTS[series_id]
    attempts = 0

    print(f"  Hunting jackpot", end="", flush=True)

    while attempts < 10_000_000:  # Safety limit
        attempts += 1
        seed = attempts

        prediction = generate_random_prediction(seed)

        if check_jackpot(prediction, actual_events):
            return (attempts, seed, prediction)

        # Progress indicator
        if attempts % 10000 == 0:
            print(".", end="", flush=True)

    print(" TIMEOUT!")
    return (attempts, -1, prediction)


def main():
    print("=" * 80)
    print("JACKPOT HUNTER: Finding Perfect 14/14 Matches")
    print("=" * 80)
    print()
    print("Testing series 3141-3148")
    print("Strategy: Try different random seeds until hitting 14/14 match")
    print()

    results = []

    for series_id in sorted(ACTUAL_RESULTS.keys()):
        print(f"Series {series_id}:")
        attempts, seed, prediction = hunt_jackpot(series_id)

        if seed != -1:
            results.append((series_id, attempts, seed, prediction))
            print(f" JACKPOT! (Attempts: {attempts:,}, Seed: {seed})")
            print(f"  Prediction: {' '.join(f'{n:02d}' for n in prediction)}")
        else:
            print(f"  No jackpot found after {attempts:,} attempts")
        print()

    # Summary Report
    if results:
        print("=" * 80)
        print("JACKPOT SUMMARY REPORT")
        print("=" * 80)
        print()
        print(f"{'Series':<10} {'Attempts':<15} {'Seed':<12} {'Prediction'}")
        print("-" * 80)

        for series_id, attempts, seed, prediction in results:
            pred_str = ' '.join(f'{n:02d}' for n in prediction)
            print(f"{series_id:<10} {attempts:<15,} {seed:<12} {pred_str}")

        print()
        total_attempts = sum(r[1] for r in results)
        print(f"Total attempts across all series: {total_attempts:,}")
        print(f"Average attempts per series: {total_attempts / len(results):,.1f}")
        print(f"Min attempts: {min(r[1] for r in results):,}")
        print(f"Max attempts: {max(r[1] for r in results):,}")
        print()

        # Calculate theoretical probability
        from math import comb
        total_combinations = comb(25, 14)
        print(f"Theoretical probability of jackpot: 1 in {total_combinations:,}")
        print(f"Expected attempts per jackpot: {total_combinations/7:,.0f} (with 7 events)")
    else:
        print("No jackpots found!")

    print()


if __name__ == "__main__":
    main()
