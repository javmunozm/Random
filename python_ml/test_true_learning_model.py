#!/usr/bin/env python3
"""
Test TrueLearningModel (from other branch) on same 12-series validation
Compare against multi-signal method to see which is better
"""

import sys
sys.path.insert(0, '/home/user/Random/python_ml')

from true_learning_model_port import TrueLearningModel
import json

def load_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def test_true_learning_model():
    """Test TrueLearningModel on Series 3140-3151"""
    data = load_data()
    test_series = range(3140, 3152)

    print("=" * 80)
    print("TRUE LEARNING MODEL VALIDATION (From python-ml-port branch)")
    print("=" * 80)
    print(f"\nTest Range: Series {min(test_series)} - {max(test_series)} ({len(test_series)} series)")

    results = []

    for series_id in test_series:
        if str(series_id) not in data:
            continue

        # Create fresh model for each series
        model = TrueLearningModel(seed=456)  # Use consistent seed

        # Train on all data before this series
        for train_id in range(2980, series_id):
            if str(train_id) in data:
                model.learn_from_series(train_id, data[str(train_id)])

        # Generate prediction
        prediction = model.predict_best_combination(series_id)

        # Evaluate
        actual_events = data[str(series_id)]
        matches = [len(set(prediction) & set(event)) for event in actual_events]
        peak = max(matches)
        avg = sum(matches) / len(matches)
        peak_event = matches.index(peak) + 1

        results.append({
            'series_id': series_id,
            'peak': peak,
            'avg': avg,
            'peak_event': peak_event,
            'matches': matches
        })

        # Print result
        peak_pct = (peak / 14) * 100
        avg_pct = (avg / 14) * 100
        rating = "🎯 EXCELLENT" if peak >= 12 else "✅ GOOD" if peak >= 10 else "🟡 FAIR" if peak >= 9 else "⚠️ POOR"

        print(f"\nSeries {series_id}: Peak {peak}/14 ({peak_pct:5.1f}%), Avg {avg:.2f}/14 ({avg_pct:4.1f}%) - Event {peak_event} {rating}")
        print(f"  Per-event: {matches}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - TrueLearningModel")
    print("=" * 80)

    peaks = [r['peak'] for r in results]
    avgs = [r['avg'] for r in results]

    print(f"\nPeak Performance:")
    print(f"  Best:   {max(peaks)}/14 ({max(peaks)/14*100:.1f}%)")
    print(f"  Worst:  {min(peaks)}/14 ({min(peaks)/14*100:.1f}%)")
    print(f"  Mean:   {sum(peaks)/len(peaks):.2f}/14 ({sum(peaks)/len(peaks)/14*100:.1f}%)")
    print(f"  Median: {sorted(peaks)[len(peaks)//2]}/14 ({sorted(peaks)[len(peaks)//2]/14*100:.1f}%)")

    excellent = len([p for p in peaks if p >= 12])
    good = len([p for p in peaks if 10 <= p < 12])
    fair = len([p for p in peaks if 9 <= p < 10])
    poor = len([p for p in peaks if p < 9])

    print(f"\nPerformance Distribution:")
    print(f"  🎯 Excellent (12-14): {excellent}/{len(peaks)} ({excellent/len(peaks)*100:.1f}%)")
    print(f"  ✅ Good (10-11):      {good}/{len(peaks)} ({good/len(peaks)*100:.1f}%)")
    print(f"  🟡 Fair (9):          {fair}/{len(peaks)} ({fair/len(peaks)*100:.1f}%)")
    print(f"  ⚠️  Poor (<9):         {poor}/{len(peaks)} ({poor/len(peaks)*100:.1f}%)")

    # Comparison to multi-signal
    print("\n" + "=" * 80)
    print("COMPARISON TO MULTI-SIGNAL METHOD")
    print("=" * 80)

    multi_signal_mean = 8.75  # From earlier validation
    true_learning_mean = sum(peaks) / len(peaks)
    diff = true_learning_mean - multi_signal_mean

    print(f"\nMulti-Signal Method:    {multi_signal_mean:.2f}/14 ({multi_signal_mean/14*100:.1f}%)")
    print(f"TrueLearningModel:      {true_learning_mean:.2f}/14 ({true_learning_mean/14*100:.1f}%)")
    print(f"Difference:             {diff:+.2f} numbers ({diff/14*100:+.1f}%)")

    if diff > 0.5:
        print(f"\n✅ TRUE LEARNING MODEL IS BETTER by {diff:.2f} numbers!")
    elif diff < -0.5:
        print(f"\n⚠️  MULTI-SIGNAL IS BETTER by {abs(diff):.2f} numbers")
    else:
        print(f"\n🟡 COMPARABLE PERFORMANCE - difference < 0.5 numbers")

    return results

if __name__ == '__main__':
    test_true_learning_model()
