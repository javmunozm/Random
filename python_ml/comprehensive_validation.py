#!/usr/bin/env python3
"""
Comprehensive Multi-Series Validation
Test original multi-signal method across Series 3140-3151 (12 series)
to establish true baseline performance and identify patterns
"""

import json
from collections import Counter
from itertools import combinations

def load_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def calculate_multi_signal_score(combo, data, recent_series, analysis_series_id):
    """
    Original multi-signal scoring (before Priority 1 changes)
    """
    # Signal 1: Global frequency (25% - original weight)
    global_counter = Counter()
    for sid, events in data.items():
        if int(sid) < analysis_series_id:  # Only historical
            for event in events:
                for num in event:
                    global_counter[num] += 1

    global_score = sum(global_counter[num] for num in combo) / len(combo)

    # Signal 2: Recent frequency (35% - original weight)
    recent_counter = Counter()
    for sid in recent_series:
        if int(sid) < analysis_series_id:
            for event in data[str(sid)]:
                for num in event:
                    recent_counter[num] += 1

    recent_score = sum(recent_counter[num] for num in combo) / len(combo)

    # Signal 3: Pattern match (20%)
    pattern_scores = []
    for sid in recent_series[-2:]:
        if int(sid) < analysis_series_id:
            for event in data[str(sid)]:
                overlap = len(set(combo) & set(event))
                pattern_scores.append(overlap / 14)

    pattern_score = max(pattern_scores) if pattern_scores else 0

    # Signal 4: Distribution score (10% - original)
    col0 = len([n for n in combo if 1 <= n <= 9])
    col1 = len([n for n in combo if 10 <= n <= 19])
    col2 = len([n for n in combo if 20 <= n <= 25])

    # Original: ideal distribution
    ideal_dist = [5, 6, 3]
    actual_dist = [col0, col1, col2]
    dist_diff = sum(abs(ideal_dist[i] - actual_dist[i]) for i in range(3))
    distribution_score = max(0, 1 - (dist_diff / 10))

    # Signal 5: Pair affinity (10%)
    pair_counter = Counter()
    for sid, events in data.items():
        if int(sid) < analysis_series_id:
            for event in events:
                for i, n1 in enumerate(event):
                    for n2 in event[i+1:]:
                        pair_counter[(min(n1, n2), max(n1, n2))] += 1

    pair_score = 0
    pair_count = 0
    for i, n1 in enumerate(combo):
        for n2 in combo[i+1:]:
            pair_count += 1
            pair_score += pair_counter[(min(n1, n2), max(n1, n2))]

    pair_score = pair_score / pair_count if pair_count > 0 else 0

    # Original composite (25/35/20/10/10)
    composite = (
        global_score * 0.25 +
        recent_score * 0.35 +
        pattern_score * 0.20 +
        distribution_score * 0.10 +
        pair_score * 0.10
    )

    return composite, {
        'global': global_score,
        'recent': recent_score,
        'pattern': pattern_score,
        'distribution': distribution_score,
        'pair_affinity': pair_score
    }

def predict_series(data, target_series):
    """
    Generate prediction for target series using original multi-signal method
    """
    all_series = sorted([int(s) for s in data.keys()])
    target_idx = all_series.index(target_series)
    recent_series = all_series[max(0, target_idx-5):target_idx]

    # Build candidate pool from top frequencies
    global_counter = Counter()
    for sid, events in data.items():
        if int(sid) < target_series:
            for event in events:
                for num in event:
                    global_counter[num] += 1

    top_16 = [num for num, _ in global_counter.most_common(16)]

    # Score all combinations of top-16
    best_combo = None
    best_score = 0

    for combo in combinations(top_16, 14):
        score, _ = calculate_multi_signal_score(combo, data, recent_series, target_series)
        if score > best_score:
            best_score = score
            best_combo = combo

    return sorted(best_combo) if best_combo else None

def evaluate_prediction(prediction, actual_events):
    """
    Evaluate prediction against actual events
    """
    matches = []
    for event in actual_events:
        match_count = len(set(prediction) & set(event))
        matches.append(match_count)

    return {
        'peak': max(matches),
        'avg': sum(matches) / len(matches),
        'matches': matches,
        'peak_event': matches.index(max(matches)) + 1
    }

