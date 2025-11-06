#!/usr/bin/env python3
"""
Phase 2 Test 4: Temporal Decay Weighting

Hypothesis: Recent series are more relevant than older series
- Apply exponential decay (0.95^distance) to weight recent series higher
- Example: Series N-1 gets 0.95 weight, N-10 gets 0.60 weight, N-50 gets 0.08 weight
- Recent patterns should be weighted more heavily than old patterns

Expected: May improve consistency by prioritizing recent trends
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


class TemporalDecayModel(TrueLearningModel):
    """
    Modified TrueLearningModel with temporal decay weighting

    Applies exponential decay to weight recent series more heavily:
    - decay_factor = decay_rate^distance
    - distance = latest_series - current_series
    - Default decay_rate = 0.95 (5% decay per series)
    """

    def __init__(self, decay_rate=0.95):
        super().__init__()
        self.decay_rate = decay_rate
        self.temporal_decay_enabled = True
        self.reference_series = None  # Set during training
        self.decay_history = []

    def learn_from_series(self, series_id: int, combinations: List[List[int]], apply_decay=True):
        """Learn from a series with optional temporal decay"""

        # Calculate decay factor if reference is set and decay is enabled
        decay_factor = 1.0
        if apply_decay and self.temporal_decay_enabled and self.reference_series is not None:
            distance = self.reference_series - series_id
            if distance > 0:
                decay_factor = self.decay_rate ** distance
                self.decay_history.append({
                    'series_id': series_id,
                    'distance': distance,
                    'decay_factor': decay_factor
                })

        # Store original learning rate
        original_lr = self.learning_rate

        # Apply decay to learning rate (effectively weights this series)
        self.learning_rate = original_lr * decay_factor

        # Call parent's learning
        super().learn_from_series(series_id, combinations)

        # Restore original learning rate
        self.learning_rate = original_lr

    def get_decay_stats(self) -> Dict:
        """Get statistics about temporal decay application"""
        if not self.decay_history:
            return {}

        return {
            'total_series_with_decay': len(self.decay_history),
            'decay_rate': self.decay_rate,
            'min_decay': min(h['decay_factor'] for h in self.decay_history),
            'max_decay': max(h['decay_factor'] for h in self.decay_history),
            'avg_decay': sum(h['decay_factor'] for h in self.decay_history) / len(self.decay_history)
        }


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


def run_temporal_decay_test(all_series_data, decay_rate=0.95, verbose=True):
    """Run single test with temporal decay weighting"""
    random.seed(999)  # Same seed as baseline

    validation_window = 8
    latest_series = 3144
    validation_start = latest_series - validation_window + 1  # 3137

    # Initialize model with temporal decay
    model = TemporalDecayModel(decay_rate=decay_rate)
    model.reference_series = validation_start - 1  # 3136 (last training series)

    if verbose:
        print(f"\n⏰ Temporal decay enabled")
        print(f"   Decay rate: {decay_rate} (per series)")
        print(f"   Reference series: {model.reference_series}")
        print(f"   Example decay factors:")
        print(f"     - Series 3136 (distance=0): {decay_rate**0:.3f} (100%)")
        print(f"     - Series 3130 (distance=6): {decay_rate**6:.3f} ({decay_rate**6*100:.1f}%)")
        print(f"     - Series 3100 (distance=36): {decay_rate**36:.3f} ({decay_rate**36*100:.1f}%)")
        print(f"     - Series 3000 (distance=136): {decay_rate**136:.4f} ({decay_rate**136*100:.2f}%)")
        print()

    # Bulk training with temporal decay
    for series in all_series_data:
        if series['series_id'] < validation_start:
            model.learn_from_series(series['series_id'], series['events'], apply_decay=True)

    # Show decay statistics
    if verbose:
        decay_stats = model.get_decay_stats()
        print(f"📊 Decay statistics for {decay_stats['total_series_with_decay']} training series:")
        print(f"   Min decay: {decay_stats['min_decay']:.4f}")
        print(f"   Max decay: {decay_stats['max_decay']:.3f}")
        print(f"   Avg decay: {decay_stats['avg_decay']:.3f}")
        print()

    # Iterative validation (no decay during validation - learn from recent data fully)
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

            # Learn (no decay during validation - these are recent, important series)
            model.learn_from_series(series_id, actual_results, apply_decay=False)

    avg_accuracy = sum(accuracies) / len(accuracies)
    peak_accuracy = max(accuracies)
    min_accuracy = min(accuracies)

    return {
        'decay_rate': decay_rate,
        'average': avg_accuracy,
        'peak': peak_accuracy,
        'min': min_accuracy,
        'series_details': series_details,
        'decay_stats': model.get_decay_stats()
    }


def main():
    print("=" * 80)
    print("PHASE 2 TEST 4: TEMPORAL DECAY WEIGHTING")
    print("=" * 80)
    print()
    print("Hypothesis: Recent series are more relevant than older series")
    print("  - Apply exponential decay: decay_factor = 0.95^distance")
    print("  - Recent series weighted higher than old series")
    print("  - Example: Series N-1 gets 95% weight, N-50 gets 8% weight")
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

    # Test with standard decay rate (0.95)
    print("\nRunning temporal decay test with seed 999...")
    result = run_temporal_decay_test(all_series_data, decay_rate=0.95, verbose=True)

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

    print(f"Baseline:        {baseline:.3%}")
    print(f"Temporal Decay:  {result['average']:.3%} (decay={result['decay_rate']})")
    print(f"Difference:      {improvement:+.3%} ({improvement_pct:+.2f}%)")
    print()

    if result['average'] > baseline:
        print(f"✅ IMPROVEMENT: +{improvement:.3%} over baseline!")
        print("   Temporal decay weighting shows positive impact")
    elif abs(improvement) < 0.001:
        print(f"➖ NEUTRAL: No significant change")
        print("   Temporal decay has no impact on this dataset")
    else:
        print(f"❌ REGRESSION: {improvement:.3%} worse than baseline")
        print("   Temporal decay negatively impacts performance")
    print()

    # Test different decay rates
    print("=" * 80)
    print("TESTING ALTERNATIVE DECAY RATES")
    print("=" * 80)
    print()

    decay_rates = [0.90, 0.95, 0.97, 0.99]
    results_by_rate = []

    for rate in decay_rates:
        print(f"Testing decay rate: {rate}")
        test_result = run_temporal_decay_test(all_series_data, decay_rate=rate, verbose=False)
        results_by_rate.append(test_result)
        print(f"  Result: {test_result['average']:.3%} ({(test_result['average'] - baseline)*100:+.2f}%)")
        print()

    # Find best decay rate
    best_result = max(results_by_rate, key=lambda r: r['average'])
    print(f"Best decay rate: {best_result['decay_rate']} → {best_result['average']:.3%}")
    print()

    # Save results
    output = {
        'test_name': 'temporal_decay_weighting',
        'hypothesis': 'Recent series more relevant than old series',
        'baseline': baseline,
        'standard_result': result,
        'all_decay_rates': results_by_rate,
        'best_decay_rate': best_result['decay_rate'],
        'best_performance': best_result['average'],
        'improvement': best_result['average'] - baseline,
        'improvement_pct': ((best_result['average'] - baseline) / baseline) * 100,
        'verdict': 'improvement' if best_result['average'] > baseline else ('neutral' if abs(best_result['average'] - baseline) < 0.001 else 'regression')
    }

    output_file = Path(__file__).parent / 'test_temporal_decay_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
