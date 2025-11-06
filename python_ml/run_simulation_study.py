#!/usr/bin/env python3
"""
Comprehensive simulation study: Test alternative architectures
Compare all models on same validation data (Series 3137-3145)
"""

import json
import random
from pathlib import Path
from collections import Counter
from true_learning_model import TrueLearningModel
from simulation_models import (
    PureFrequencyModel,
    WeightedRandomModel,
    TrendBasedModel,
    AdaptiveLearningRateModel,
    EnsembleVotingModel,
    PatternRecognitionModel,
    MomentumTrackerModel,
)

# Load historical data
json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

with open(json_path, 'r') as f:
    json_data = json.load(f)

all_series_data = []
for series in json_data.get('data', []):
    series_id = series['series_id']
    events = [event['numbers'] for event in series['events']]
    all_series_data.append({'series_id': series_id, 'events': events})

# Add Series 3144 and 3145
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]

SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
]

all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

print("=" * 80)
print("COMPREHENSIVE SIMULATION STUDY")
print("=" * 80)
print()
print("Testing alternative architectures to find optimal approach")
print(f"Training data: Series 2898-3136 ({len([s for s in all_series_data if s['series_id'] < 3137])} series)")
print("Validation data: Series 3137-3145 (9 series)")
print()

# Initialize all models
models = [
    ("Pure Frequency", PureFrequencyModel()),
    ("Weighted Random", WeightedRandomModel()),
    ("Trend (decay=0.90)", TrendBasedModel(decay_rate=0.90)),
    ("Trend (decay=0.95)", TrendBasedModel(decay_rate=0.95)),
    ("Adaptive Learning Rate", AdaptiveLearningRateModel()),
    ("Ensemble Voting", EnsembleVotingModel()),
    ("Pattern Recognition", PatternRecognitionModel()),
    ("Momentum (window=3)", MomentumTrackerModel(window=3)),
    ("Momentum (window=5)", MomentumTrackerModel(window=5)),
]

# Add Phase 1 Pure as baseline
class Phase1PureWrapper:
    """Wrapper for TrueLearningModel to match interface"""
    def __init__(self):
        self.model = None

    def train(self, series_data):
        random.seed(999)
        self.model = TrueLearningModel()
        for series in series_data:
            self.model.learn_from_series(series['series_id'], series['events'])

    def predict(self, target_series_id):
        return self.model.predict_best_combination(target_series_id)

    def learn_from_result(self, prediction, actual_events):
        # Phase 1 doesn't have this method, it uses validate_and_learn
        # We'll handle this specially in the main loop
        pass

    def get_name(self):
        return "Phase 1 Pure (Baseline)"

models.insert(0, ("Phase 1 Pure (Baseline)", Phase1PureWrapper()))

# Prepare training/validation split
validation_start = 3137
training_data = [s for s in all_series_data if s['series_id'] < validation_start]
validation_data = [s for s in all_series_data if 3137 <= s['series_id'] <= 3145]

print(f"Models to test: {len(models)}")
for name, model in models:
    print(f"  - {name}")
print()

# Run simulations
results = {}

