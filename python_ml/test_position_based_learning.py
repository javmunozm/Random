#!/usr/bin/env python3
"""
Phase 2 Test 2: Position-Based Learning

Hypothesis: Numbers prefer certain positions in the 14-number array
- Track which positions each number appears at most frequently
- Apply position-based scoring bonus when generating candidates
- Example: Number 01 might appear more at positions 0-2, Number 25 at positions 12-13

Expected: High potential - patterns may exist in positional preferences
Baseline: 73.214% (seed 999, perfectly stable)
Target: >73.214% to show improvement
"""

import json
import random
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
from true_learning_model import TrueLearningModel

# Series 3144 actual results
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]


class PositionBasedLearningModel(TrueLearningModel):
    """
    Modified TrueLearningModel with position-based learning

    Tracks which positions each number appears at most frequently,
    then applies position-based scoring bonus during candidate generation.
    """

    def __init__(self):
        super().__init__()
        # Track position preferences: position_preferences[number][position] = count
        self.position_preferences = defaultdict(lambda: defaultdict(int))
        self.position_learning_enabled = True

    def learn_from_series(self, series_id: int, combinations: List[List[int]]):
        """Learn from a complete series including position preferences"""
        # Call parent to handle standard learning
        super().learn_from_series(series_id, combinations)

        # Learn position preferences from each event
        if self.position_learning_enabled:
            for combo in combinations:
                sorted_combo = sorted(combo)  # Numbers are always sorted
                for position, number in enumerate(sorted_combo):
                    self.position_preferences[number][position] += 1

    def _score_candidate_position_bonus(self, candidate: List[int]) -> float:
        """
        Calculate position-based scoring bonus for a candidate.

        For each number in the candidate, check if it's in a position it prefers.
        Return a bonus multiplier based on position match quality.
        """
        if not self.position_preferences:
            return 1.0  # No position data yet

        sorted_candidate = sorted(candidate)
        position_score = 0.0
        max_possible_score = 0.0

        for position, number in enumerate(sorted_candidate):
            if number in self.position_preferences:
                # Get total appearances of this number across all positions
                total_appearances = sum(self.position_preferences[number].values())

                if total_appearances > 0:
                    # Get appearances at this specific position
                    position_appearances = self.position_preferences[number][position]

                    # Calculate position preference ratio (0.0 to 1.0)
                    position_ratio = position_appearances / total_appearances

                    # Accumulate score
                    position_score += position_ratio
                    max_possible_score += 1.0

        if max_possible_score > 0:
            # Normalize to 0.0-1.0 range, then convert to multiplier (1.0-1.2)
            normalized_score = position_score / max_possible_score
            # Modest bonus: 1.0 (no match) to 1.2 (perfect match)
            return 1.0 + (normalized_score * 0.2)
        else:
            return 1.0

    def _score_candidate(self, candidate: List[int]) -> float:
        """Score a candidate combination (override to add position bonus)"""
        # Get base score from parent
        base_score = super()._score_candidate(candidate)

        # Apply position-based bonus
        position_bonus = self._score_candidate_position_bonus(candidate)

        return base_score * position_bonus

    def get_position_analysis(self) -> Dict:
        """Get analysis of position preferences for reporting"""
        analysis = {}

        for number in range(self.MIN_NUMBER, self.MAX_NUMBER + 1):
            if number in self.position_preferences:
                total = sum(self.position_preferences[number].values())
                if total > 0:
                    # Find preferred positions (top 3)
                    position_counts = self.position_preferences[number]
                    sorted_positions = sorted(position_counts.items(), key=lambda x: x[1], reverse=True)[:3]

                    analysis[number] = {
                        'total_appearances': total,
                        'top_positions': [
                            {
                                'position': pos,
                                'count': count,
                                'percentage': (count / total) * 100
                            }
                            for pos, count in sorted_positions
                        ]
                    }

        return analysis


