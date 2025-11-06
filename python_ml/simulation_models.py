#!/usr/bin/env python3
"""
Alternative model implementations for simulation study
Each model must implement: train(), predict(), get_name()
"""

import random
from collections import Counter, defaultdict
from typing import List, Set, Tuple, Dict


class BaseModel:
    """Base class for all models"""

    def __init__(self):
        self.training_data = []

    def train(self, series_data: List[Dict]):
        """Train model on historical data"""
        self.training_data = series_data

    def predict(self, target_series_id: int) -> List[int]:
        """Generate prediction for target series"""
        raise NotImplementedError

    def get_name(self) -> str:
        """Return model name"""
        raise NotImplementedError


# ==============================================================================
# MODEL 1: Pure Frequency Baseline
# ==============================================================================

class PureFrequencyModel(BaseModel):
    """Select 14 most frequent numbers from all historical data"""

    def get_name(self) -> str:
        return "Pure Frequency Baseline"

    def predict(self, target_series_id: int) -> List[int]:
        # Count frequency across ALL historical data
        freq = Counter()
        for series in self.training_data:
            for event in series['events']:
                freq.update(event)

        # Select top 14 most frequent
        top_14 = [num for num, count in freq.most_common(14)]
        return sorted(top_14)


# ==============================================================================
# MODEL 2: Weighted Random (Simplified Current)
# ==============================================================================

