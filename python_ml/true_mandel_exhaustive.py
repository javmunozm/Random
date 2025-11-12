#!/usr/bin/env python3
"""
TRUE MANDEL METHOD - Exhaustive Combination Generation
======================================================

Instead of sampling 10,000 random candidates, generate ALL 4,457,400 possible
combinations and let the ML model pick the highest-scoring one.

Strategy:
1. Generate ALL C(25,14) combinations (4,457,400 total)
2. Score each combination using the trained ML model
3. Return the combination with highest ML score

This guarantees we find the BEST combination according to the ML model,
not just a good one from a limited sample.

Computational Cost:
- Combinations: 4.4M to generate
- Scoring: ~0.0001s per combination = ~450 seconds total (~7.5 minutes)
- Memory: Can generate on-the-fly (iterator), minimal memory usage
"""

import sys
import time
from pathlib import Path
from itertools import combinations
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from true_learning_model import TrueLearningModel


class TrueMandel:
    """
    True Mandel Method: Exhaustive combination generation + ML scoring

    This is the REAL Mandel approach adapted for ML:
    - Stefan Mandel bought ALL combinations to guarantee win
    - We generate ALL combinations to guarantee finding ML's best pick
    """

    def __init__(self, model: TrueLearningModel):
        """
        Initialize with trained ML model

        Args:
            model: Trained TrueLearningModel instance
        """
        self.model = model
        self.total_combinations = 4457400  # C(25,14)

    def generate_all_combinations(self):
        """
        Generate ALL 4,457,400 possible combinations of 14 numbers from 25.

        Uses iterator to avoid storing all combinations in memory.

        Yields:
            List[int]: Each possible 14-number combination (sorted)
        """
        # All numbers from 1-25
        all_numbers = range(1, 26)

        # Generate all C(25,14) combinations
        for combo in combinations(all_numbers, 14):
            yield list(combo)

    def find_best_combination(self, show_progress: bool = True) -> dict:
        """
        Find the BEST combination by scoring ALL possibilities.

        This is computationally expensive (~7-10 minutes) but guarantees
        we find the absolute best combination according to the ML model.

        Args:
            show_progress: Whether to print progress updates

        Returns:
            dict with:
                - best_combination: The highest-scoring combination
                - best_score: Its ML score
                - total_scored: How many combinations were scored
                - time_taken: Computation time in seconds
        """
        print("=" * 80)
        print("TRUE MANDEL METHOD - Exhaustive Search")
        print("=" * 80)
        print(f"Total combinations to score: {self.total_combinations:,}")
        print(f"Estimated time: 7-10 minutes")
        print()

        start_time = time.time()

        best_combination = None
        best_score = -float('inf')
        count = 0

        # Progress tracking
        progress_interval = 100000  # Report every 100K combinations
        next_report = progress_interval

        # Score every combination
        for combination in self.generate_all_combinations():
            score = self.model._calculate_score(combination)

            if score > best_score:
                best_score = score
                best_combination = combination

                if show_progress:
                    elapsed = time.time() - start_time
                    print(f"🎯 New best at {count:,}: score={score:.2f}, combo={combination[:5]}...{combination[-3:]}, time={elapsed:.1f}s")

            count += 1

            # Progress report
            if show_progress and count >= next_report:
                elapsed = time.time() - start_time
                rate = count / elapsed
                remaining = (self.total_combinations - count) / rate
                progress_pct = (count / self.total_combinations) * 100

                print(f"Progress: {count:,}/{self.total_combinations:,} ({progress_pct:.1f}%) - "
                      f"{rate:.0f} combos/sec - ETA: {remaining/60:.1f} min")

                next_report += progress_interval

        end_time = time.time()
        time_taken = end_time - start_time

        print()
        print("=" * 80)
        print("EXHAUSTIVE SEARCH COMPLETE")
        print("=" * 80)
        print(f"Total scored: {count:,} combinations")
        print(f"Time taken: {time_taken:.1f} seconds ({time_taken/60:.2f} minutes)")
        print(f"Scoring rate: {count/time_taken:.0f} combinations/second")
        print()
        print(f"BEST COMBINATION: {best_combination}")
        print(f"ML SCORE: {best_score:.4f}")
        print("=" * 80)

        return {
            'best_combination': best_combination,
            'best_score': best_score,
            'total_scored': count,
            'time_taken': time_taken,
            'rate': count / time_taken
        }


def test_feasibility():
    """
    Test if exhaustive search is computationally feasible

    Score first 10,000 combinations to estimate total time
    """
    print("=" * 80)
    print("FEASIBILITY TEST - Scoring 10,000 combinations")
    print("=" * 80)

    # Create dummy model (weights don't matter for speed test)
    model = TrueLearningModel(seed=999)

    # Initialize some dummy weights so scoring works
    for i in range(1, 26):
        model.number_frequency_weights[i] = 1.0

    mandel = TrueMandel(model)

    start = time.time()
    count = 0

    for combo in mandel.generate_all_combinations():
        score = model._calculate_score(combo)
        count += 1

        if count >= 10000:
            break

    elapsed = time.time() - start
    rate = count / elapsed
    estimated_total = 4457400 / rate

    print(f"\nScored: {count:,} combinations")
    print(f"Time: {elapsed:.2f} seconds")
    print(f"Rate: {rate:.0f} combinations/second")
    print(f"\nESTIMATED TOTAL TIME: {estimated_total:.1f} seconds ({estimated_total/60:.2f} minutes)")
    print("=" * 80)

    return rate


if __name__ == '__main__':
    # Run feasibility test first
    rate = test_feasibility()

    print("\n" * 2)

    # Ask user if they want to proceed
    if rate < 1000:
        print("⚠️  WARNING: Scoring rate is slow. Full exhaustive search may take 1+ hours.")
        print("Consider optimizing the ML scoring function first.")
    else:
        print("✅ Scoring rate is acceptable. Full search estimated at ~7-10 minutes.")
        print("\nTo run full exhaustive search on a trained model, use:")
        print("  from true_mandel_exhaustive import TrueMandel")
        print("  mandel = TrueMandel(trained_model)")
        print("  result = mandel.find_best_combination()")
