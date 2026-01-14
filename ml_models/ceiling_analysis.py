#!/usr/bin/env python3
"""
Ceiling Analysis - Why is 14/14 so hard?
"""
import json
from collections import Counter
from pathlib import Path
from itertools import combinations

from production_predictor import predict, evaluate, latest, validate, load_data

def analyze_ceiling():
    data = load_data()
    series_ids = sorted([int(s) for s in data.keys()])

    print("=" * 70)
    print("THEORETICAL CEILING ANALYSIS")
    print("=" * 70)

    # 1. Probability of 14/14 under random selection
    # P(14/14) = C(14,14) * C(11,0) / C(25,14)
    from math import comb
    p_14_random = comb(14, 14) * comb(11, 0) / comb(25, 14)
    print(f"\nP(14/14) random single set:  {p_14_random:.6f} = 1 in {1/p_14_random:,.0f}")

    # With 7 events, 10 sets
    n_sets = 10
    n_events = 7
    p_14_none = (1 - p_14_random) ** (n_sets * n_events)
    p_14_any = 1 - p_14_none
    print(f"P(14/14) any set/event (random): {p_14_any:.4%}")

    # 2. What would it take?
    print("\n" + "=" * 70)
    print("WHAT WOULD IT TAKE TO HIT 14/14?")
    print("=" * 70)

    # Analyze the "miss patterns" - what numbers miss when we get 11, 12, 13
    results = []
    for sid in range(2981, max(series_ids) + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue
        r = evaluate(data, sid)
        if r:
            r['pred'] = predict(data, sid)
            results.append(r)

    # For 12+ matches, what was missing?
    print("\n12+ Match Analysis - What numbers were missing?")
    print("-" * 50)

    at_12_plus = []
    for r in results:
        for i, score in enumerate(r['set_bests'], 1):
            if score >= 12:
                pred_set = set(r['pred']['sets'][i-1])
                # Find which event gave 12+
                for event in data[str(r['series'])]:
                    event_set = set(event)
                    if len(pred_set & event_set) == score:
                        missing = pred_set - event_set
                        extra_in_event = event_set - pred_set
                        at_12_plus.append({
                            'series': r['series'],
                            'set': i,
                            'score': score,
                            'missing': missing,
                            'extra': extra_in_event,
                        })
                        break

    # What numbers are typically missing?
    missing_counts = Counter()
    for m in at_12_plus:
        for n in m['missing']:
            missing_counts[n] += 1

    print(f"\nNumbers missing in 12+ events (total {len(at_12_plus)} events):")
    for num, count in missing_counts.most_common(10):
        print(f"  #{num}: {count} times ({count/len(at_12_plus)*100:.1f}%)")

    # What numbers could have been swapped in?
    extra_counts = Counter()
    for m in at_12_plus:
        for n in m['extra']:
            extra_counts[n] += 1

    print(f"\nNumbers that appeared in 12+ events but NOT in our prediction:")
    for num, count in extra_counts.most_common(10):
        print(f"  #{num}: {count} times ({count/len(at_12_plus)*100:.1f}%)")

    # 3. The 13/14 event
    print("\n" + "=" * 70)
    print("THE 13/14 EVENT (Series 3061)")
    print("=" * 70)

    for r in results:
        if r['series'] == 3061:
            pred = r['pred']
            print(f"\nS9 (Event 6) prediction: {pred['sets'][8]}")
            print(f"Actual event 6: {pred['event6']}")

            for i, event in enumerate(data['3061'], 1):
                event_set = set(event)
                s9_set = set(pred['sets'][8])
                match = len(s9_set & event_set)
                if match == 13:
                    missing = s9_set - event_set
                    extra = event_set - s9_set
                    print(f"\nMatched event {i}: {sorted(event)}")
                    print(f"Match: {match}/14")
                    print(f"Missing from prediction: {missing}")
                    print(f"Was in event, not in prediction: {extra}")

    # 4. How close are we to ceiling?
    print("\n" + "=" * 70)
    print("CEILING ESTIMATION")
    print("=" * 70)

    # What's the theoretical maximum if we had perfect knowledge?
    # For each series, what's the max score ANY set could achieve?
    oracle_scores = []
    for r in results:
        oracle_scores.append(max(r['set_bests']))

    print(f"\nOracle max (if we always picked best set):")
    print(f"  Mean: {sum(oracle_scores)/len(oracle_scores):.2f}/14")
    print(f"  Best: {max(oracle_scores)}/14")
    print(f"  Worst: {min(oracle_scores)}/14")

    # What if we could perfectly predict which number to add at rank 15/16?
    # This is the theoretical ceiling for the E1-based approach
    all_14_possible = 0
    for sid in range(2981, max(series_ids) + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue

        e1 = set(data[str(sid - 1)][0])
        events = data[str(sid)]

        # For any event, is there a 14-number set starting with top-13 of E1 that works?
        for event in events:
            event_set = set(event)
            if len(e1 & event_set) >= 13:
                # Top-13 from E1 all appear, need 1 more
                all_14_possible += 1
                break

    print(f"\nSeries where 14/14 was theoretically possible (top-13 E1 + 1 swap):")
    print(f"  {all_14_possible} / {len(results)} series ({all_14_possible/len(results)*100:.1f}%)")

if __name__ == "__main__":
    analyze_ceiling()