class WeightedRandomModel(BaseModel):
    """Like Phase 1 but without pair affinity and critical boosts"""

    def __init__(self):
        super().__init__()
        self.number_weights = defaultdict(lambda: 1.0)
        self.learning_rate = 0.10

    def get_name(self) -> str:
        return "Weighted Random (Simplified)"

    def train(self, series_data: List[Dict]):
        super().train(series_data)

        # Initial frequency-based weights
        freq = Counter()
        for series in series_data:
            for event in series['events']:
                freq.update(event)

        for num in range(1, 26):
            self.number_weights[num] = freq.get(num, 0) / len(series_data)

    def predict(self, target_series_id: int) -> List[int]:
        # Generate 5000 weighted candidates
        candidates = []
        for _ in range(5000):
            candidate = self._generate_weighted_candidate()
            if len(set(candidate)) == 14:
                candidates.append(tuple(sorted(candidate)))

        # Remove duplicates
        candidates = list(set(candidates))

        # Score by sum of weights
        scored = []
        for cand in candidates:
            score = sum(self.number_weights[num] for num in cand)
            scored.append((cand, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return list(scored[0][0])

    def _generate_weighted_candidate(self) -> List[int]:
        numbers = []
        used = set()

        while len(numbers) < 14:
            # Weighted selection
            weights = {n: self.number_weights[n] for n in range(1, 26) if n not in used}
            total = sum(weights.values())

            rand_val = random.random() * total
            cumsum = 0
            selected = 1

            for num, weight in weights.items():
                cumsum += weight
                if cumsum >= rand_val:
                    selected = num
                    break

            if selected not in used:
                numbers.append(selected)
                used.add(selected)

        return numbers

    def learn_from_result(self, prediction: List[int], actual_events: List[List[int]]):
        """Simple learning: boost missed, penalize wrong"""
        for event in actual_events:
            missed = set(event) - set(prediction)
            wrong = set(prediction) - set(event)

            for num in missed:
                self.number_weights[num] *= (1 + self.learning_rate)

            for num in wrong:
                self.number_weights[num] *= (1 - self.learning_rate * 0.5)


# ==============================================================================
# MODEL 3: Recent Trend Predictor
# ==============================================================================

class TrendBasedModel(BaseModel):
    """Weight recent series much more heavily than old data"""

    def __init__(self, decay_rate=0.90):
        super().__init__()
        self.decay_rate = decay_rate

    def get_name(self) -> str:
        return f"Trend-Based (decay={self.decay_rate})"

    def predict(self, target_series_id: int) -> List[int]:
        # Calculate weighted frequency with exponential decay
        weighted_freq = defaultdict(float)

        # Sort by series_id to get chronological order
        sorted_data = sorted(self.training_data, key=lambda x: x['series_id'])

        for i, series in enumerate(sorted_data):
            # More recent = higher weight
            distance_from_target = len(sorted_data) - i
            weight = self.decay_rate ** distance_from_target

            for event in series['events']:
                for num in event:
                    weighted_freq[num] += weight

        # Select top 14
        ranked = sorted(weighted_freq.items(), key=lambda x: x[1], reverse=True)
        top_14 = [num for num, freq in ranked[:14]]

        return sorted(top_14)


# ==============================================================================
# MODEL 4: Adaptive Learning Rate Model
# ==============================================================================

class AdaptiveLearningRateModel(BaseModel):
    """Current model but with adaptive learning rate based on performance"""

    def __init__(self):
        super().__init__()
        self.number_weights = defaultdict(lambda: 1.0)
        self.base_learning_rate = 0.10
        self.current_learning_rate = 0.10
        self.recent_accuracies = []

    def get_name(self) -> str:
        return "Adaptive Learning Rate"

    def train(self, series_data: List[Dict]):
        super().train(series_data)

        # Initial weights from frequency
        freq = Counter()
        for series in series_data:
            for event in series['events']:
                freq.update(event)

        for num in range(1, 26):
            self.number_weights[num] = freq.get(num, 0) / len(series_data) + 1.0

    def predict(self, target_series_id: int) -> List[int]:
        # Generate candidates
        candidates = []
        for _ in range(5000):
            candidate = self._generate_weighted_candidate()
            if len(set(candidate)) == 14:
                candidates.append(tuple(sorted(candidate)))

        candidates = list(set(candidates))

        # Score
        scored = []
        for cand in candidates:
            score = sum(self.number_weights[num] for num in cand)
            scored.append((cand, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return list(scored[0][0])

    def _generate_weighted_candidate(self) -> List[int]:
        numbers = []
        used = set()

        while len(numbers) < 14:
            weights = {n: self.number_weights[n] for n in range(1, 26) if n not in used}
            total = sum(weights.values())

            rand_val = random.random() * total
            cumsum = 0
            selected = 1

            for num, weight in weights.items():
                cumsum += weight
                if cumsum >= rand_val:
                    selected = num
                    break

            if selected not in used:
                numbers.append(selected)
                used.add(selected)

        return numbers

    def learn_from_result(self, prediction: List[int], actual_events: List[List[int]]):
        """Learn with adaptive rate based on recent performance"""

        # Calculate accuracy
        best_accuracy = max(len(set(prediction) & set(event)) / 14.0 for event in actual_events)
        self.recent_accuracies.append(best_accuracy)

        # Keep last 5 accuracies
        if len(self.recent_accuracies) > 5:
            self.recent_accuracies.pop(0)

        # Adapt learning rate
        avg_accuracy = sum(self.recent_accuracies) / len(self.recent_accuracies)

        if avg_accuracy > 0.75:
            # High accuracy: small adjustments (pattern is stable)
            self.current_learning_rate = 0.05
        elif avg_accuracy > 0.65:
            # Medium accuracy: normal adjustments
            self.current_learning_rate = 0.10
        else:
            # Low accuracy: large adjustments (pattern shifted)
            self.current_learning_rate = 0.20

        # Apply learning
        for event in actual_events:
            missed = set(event) - set(prediction)
            wrong = set(prediction) - set(event)

            for num in missed:
                self.number_weights[num] *= (1 + self.current_learning_rate)

            for num in wrong:
                self.number_weights[num] *= (1 - self.current_learning_rate * 0.5)


# ==============================================================================
# MODEL 5: Ensemble Voting
# ==============================================================================

class EnsembleVotingModel(BaseModel):
    """Combine multiple strategies via voting"""

    def __init__(self):
        super().__init__()
        self.frequency_model = PureFrequencyModel()
        self.trend_model = TrendBasedModel(decay_rate=0.95)
        self.weighted_model = WeightedRandomModel()

    def get_name(self) -> str:
        return "Ensemble Voting (3 models)"

    def train(self, series_data: List[Dict]):
        super().train(series_data)
        self.frequency_model.train(series_data)
        self.trend_model.train(series_data)
        self.weighted_model.train(series_data)

    def predict(self, target_series_id: int) -> List[int]:
        # Get predictions from all models
        pred1 = self.frequency_model.predict(target_series_id)
        pred2 = self.trend_model.predict(target_series_id)
        pred3 = self.weighted_model.predict(target_series_id)

        # Vote: count how many models selected each number
        votes = Counter()
        for pred in [pred1, pred2, pred3]:
            votes.update(pred)

        # Select top 14 by votes
        top_14 = [num for num, count in votes.most_common(14)]

        # If less than 14 (shouldn't happen), fill with most frequent
        if len(top_14) < 14:
            freq = Counter()
            for series in self.training_data:
                for event in series['events']:
                    freq.update(event)

            for num, _ in freq.most_common(25):
                if num not in top_14:
                    top_14.append(num)
                    if len(top_14) == 14:
                        break

        return sorted(top_14[:14])

    def learn_from_result(self, prediction: List[int], actual_events: List[List[int]]):
        """Let sub-models learn"""
        self.weighted_model.learn_from_result(prediction, actual_events)


# ==============================================================================
# MODEL 6: Pattern Recognition (Gaps/Distribution)
# ==============================================================================

class PatternRecognitionModel(BaseModel):
    """Focus on distribution patterns: gaps, clusters, balance"""

    def __init__(self):
        super().__init__()
        self.number_weights = defaultdict(lambda: 1.0)

    def get_name(self) -> str:
        return "Pattern Recognition (Gaps)"

    def train(self, series_data: List[Dict]):
        super().train(series_data)

        # Learn frequency
        freq = Counter()
        for series in series_data:
            for event in series['events']:
                freq.update(event)

        for num in range(1, 26):
            self.number_weights[num] = freq.get(num, 0) / len(series_data) + 1.0

        # Analyze historical gap patterns
        self.avg_gap = self._analyze_gaps(series_data)

    def _analyze_gaps(self, series_data: List[Dict]) -> float:
        """Calculate average gap between numbers"""
        gaps = []
        for series in series_data:
            for event in series['events']:
                sorted_nums = sorted(event)
                for i in range(len(sorted_nums) - 1):
                    gap = sorted_nums[i+1] - sorted_nums[i]
                    gaps.append(gap)

        return sum(gaps) / len(gaps) if gaps else 1.5

    def predict(self, target_series_id: int) -> List[int]:
        # Generate candidates and score by distribution quality
        best_candidate = None
        best_score = -999999

        for _ in range(5000):
            candidate = self._generate_weighted_candidate()
            if len(set(candidate)) == 14:
                score = self._score_candidate(candidate)
                if score > best_score:
                    best_score = score
                    best_candidate = candidate

        return sorted(best_candidate) if best_candidate else sorted(list(range(1, 15)))

    def _generate_weighted_candidate(self) -> List[int]:
        numbers = []
        used = set()

        while len(numbers) < 14:
            weights = {n: self.number_weights[n] for n in range(1, 26) if n not in used}
            total = sum(weights.values())

            rand_val = random.random() * total
            cumsum = 0
            selected = 1

            for num, weight in weights.items():
                cumsum += weight
                if cumsum >= rand_val:
                    selected = num
                    break

            if selected not in used:
                numbers.append(selected)
                used.add(selected)

        return numbers

    def _score_candidate(self, candidate: List[int]) -> float:
        """Score based on frequency weights + distribution quality"""
        # Base score from weights
        base_score = sum(self.number_weights[num] for num in candidate)

        # Bonus for good gap distribution
        sorted_cand = sorted(candidate)
        gaps = [sorted_cand[i+1] - sorted_cand[i] for i in range(len(sorted_cand) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        gap_penalty = abs(avg_gap - self.avg_gap) * 5.0

        # Bonus for balanced distribution (low/mid/high)
        low = sum(1 for n in candidate if n <= 8)
        mid = sum(1 for n in candidate if 9 <= n <= 17)
        high = sum(1 for n in candidate if n >= 18)
        balance_penalty = abs(low - 4.67) + abs(mid - 4.67) + abs(high - 4.67)

        return base_score - gap_penalty - balance_penalty

    def learn_from_result(self, prediction: List[int], actual_events: List[List[int]]):
        """Simple frequency learning"""
        for event in actual_events:
            missed = set(event) - set(prediction)
            wrong = set(prediction) - set(event)

            for num in missed:
                self.number_weights[num] *= 1.10

            for num in wrong:
                self.number_weights[num] *= 0.95


# ==============================================================================
# MODEL 7: Momentum Tracker
# ==============================================================================

class MomentumTrackerModel(BaseModel):
    """Track numbers appearing in consecutive series (short-term momentum)"""

    def __init__(self, window=5):
        super().__init__()
        self.window = window
        self.number_weights = defaultdict(lambda: 1.0)

    def get_name(self) -> str:
        return f"Momentum Tracker (window={self.window})"

    def train(self, series_data: List[Dict]):
        super().train(series_data)

        # Base weights from frequency
        freq = Counter()
        for series in series_data:
            for event in series['events']:
                freq.update(event)

        for num in range(1, 26):
            self.number_weights[num] = freq.get(num, 0) / len(series_data) + 1.0

    def predict(self, target_series_id: int) -> List[int]:
        # Calculate momentum bonus from last N series
        momentum_bonus = defaultdict(float)

        # Get last N series
        sorted_data = sorted(self.training_data, key=lambda x: x['series_id'], reverse=True)
        recent = sorted_data[:self.window]

        for series in recent:
            # Count frequency in this series
            series_freq = Counter()
            for event in series['events']:
                series_freq.update(event)

            # Numbers appearing in many events of this series get momentum
            for num, count in series_freq.items():
                if count >= 4:  # Hot in this series
                    momentum_bonus[num] += 2.0

        # Generate candidates with momentum bonus
        best_candidate = None
        best_score = -999999

        for _ in range(5000):
            candidate = self._generate_weighted_candidate()
            if len(set(candidate)) == 14:
                score = sum(self.number_weights[num] + momentum_bonus.get(num, 0) for num in candidate)
                if score > best_score:
                    best_score = score
                    best_candidate = candidate

        return sorted(best_candidate) if best_candidate else sorted(list(range(1, 15)))

    def _generate_weighted_candidate(self) -> List[int]:
        numbers = []
        used = set()

        while len(numbers) < 14:
            weights = {n: self.number_weights[n] for n in range(1, 26) if n not in used}
            total = sum(weights.values())

            rand_val = random.random() * total
            cumsum = 0
            selected = 1

            for num, weight in weights.items():
                cumsum += weight
                if cumsum >= rand_val:
                    selected = num
                    break

            if selected not in used:
                numbers.append(selected)
                used.add(selected)

        return numbers

    def learn_from_result(self, prediction: List[int], actual_events: List[List[int]]):
        """Update base weights"""
        for event in actual_events:
            missed = set(event) - set(prediction)
            wrong = set(prediction) - set(event)

            for num in missed:
                self.number_weights[num] *= 1.10

            for num in wrong:
                self.number_weights[num] *= 0.95
