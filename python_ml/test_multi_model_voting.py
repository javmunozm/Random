#!/usr/bin/env python3
"""
Test multi-model voting with different hyperparameters.

Instead of voting across seeds (tested earlier, failed),
vote across models with different hyperparameter configurations:
- Different recent window sizes (60, 70, 80)
- Different candidate pools (1.5k, 2k, 2.5k)
- Different learning rates (0.08, 0.10, 0.12)

Hypothesis: Models with different biases might capture different patterns.
Voting might create more robust prediction.

Current best: 70 series + 2k candidates → 58.0%
"""

import json
import sys
import random
from pathlib import Path
from collections import Counter
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


def train_and_predict(all_series_data, series_id, config, seed=999):
    """Train model with specific config and predict"""
    random.seed(seed)
    model = TrueLearningModel()

    # Apply configuration
    recent_count = config['recent_count']
    model.CANDIDATES_TO_SCORE = config['candidates_to_score']
    model.CANDIDATE_POOL_SIZE = config['candidate_pool_size']
    model.learning_rate = config['learning_rate']

    # Training
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1
    training_start = validation_start - recent_count

    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]
    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    # Learn from earlier validation series
    if series_id > validation_start:
        validation_data = [s for s in all_series_data
                          if validation_start <= s['series_id'] < series_id]
        for series in validation_data:
            model.learn_from_series(series['series_id'], series['events'])

    # Predict
    prediction = model.predict_best_combination(series_id)
    return prediction


def ensemble_predict(all_series_data, series_id, model_configs):
    """Generate ensemble prediction via voting"""
    predictions = []

    for config in model_configs:
        pred = train_and_predict(all_series_data, series_id, config)
        predictions.append(pred)

    # Vote
    number_votes = Counter()
    for pred in predictions:
        for num in pred:
            number_votes[num] += 1

    # Top 14 by votes
    sorted_numbers = sorted(number_votes.items(), key=lambda x: (-x[1], x[0]))
    ensemble = sorted([num for num, _ in sorted_numbers[:14]])

    return ensemble


def test_ensemble(config_name, model_configs):
    """Test ensemble approach"""
    print(f"Testing {config_name:45} ... ", end='', flush=True)

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Validation
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1

    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    results = []
    for series in validation_series:
        series_id = series['series_id']
        actual_events = series['events']

        prediction = ensemble_predict(all_series_data, series_id, model_configs)

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

    overall_actual_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print(f"{overall_actual_avg*100:.1f}%")

    return {
        'config': config_name,
        'actual_avg': overall_actual_avg,
        'results': results
    }


def main():
    """Test multi-model voting"""
    print("="*80)
    print("MULTI-MODEL VOTING - ROUND 3")
    print("="*80)
    print()
    print("Current best: 70 series + 2k candidates → 58.0%")
    print("Testing: Voting across models with different hyperparameters")
    print("="*80)
    print()

    all_results = []

    # Define model configurations
    config_60_1_5k = {
        'recent_count': 60,
        'candidates_to_score': 1500,
        'candidate_pool_size': 15000,
        'learning_rate': 0.10
    }

    config_70_2k = {
        'recent_count': 70,
        'candidates_to_score': 2000,
        'candidate_pool_size': 20000,
        'learning_rate': 0.10
    }

    config_80_2_5k = {
        'recent_count': 80,
        'candidates_to_score': 2500,
        'candidate_pool_size': 25000,
        'learning_rate': 0.10
    }

    config_70_2k_lr08 = {
        'recent_count': 70,
        'candidates_to_score': 2000,
        'candidate_pool_size': 20000,
        'learning_rate': 0.08
    }

    config_70_2k_lr12 = {
        'recent_count': 70,
        'candidates_to_score': 2000,
        'candidate_pool_size': 20000,
        'learning_rate': 0.12
    }

    # Test 1: Baseline (single model)
    all_results.append(test_ensemble(
        "Single model (70 + 2k)",
        [config_70_2k]
    ))

    # Test 2: 3 models with different window sizes
    all_results.append(test_ensemble(
        "Ensemble: 3 windows (60, 70, 80)",
        [config_60_1_5k, config_70_2k, config_80_2_5k]
    ))

    # Test 3: 3 models with different LRs
    all_results.append(test_ensemble(
        "Ensemble: 3 LRs (0.08, 0.10, 0.12)",
        [config_70_2k_lr08, config_70_2k, config_70_2k_lr12]
    ))

    # Test 4: All 5 models
    all_results.append(test_ensemble(
        "Ensemble: All 5 models",
        [config_60_1_5k, config_70_2k, config_80_2_5k,
         config_70_2k_lr08, config_70_2k_lr12]
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
        print(f"   Voting doesn't help")

    # Save results
    output_file = "test_multi_model_voting_results.json"
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
