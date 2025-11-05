#!/usr/bin/env python3
"""
TrueLearningModel - IMPROVED with Ensemble Predictions

Improvement Strategy: Reduce Variance with Multiple Runs
- Run prediction 5 times with different random seeds
- Count number frequency across all 5 predictions
- Select top 14 most frequent numbers
- This reduces random variance and improves consistency

Expected: More stable results, potentially beating 71.4% baseline
"""

import random
from typing import List
from collections import Counter
from true_learning_model import TrueLearningModel


class TrueLearningModelImproved(TrueLearningModel):
    """Phase 1 Pure with ensemble predictions to reduce variance"""

    def __init__(self, ensemble_size=5):
        super().__init__()
        self.ensemble_size = ensemble_size

    def predict_best_combination(self, target_series_id: int) -> List[int]:
        """Generate ensemble prediction from multiple runs"""

        # Store original random state
        original_state = random.getstate()

        # Generate multiple predictions with different seeds
        all_predictions = []
        for seed_offset in range(self.ensemble_size):
            # Set different seed for each run
            random.seed(target_series_id + seed_offset)

            # Generate prediction with this seed
            candidates = self._generate_candidates(target_series_id)
            scored = [(c, self._calculate_score(c)) for c in candidates]
            scored.sort(key=lambda x: x[1], reverse=True)

            prediction = scored[0][0]
            all_predictions.append(prediction)

        # Restore original random state
        random.setstate(original_state)

        # Count frequency of each number across all predictions
        number_frequency = Counter()
        for prediction in all_predictions:
            for num in prediction:
                number_frequency[num] += 1

        # Select top 14 most frequent numbers
        most_common = number_frequency.most_common(14)
        ensemble_prediction = sorted([num for num, _ in most_common])

        # Ensure we have exactly 14 numbers
        if len(ensemble_prediction) < 14:
            # Add missing numbers from highest scored individual prediction
            missing_count = 14 - len(ensemble_prediction)
            best_prediction = all_predictions[0]
            for num in best_prediction:
                if num not in ensemble_prediction:
                    ensemble_prediction.append(num)
                    if len(ensemble_prediction) == 14:
                        break
            ensemble_prediction.sort()

        return ensemble_prediction
