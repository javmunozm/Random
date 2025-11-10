"""
Refined Mandel Method - Enhanced Pool Generation with ML Integration

Improvements over v1:
1. Pair affinity integration during generation (not just scoring)
2. Historical distribution analysis for adaptive targets
3. Smarter consecutive/gap handling
4. Multiple generation strategies with diversity
5. Quality scoring for candidate selection
"""

import random
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter
import statistics

class RefinedMandelPoolGenerator:
    """Enhanced Mandel pool generator with ML-informed optimization"""

    def __init__(self,
                 frequency_weights: Dict[int, float] = None,
                 pair_affinities: Dict[Tuple[int, int], float] = None,
                 historical_data: Dict[int, List[List[int]]] = None):
        """
        Args:
            frequency_weights: ML-learned number weights
            pair_affinities: ML-learned pair co-occurrence weights
            historical_data: Full historical dataset for pattern analysis
        """
        self.frequency_weights = frequency_weights or {}
        self.pair_affinities = pair_affinities or {}
        self.historical_data = historical_data or {}

        # Normalize frequency weights
        if self.frequency_weights:
            total = sum(self.frequency_weights.values())
            self.freq_probs = {k: v/total for k, v in self.frequency_weights.items()}
        else:
            self.freq_probs = {i: 1/25 for i in range(1, 26)}

        # Analyze historical patterns if data provided
        self._analyze_historical_patterns()

    def _analyze_historical_patterns(self):
        """Analyze historical data to learn optimal distributions"""
        if not self.historical_data:
            # Use defaults if no data
            self.target_col0_range = (5, 7)
            self.target_col1_range = (4, 6)
            self.target_sum_mean = 182
            self.target_sum_std = 20
            self.typical_consecutive = 3
            self.typical_gaps = [1, 2, 3]
            return

        # Analyze all historical events
        col0_counts = []
        col1_counts = []
        col2_counts = []
        sums = []
        consecutive_counts = []
        gaps = []

        for series_id, events in self.historical_data.items():
            for event in events:
                # Column distribution
                col0 = sum(1 for n in event if 1 <= n <= 9)
                col1 = sum(1 for n in event if 10 <= n <= 19)
                col2 = sum(1 for n in event if 20 <= n <= 25)

                col0_counts.append(col0)
                col1_counts.append(col1)
                col2_counts.append(col2)
                sums.append(sum(event))

                # Consecutive analysis
                sorted_event = sorted(event)
                consec = sum(1 for i in range(len(sorted_event)-1)
                            if sorted_event[i+1] - sorted_event[i] == 1)
                consecutive_counts.append(consec)

                # Gap analysis
                for i in range(len(sorted_event)-1):
                    gaps.append(sorted_event[i+1] - sorted_event[i])

        # Learn optimal ranges using sorted percentiles
        col0_sorted = sorted(col0_counts)
        col1_sorted = sorted(col1_counts)

        n0 = len(col0_sorted)
        n1 = len(col1_sorted)

        self.target_col0_range = (col0_sorted[n0 // 4], col0_sorted[3 * n0 // 4])
        self.target_col1_range = (col1_sorted[n1 // 4], col1_sorted[3 * n1 // 4])
        self.target_sum_mean = statistics.mean(sums)
        self.target_sum_std = statistics.stdev(sums)
        self.typical_consecutive = int(statistics.median(consecutive_counts))
        self.typical_gaps = [g for g, _ in Counter(gaps).most_common(5)]

        print(f"📊 Historical Pattern Analysis:")
        print(f"   Col 0 (01-09): {self.target_col0_range[0]}-{self.target_col0_range[1]} numbers")
        print(f"   Col 1 (10-19): {self.target_col1_range[0]}-{self.target_col1_range[1]} numbers")
        print(f"   Sum: {self.target_sum_mean:.1f} ± {self.target_sum_std:.1f}")
        print(f"   Typical consecutive: {self.typical_consecutive} pairs")
        print(f"   Common gaps: {self.typical_gaps[:3]}")
        print()

    def generate_pool(self, size: int, seed: int = None) -> List[List[int]]:
        """
        Generate pool with multiple strategies for diversity

        Strategy mix:
        - 50% Pair-affinity driven
        - 30% Frequency-weighted balanced
        - 20% Pure balanced (diversity)
        """
        if seed is not None:
            random.seed(seed)

        candidates = []
        seen = set()

        # Strategy quotas
        quota_affinity = int(size * 0.5)
        quota_frequency = int(size * 0.3)
        quota_balanced = size - quota_affinity - quota_frequency

        attempts = 0
        max_attempts = size * 15

        while len(candidates) < size and attempts < max_attempts:
            # Select strategy based on quotas
            if len(candidates) < quota_affinity:
                candidate = self._generate_with_pair_affinity()
            elif len(candidates) < quota_affinity + quota_frequency:
                candidate = self._generate_frequency_weighted()
            else:
                candidate = self._generate_pure_balanced()

            # Validate and deduplicate
            cand_tuple = tuple(sorted(candidate))
            if self._is_valid_pattern(candidate) and cand_tuple not in seen:
                candidates.append(candidate)
                seen.add(cand_tuple)

            attempts += 1

        if len(candidates) < size:
            print(f"⚠️  Generated {len(candidates)}/{size} candidates (tried {attempts} times)")

        return candidates

    def _generate_with_pair_affinity(self) -> List[int]:
        """
        Generate candidate using pair affinities
        Start with high-affinity pairs, then fill in
        """
        if not self.pair_affinities:
            return self._generate_frequency_weighted()

        candidate = []

        # Sort pairs by affinity score
        sorted_pairs = sorted(self.pair_affinities.items(),
                             key=lambda x: x[1],
                             reverse=True)

        # Start with top affinity pairs (with some randomness)
        top_pairs = sorted_pairs[:50]  # Top 50 pairs

        # Randomly select 2-3 high-affinity pairs as seeds
        num_seed_pairs = random.randint(2, 3)
        seed_pairs = random.sample(top_pairs, min(num_seed_pairs, len(top_pairs)))

        for (n1, n2), _ in seed_pairs:
            if n1 not in candidate:
                candidate.append(n1)
            if n2 not in candidate and len(candidate) < 14:
                candidate.append(n2)

        # Fill remaining with frequency-weighted selection
        while len(candidate) < 14:
            # Get weights for numbers not yet selected
            available = [n for n in range(1, 26) if n not in candidate]
            weights = [self.freq_probs.get(n, 1/25) for n in available]

            # Add affinity bonus for numbers that pair well with current selection
            affinity_bonus = []
            for num in available:
                bonus = 0
                for existing in candidate:
                    pair = tuple(sorted([num, existing]))
                    bonus += self.pair_affinities.get(pair, 0)
                affinity_bonus.append(bonus / max(len(candidate), 1))

            # Combine frequency and affinity
            combined_weights = [w + b*0.3 for w, b in zip(weights, affinity_bonus)]

            # Normalize
            total = sum(combined_weights)
            if total > 0:
                probs = [w/total for w in combined_weights]
                choice = random.choices(available, weights=probs, k=1)[0]
                candidate.append(choice)
            else:
                candidate.append(random.choice(available))

        return sorted(candidate)

    def _generate_frequency_weighted(self) -> List[int]:
        """
        Generate with frequency weighting and column balance
        """
        # Use learned column ranges
        target_col0 = random.randint(self.target_col0_range[0],
                                     self.target_col0_range[1])
        target_col1 = random.randint(self.target_col1_range[0],
                                     self.target_col1_range[1])
        target_col2 = 14 - target_col0 - target_col1

        # Clamp col2 to valid range
        target_col2 = max(1, min(6, target_col2))
        target_col1 = 14 - target_col0 - target_col2

        # Weighted sample from each column
        col0_nums = self._weighted_sample(range(1, 10), target_col0)
        col1_nums = self._weighted_sample(range(10, 20), target_col1)
        col2_nums = self._weighted_sample(range(20, 26), target_col2)

        candidate = col0_nums + col1_nums + col2_nums
        random.shuffle(candidate)

        return sorted(candidate)

    def _generate_pure_balanced(self) -> List[int]:
        """
        Generate with pure random selection for diversity
        (No frequency or affinity bias)
        """
        return sorted(random.sample(range(1, 26), 14))

    def _weighted_sample(self, population: range, k: int) -> List[int]:
        """Sample k numbers from population using frequency weights"""
        weights = [self.freq_probs.get(n, 1/25) for n in population]
        selected = []
        pop_list = list(population)
        weights_list = list(weights)

        for _ in range(min(k, len(pop_list))):
            total = sum(weights_list)
            if total == 0:
                weights_list = [1] * len(weights_list)
                total = len(weights_list)

            probs = [w/total for w in weights_list]
            choice = random.choices(pop_list, weights=probs, k=1)[0]
            selected.append(choice)

            idx = pop_list.index(choice)
            pop_list.pop(idx)
            weights_list.pop(idx)

        return selected

    def _is_valid_pattern(self, candidate: List[int]) -> bool:
        """
        Enhanced pattern validation using historical patterns
        """
        if len(candidate) != 14:
            return False

        # Column distribution (use learned ranges)
        col0 = [n for n in candidate if 1 <= n <= 9]
        col1 = [n for n in candidate if 10 <= n <= 19]
        col2 = [n for n in candidate if 20 <= n <= 25]

        # Must have numbers from all columns
        if len(col0) == 0 or len(col1) == 0 or len(col2) == 0:
            return False

        # Check if within reasonable ranges (allow some flexibility)
        if len(col0) < self.target_col0_range[0]-1 or len(col0) > self.target_col0_range[1]+1:
            return False
        if len(col1) < self.target_col1_range[0]-1 or len(col1) > self.target_col1_range[1]+1:
            return False
        if len(col2) > 6:  # Max col2 is 6 (all numbers 20-25)
            return False

        # Sum validation (use learned mean ± 2*std)
        total = sum(candidate)
        if abs(total - self.target_sum_mean) > 2.5 * self.target_sum_std:
            return False

        # Consecutive check (allow typical amount ± 3)
        sorted_cand = sorted(candidate)
        consecutive_count = sum(1 for i in range(13)
                               if sorted_cand[i+1] - sorted_cand[i] == 1)

        # More lenient: allow 0 to typical+4
        if consecutive_count > self.typical_consecutive + 4:
            return False

        # Even/odd balance (4-10 evens is reasonable)
        evens = sum(1 for n in candidate if n % 2 == 0)
        if evens < 3 or evens > 11:
            return False

        return True

    def score_candidate(self, candidate: List[int]) -> float:
        """
        Score candidate quality for selection

        Higher score = better candidate
        """
        score = 0.0

        # Frequency weight bonus
        for num in candidate:
            score += self.freq_probs.get(num, 1/25) * 10

        # Pair affinity bonus
        for i, n1 in enumerate(candidate):
            for n2 in candidate[i+1:]:
                pair = tuple(sorted([n1, n2]))
                score += self.pair_affinities.get(pair, 0) * 5

        # Distribution bonus (closer to target = higher score)
        col0 = sum(1 for n in candidate if 1 <= n <= 9)
        col1 = sum(1 for n in candidate if 10 <= n <= 19)

        target_col0_mid = (self.target_col0_range[0] + self.target_col0_range[1]) / 2
        target_col1_mid = (self.target_col1_range[0] + self.target_col1_range[1]) / 2

        dist_col0 = abs(col0 - target_col0_mid)
        dist_col1 = abs(col1 - target_col1_mid)

        score += max(0, 5 - dist_col0 - dist_col1)

        # Sum bonus (closer to mean = higher score)
        total = sum(candidate)
        sum_distance = abs(total - self.target_sum_mean) / self.target_sum_std
        score += max(0, 5 - sum_distance)

        return score


def test_refined_generator():
    """Test the refined generator with sample data"""
    print("="*70)
    print("REFINED MANDEL POOL GENERATOR TEST")
    print("="*70)
    print()

    # Create with dummy weights
    freq_weights = {i: 1.0 + (i % 5) * 0.1 for i in range(1, 26)}
    pair_affinities = {
        (1, 2): 1.5, (1, 11): 1.4, (2, 23): 1.3,
        (7, 18): 1.2, (9, 21): 1.1
    }

    generator = RefinedMandelPoolGenerator(
        frequency_weights=freq_weights,
        pair_affinities=pair_affinities
    )

    # Generate pool
    print("Generating pool of 2000 candidates...")
    pool = generator.generate_pool(size=2000, seed=999)

    print(f"✅ Generated {len(pool)} candidates")
    print()

    # Show sample candidates
    print("Sample candidates (first 5):")
    for i, cand in enumerate(pool[:5], 1):
        score = generator.score_candidate(cand)
        print(f"  {i}. {' '.join(f'{n:02d}' for n in cand)} (score: {score:.2f})")

    print()
    print("="*70)

if __name__ == "__main__":
    test_refined_generator()
