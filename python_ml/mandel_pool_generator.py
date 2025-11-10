"""
Mandel Method - Smart Candidate Pool Generation

Instead of random candidates, generate combinations using:
1. Balanced distribution (columns balanced)
2. Frequency weighting (favor common numbers)
3. Pattern filtering (exclude unlikely patterns)
4. Diversity guarantee (varied combinations)
"""

import random
from typing import List, Dict, Tuple, Set
from collections import defaultdict

class MandelPoolGenerator:
    """Generate candidate pools using Mandel principles + ML weights"""

    def __init__(self, frequency_weights: Dict[int, float] = None,
                 pair_affinities: Dict[Tuple[int, int], float] = None,
                 hybrid_cold_numbers: Set[int] = None,
                 hybrid_hot_numbers: Set[int] = None):
        self.frequency_weights = frequency_weights or {}
        self.pair_affinities = pair_affinities or {}
        self.hybrid_cold_numbers = hybrid_cold_numbers or set()
        self.hybrid_hot_numbers = hybrid_hot_numbers or set()

        # Normalize frequency weights for probability distribution
        if self.frequency_weights:
            total = sum(self.frequency_weights.values())
            self.freq_probs = {k: v/total for k, v in self.frequency_weights.items()}
        else:
            # Uniform if no weights provided
            self.freq_probs = {i: 1/25 for i in range(1, 26)}

    def generate_pool(self, size: int, seed: int = None) -> List[List[int]]:
        """
        Generate pool of candidates using Mandel method

        Args:
            size: Number of candidates to generate
            seed: Random seed for reproducibility

        Returns:
            List of candidate combinations (each is list of 14 numbers)
        """
        if seed is not None:
            random.seed(seed)

        candidates = []
        seen = set()  # Avoid duplicates
        attempts = 0
        max_attempts = size * 10  # Prevent infinite loop

        while len(candidates) < size and attempts < max_attempts:
            candidate = self._generate_balanced_candidate()

            # Convert to tuple for set membership
            cand_tuple = tuple(sorted(candidate))

            if self._is_valid_pattern(candidate) and cand_tuple not in seen:
                candidates.append(candidate)
                seen.add(cand_tuple)

            attempts += 1

        if len(candidates) < size:
            print(f"Warning: Only generated {len(candidates)}/{size} valid candidates")

        return candidates

    def _generate_balanced_candidate(self) -> List[int]:
        """
        Generate one candidate with balanced distribution
        """
        # Target distribution across columns
        # Column 0 (01-09): 5-7 numbers (9 available, ~56% selection rate)
        # Column 1 (10-19): 4-6 numbers (10 available, ~50% selection rate)
        # Column 2 (20-25): 2-4 numbers (6 available, ~50% selection rate)

        target_col0 = random.randint(5, 7)
        target_col1 = random.randint(4, 6)
        target_col2 = 14 - target_col0 - target_col1

        # Ensure valid distribution
        if target_col2 < 1 or target_col2 > 5:
            target_col2 = max(1, min(5, target_col2))
            target_col1 = 14 - target_col0 - target_col2

        # Generate from each column with frequency weighting
        col0_nums = self._weighted_sample(range(1, 10), target_col0)
        col1_nums = self._weighted_sample(range(10, 20), target_col1)
        col2_nums = self._weighted_sample(range(20, 26), target_col2)

        candidate = col0_nums + col1_nums + col2_nums

        # Shuffle to remove positional bias
        random.shuffle(candidate)

        return sorted(candidate)

    def _weighted_sample(self, population: range, k: int) -> List[int]:
        """
        Sample k numbers from population using frequency weights + cold/hot boost
        """
        # Get base frequency weights for this population
        weights = [self.freq_probs.get(n, 1/25) for n in population]

        # Apply 50x boost to cold/hot numbers (CRITICAL FIX!)
        for i, n in enumerate(population):
            if n in self.hybrid_cold_numbers or n in self.hybrid_hot_numbers:
                weights[i] *= 50.0  # Match C# model's massive boost

        # Weighted random sampling without replacement
        selected = []
        pop_list = list(population)
        weights_list = list(weights)

        for _ in range(min(k, len(pop_list))):
            # Normalize weights
            total = sum(weights_list)
            if total == 0:
                # Fallback to uniform if all weights are zero
                weights_list = [1] * len(weights_list)
                total = len(weights_list)

            probs = [w/total for w in weights_list]

            # Select one
            choice = random.choices(pop_list, weights=probs, k=1)[0]
            selected.append(choice)

            # Remove from population
            idx = pop_list.index(choice)
            pop_list.pop(idx)
            weights_list.pop(idx)

        return selected

    def _is_valid_pattern(self, candidate: List[int]) -> bool:
        """
        Validate candidate has reasonable patterns

        Checks:
        - Distribution across columns (must have from all 3)
        - Not all consecutive
        - Sum in reasonable range
        - Even/odd balance
        - Not too many gaps
        """
        if len(candidate) != 14:
            return False

        # Column distribution
        col0 = [n for n in candidate if 1 <= n <= 9]
        col1 = [n for n in candidate if 10 <= n <= 19]
        col2 = [n for n in candidate if 20 <= n <= 25]

        # Must have numbers from all columns
        if len(col0) == 0 or len(col1) == 0 or len(col2) == 0:
            return False

        # Column extremes (not too skewed)
        if len(col0) > 9 or len(col1) > 9 or len(col2) > 5:
            return False

        # Check for all consecutive
        sorted_cand = sorted(candidate)
        consecutive_count = 0
        for i in range(len(sorted_cand) - 1):
            if sorted_cand[i+1] - sorted_cand[i] == 1:
                consecutive_count += 1

        # Reject if more than 10 consecutive pairs (nearly all consecutive)
        if consecutive_count > 10:
            return False

        # Sum range check
        # Expected sum for 14 numbers from 1-25: ~182
        # Allow ±35 range (more lenient)
        total = sum(candidate)
        if total < 145 or total > 220:
            return False

        # Even/odd balance
        evens = sum(1 for n in candidate if n % 2 == 0)
        # Should have 4-10 evens (not all even or all odd)
        if evens < 3 or evens > 11:
            return False

        # Gap analysis - reject if too many large gaps
        gaps = [sorted_cand[i+1] - sorted_cand[i] for i in range(len(sorted_cand)-1)]
        large_gaps = sum(1 for g in gaps if g > 3)
        # Reject if more than half the gaps are large
        if large_gaps > 7:
            return False

        return True

    def get_pool_statistics(self, pool: List[List[int]]) -> Dict:
        """
        Analyze pool diversity and quality
        """
        if not pool:
            return {}

        # Distribution statistics
        col0_counts = []
        col1_counts = []
        col2_counts = []
        sums = []
        even_counts = []

        for cand in pool:
            col0 = sum(1 for n in cand if 1 <= n <= 9)
            col1 = sum(1 for n in cand if 10 <= n <= 19)
            col2 = sum(1 for n in cand if 20 <= n <= 25)

            col0_counts.append(col0)
            col1_counts.append(col1)
            col2_counts.append(col2)
            sums.append(sum(cand))
            even_counts.append(sum(1 for n in cand if n % 2 == 0))

        # Number frequency in pool
        num_freq = defaultdict(int)
        for cand in pool:
            for num in cand:
                num_freq[num] += 1

        return {
            "pool_size": len(pool),
            "avg_col0": sum(col0_counts) / len(pool),
            "avg_col1": sum(col1_counts) / len(pool),
            "avg_col2": sum(col2_counts) / len(pool),
            "avg_sum": sum(sums) / len(pool),
            "avg_evens": sum(even_counts) / len(pool),
            "number_coverage": len(num_freq),  # How many different numbers appear
            "number_frequency": dict(num_freq),
            "unique_combinations": len(pool)  # Should equal pool_size
        }


