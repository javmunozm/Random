#!/usr/bin/env python3
"""
Test: Manual Intuition vs ML Program
Compare simple manual heuristics against ML predictions on historical data
"""

import json
from collections import Counter

def load_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def manual_prediction(lookback_series, data):
    """
    Simulate human manual prediction using simple heuristics

    Manual approach:
    1. Count frequency in last 3 series
    2. Pick top-14 most frequent
    3. Balance columns roughly (4-5-5 or 5-5-4)
    """

    # Count from last 3 series only (human attention span)
    counter = Counter()
    for sid in lookback_series[-3:]:
        for event in data[str(sid)]:
            for num in event:
                counter[num] += 1

    # Get top candidates
    top_candidates = [num for num, _ in counter.most_common(18)]

    # Manual balancing: aim for ~5 from each column
    col0 = [n for n in top_candidates if 1 <= n <= 9]
    col1 = [n for n in top_candidates if 10 <= n <= 19]
    col2 = [n for n in top_candidates if 20 <= n <= 25]

    # Pick 5-5-4 or 4-5-5
    selected = col0[:5] + col1[:5] + col2[:4]

    # If not 14, adjust
    if len(selected) < 14:
        remaining = [n for n in top_candidates if n not in selected]
        selected.extend(remaining[:14-len(selected)])

    return sorted(selected[:14])

def ml_prediction(lookback_series, data):
    """
    Simulate ML program prediction (Top-8 + Frequent Gaps)

    ML approach:
    1. Analyze most recent series for Top-8
    2. Find gaps appearing in 3+ events
    3. Combine for reduced pool
    4. Pick top-14 by frequency from that pool
    """

    latest_sid = lookback_series[-1]
    latest = data[str(latest_sid)]

    # Top-8 from latest series
    counter = Counter()
    for event in latest:
        for num in event:
            counter[num] += 1

    top_8 = [num for num, _ in counter.most_common(8)]

    # Frequent gaps (3+ events)
    gap_counter = Counter()
    for event in latest:
        gaps = set(event) - set(top_8)
        for num in gaps:
            gap_counter[num] += 1

    frequent_gaps = [num for num, count in gap_counter.items() if count >= 3]

    # Reduced pool
    reduced_pool = sorted(set(top_8 + frequent_gaps))

    # Get top-14 from pool by global frequency
    global_counter = Counter()
    for sid in lookback_series:
        for event in data[str(sid)]:
            for num in event:
                if num in reduced_pool:
                    global_counter[num] += 1

    top_14 = [num for num, _ in global_counter.most_common(14)]

    return sorted(top_14)

def evaluate_prediction(prediction, actual_events):
    """Calculate best match against actual events"""
    best_match = 0
    best_event = None

    for i, event in enumerate(actual_events, 1):
        overlap = len(set(prediction) & set(event))
        if overlap > best_match:
            best_match = overlap
            best_event = i

    return best_match, best_event

def run_comparison_test(test_series_ids):
    """Compare manual vs ML predictions on historical data"""

    data = load_data()

    print("="*80)
    print("MANUAL INTUITION vs ML PROGRAM - HISTORICAL COMPARISON")
    print("="*80)
    print("\nManual Method: Top-14 from last 3 series with column balancing")
    print("ML Method: Top-8 + Frequent Gaps from latest series")
    print("="*80)

    results = []

    for target_id in test_series_ids:
        lookback = list(range(target_id - 5, target_id))

        # Make predictions (without knowing actual results)
        manual_pred = manual_prediction(lookback, data)
        ml_pred = ml_prediction(lookback, data)

        # Get actual results
        actual = data[str(target_id)]

        # Evaluate
        manual_match, manual_event = evaluate_prediction(manual_pred, actual)
        ml_match, ml_event = evaluate_prediction(ml_pred, actual)

        manual_pct = manual_match / 14 * 100
        ml_pct = ml_match / 14 * 100

        winner = "MANUAL" if manual_match > ml_match else ("ML" if ml_match > manual_match else "TIE")

        results.append({
            'series': target_id,
            'manual_match': manual_match,
            'ml_match': ml_match,
            'winner': winner,
            'manual_pred': manual_pred,
            'ml_pred': ml_pred
        })

        print(f"\nSeries {target_id}:")
        print(f"  Manual: {manual_match}/14 ({manual_pct:.1f}%) - Event {manual_event}")
        print(f"  ML:     {ml_match}/14 ({ml_pct:.1f}%) - Event {ml_event}")
        print(f"  Winner: {winner}")

        # Show predictions
        print(f"\n  Manual predicted: {' '.join(f'{n:02d}' for n in manual_pred)}")
        print(f"  ML predicted:     {' '.join(f'{n:02d}' for n in ml_pred)}")

    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL RESULTS")
    print(f"{'='*80}\n")

    manual_wins = sum(1 for r in results if r['winner'] == 'MANUAL')
    ml_wins = sum(1 for r in results if r['winner'] == 'ML')
    ties = sum(1 for r in results if r['winner'] == 'TIE')

    manual_avg = sum(r['manual_match'] for r in results) / len(results)
    ml_avg = sum(r['ml_match'] for r in results) / len(results)

    print(f"Series tested: {len(results)}")
    print(f"\nWins:")
    print(f"  Manual: {manual_wins}")
    print(f"  ML:     {ml_wins}")
    print(f"  Ties:   {ties}")

    print(f"\nAverage Match:")
    print(f"  Manual: {manual_avg:.2f}/14 ({manual_avg/14*100:.1f}%)")
    print(f"  ML:     {ml_avg:.2f}/14 ({ml_avg/14*100:.1f}%)")

    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}\n")

    if manual_avg > ml_avg:
        diff = manual_avg - ml_avg
        print(f"✅ MANUAL WINS by {diff:.2f} numbers on average ({diff/14*100:.1f}%)")
        print("   Simple frequency counting beats complex ML patterns")
    elif ml_avg > manual_avg:
        diff = ml_avg - manual_avg
        print(f"✅ ML WINS by {diff:.2f} numbers on average ({diff/14*100:.1f}%)")
        print("   ML pattern recognition (Top-8 + Gaps) is superior")
    else:
        print(f"🤝 TIE - Both methods perform equally")

    print(f"\n{'='*80}\n")

    return results

if __name__ == '__main__':
    # Test on last 10 series
    test_series = [3142, 3143, 3144, 3145, 3146, 3147, 3148, 3149, 3150, 3151]
    run_comparison_test(test_series)
