#!/usr/bin/env python3
"""
TrueLearningModel - ENHANCED V2 (Phase 1++)

Enhancement 2: Proportional Scoring Bonuses
- Replaces flat bonuses with proportional multipliers
- Sum range optimal (180-189): 1.05x multiplier (not flat +0.15)
- Even/odd balance (6-8): 1.03x multiplier (not flat +2.0)
- Gap preference: 1.02x for 55%+ gap-1 (not flat +1.0)

Based on Phase 2 analysis: Flat bonuses (2-15 points) invisible in 270-550 score range.
Proportional multipliers scale with score = actually matter!
"""

import random
from typing import List, Set
from collections import defaultdict

# Import base model
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from true_learning_model import TrueLearningModel


class TrueLearningModelEnhanced2(TrueLearningModel):
    """Phase 1++ with proportional scoring bonuses"""

    def __init__(self):
        super().__init__()

    def _calculate_score(self, combination: List[int]) -> float:
        """ENHANCED: Calculate score with proportional bonuses"""
        # Start with base frequency score
        base_score = 0.0
        for num in combination:
            base_score += self.number_frequency_weights[num]

        # Pattern scores (original)
        consecutive_count = self._count_consecutive(combination)
        total_sum = sum(combination)
        distribution = self._calculate_distribution(combination)

        base_score += consecutive_count * self.pattern_weights['consecutive']
        base_score += distribution * self.pattern_weights['distribution']

        # Sum range scoring (Phase 1 original: 160-240)
        if 160 <= total_sum <= 240:
            base_score += self.pattern_weights['sum_range']

        # Pair affinity score (baseline multipliers)
        base_score += self._calculate_pair_affinity_score(combination)

        # Triplet affinity score (baseline multipliers)
        base_score += self._calculate_triplet_affinity_score(combination)

        # Critical number bonus
        critical_count = sum(1 for num in combination if num in self.recent_critical_numbers)
        base_score += critical_count * 10.0

        # ENHANCEMENT 2: Proportional bonuses instead of flat
        multiplier = 1.0

        # Optimal sum range bonus (180-189 = 23.1% of events)
        if 180 <= total_sum <= 189:
            multiplier *= 1.05  # 5% boost (vs flat +0.15 which was 0.05% of score)

        # Even/odd balance bonus (6-8 even = 74% of events)
        even_count = sum(1 for n in combination if n % 2 == 0)
        if 6 <= even_count <= 8:
            multiplier *= 1.03  # 3% boost (vs flat +2.0 which was 0.7% of score)

        # Gap preference bonus (55% of gaps are 1)
        gaps = [combination[i + 1] - combination[i] for i in range(len(combination) - 1)]
        gap_1_ratio = sum(1 for g in gaps if g == 1) / len(gaps)
        if gap_1_ratio >= 0.45:  # 45%+ gaps are 1
            multiplier *= 1.02  # 2% boost (vs flat +1.0 which was 0.3% of score)

        # Apply proportional multiplier to final score
        final_score = base_score * multiplier

        return final_score
