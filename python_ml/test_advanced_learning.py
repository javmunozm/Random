#!/usr/bin/env python3
"""
Test advanced learning strategies:
1. Progressive learning rate decay (start high, decrease over iterations)
2. Momentum-based updates (smooth weight changes)
3. Temperature-based softmax selection (probabilistic candidate selection)

Current best: 70 series + 2k candidates → 58.0%
Target: Beat 58.0%
"""

import json
import sys
import random
import math
from pathlib import Path
from true_learning_model import TrueLearningModel

# Series data
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


def load_database_export():
    """Load data from JSON export"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found: {json_path}")
        return []

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    series_list = []
    for series in json_data.get('data', []):
        series_id = series['series_id']
        events = []
        for event in series['events']:
            numbers = event['numbers']
            events.append(numbers)

        series_list.append({
            'series_id': series_id,
            'events': events
        })

    return series_list


def test_progressive_lr(config_name, lr_start, lr_end, seed=999):
    """Test progressive learning rate decay"""
    print(f"Testing {config_name:45} ... ", end='', flush=True)

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Fixed settings
    recent_count = 70
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1
    training_start = validation_start - recent_count

    # Initialize model
    random.seed(seed)
    model = TrueLearningModel()
    model.CANDIDATES_TO_SCORE = 2000
    model.CANDIDATE_POOL_SIZE = 20000

    # Phase 1: Bulk training
    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]

    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    # Phase 2: Iterative validation with progressive LR
    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    results = []
    total_iterations = len(validation_series)

    for i, series in enumerate(validation_series):
        series_id = series['series_id']
        actual_events = series['events']

        # Calculate progressive LR
        progress = i / (total_iterations - 1) if total_iterations > 1 else 0
        current_lr = lr_start + (lr_end - lr_start) * progress
        model.learning_rate = current_lr

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Calculate accuracy
        event_accuracies = []
        for actual in actual_events:
            matches = len(set(prediction) & set(actual))
            accuracy = matches / 14
            event_accuracies.append(accuracy)

        best_accuracy = max(event_accuracies)
        avg_accuracy = sum(event_accuracies) / len(event_accuracies)

        results.append({
            'series_id': series_id,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy
        })

        # Learn from this series
        model.learn_from_series(series_id, actual_events)

    # Calculate overall metrics
    overall_actual_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print(f"{overall_actual_avg*100:.1f}%")

    return {
        'config': config_name,
        'actual_avg': overall_actual_avg,
        'results': results
    }


def test_exponential_decay_weights(config_name, decay_rate, seed=999):
    """Test exponential decay for historical series weighting"""
    print(f"Testing {config_name:45} ... ", end='', flush=True)

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Fixed settings
    recent_count = 70
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1
    training_start = validation_start - recent_count

    # Initialize model
    random.seed(seed)
    model = TrueLearningModel()
    model.CANDIDATES_TO_SCORE = 2000
    model.CANDIDATE_POOL_SIZE = 20000

    # Phase 1: Bulk training with exponential decay
    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]

    # Apply exponential decay to learning rate based on data age
    for idx, series in enumerate(training_data):
        # More recent = higher weight
        recency_factor = math.exp(-decay_rate * (len(training_data) - idx - 1))
        original_lr = model.learning_rate
        model.learning_rate = original_lr * recency_factor

        model.learn_from_series(series['series_id'], series['events'])

        model.learning_rate = original_lr  # Reset for next

    # Phase 2: Iterative validation
    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    results = []
    for series in validation_series:
        series_id = series['series_id']
        actual_events = series['events']

        prediction = model.predict_best_combination(series_id)

        event_accuracies = []
        for actual in actual_events:
            matches = len(set(prediction) & set(actual))
            accuracy = matches / 14
            event_accuracies.append(accuracy)

        best_accuracy = max(event_accuracies)
        avg_accuracy = sum(event_accuracies) / len(event_accuracies)

        results.append({
            'series_id': series_id,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy
        })

        model.learn_from_series(series_id, actual_events)

    overall_actual_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print(f"{overall_actual_avg*100:.1f}%")

    return {
        'config': config_name,
        'actual_avg': overall_actual_avg,
        'results': results
    }


def main():
    """Test advanced learning strategies"""
    print("="*80)
    print("ADVANCED LEARNING STRATEGIES - ROUND 3")
    print("="*80)
    print()
    print("Current best: 70 series + 2k candidates → 58.0%")
    print("Testing: Progressive LR decay, exponential data weighting")
    print("="*80)
    print()

    all_results = []

    # Baseline
    all_results.append(test_progressive_lr(
        "70 + 2k (baseline, LR=0.10 constant)",
        0.10, 0.10
    ))

    # Progressive LR: Start high, decay to low
    all_results.append(test_progressive_lr(
        "70 + 2k + Progressive LR (0.20→0.05)",
        0.20, 0.05
    ))

    all_results.append(test_progressive_lr(
        "70 + 2k + Progressive LR (0.15→0.08)",
        0.15, 0.08
    ))

    all_results.append(test_progressive_lr(
        "70 + 2k + Progressive LR (0.12→0.08)",
        0.12, 0.08
    ))

    # Inverse progressive: Start low, increase (exploration→exploitation)
    all_results.append(test_progressive_lr(
        "70 + 2k + Inverse LR (0.05→0.15)",
        0.05, 0.15
    ))

    # Exponential decay weighting
    all_results.append(test_exponential_decay_weights(
        "70 + 2k + Exp decay (rate=0.02)",
        0.02
    ))

    all_results.append(test_exponential_decay_weights(
        "70 + 2k + Exp decay (rate=0.05)",
        0.05
    ))

    all_results.append(test_exponential_decay_weights(
        "70 + 2k + Exp decay (rate=0.10)",
        0.10
    ))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - RANKED BY ACTUAL AVERAGE")
    print("="*80)
    print()
    print("Configuration                                    | ACTUAL | vs 58.0%")
    print("-------------------------------------------------|--------|----------")

    sorted_results = sorted(all_results, key=lambda x: x['actual_avg'], reverse=True)
    baseline_actual = 0.580

    for result in sorted_results:
        config = result['config']
        actual = result['actual_avg'] * 100
        vs_baseline = result['actual_avg'] - baseline_actual

        if vs_baseline > 0.01:
            verdict = f"+{vs_baseline*100:.1f}% ✅"
        elif vs_baseline > -0.01:
            verdict = "~same ➖"
        else:
            verdict = f"{vs_baseline*100:.1f}% ❌"

        print(f"  {config:46} | {actual:5.1f}% | {verdict}")

    print()
    print("="*80)
    print("CONCLUSION:")
    print("="*80)

    best = sorted_results[0]
    if best['actual_avg'] > baseline_actual + 0.01:
        print(f"✅ IMPROVEMENT: {best['config']}")
        print(f"   Actual: {best['actual_avg']*100:.1f}% (vs {baseline_actual*100:.1f}% baseline)")
        print(f"   Improvement: +{(best['actual_avg'] - baseline_actual)*100:.1f}%")
    else:
        print(f"➖ NO IMPROVEMENT")
        print(f"   Best: {best['actual_avg']*100:.1f}%")
        print(f"   All within noise of 58.0%")

    # Save results
    output_file = "test_advanced_learning_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'baseline': baseline_actual,
            'results': all_results,
            'best': {
                'config': best['config'],
                'actual_avg': best['actual_avg'],
                'improvement': best['actual_avg'] - baseline_actual
            }
        }, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
