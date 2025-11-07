#!/usr/bin/env python3
"""
Test simple baseline approaches that might outperform complex ML.

Sometimes simpler is better. Testing:
1. Pure frequency (most common 14 numbers)
2. Weighted random (frequency-weighted random selection)
3. Recent frequency (most common in last N series)
4. Hybrid (frequency + small random variation)

Current best: 57.7% (50 recent series ML)
Target: Beat 57.7% with simpler approach
"""

import json
import sys
import random
from pathlib import Path
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


def pure_frequency_predict(training_data):
    """Select 14 most frequent numbers from training data"""
    number_counts = Counter()

    for series in training_data:
        for event in series['events']:
            for num in event:
                number_counts[num] += 1

    # Select top 14 most frequent
    most_common = [num for num, _ in number_counts.most_common(14)]
    return sorted(most_common)


def weighted_random_predict(training_data, seed):
    """Random selection weighted by frequency"""
    random.seed(seed)

    number_counts = Counter()
    for series in training_data:
        for event in series['events']:
            for num in event:
                number_counts[num] += 1

    # Normalize to probabilities
    total = sum(number_counts.values())
    probabilities = {num: count/total for num, count in number_counts.items()}

    # Weighted random selection without replacement
    selected = []
    available = list(range(1, 26))

    while len(selected) < 14 and available:
        weights = [probabilities.get(num, 0) for num in available]
        total_weight = sum(weights)
        if total_weight == 0:
            # Fallback to uniform
            chosen = random.choice(available)
        else:
            weights = [w/total_weight for w in weights]
            chosen = random.choices(available, weights=weights)[0]

        selected.append(chosen)
        available.remove(chosen)

    return sorted(selected)


def hybrid_frequency_predict(training_data, noise_factor=0.1, seed=42):
    """Most frequent + small random variation"""
    random.seed(seed)

    number_counts = Counter()
    for series in training_data:
        for event in series['events']:
            for num in event:
                number_counts[num] += 1

    # Get top 14 most frequent
    top_14 = [num for num, _ in number_counts.most_common(14)]

    # With small probability, replace some with random
    num_to_replace = int(14 * noise_factor)
    if num_to_replace > 0:
        # Replace least frequent of top 14
        to_replace = top_14[-num_to_replace:]
        keep = top_14[:-num_to_replace]

        # Get candidates from next most frequent
        candidates = [num for num, _ in number_counts.most_common(20)]
        candidates = [num for num in candidates if num not in keep]

        if len(candidates) >= num_to_replace:
            replacements = random.sample(candidates, num_to_replace)
            top_14 = keep + replacements

    return sorted(top_14)


def test_approach(approach_name, predict_fn, recent_series_count=50, seed=999):
    """Test a prediction approach"""
    print(f"\n{'='*80}")
    print(f"Testing: {approach_name}")
    print(f"{'='*80}\n")

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Fixed validation window (8 series)
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1  # 3138
    training_start = validation_start - recent_series_count  # 3088

    print(f"Training: Series {training_start}-{validation_start-1} ({recent_series_count} series)")
    print(f"Validation: Series {validation_start}-{latest_series} ({validation_window} series)")
    print()

    # Get training data
    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]

    # Validation
    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    results = []
    for series in validation_series:
        series_id = series['series_id']
        actual_events = series['events']

        # Generate prediction (update training data each iteration)
        current_training = [s for s in all_series_data
                          if training_start <= s['series_id'] < series_id]

        if 'seed' in predict_fn.__code__.co_varnames:
            prediction = predict_fn(current_training, seed)
        else:
            prediction = predict_fn(current_training)

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

    # Calculate overall metrics
    overall_best_avg = sum(r['best_accuracy'] for r in results) / len(results)
    overall_actual_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print(f"Results:")
    print(f"  Best Match Average: {overall_best_avg*100:.1f}%")
    print(f"  ACTUAL Average: {overall_actual_avg*100:.1f}%")

    return {
        'approach': approach_name,
        'actual_avg': overall_actual_avg,
        'best_match_avg': overall_best_avg,
        'results': results
    }


def main():
    """Test simple baseline approaches"""
    print("="*80)
    print("SIMPLE BASELINE APPROACHES TEST")
    print("="*80)
    print()
    print("Hypothesis: Simpler might be better than complex ML")
    print("Current best: 57.7% (50 recent series ML)")
    print("Testing: Pure frequency, weighted random, hybrid")
    print()
    print("CRITICAL: Using ACTUAL average (all 7 events), not 'best match'")
    print("="*80)

    all_results = []

    # Test 1: Pure frequency
    result = test_approach(
        "Pure Frequency (top 14 most common)",
        pure_frequency_predict,
        recent_series_count=50
    )
    all_results.append(result)

    # Test 2: Weighted random
    result = test_approach(
        "Weighted Random (frequency-weighted)",
        weighted_random_predict,
        recent_series_count=50
    )
    all_results.append(result)

    # Test 3: Hybrid (90% frequency + 10% random)
    result = test_approach(
        "Hybrid (90% freq + 10% random)",
        lambda td: hybrid_frequency_predict(td, noise_factor=0.1),
        recent_series_count=50
    )
    all_results.append(result)

    # Test 4: Hybrid (80% frequency + 20% random)
    result = test_approach(
        "Hybrid (80% freq + 20% random)",
        lambda td: hybrid_frequency_predict(td, noise_factor=0.2),
        recent_series_count=50
    )
    all_results.append(result)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - RANKED BY ACTUAL AVERAGE")
    print("="*80)
    print()
    print("Approach                                  | ACTUAL Avg | vs Best (57.7%)")
    print("------------------------------------------|------------|----------------")

    # Sort by actual average (descending)
    sorted_results = sorted(all_results, key=lambda x: x['actual_avg'], reverse=True)
    baseline_actual = 0.577  # Current best

    for result in sorted_results:
        approach = result['approach']
        actual = result['actual_avg'] * 100
        vs_baseline = result['actual_avg'] - baseline_actual

        if vs_baseline > 0.01:
            verdict = f"+{vs_baseline*100:.1f}% ✅"
        elif vs_baseline > -0.01:
            verdict = "~same ➖"
        else:
            verdict = f"{vs_baseline*100:.1f}% ❌"

        print(f"  {approach:40} |     {actual:5.1f}% | {verdict}")

    print()
    print("="*80)
    print("CONCLUSION:")
    print("="*80)

    best = sorted_results[0]
    if best['actual_avg'] > baseline_actual + 0.01:
        print(f"✅ IMPROVEMENT: {best['approach']}")
        print(f"   Actual average: {best['actual_avg']*100:.1f}% (vs {baseline_actual*100:.1f}% baseline)")
        print(f"   Improvement: +{(best['actual_avg'] - baseline_actual)*100:.1f}%")
        print(f"   SIMPLER IS BETTER!")
    else:
        print(f"➖ NO IMPROVEMENT")
        print(f"   Best simple approach: {best['actual_avg']*100:.1f}%")
        print(f"   Current ML approach: {baseline_actual*100:.1f}%")
        print(f"   ML still slightly better")

    # Save results
    output_file = "test_simple_baselines_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'baseline': baseline_actual,
            'results': all_results,
            'best': {
                'approach': best['approach'],
                'actual_avg': best['actual_avg'],
                'improvement': best['actual_avg'] - baseline_actual
            }
        }, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