def load_all_data():
    """Load all series data"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found")
        return []

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    all_series = []
    for series in json_data.get('data', []):
        all_series.append({
            'series_id': series['series_id'],
            'events': [event['numbers'] for event in series['events']]
        })

    # Add Series 3144
    all_series.append({'series_id': 3144, 'events': SERIES_3144})

    return all_series


def run_position_based_test(all_series_data, verbose=True):
    """Run single test with position-based learning"""
    random.seed(999)  # Same seed as baseline

    validation_window = 8
    latest_series = 3144
    validation_start = latest_series - validation_window + 1  # 3137

    # Initialize position-based model
    model = PositionBasedLearningModel()

    # Bulk training
    for series in all_series_data:
        if series['series_id'] < validation_start:
            model.learn_from_series(series['series_id'], series['events'])

    if verbose:
        print(f"\n📍 Position preferences learned from {validation_start - 2898} series")
        print(f"   Example: Number 01 position preferences:")
        if 1 in model.position_preferences:
            pos_data = model.position_preferences[1]
            total = sum(pos_data.values())
            top_3 = sorted(pos_data.items(), key=lambda x: x[1], reverse=True)[:3]
            for pos, count in top_3:
                print(f"      Position {pos}: {count}/{total} ({count/total*100:.1f}%)")
        print()

    # Iterative validation
    accuracies = []
    series_details = []

    for series_data in all_series_data:
        if validation_start <= series_data['series_id'] <= latest_series:
            series_id = series_data['series_id']
            actual_results = series_data['events']

            # Predict
            prediction = model.predict_best_combination(series_id)

            # Calculate best match
            best_match = max(len(set(prediction) & set(actual)) for actual in actual_results)
            best_accuracy = best_match / 14.0
            accuracies.append(best_accuracy)

            series_details.append({
                'series_id': series_id,
                'best_match': best_match,
                'accuracy': best_accuracy
            })

            if verbose:
                print(f"  Series {series_id}: {best_accuracy:.1%} ({best_match}/14)")

            # Learn
            model.validate_and_learn(series_id, prediction, actual_results)

    avg_accuracy = sum(accuracies) / len(accuracies)
    peak_accuracy = max(accuracies)
    min_accuracy = min(accuracies)

    return {
        'average': avg_accuracy,
        'peak': peak_accuracy,
        'min': min_accuracy,
        'series_details': series_details,
        'position_analysis': model.get_position_analysis()
    }


def main():
    print("=" * 80)
    print("PHASE 2 TEST 2: POSITION-BASED LEARNING")
    print("=" * 80)
    print()
    print("Hypothesis: Numbers prefer certain positions in the 14-number array")
    print("  - Track position preferences during training")
    print("  - Apply position-based scoring bonus (1.0-1.2x)")
    print("  - Example: #01 at position 0 vs position 13")
    print()
    print("Baseline: 73.214% (seed 999)")
    print("Target: >73.214% to demonstrate improvement")
    print()

    # Load data
    print("Loading data...")
    all_series_data = load_all_data()
    if not all_series_data:
        print("❌ Failed to load data")
        return
    print(f"✅ Loaded {len(all_series_data)} series")

    # Run test
    print("\nRunning position-based learning test with seed 999...")
    result = run_position_based_test(all_series_data, verbose=True)

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    # Performance metrics
    print(f"Average Performance: {result['average']:.3%}")
    print(f"Peak Performance:    {result['peak']:.3%}")
    print(f"Min Performance:     {result['min']:.3%}")
    print()

    # Comparison to baseline
    baseline = 0.73214
    improvement = result['average'] - baseline
    improvement_pct = (improvement / baseline) * 100

    print(f"Baseline:         {baseline:.3%}")
    print(f"Position-Based:   {result['average']:.3%}")
    print(f"Difference:       {improvement:+.3%} ({improvement_pct:+.2f}%)")
    print()

    if result['average'] > baseline:
        print(f"✅ IMPROVEMENT: +{improvement:.3%} over baseline!")
        print("   Position-based learning shows positive impact")
    elif abs(improvement) < 0.001:
        print(f"➖ NEUTRAL: No significant change")
        print("   Position-based learning has no impact on this dataset")
    else:
        print(f"❌ REGRESSION: {improvement:.3%} worse than baseline")
        print("   Position-based learning negatively impacts performance")
    print()

    # Position analysis
    print("=" * 80)
    print("POSITION PREFERENCE ANALYSIS (Sample)")
    print("=" * 80)
    print()

    sample_numbers = [1, 7, 14, 21, 25]
    for num in sample_numbers:
        if num in result['position_analysis']:
            data = result['position_analysis'][num]
            print(f"Number {num:02d} (appeared {data['total_appearances']} times):")
            for pos_data in data['top_positions']:
                print(f"  Position {pos_data['position']:2d}: {pos_data['count']:3d} times ({pos_data['percentage']:5.1f}%)")
            print()

    # Save results
    output = {
        'test_name': 'position_based_learning',
        'hypothesis': 'Numbers prefer certain positions in the sorted array',
        'baseline': baseline,
        'result': result,
        'improvement': improvement,
        'improvement_pct': improvement_pct,
        'verdict': 'improvement' if result['average'] > baseline else ('neutral' if abs(improvement) < 0.001 else 'regression')
    }

    output_file = Path(__file__).parent / 'test_position_based_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
