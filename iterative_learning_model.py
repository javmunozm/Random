#!/usr/bin/env python3
"""
TRUE ITERATIVE LEARNING MODEL

This model actually LEARNS from its prediction mistakes:
1. Makes a prediction
2. Compares against actual results
3. Updates weights based on what it got right/wrong
4. Uses updated weights for next prediction

This is the missing piece - learning from performance, not just historical data.
"""

import random
import json
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter


class IterativeLearningModel:
    """ML model that learns from its own prediction performance"""

    MIN_NUMBER = 1
    MAX_NUMBER = 25
    NUMBERS_PER_COMBINATION = 14

    # Learning rates
    MISSED_NUMBER_BOOST = 1.30          # Boost numbers we missed
    MISSED_CRITICAL_BOOST = 1.50        # Heavy boost for critical numbers we missed
    WRONG_NUMBER_PENALTY = 0.80         # Penalize numbers we wrongly included
    CORRECT_NUMBER_BOOST = 1.10         # Slight boost for correct predictions
    PAIR_LEARNING_RATE = 0.15           # How much to learn from pair patterns

    def __init__(self, seed=999):
        random.seed(seed)
        self.seed = seed

        # Initialize weights (all start equal)
        self.number_weights = {i: 1.0 for i in range(self.MIN_NUMBER, self.MAX_NUMBER + 1)}
        self.pair_affinities = defaultdict(float)

        # Track learning history
        self.prediction_history = []
        self.learning_events = []

    def train_on_historical_data(self, historical_data: Dict[int, List[List[int]]]):
        """Initial training on historical data"""
        print("Initial training on historical data...")

        for series_id, events in historical_data.items():
            # Count number frequencies
            frequency = Counter()
            for event in events:
                for num in event:
                    frequency[num] += 1

            # Update weights based on frequency
            total = sum(frequency.values())
            for num in range(self.MIN_NUMBER, self.MAX_NUMBER + 1):
                freq = frequency.get(num, 0)
                self.number_weights[num] *= (1.0 + (freq / total) * 0.1)

            # Learn pair affinities
            for event in events:
                for i in range(len(event)):
                    for j in range(i + 1, len(event)):
                        pair = tuple(sorted([event[i], event[j]]))
                        self.pair_affinities[pair] += 0.1

        print(f"✅ Initial training complete on {len(historical_data)} series")

    def predict(self, series_id: int) -> List[int]:
        """Generate prediction using current weights"""
        candidates = self._generate_candidates(5000)
        scored = [(c, self._score_candidate(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        prediction = scored[0][0]

        # Store prediction
        self.prediction_history.append({
            'series_id': series_id,
            'prediction': prediction,
            'weights_snapshot': self.number_weights.copy()
        })

        return prediction

    def learn_from_results(self, series_id: int, actual_events: List[List[int]]):
        """
        THIS IS THE KEY: Learn from how well we predicted
        Update weights based on what we got right/wrong
        """
        # Find our prediction
        prediction = None
        for record in self.prediction_history:
            if record['series_id'] == series_id:
                prediction = record['prediction']
                break

        if prediction is None:
            print(f"⚠️ No prediction found for series {series_id}")
            return

        prediction_set = set(prediction)

        # Analyze actual results
        all_numbers = set()
        critical_numbers = set()
        number_frequencies = Counter()

        for event in actual_events:
            for num in event:
                all_numbers.add(num)
                number_frequencies[num] += 1

        # Identify critical numbers (appeared in 5+ events)
        for num, count in number_frequencies.items():
            if count >= 5:
                critical_numbers.add(num)

        # Calculate what we got right/wrong
        correct_predictions = prediction_set & all_numbers
        missed_numbers = all_numbers - prediction_set
        wrong_predictions = prediction_set - all_numbers

        # Identify missed critical numbers (BIG PROBLEM)
        missed_critical = missed_numbers & critical_numbers

        # Calculate best possible match
        best_match = 0
        for event in actual_events:
            match_count = len(set(event) & prediction_set)
            best_match = max(best_match, match_count)

        # LEARNING: Update weights based on performance
        learning_log = {
            'series_id': series_id,
            'best_match': best_match,
            'total_match': f"{best_match}/14 ({best_match/14*100:.1f}%)",
            'critical_numbers': sorted(list(critical_numbers)),
            'missed_critical': sorted(list(missed_critical)),
            'adjustments': {}
        }

        # 1. BOOST missed numbers (especially critical ones)
        for num in missed_numbers:
            if num in critical_numbers:
                old_weight = self.number_weights[num]
                self.number_weights[num] *= self.MISSED_CRITICAL_BOOST
                learning_log['adjustments'][f'missed_critical_{num:02d}'] = {
                    'old': f"{old_weight:.3f}",
                    'new': f"{self.number_weights[num]:.3f}",
                    'reason': 'CRITICAL number we missed!'
                }
            else:
                old_weight = self.number_weights[num]
                self.number_weights[num] *= self.MISSED_NUMBER_BOOST
                learning_log['adjustments'][f'missed_{num:02d}'] = {
                    'old': f"{old_weight:.3f}",
                    'new': f"{self.number_weights[num]:.3f}",
                    'reason': 'Number we missed'
                }

        # 2. PENALIZE wrong predictions
        for num in wrong_predictions:
            old_weight = self.number_weights[num]
            self.number_weights[num] *= self.WRONG_NUMBER_PENALTY
            learning_log['adjustments'][f'wrong_{num:02d}'] = {
                'old': f"{old_weight:.3f}",
                'new': f"{self.number_weights[num]:.3f}",
                'reason': 'Wrongly predicted'
            }

        # 3. BOOST correct predictions (reinforce good choices)
        for num in correct_predictions:
            old_weight = self.number_weights[num]
            self.number_weights[num] *= self.CORRECT_NUMBER_BOOST
            learning_log['adjustments'][f'correct_{num:02d}'] = {
                'old': f"{old_weight:.3f}",
                'new': f"{self.number_weights[num]:.3f}",
                'reason': 'Correctly predicted'
            }

        # 4. LEARN pair patterns from actual results
        for event in actual_events:
            for i in range(len(event)):
                for j in range(i + 1, len(event)):
                    pair = tuple(sorted([event[i], event[j]]))
                    self.pair_affinities[pair] += self.PAIR_LEARNING_RATE

        self.learning_events.append(learning_log)

        print(f"\n📚 LEARNED from Series {series_id}:")
        print(f"   Performance: {best_match}/14 ({best_match/14*100:.1f}%)")
        print(f"   Critical numbers: {len(critical_numbers)}")
        print(f"   Missed critical: {len(missed_critical)} - {sorted(missed_critical)}")
        print(f"   Weight adjustments: {len(learning_log['adjustments'])}")

    def _generate_candidates(self, pool_size: int) -> List[List[int]]:
        """Generate candidate combinations using current weights"""
        candidates = []
        attempts = 0
        max_attempts = pool_size * 3

        while len(candidates) < pool_size and attempts < max_attempts:
            candidate = self._generate_weighted_candidate()
            if candidate not in candidates:
                candidates.append(candidate)
            attempts += 1

        return candidates

    def _generate_weighted_candidate(self) -> List[int]:
        """Generate single candidate using weighted selection"""
        numbers = []
        used = set()

        while len(numbers) < self.NUMBERS_PER_COMBINATION:
            num = self._select_weighted_number(used)
            if num not in used:
                numbers.append(num)
                used.add(num)

        return sorted(numbers)

    def _select_weighted_number(self, used: Set[int]) -> int:
        """Select number based on current weights"""
        weights = {}

        for i in range(self.MIN_NUMBER, self.MAX_NUMBER + 1):
            if i not in used:
                weights[i] = self.number_weights[i]

        total_weight = sum(weights.values())
        rand_val = random.random() * total_weight

        current_weight = 0.0
        for num, weight in weights.items():
            current_weight += weight
            if current_weight >= rand_val:
                return num

        available = [i for i in range(self.MIN_NUMBER, self.MAX_NUMBER + 1) if i not in used]
        return random.choice(available) if available else 1

    def _score_candidate(self, combination: List[int]) -> float:
        """Score candidate based on current weights and pair affinities"""
        score = 0.0

        # Number weights
        for num in combination:
            score += self.number_weights[num]

        # Pair affinities
        for i in range(len(combination)):
            for j in range(i + 1, len(combination)):
                pair = tuple(sorted([combination[i], combination[j]]))
                if pair in self.pair_affinities:
                    score += self.pair_affinities[pair] * 10.0

        return score

    def get_learning_summary(self) -> Dict:
        """Get summary of what the model learned"""
        return {
            'predictions_made': len(self.prediction_history),
            'learning_events': len(self.learning_events),
            'current_top_weights': sorted(
                [(num, weight) for num, weight in self.number_weights.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'learning_history': self.learning_events
        }


def load_actual_results() -> Dict[int, List[List[int]]]:
    """Load all actual results"""
    return {
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
        ],
        3150: [
            [1, 2, 4, 6, 8, 10, 12, 13, 15, 17, 19, 21, 22, 23],
            [1, 2, 3, 4, 9, 10, 11, 15, 17, 19, 20, 21, 24, 25],
            [2, 3, 4, 6, 7, 10, 14, 15, 16, 19, 20, 21, 22, 23],
            [2, 7, 9, 10, 12, 13, 14, 17, 18, 20, 21, 22, 23, 24],
            [2, 4, 6, 8, 9, 10, 11, 12, 14, 16, 17, 18, 21, 22],
            [1, 3, 4, 5, 7, 9, 10, 12, 14, 15, 19, 23, 24, 25],
            [5, 6, 7, 9, 10, 11, 13, 14, 16, 18, 21, 22, 24, 25]
        ]
    }


if __name__ == "__main__":
    print("=" * 80)
    print("ITERATIVE LEARNING MODEL - TRUE MACHINE LEARNING")
    print("Learning from prediction performance, not just historical data")
    print("=" * 80)
    print()

    # Load all data
    all_data = load_actual_results()

    # Train on 3141-3148
    initial_training = {k: v for k, v in all_data.items() if k <= 3148}

    model = IterativeLearningModel(seed=999)
    model.train_on_historical_data(initial_training)

    print("\n" + "=" * 80)
    print("ITERATIVE LEARNING CYCLE")
    print("=" * 80)

    # Predict 3149, learn from results
    print("\n🎯 Predicting Series 3149...")
    pred_3149 = model.predict(3149)
    print(f"Prediction: {' '.join(f'{n:02d}' for n in pred_3149)}")
    model.learn_from_results(3149, all_data[3149])

    # Predict 3150, learn from results
    print("\n🎯 Predicting Series 3150...")
    pred_3150 = model.predict(3150)
    print(f"Prediction: {' '.join(f'{n:02d}' for n in pred_3150)}")
    model.learn_from_results(3150, all_data[3150])

    # NOW predict 3151 with all learnings
    print("\n" + "=" * 80)
    print("🎯 PREDICTING SERIES 3151 (with iterative learning)")
    print("=" * 80)
    pred_3151 = model.predict(3151)
    print(f"\nPrediction: {' '.join(f'{n:02d}' for n in pred_3151)}")

    # Show what the model learned
    print("\n" + "=" * 80)
    print("LEARNING SUMMARY")
    print("=" * 80)
    summary = model.get_learning_summary()

    print(f"\nPredictions made: {summary['predictions_made']}")
    print(f"Learning events: {summary['learning_events']}")

    print("\nTop 10 Learned Weights:")
    for i, (num, weight) in enumerate(summary['current_top_weights'], 1):
        print(f"  {i:2d}. Number {num:02d}: {weight:.3f}")

    # Save results
    output = {
        'series_id': 3151,
        'method': 'IterativeLearningModel',
        'prediction': pred_3151,
        'prediction_formatted': ' '.join(f'{n:02d}' for n in pred_3151),
        'learning_summary': {
            'predictions_made': summary['predictions_made'],
            'learning_events': summary['learning_events'],
            'top_weights': [(num, f"{weight:.3f}") for num, weight in summary['current_top_weights']]
        },
        'learning_history': summary['learning_history']
    }

    with open('Results/prediction_3151_iterative_learning.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n📁 Saved to: Results/prediction_3151_iterative_learning.json")
