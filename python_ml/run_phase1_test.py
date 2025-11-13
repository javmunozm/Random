#!/usr/bin/env python3
"""
Phase 1 Test Runner - Validates Phase 1 Pure performance

Loads real data from JSON export + Series 3144, runs same training cycle as C#.
"""

import json
import sys
import random
from pathlib import Path
from true_learning_model import TrueLearningModel


# Series 3144 actual results (provided by user)
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]

# Series 3145 actual results (provided by user)
SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
]

# Series 3147 actual results (provided by user)
SERIES_3147 = [
    [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
    [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
    [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
    [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
    [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
    [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
    [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
]

# Series 3148 actual results (provided by user)
SERIES_3148 = [
    [1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 19, 22, 23, 25],
    [2, 3, 6, 7, 10, 12, 13, 14, 15, 16, 17, 19, 21, 23],
    [1, 2, 4, 5, 6, 8, 10, 12, 14, 15, 17, 18, 20, 22],
    [2, 3, 4, 5, 8, 10, 12, 13, 14, 15, 18, 20, 21, 25],
    [3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 19, 20, 21, 24],
    [2, 3, 4, 5, 9, 10, 12, 14, 15, 16, 17, 18, 22, 25],
    [1, 4, 6, 7, 9, 11, 12, 14, 16, 19, 20, 21, 23, 25],
]


def load_database_export():
    """Load data from JSON export"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found: {json_path}")
        return []

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    # Extract series data from JSON structure
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

    print(f"✅ Loaded {len(series_list)} series from JSON export (2898-3143)")
    return series_list


def run_iterative_training(validation_window_size=8, recent_series_count=50, random_seed=999):
    """
    Run training with OPTIMIZED configuration (50 recent series only)

    Based on systematic testing of 50 improvement attempts:
    - Best performer: 50 recent series (+1.4% over baseline)
    - Performance: 57.1% actual average (vs 55.7% baseline)
    - Still below random: 67.9% random vs 57.1% model (-10.8%)
    """

    # Set optimal seed
    random.seed(random_seed)

    print("=" * 80)
    print("OPTIMIZED ML TRAINING (50 Recent Series)")
    print("=" * 80)
    print()
    print(f"Configuration: seed={random_seed}, recent_series={recent_series_count}")
    print(f"Expected performance: ~57% actual avg (still 11% below random)")
    print()

    # Load data
    all_series_data = load_database_export()
    if not all_series_data:
        print("❌ No data loaded")
        return

    # Add Series 3144
    all_series_data.append({
        'series_id': 3144,
        'events': SERIES_3144
    })

    # Add Series 3145
    all_series_data.append({
        'series_id': 3145,
        'events': SERIES_3145
    })

    # Add Series 3147
    all_series_data.append({
        'series_id': 3147,
        'events': SERIES_3147
    })

    # Add Series 3148
    all_series_data.append({
        'series_id': 3148,
        'events': SERIES_3148
    })

    latest_series = 3148
    validation_start = latest_series - validation_window_size + 1  # 3138

    # NEW: Use only 50 most recent series before validation
    training_start = validation_start - recent_series_count  # 3088

    print(f"Phase 1: Training on RECENT data only")
    print(f"         Training: Series {training_start}-{validation_start-1} ({recent_series_count} series)")
    print(f"         Validation: Series {validation_start}-{latest_series} ({validation_window_size} series)")
    print(f"         Skipping old data: Series 2898-{training_start-1} (noise reduction)")
    print("=" * 80)

    # Initialize model
    model = TrueLearningModel()

    # Phase 1: Bulk training (ONLY recent series)
    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]
    for series in training_data:
        model.learn_from_series(series['series_id'], series['events'])

    print(f"✅ Trained on {len(training_data)} recent series")
    print(f"   Skipped {training_start - 2898} old series (noise reduction)")
    print()

    # Phase 2: Iterative validation
    validation_series = [s for s in all_series_data if validation_start <= s['series_id'] <= latest_series]

    print(f"Phase 2: Iterative validation on {len(validation_series)} series ({validation_start}-{latest_series})")
    print("=" * 80)
    print()

    results = []

    for series_data in validation_series:
        series_id = series_data['series_id']
        actual_results = series_data['events']

        print("=" * 80)
        print(f"Series {series_id}")
        print("=" * 80)

        # Generate prediction
        print(f"🔮 Generating prediction for Series {series_id}...")
        prediction = model.predict_best_combination(series_id)
        print(f"Prediction: {' '.join(f'{n:02d}' for n in prediction)}")
        print()

        # Calculate accuracy for each event
        print("📊 Validation against actual results:")
        accuracies = []
        for i, actual in enumerate(actual_results):
            matches = len(set(prediction) & set(actual))
            accuracy = matches / 14.0
            accuracies.append(accuracy)
            print(f"  Event {i+1}: {matches}/14 ({accuracy:.1%})")

        best_accuracy = max(accuracies)
        avg_accuracy = sum(accuracies) / len(accuracies)

        print()
        print(f"✨ Best Match: {best_accuracy:.1%}")
        print(f"📊 Average: {avg_accuracy:.1%}")
        print()

        # LEARN from the results
        model.validate_and_learn(series_id, prediction, actual_results)
        print()

        results.append({
            'series_id': series_id,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy
        })

    # Summary
    print("=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)
    print()
    print("Series | Best Match | Average")
    print("-------|------------|--------")
    for r in results:
        print(f" {r['series_id']} | {r['best_accuracy']:10.1%} | {r['avg_accuracy']:.1%}")
    print()

    avg_best = sum(r['best_accuracy'] for r in results) / len(results)
    avg_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print(f"📈 Overall Best Average: {avg_best:.1%}")
    print(f"📊 Overall Average: {avg_avg:.1%}")
    print()

    # Check for improvement
    if len(results) >= 6:
        first_three = sum(r['avg_accuracy'] for r in results[:3]) / 3
        last_three = sum(r['avg_accuracy'] for r in results[-3:]) / 3
        improvement = last_three - first_three

        print(f"📉 First 3 series average: {first_three:.1%}")
        print(f"📈 Last 3 series average: {last_three:.1%}")
        print(f"🎯 Improvement: {improvement:+.1%} ({'✅ LEARNING DETECTED' if improvement > 0 else '❌ NO IMPROVEMENT'})")
        print()

    # Save results
    summary = {
        'validation_range': f'{validation_start}-{latest_series}',
        'validation_series_count': len(results),
        'overall_best_average': avg_best,
        'overall_average': avg_avg,
        'series_results': results,
        'improvement_analysis': {
            'first_three_avg': sum(r['avg_accuracy'] for r in results[:3]) / 3 if len(results) >= 3 else 0,
            'last_three_avg': sum(r['avg_accuracy'] for r in results[-3:]) / 3 if len(results) >= 3 else 0,
            'improvement': improvement if len(results) >= 6 else 0
        } if len(results) >= 6 else None
    }

    output_path = Path(__file__).parent / "phase1_python_results.json"
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"📁 Results saved to: {output_path}")
    print()

    # Final prediction
    next_series = latest_series + 1
    print("=" * 80)
    print(f"FINAL PREDICTION: Series {next_series}")
    print("=" * 80)
    print()

    final_prediction = model.predict_best_combination(next_series)
    print(f"🎯 Prediction: {' '.join(f'{n:02d}' for n in final_prediction)}")
    print()
    print(f"✅ Trained on {model.get_training_size()} series")
    print(f"✅ Model has learned from actual results of {validation_start}-{latest_series} ({len(validation_series)} series)")
    print()

    # Comparison with Phase 2
    print("=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print()
    print("Version                | Overall Best Avg | Status")
    print("-----------------------|------------------|--------")
    print("Phase 1 Baseline (C#)  | 71.4%            | Target")
    print("Phase 2.0 (C#)         | 66.96%           | -4.4% ❌")
    print("Phase 2.1 (C#)         | 64.29%           | -7.1% ❌")
    print(f"Phase 1 Pure (Python)  | {avg_best:5.1%}           | {'✅' if avg_best >= 0.714 else '⚠️'}")
    print()

    if avg_best >= 0.714:
        print("✅ SUCCESS: Phase 1 Pure Python matches or exceeds baseline!")
        print("   This confirms Phase 1 restoration was correct.")
    elif avg_best >= 0.650:
        print("⚠️  CLOSE: Phase 1 Pure Python is close to baseline.")
        print("   May need minor adjustments or more training data.")
    else:
        print("❌ REGRESSION: Phase 1 Pure Python below baseline.")
        print("   Need to investigate implementation differences.")
    print()


if __name__ == "__main__":
    # OPTIMIZED configuration: 50 recent series (+1.4% improvement)
    run_iterative_training(validation_window_size=8, recent_series_count=50)