def compare_pool_generators(size: int = 2000, seed: int = 999):
    """
    Compare random pool vs Mandel pool
    """
    print("="*70)
    print(f"POOL GENERATION COMPARISON (size={size}, seed={seed})")
    print("="*70)
    print()

    # Generate random pool (current method)
    print("1. Generating RANDOM pool...")
    random.seed(seed)
    random_pool = []
    for _ in range(size):
        cand = sorted(random.sample(range(1, 26), 14))
        random_pool.append(cand)

    print(f"   Generated {len(random_pool)} random candidates")

    # Generate Mandel pool
    print("\n2. Generating MANDEL pool...")

    # Use uniform weights for fair comparison (no frequency bias yet)
    mandel_gen = MandelPoolGenerator()
    mandel_pool = mandel_gen.generate_pool(size, seed=seed)

    print(f"   Generated {len(mandel_pool)} Mandel candidates")

    # Analyze both
    print("\n" + "="*70)
    print("STATISTICS COMPARISON:")
    print("="*70)

    random_stats = mandel_gen.get_pool_statistics(random_pool)
    mandel_stats = mandel_gen.get_pool_statistics(mandel_pool)

    print(f"\nRANDOM Pool:")
    print(f"  Avg Col 0 (01-09): {random_stats['avg_col0']:.2f}")
    print(f"  Avg Col 1 (10-19): {random_stats['avg_col1']:.2f}")
    print(f"  Avg Col 2 (20-25): {random_stats['avg_col2']:.2f}")
    print(f"  Avg Sum: {random_stats['avg_sum']:.1f}")
    print(f"  Avg Evens: {random_stats['avg_evens']:.2f}")
    print(f"  Number Coverage: {random_stats['number_coverage']}/25")

    print(f"\nMANDEL Pool:")
    print(f"  Avg Col 0 (01-09): {mandel_stats['avg_col0']:.2f}")
    print(f"  Avg Col 1 (10-19): {mandel_stats['avg_col1']:.2f}")
    print(f"  Avg Col 2 (20-25): {mandel_stats['avg_col2']:.2f}")
    print(f"  Avg Sum: {mandel_stats['avg_sum']:.1f}")
    print(f"  Avg Evens: {mandel_stats['avg_evens']:.2f}")
    print(f"  Number Coverage: {mandel_stats['number_coverage']}/25")

    print("\n" + "="*70)
    print("QUALITY METRICS:")
    print("="*70)

    # Count valid patterns in random pool
    valid_random = sum(1 for cand in random_pool if mandel_gen._is_valid_pattern(cand))
    valid_mandel = sum(1 for cand in mandel_pool if mandel_gen._is_valid_pattern(cand))

    print(f"\nValid patterns (pass Mandel filters):")
    print(f"  Random: {valid_random}/{len(random_pool)} ({valid_random/len(random_pool)*100:.1f}%)")
    print(f"  Mandel: {valid_mandel}/{len(mandel_pool)} ({valid_mandel/len(mandel_pool)*100:.1f}%)")

    print("\n" + "="*70)
    print("VERDICT:")
    print("="*70)

    if valid_mandel > valid_random:
        print(f"✅ Mandel pool has MORE valid patterns (+{valid_mandel - valid_random})")
    else:
        print(f"⚠️  Random pool has more valid patterns")

    print()
    print("Next step: Test both pools with ML model on Series 3146!")
    print("="*70)

if __name__ == "__main__":
    compare_pool_generators(size=2000, seed=999)
