#!/usr/bin/env python3
"""
Phase 2 Test 5: Cross-Series Momentum Tracking

Hypothesis: Patterns that appear in recent consecutive series have "momentum"
- Track which numbers appeared in last N series
- If a number appeared in 2+ of last 3 series, it has momentum
- Apply momentum bonus to candidate scoring

Expected: May capture short-term trends
Baseline: 73.214% (seed 999, perfectly stable)
Target: >73.214% to show improvement
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Set
from collections import deque, Counter
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


class CrossSeriesMomentumModel(TrueLearningModel):
    """
    Modified TrueLearningModel with cross-series momentum tracking

    Tracks which numbers appear consistently across recent series
    and applies momentum bonus to candidates containing those numbers.
    """

    def __init__(self, momentum_window=3, momentum_threshold=2):
        super().__init__()
        self.momentum_window = momentum_window  # Look back N series
        self.momentum_threshold = momentum_threshold  # Appear in M series for momentum
        self.recent_series_numbers = deque(maxlen=momentum_window)
        self.momentum_enabled = True

    def learn_from_series(self, series_id: int, combinations: List[List[int]]):
        """Learn from series and track numbers for momentum"""
        # Call parent's learning
        super().learn_from_series(series_id, combinations)

        # Extract all unique numbers from this series
        if self.momentum_enabled:
            series_numbers = set()
            for combo in combinations:
                series_numbers.update(combo)

            self.recent_series_numbers.append({
                'series_id': series_id,
                'numbers': series_numbers
            })

    def get_momentum_numbers(self) -> Dict[int, int]:
        """
        Get numbers with momentum (appeared in threshold+ recent series)
        Returns: {number: appearance_count}
        """
        if len(self.recent_series_numbers) < self.momentum_threshold:
            return {}

        number_counts = Counter()
        for series_data in self.recent_series_numbers:
            for number in series_data['numbers']:
                number_counts[number] += 1

        # Return numbers that meet threshold
        momentum_numbers = {
            num: count
            for num, count in number_counts.items()
            if count >= self.momentum_threshold
        }

        return momentum_numbers

    def _calculate_momentum_bonus(self, combination: List[int]) -> float:
        """
        Calculate momentum bonus multiplier for a candidate

        Returns multiplier: 1.0 (no momentum) to 1.3 (strong momentum)
        """
        if not self.momentum_enabled:
            return 1.0

        momentum_numbers = self.get_momentum_numbers()
        if not momentum_numbers:
            return 1.0

        # Count how many numbers in candidate have momentum
        momentum_count = sum(1 for num in combination if num in momentum_numbers)

        if momentum_count == 0:
            return 1.0

        # Calculate bonus based on momentum count
        # More momentum numbers → higher bonus
        # Max bonus: 30% (1.3x) if 10+ numbers have momentum
        momentum_ratio = momentum_count / 14.0  # 14 numbers in combination
        bonus = 1.0 + (momentum_ratio * 0.3)  # 1.0 to 1.3

        return min(bonus, 1.3)  # Cap at 1.3x

    def _calculate_score(self, combination: List[int]) -> float:
        """Score a candidate with momentum bonus"""
        # Get base score from parent
        base_score = super()._calculate_score(combination)

        # Apply momentum bonus
        momentum_bonus = self._calculate_momentum_bonus(combination)

        return base_score * momentum_bonus


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


def run_momentum_test(all_series_data, momentum_window=3, momentum_threshold=2, verbose=True):
    """Run single test with cross-series momentum"""
    random.seed(999)  # Same seed as baseline

    validation_window = 8
    latest_series = 3144
    validation_start = latest_series - validation_window + 1  # 3137

    # Initialize model
    model = CrossSeriesMomentumModel(
        momentum_window=momentum_window,
        momentum_threshold=momentum_threshold
    )

    if verbose:
        print(f"\n🔄 Cross-series momentum enabled")
        print(f"   Momentum window: {momentum_window} series")
        print(f"   Momentum threshold: {momentum_threshold}+ appearances")
        print(f"   Bonus: Up to 1.3x for high-momentum candidates")
        print()

    # Bulk training
    for series in all_series_data:
        if series['series_id'] < validation_start:
            model.learn_from_series(series['series_id'], series['events'])

    if verbose:
        momentum_nums = model.get_momentum_numbers()
        print(f"📊 Momentum numbers after training ({len(momentum_nums)} numbers):")
        if momentum_nums:
            sorted_momentum = sorted(momentum_nums.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"   Top 10: {', '.join(f'#{num:02d}({count})' for num, count in sorted_momentum)}")
        print()

    # Iterative validation
    accuracies = []
    series_details = []

    for series_data in all_series_data:
        if validation_start <= series_data['series_id'] <= latest_series:
            series_id = series_data['series_id']
            actual_results = series_data['events']

            # Show momentum before prediction
            if verbose:
                momentum_nums = model.get_momentum_numbers()
                print(f"  Series {series_id} momentum: {len(momentum_nums)} numbers")

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
                print(f"    Result: {best_accuracy:.1%} ({best_match}/14)")

            # Learn
            model.learn_from_series(series_id, actual_results)
            model.validate_and_learn(series_id, prediction, actual_results)

    avg_accuracy = sum(accuracies) / len(accuracies)
    peak_accuracy = max(accuracies)
    min_accuracy = min(accuracies)

    return {
        'momentum_window': momentum_window,
        'momentum_threshold': momentum_threshold,
        'average': avg_accuracy,
        'peak': peak_accuracy,
        'min': min_accuracy,
        'series_details': series_details
    }


def main():
    print("=" * 80)
    print("PHASE 2 TEST 5: CROSS-SERIES MOMENTUM TRACKING")
    print("=" * 80)
    print()
    print("Hypothesis: Patterns from recent series have momentum")
    print("  - Track numbers across last N series")
    print("  - Apply bonus if number appeared in M+ of last N")
    print("  - Default: Window=3, Threshold=2 (appear in 2 of last 3)")
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

    # Test standard configuration
    print("\nRunning cross-series momentum test with seed 999...")
    result = run_momentum_test(all_series_data, momentum_window=3, momentum_threshold=2, verbose=True)

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

    print(f"Baseline:       {baseline:.3%}")
    print(f"Momentum:       {result['average']:.3%} (win={result['momentum_window']}, thresh={result['momentum_threshold']})")
    print(f"Difference:     {improvement:+.3%} ({improvement_pct:+.2f}%)")
    print()

    if result['average'] > baseline:
        print(f"✅ IMPROVEMENT: +{improvement:.3%} over baseline!")
        print("   Cross-series momentum shows positive impact")
    elif abs(improvement) < 0.001:
        print(f"➖ NEUTRAL: No significant change")
        print("   Cross-series momentum has no impact on this dataset")
    else:
        print(f"❌ REGRESSION: {improvement:.3%} worse than baseline")
        print("   Cross-series momentum negatively impacts performance")
    print()

    # Test alternative configurations
    print("=" * 80)
    print("TESTING ALTERNATIVE CONFIGURATIONS")
    print("=" * 80)
    print()

    configs = [
        (2, 2),  # Last 2, appear in 2
        (3, 2),  # Last 3, appear in 2
        (3, 3),  # Last 3, appear in all 3
        (5, 3),  # Last 5, appear in 3
    ]

    results_by_config = []
    for window, threshold in configs:
        print(f"Testing window={window}, threshold={threshold}")
        test_result = run_momentum_test(all_series_data, momentum_window=window, momentum_threshold=threshold, verbose=False)
        results_by_config.append(test_result)
        print(f"  Result: {test_result['average']:.3%} ({(test_result['average'] - baseline)*100:+.2f}%)")
        print()

    # Find best configuration
    best_result = max(results_by_config, key=lambda r: r['average'])
    print(f"Best config: window={best_result['momentum_window']}, threshold={best_result['momentum_threshold']} → {best_result['average']:.3%}")
    print()

    # Save results
    output = {
        'test_name': 'cross_series_momentum',
        'hypothesis': 'Recent patterns have momentum',
        'baseline': baseline,
        'standard_result': result,
        'all_configs': results_by_config,
        'best_config': {
            'window': best_result['momentum_window'],
            'threshold': best_result['momentum_threshold']
        },
        'best_performance': best_result['average'],
        'improvement': best_result['average'] - baseline,
        'improvement_pct': ((best_result['average'] - baseline) / baseline) * 100,
        'verdict': 'improvement' if best_result['average'] > baseline else ('neutral' if abs(best_result['average'] - baseline) < 0.001 else 'regression')
    }

    output_file = Path(__file__).parent / 'test_cross_series_momentum_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
