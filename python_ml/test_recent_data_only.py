#!/usr/bin/env python3
"""
Test using only recent data for training (removing oldest series).

Hypothesis: Very old patterns may be noise, recent data may be more relevant.

Current baseline: All historical data (174 series), 55.7% actual average
Testing: Most recent 50, 75, 100, 125 series only
"""

import json
import sys
import random
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


def test_recent_data_only(recent_series_count, seed=999):
    """Test using only recent N series for training"""
    print(f"\n{'='*80}")
    print(f"Testing Recent Data Only: {recent_series_count} series")
    print(f"{'='*80}\n")

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Fixed validation window (8 series)
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1  # 3138

    # Limit training data to recent N series before validation
    training_start = validation_start - recent_series_count

    print(f"Training: Series {training_start}-{validation_start-1} ({recent_series_count} series)")
    print(f"Validation: Series {validation_start}-{latest_series} ({validation_window} series)")
    print(f"Skipped old data: Series 2898-{training_start-1} ({training_start - 2898} series)")
    print()

    # Initialize model
    random.seed(seed)
    model = TrueLearningModel()

    # Phase 1: Bulk training (only recent data)
    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]

    if len(training_data) < recent_series_count:
        print(f"⚠️  Warning: Only {len(training_data)} series available for training")

    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    # Phase 2: Iterative validation
    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    results = []
    for series in validation_series:
        series_id = series['series_id']
        actual_events = series['events']

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Calculate accuracy for each event
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
    print(f"  Training series used: {len(training_data)}")
    print(f"  Validation series: {len(validation_series)}")

    return {
        'recent_series_count': recent_series_count,
        'actual_training_count': len(training_data),
        'best_match_avg': overall_best_avg,
        'actual_avg': overall_actual_avg,
        'improvement': improvement,
        'results': results
    }


def main():
    """Test multiple recent data configurations"""
    print("="*80)
    print("RECENT DATA ONLY OPTIMIZATION")
    print("="*80)
    print()
    print("Hypothesis: Old data is noise, recent data more relevant")
    print("Current baseline: All 168 series, 55.7% actual average")
    print("Testing: Most recent 50, 75, 100, 125, 150 series only")
    print()
    print("CRITICAL: Using ACTUAL average (all 7 events), not 'best match'")
    print("="*80)

    recent_counts = [50, 75, 100, 125, 150, 168]  # 168 = baseline (all data before validation)
    all_results = []

    for count in recent_counts:
        result = test_recent_data_only(count)
        all_results.append(result)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - RANKED BY ACTUAL AVERAGE")
    print("="*80)
    print()
    print("Recent | Training | Best Match | ACTUAL Avg | Improvement | Verdict")
    print("-------|----------|------------|------------|-------------|--------")

    # Sort by actual average (descending)
    sorted_results = sorted(all_results, key=lambda x: x['actual_avg'], reverse=True)
    baseline_actual = 0.557  # Current baseline

    for result in sorted_results:
        recent = result['recent_series_count']
        training = result['actual_training_count']
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

        print(f"  {recent:4d} |     {training:3d} |     {best_match:5.1f}% |     {actual:5.1f}% |      {improvement:+5.1f}% | {verdict}")

    print()
    print("="*80)
    print("CONCLUSION:")
    print("="*80)

    best = sorted_results[0]
    if best['actual_avg'] > baseline_actual + 0.01:
        print(f"✅ IMPROVEMENT FOUND: Using {best['recent_series_count']} recent series")
        print(f"   Actual average: {best['actual_avg']*100:.1f}% (vs {baseline_actual*100:.1f}% baseline)")
        print(f"   Improvement: +{(best['actual_avg'] - baseline_actual)*100:.1f}%")
        print(f"   RECOMMENDATION: Limit training to {best['recent_series_count']} most recent series")
    elif best['actual_avg'] > baseline_actual - 0.01:
        print(f"➖ NO SIGNIFICANT DIFFERENCE")
        print(f"   All configurations perform similarly (~{best['actual_avg']*100:.1f}%)")
        print(f"   RECOMMENDATION: Keep using all available data")
    else:
        print(f"❌ NO IMPROVEMENT FOUND")
        print(f"   Best: {best['actual_avg']*100:.1f}% with {best['recent_series_count']} recent series")
        print(f"   Still at or below baseline: {baseline_actual*100:.1f}%")
        print(f"   RECOMMENDATION: Try different approach")

    # Save results
    output_file = "test_recent_data_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'baseline': baseline_actual,
            'results': all_results,
            'best_config': {
                'recent_series_count': best['recent_series_count'],
                'actual_avg': best['actual_avg'],
                'improvement_vs_baseline': best['actual_avg'] - baseline_actual
            }
        }, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
