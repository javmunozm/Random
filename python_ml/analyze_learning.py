#!/usr/bin/env python3
"""
Analyze Learning Mechanism - Check if model is learning from previous results
"""

import json
import sys
from true_learning_model import TrueLearningModel

def analyze_learning():
    """Analyze if the model learns and improves over iterations"""

    print("=" * 80)
    print("LEARNING MECHANISM ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    with open('full_series_data.json', 'r') as f:
        data = json.load(f)

    # Initialize model
    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)

    # Train on bulk data (Series 2980-3140)
    print("Phase 1: Bulk training on Series 2980-3140...")
    for series_id_str in sorted(data.keys()):
        series_id = int(series_id_str)
        if 2980 <= series_id <= 3140:
            model.learn_from_series(series_id, data[series_id_str])

    print(f"✅ Trained on {model.get_training_size()} series\n")

    # Track learning progression on Series 3141-3145
    print("=" * 80)
    print("Phase 2: Iterative Learning Analysis (Series 3141-3145)")
    print("=" * 80)
    print()

    results = []

    for i, series_id_str in enumerate(['3141', '3142', '3143', '3144', '3145'], 1):
        if series_id_str not in data:
            continue

        series_id = int(series_id_str)
        actual = data[series_id_str]

        print(f"\n{'=' * 80}")
        print(f"Iteration {i}: Series {series_id}")
        print(f"{'=' * 80}")

        # Check weights BEFORE prediction
        top_weights_before = sorted(model.number_frequency_weights.items(),
                                    key=lambda x: x[1], reverse=True)[:5]
        print(f"\n📊 Top 5 weights BEFORE prediction:")
        for num, weight in top_weights_before:
            print(f"   #{num:02d}: {weight:.3f}")

        # Generate prediction
        prediction = model.predict_best_combination(series_id)
        print(f"\n🎯 Prediction: {' '.join(f'{n:02d}' for n in prediction)}")

        # Calculate accuracy
        best_match = max(actual, key=lambda a: len(set(prediction) & set(a)))
        accuracy = len(set(prediction) & set(best_match)) / 14.0

        print(f"\n📈 Accuracy: {accuracy:.1%} ({len(set(prediction) & set(best_match))}/14)")

        # Learn from actual results
        print(f"\n📚 Learning from actual results...")
        model.validate_and_learn(series_id, prediction, actual)

        # Check weights AFTER learning
        top_weights_after = sorted(model.number_frequency_weights.items(),
                                   key=lambda x: x[1], reverse=True)[:5]
        print(f"\n📊 Top 5 weights AFTER learning:")
        for num, weight in top_weights_after:
            print(f"   #{num:02d}: {weight:.3f}")

        # Check what changed
        before_dict = dict(top_weights_before)
        after_dict = dict(top_weights_after)

        print(f"\n🔍 Weight Changes:")
        all_nums = set(before_dict.keys()) | set(after_dict.keys())
        for num in sorted(all_nums):
            before = before_dict.get(num, 0)
            after = after_dict.get(num, 0)
            change = after - before
            if abs(change) > 0.01:
                change_pct = (change / before * 100) if before > 0 else 0
                print(f"   #{num:02d}: {before:.3f} → {after:.3f} ({change:+.3f}, {change_pct:+.1f}%)")

        results.append({
            'series_id': series_id,
            'accuracy': accuracy,
            'weights_before': top_weights_before,
            'weights_after': top_weights_after
        })

    # Analysis
    print("\n" + "=" * 80)
    print("LEARNING ANALYSIS SUMMARY")
    print("=" * 80)
    print()

    accuracies = [r['accuracy'] for r in results]
    print(f"Accuracy progression: {' → '.join(f'{a:.1%}' for a in accuracies)}")

    if len(accuracies) >= 3:
        early_avg = sum(accuracies[:2]) / 2
        late_avg = sum(accuracies[-2:]) / 2
        improvement = late_avg - early_avg
        print(f"\nEarly average (first 2): {early_avg:.1%}")
        print(f"Late average (last 2): {late_avg:.1%}")
        print(f"Improvement: {improvement:+.1%}")

        if improvement > 0:
            print("✅ LEARNING DETECTED: Performance improved over iterations")
        elif improvement < -0.05:
            print("❌ REGRESSION: Performance decreased over iterations")
        else:
            print("➖ STABLE: No significant change (within ±5%)")

    # Check if weights are actually changing
    print(f"\n🔍 Weight Update Verification:")

    total_weight_changes = 0
    for r in results:
        before = dict(r['weights_before'])
        after = dict(r['weights_after'])
        all_nums = set(before.keys()) | set(after.keys())
        for num in all_nums:
            b = before.get(num, 0)
            a = after.get(num, 0)
            if abs(a - b) > 0.01:
                total_weight_changes += 1

    print(f"Total significant weight changes: {total_weight_changes}")

    if total_weight_changes > 0:
        print("✅ Weights ARE changing (learning is active)")
    else:
        print("❌ Weights NOT changing (learning may be broken)")

    return results

if __name__ == "__main__":
    results = analyze_learning()
    sys.exit(0)
