#!/usr/bin/env python3
"""
Test ensemble voting across multiple random seeds.

Hypothesis: Different seeds may capture different patterns. Voting across
multiple seeds might give more robust predictions.

Current baseline: seed 999, 55.7% actual average
Testing: Ensemble of top 5 seeds (999, 42, 2024, 123, 777)
"""

import json
import sys
import random
from pathlib import Path
from true_learning_model import TrueLearningModel
from collections import Counter

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


def train_and_predict_with_seed(all_series_data, series_id, seed):
    """Train model with specific seed and generate prediction"""
    random.seed(seed)
    model = TrueLearningModel()

    # Fixed validation window (8 series)
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1  # 3138

    # Training data (all before validation)
    training_data = [s for s in all_series_data if s['series_id'] < validation_start]
    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    # If predicting a validation series, also learn from earlier validation series
    if series_id >= validation_start:
        validation_data = [s for s in all_series_data
                          if validation_start <= s['series_id'] < series_id]
        for series in validation_data:
            model.learn_from_series(series['series_id'], series['events'])

    # Generate prediction
    prediction = model.predict_best_combination(series_id)
    return prediction


def ensemble_predict(all_series_data, series_id, seeds):
    """Generate ensemble prediction by voting across multiple seeds"""
    # Get predictions from each seed
    predictions = []
    for seed in seeds:
        pred = train_and_predict_with_seed(all_series_data, series_id, seed)
        predictions.append(pred)

    # Count votes for each number
    number_votes = Counter()
    for pred in predictions:
        for num in pred:
            number_votes[num] += 1

    # Select top 14 numbers by vote count
    # In case of ties, select by lower number (deterministic)
    sorted_numbers = sorted(number_votes.items(), key=lambda x: (-x[1], x[0]))
    ensemble_prediction = sorted([num for num, _ in sorted_numbers[:14]])

    return ensemble_prediction, predictions


def test_ensemble(seeds):
    """Test ensemble approach across validation series"""
    print(f"\n{'='*80}")
    print(f"Testing Ensemble of {len(seeds)} seeds: {seeds}")
    print(f"{'='*80}\n")

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Fixed validation window
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1  # 3138

    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    print(f"Validation: Series {validation_start}-{latest_series} ({len(validation_series)} series)")
    print()

    results = []
    for series in validation_series:
        series_id = series['series_id']
        actual_events = series['events']

        print(f"Series {series_id}: Generating ensemble prediction...")

        # Generate ensemble prediction
        prediction, individual_predictions = ensemble_predict(all_series_data, series_id, seeds)

        # Calculate accuracy for each event
        event_accuracies = []
        for actual in actual_events:
            matches = len(set(prediction) & set(actual))
            accuracy = matches / 14
            event_accuracies.append(accuracy)

        best_accuracy = max(event_accuracies)
        avg_accuracy = sum(event_accuracies) / len(event_accuracies)

        print(f"  Best: {best_accuracy*100:.1f}%, Avg: {avg_accuracy*100:.1f}%")

        results.append({
            'series_id': series_id,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy,
            'prediction': prediction,
            'individual_predictions': individual_predictions
        })

    # Calculate overall metrics
    overall_best_avg = sum(r['best_accuracy'] for r in results) / len(results)
    overall_actual_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    # Calculate improvement
    first_half = len(results) // 2
    first_avg = sum(r['avg_accuracy'] for r in results[:first_half]) / first_half
    last_avg = sum(r['avg_accuracy'] for r in results[first_half:]) / (len(results) - first_half)
    improvement = last_avg - first_avg

    print(f"\nResults:")
    print(f"  Best Match Average: {overall_best_avg*100:.1f}% (misleading)")
    print(f"  ACTUAL Average: {overall_actual_avg*100:.1f}% ← REAL METRIC")
    print(f"  Improvement: {improvement*100:+.1f}%")
    print(f"  Seeds used: {len(seeds)}")

    return {
        'seeds': seeds,
        'seed_count': len(seeds),
        'best_match_avg': overall_best_avg,
        'actual_avg': overall_actual_avg,
        'improvement': improvement,
        'results': results
    }