def comprehensive_validation():
    """
    Validate across Series 3140-3151 (12 series)
    """
    data = load_data()
    test_series = range(3140, 3152)  # 3140 through 3151

    print("=" * 80)
    print("COMPREHENSIVE MULTI-SERIES VALIDATION")
    print("Original Multi-Signal Method (25/35/20/10/10)")
    print("=" * 80)
    print(f"\nTest Range: Series {min(test_series)} - {max(test_series)} ({len(test_series)} series)")

    results = []

    for series_id in test_series:
        if str(series_id) not in data:
            print(f"\n⚠️  Series {series_id}: No data available")
            continue

        # Generate prediction
        prediction = predict_series(data, series_id)

        if not prediction:
            print(f"\n⚠️  Series {series_id}: Prediction failed")
            continue

        # Evaluate
        actual_events = data[str(series_id)]
        eval_result = evaluate_prediction(prediction, actual_events)

        results.append({
            'series_id': series_id,
            'prediction': prediction,
            'peak': eval_result['peak'],
            'avg': eval_result['avg'],
            'peak_event': eval_result['peak_event'],
            'matches': eval_result['matches']
        })

        # Print individual result
        peak_pct = (eval_result['peak'] / 14) * 100
        avg_pct = (eval_result['avg'] / 14) * 100
        rating = "🎯 EXCELLENT" if eval_result['peak'] >= 12 else "✅ GOOD" if eval_result['peak'] >= 10 else "🟡 FAIR" if eval_result['peak'] >= 9 else "⚠️ POOR"

        print(f"\nSeries {series_id}: Peak {eval_result['peak']}/14 ({peak_pct:5.1f}%), Avg {eval_result['avg']:.2f}/14 ({avg_pct:4.1f}%) - Event {eval_result['peak_event']} {rating}")
        print(f"  Prediction: {' '.join(f'{n:02d}' for n in prediction)}")
        print(f"  Per-event:  {eval_result['matches']}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    if not results:
        print("\n⚠️  No results to analyze")
        return

    peaks = [r['peak'] for r in results]
    avgs = [r['avg'] for r in results]

    print(f"\nPeak Performance:")
    print(f"  Best:   {max(peaks)}/14 ({max(peaks)/14*100:.1f}%)")
    print(f"  Worst:  {min(peaks)}/14 ({min(peaks)/14*100:.1f}%)")
    print(f"  Mean:   {sum(peaks)/len(peaks):.2f}/14 ({sum(peaks)/len(peaks)/14*100:.1f}%)")
    print(f"  Median: {sorted(peaks)[len(peaks)//2]}/14 ({sorted(peaks)[len(peaks)//2]/14*100:.1f}%)")

    print(f"\nAverage Performance:")
    print(f"  Mean:   {sum(avgs)/len(avgs):.2f}/14 ({sum(avgs)/len(avgs)/14*100:.1f}%)")

    # Performance distribution
    excellent = len([p for p in peaks if p >= 12])
    good = len([p for p in peaks if 10 <= p < 12])
    fair = len([p for p in peaks if 9 <= p < 10])
    poor = len([p for p in peaks if p < 9])

    print(f"\nPerformance Distribution:")
    print(f"  🎯 Excellent (12-14): {excellent}/{len(peaks)} ({excellent/len(peaks)*100:.1f}%)")
    print(f"  ✅ Good (10-11):      {good}/{len(peaks)} ({good/len(peaks)*100:.1f}%)")
    print(f"  🟡 Fair (9):          {fair}/{len(peaks)} ({fair/len(peaks)*100:.1f}%)")
    print(f"  ⚠️  Poor (<9):         {poor}/{len(peaks)} ({poor/len(peaks)*100:.1f}%)")

    # Best performers
    print(f"\n" + "=" * 80)
    print("BEST PERFORMERS (Peak ≥ 12)")
    print("=" * 80)

    best_performers = [r for r in results if r['peak'] >= 12]
    if best_performers:
        for r in sorted(best_performers, key=lambda x: x['peak'], reverse=True):
            print(f"\n📈 Series {r['series_id']}: {r['peak']}/14 ({r['peak']/14*100:.1f}%) on Event {r['peak_event']}")
            print(f"   Prediction: {' '.join(f'{n:02d}' for n in r['prediction'])}")
    else:
        print("\n  None (no series achieved ≥12/14)")

    # Pattern analysis
    print(f"\n" + "=" * 80)
    print("PATTERN ANALYSIS")
    print("=" * 80)

    # Which numbers appear most in best predictions?
    if best_performers:
        best_numbers = Counter()
        for r in best_performers:
            best_numbers.update(r['prediction'])

        print(f"\nMost common numbers in EXCELLENT predictions (≥12/14):")
        for num, count in best_numbers.most_common(14):
            print(f"  {num:02d}: appears in {count}/{len(best_performers)} predictions ({count/len(best_performers)*100:.0f}%)")

    # Consistency check
    print(f"\n" + "=" * 80)
    print("CONSISTENCY ANALYSIS")
    print("=" * 80)

    variance = sum((p - sum(peaks)/len(peaks))**2 for p in peaks) / len(peaks)
    std_dev = variance ** 0.5

    print(f"\nPeak Performance Variance: {variance:.2f}")
    print(f"Standard Deviation: {std_dev:.2f} numbers")

    if std_dev < 1.5:
        print(f"✅ VERY CONSISTENT - Low variance across series")
    elif std_dev < 2.5:
        print(f"🟡 MODERATELY CONSISTENT - Some variance expected")
    else:
        print(f"⚠️  HIGH VARIANCE - Performance varies significantly by series")

    # Save results
    output = {
        'test_range': {'start': min(test_series), 'end': max(test_series), 'count': len(results)},
        'summary': {
            'peak_best': max(peaks),
            'peak_worst': min(peaks),
            'peak_mean': sum(peaks) / len(peaks),
            'peak_median': sorted(peaks)[len(peaks)//2],
            'avg_mean': sum(avgs) / len(avgs),
            'std_dev': std_dev
        },
        'distribution': {
            'excellent': excellent,
            'good': good,
            'fair': fair,
            'poor': poor
        },
        'detailed_results': results
    }

    with open('comprehensive_validation_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n" + "=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)
    print(f"\n📁 Results saved to: comprehensive_validation_results.json")
    print(f"\nBaseline established: Mean peak = {sum(peaks)/len(peaks):.2f}/14 ({sum(peaks)/len(peaks)/14*100:.1f}%)")
    print(f"Target for improvements: >{sum(peaks)/len(peaks):.1f}/14")
    print("=" * 80)

    return results

if __name__ == '__main__':
    comprehensive_validation()
