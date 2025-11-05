#!/usr/bin/env python3
"""
Phase 2 Test 1: Adaptive Learning Rate

Hypothesis: Adjust learning rate based on prediction accuracy
- High accuracy series (>75%) → lower learning rate (0.05) - don't change what works
- Medium accuracy series (70-75%) → normal learning rate (0.10)
- Low accuracy series (<70%) → higher learning rate (0.20) - learn more aggressively

Expected: May improve consistency by adapting to prediction quality
Baseline: 73.214% (seed 999, perfectly stable)
Target: >73.214% to show improvement
"""

import json
import random
from pathlib import Path
from typing import List, Dict
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


class AdaptiveLearningRateModel(TrueLearningModel):
    """
    Modified TrueLearningModel with adaptive learning rate

    Adjusts learning_rate based on prediction accuracy:
    - accuracy > 0.75: learning_rate = 0.05 (conservative)
    - accuracy > 0.70: learning_rate = 0.10 (normal)
    - accuracy ≤ 0.70: learning_rate = 0.20 (aggressive)
    """

    def __init__(self):
        super().__init__()
        self.base_learning_rate = 0.10  # Store original rate
        self.learning_rate_history = []  # Track rate changes

    def validate_and_learn(self, series_id: int, prediction: List[int], actual_results: List[List[int]]):
        """Validate prediction and learn with adaptive rate"""
        # Calculate accuracy first
        best_match = max(actual_results, key=lambda actual: len(set(prediction) & set(actual)))
        accuracy = len(set(prediction) & set(best_match)) / 14.0

        # Adaptive learning rate based on accuracy
        if accuracy > 0.75:
            # High accuracy - conservative learning (don't change what works)
            self.learning_rate = 0.05
            rate_label = "CONSERVATIVE"
        elif accuracy > 0.70:
            # Medium accuracy - normal learning
            self.learning_rate = 0.10
            rate_label = "NORMAL"
        else:
            # Low accuracy - aggressive learning (learn more from failures)
            self.learning_rate = 0.20
            rate_label = "AGGRESSIVE"

        self.learning_rate_history.append({
            'series_id': series_id,
            'accuracy': accuracy,
            'learning_rate': self.learning_rate,
            'label': rate_label
        })

        # Update learning_rate BEFORE calling parent (parent uses self.learning_rate)
        # Now call parent's learning logic with adjusted rate
        super().validate_and_learn(series_id, prediction, actual_results)

        # Add our custom output after parent's output
        print(f"   🎓 Adaptive Learning Rate: {self.learning_rate:.2f} ({rate_label})")


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


def run_adaptive_test(all_series_data, verbose=True):
    """Run single test with adaptive learning rate"""
    random.seed(999)  # Same seed as baseline

    validation_window = 8
    latest_series = 3144
    validation_start = latest_series - validation_window + 1  # 3137

    # Initialize adaptive model
    model = AdaptiveLearningRateModel()

    # Bulk training
    for series in all_series_data:
        if series['series_id'] < validation_start:
            model.learn_from_series(series['series_id'], series['events'])

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

            # Learn with adaptive rate
            model.validate_and_learn(series_id, prediction, actual_results)

    avg_accuracy = sum(accuracies) / len(accuracies)
    peak_accuracy = max(accuracies)
    min_accuracy = min(accuracies)

    return {
        'average': avg_accuracy,
        'peak': peak_accuracy,
        'min': min_accuracy,
        'series_details': series_details,
        'learning_rate_history': model.learning_rate_history
    }


def main():
    print("=" * 80)
    print("PHASE 2 TEST 1: ADAPTIVE LEARNING RATE")
    print("=" * 80)
    print()
    print("Hypothesis: Adjust learning rate based on prediction accuracy")
    print("  - High accuracy (>75%): 0.05 learning rate (conservative)")
    print("  - Medium accuracy (70-75%): 0.10 learning rate (normal)")
    print("  - Low accuracy (<70%): 0.20 learning rate (aggressive)")
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
    print()

    # Run test
    print("Running adaptive learning rate test with seed 999...")
    print()
    result = run_adaptive_test(all_series_data)

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

    print(f"Baseline:     {baseline:.3%}")
    print(f"Adaptive LR:  {result['average']:.3%}")
    print(f"Difference:   {improvement:+.3%} ({improvement_pct:+.2f}%)")
    print()

    if result['average'] > baseline:
        print(f"✅ IMPROVEMENT: +{improvement:.3%} over baseline!")
        print("   Adaptive learning rate shows positive impact")
    elif abs(improvement) < 0.001:
        print(f"➖ NEUTRAL: No significant change")
        print("   Adaptive learning rate has no impact on this dataset")
    else:
        print(f"❌ REGRESSION: {improvement:.3%} worse than baseline")
        print("   Adaptive learning rate negatively impacts performance")
    print()

    # Learning rate usage analysis
    print("=" * 80)
    print("LEARNING RATE USAGE ANALYSIS")
    print("=" * 80)
    print()

    lr_counts = {'CONSERVATIVE': 0, 'NORMAL': 0, 'AGGRESSIVE': 0}
    for entry in result['learning_rate_history']:
        lr_counts[entry['label']] += 1

    print(f"Conservative (0.05): {lr_counts['CONSERVATIVE']}/8 series ({lr_counts['CONSERVATIVE']/8*100:.1f}%)")
    print(f"Normal (0.10):       {lr_counts['NORMAL']}/8 series ({lr_counts['NORMAL']/8*100:.1f}%)")
    print(f"Aggressive (0.20):   {lr_counts['AGGRESSIVE']}/8 series ({lr_counts['AGGRESSIVE']/8*100:.1f}%)")
    print()

    print("Per-Series Learning Rates:")
    for entry in result['learning_rate_history']:
        print(f"  Series {entry['series_id']}: {entry['accuracy']:.1%} → {entry['learning_rate']:.2f} ({entry['label']})")
    print()

    # Save results
    output = {
        'test_name': 'adaptive_learning_rate',
        'hypothesis': 'Adjust learning rate based on prediction accuracy',
        'baseline': baseline,
        'result': result,
        'improvement': improvement,
        'improvement_pct': improvement_pct,
        'verdict': 'improvement' if result['average'] > baseline else ('neutral' if abs(improvement) < 0.001 else 'regression')
    }

    output_file = Path(__file__).parent / 'test_adaptive_lr_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