def main():
    """Test ensemble voting approach"""
    print("="*80)
    print("SEED ENSEMBLE VOTING OPTIMIZATION")
    print("="*80)
    print()
    print("Hypothesis: Voting across multiple seeds gives more robust predictions")
    print("Current baseline: seed 999 only, 55.7% actual average")
    print("Testing: Ensembles of 3, 5, 7 seeds")
    print()
    print("CRITICAL: Using ACTUAL average (all 7 events), not 'best match'")
    print("="*80)

    # Top performing seeds from previous study
    top_seeds = [999, 42, 2024, 123, 777, 456, 888]

    # Test different ensemble sizes
    ensemble_configs = [
        [999],  # Baseline (single seed)
        [999, 42, 2024],  # Top 3
        [999, 42, 2024, 123, 777],  # Top 5
        [999, 42, 2024, 123, 777, 456, 888],  # Top 7
    ]

    all_results = []

    for seeds in ensemble_configs:
        result = test_ensemble(seeds)
        all_results.append(result)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - RANKED BY ACTUAL AVERAGE")
    print("="*80)
    print()
    print("Seeds | Best Match | ACTUAL Avg | Improvement | Verdict")
    print("------|------------|------------|-------------|--------")

    # Sort by actual average (descending)
    sorted_results = sorted(all_results, key=lambda x: x['actual_avg'], reverse=True)
    baseline_actual = 0.557  # Current baseline

    for result in sorted_results:
        seed_count = result['seed_count']
        best_match = result['best_match_avg'] * 100
        actual = result['actual_avg'] * 100
        improvement = result['improvement'] * 100
        vs_baseline = result['actual_avg'] - baseline_actual

        if vs_baseline > 0.01:
            verdict = f"+{vs_baseline*100:.1f}% ✅"
        elif vs_baseline > -0.01:
            verdict = "~same ➖"
        else:
            verdict = f"{vs_baseline*100:.1f}% ❌"

        seeds_str = f"{seed_count} seed{'s' if seed_count > 1 else ''}"
        print(f"  {seeds_str:>10} |     {best_match:5.1f}% |     {actual:5.1f}% |      {improvement:+5.1f}% | {verdict}")

    print()
    print("="*80)
    print("CONCLUSION:")
    print("="*80)

    best = sorted_results[0]
    if best['actual_avg'] > baseline_actual + 0.01:
        print(f"✅ IMPROVEMENT FOUND: Ensemble of {best['seed_count']} seeds")
        print(f"   Seeds: {best['seeds']}")
        print(f"   Actual average: {best['actual_avg']*100:.1f}% (vs {baseline_actual*100:.1f}% baseline)")
        print(f"   Improvement: +{(best['actual_avg'] - baseline_actual)*100:.1f}%")
        print(f"   RECOMMENDATION: Use ensemble voting with {best['seed_count']} seeds")
    elif best['actual_avg'] > baseline_actual - 0.01:
        print(f"➖ NO SIGNIFICANT DIFFERENCE")
        print(f"   All ensemble sizes perform similarly (~{best['actual_avg']*100:.1f}%)")
        print(f"   RECOMMENDATION: Keep single seed (simpler, faster)")
    else:
        print(f"❌ NO IMPROVEMENT FOUND")
        print(f"   Best: {best['actual_avg']*100:.1f}% with {best['seed_count']} seeds")
        print(f"   Still at or below baseline: {baseline_actual*100:.1f}%")
        print(f"   RECOMMENDATION: Try different approach")

    # Save results
    output_file = "test_seed_ensemble_results.json"
    with open(output_file, 'w') as f:
        # Convert predictions to lists for JSON serialization
        for result in all_results:
            for r in result['results']:
                r['prediction'] = list(r['prediction'])
                r['individual_predictions'] = [list(p) for p in r['individual_predictions']]

        json.dump({
            'baseline': baseline_actual,
            'results': all_results,
            'best_config': {
                'seeds': best['seeds'],
                'seed_count': best['seed_count'],
                'actual_avg': best['actual_avg'],
                'improvement_vs_baseline': best['actual_avg'] - baseline_actual
            }
        }, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