for model_name, model in models:
    print("=" * 80)
    print(f"Testing: {model_name}")
    print("=" * 80)
    print()

    # Reset random seed for each model
    random.seed(999)

    # Train on bulk data
    print(f"Training on {len(training_data)} series...")
    model.train(training_data)
    print("Training complete.")
    print()

    # Iterative validation
    series_results = []

    for series_data in validation_data:
        series_id = series_data['series_id']
        actual_events = series_data['events']

        # Generate prediction
        prediction = model.predict(series_id)

        # Calculate accuracy
        accuracies = []
        for event in actual_events:
            matches = len(set(prediction) & set(event))
            accuracy = matches / 14.0
            accuracies.append(accuracy)

        best_accuracy = max(accuracies)
        avg_accuracy = sum(accuracies) / len(accuracies)

        # Calculate critical number hit rate
        freq_in_series = Counter()
        for event in actual_events:
            freq_in_series.update(event)

        critical_numbers = {num for num, count in freq_in_series.items() if count >= 5}
        critical_hit = sum(1 for num in critical_numbers if num in prediction)
        critical_rate = critical_hit / len(critical_numbers) if critical_numbers else 0

        series_results.append({
            'series_id': series_id,
            'prediction': prediction,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy,
            'critical_numbers': len(critical_numbers),
            'critical_hit': critical_hit,
            'critical_rate': critical_rate,
        })

        print(f"  Series {series_id}: Best={best_accuracy:.1%}, Avg={avg_accuracy:.1%}, Critical={critical_hit}/{len(critical_numbers)}")

        # Learn from result (if model supports it)
        if hasattr(model, 'learn_from_result') and model_name != "Phase 1 Pure (Baseline)":
            model.learn_from_result(prediction, actual_events)
        elif model_name == "Phase 1 Pure (Baseline)":
            # Special handling for Phase 1
            model.model.validate_and_learn(series_id, prediction, actual_events)

    # Calculate overall metrics
    avg_best = sum(r['best_accuracy'] for r in series_results) / len(series_results)
    avg_avg = sum(r['avg_accuracy'] for r in series_results) / len(series_results)
    series_3145_result = [r for r in series_results if r['series_id'] == 3145][0]

    # Calculate variance
    variance = sum((r['best_accuracy'] - avg_best) ** 2 for r in series_results) / len(series_results)
    std_dev = variance ** 0.5

    print()
    print(f"📊 Overall Best Average: {avg_best:.1%}")
    print(f"📊 Overall Average: {avg_avg:.1%}")
    print(f"📊 Stability (Std Dev): {std_dev:.2%}")
    print(f"📊 Series 3145 Performance: {series_3145_result['best_accuracy']:.1%}")
    print()

    results[model_name] = {
        'avg_best': avg_best,
        'avg_avg': avg_avg,
        'std_dev': std_dev,
        'series_3145_best': series_3145_result['best_accuracy'],
        'series_3145_avg': series_3145_result['avg_accuracy'],
        'series_results': series_results,
    }

# Save results
output_path = Path(__file__).parent / "simulation_results.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("SIMULATION STUDY COMPLETE")
print("=" * 80)
print()

# Rank models
ranked = sorted(results.items(), key=lambda x: x[1]['avg_best'], reverse=True)

print("📊 OVERALL RANKING (by Best Match Average):")
print()
print("Rank | Model                          | Avg Best | Series 3145 | Stability")
print("-----|--------------------------------|----------|-------------|----------")
for i, (name, data) in enumerate(ranked, 1):
    print(f" {i:2d}  | {name:30s} | {data['avg_best']:7.1%} | {data['series_3145_best']:10.1%} | {data['std_dev']:8.2%}")

print()
print("=" * 80)
print("KEY FINDINGS")
print("=" * 80)
print()

# Find best model
best_model_name, best_model_data = ranked[0]
baseline_data = results.get("Phase 1 Pure (Baseline)")

if baseline_data:
    improvement = best_model_data['avg_best'] - baseline_data['avg_best']
    print(f"🏆 Best Model: {best_model_name}")
    print(f"   Performance: {best_model_data['avg_best']:.1%}")
    print(f"   vs Baseline: {improvement:+.1%}")
    print(f"   Series 3145: {best_model_data['series_3145_best']:.1%}")
    print(f"   Stability: {best_model_data['std_dev']:.2%}")
    print()

    if improvement > 0.02:
        print("✅ SIGNIFICANT IMPROVEMENT FOUND")
        print(f"   {best_model_name} outperforms baseline by {improvement:.1%}")
        print(f"   Recommendation: Consider deploying {best_model_name}")
    elif improvement > 0:
        print("⚠️  MARGINAL IMPROVEMENT")
        print(f"   {best_model_name} slightly better (+{improvement:.1%})")
        print(f"   May not justify switching from current system")
    else:
        print("❌ NO IMPROVEMENT")
        print("   All alternatives perform at or below baseline")
        print("   Current Phase 1 Pure is optimal")

print()
print(f"📁 Detailed results saved to: {output_path}")
print()
