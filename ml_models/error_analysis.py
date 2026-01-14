#!/usr/bin/env python3
"""
Error Pattern Analysis
"""
import json
from collections import Counter
from pathlib import Path

from production_predictor import predict, evaluate, latest, validate, load_data

def analyze_errors():
    data = load_data()
    series_ids = sorted([int(s) for s in data.keys()])

    print("=" * 70)
    print("ERROR PATTERN ANALYSIS")
    print("=" * 70)

    results = []
    for sid in range(2981, max(series_ids) + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue
        r = evaluate(data, sid)
        if r:
            r['pred'] = predict(data, sid)
            results.append(r)

    # 1. When do we get 9/14 (worst case)?
    print("\n9/14 EVENTS (Below Average)")
    print("-" * 50)
    worst_cases = [r for r in results if r['best'] == 9]
    print(f"Count: {len(worst_cases)} ({len(worst_cases)/len(results)*100:.1f}%)")

    for r in worst_cases[:5]:  # First 5
        print(f"\nSeries {r['series']}:")
        print(f"  Set scores: {r['set_bests']}")
        print(f"  Winner: S{r['winner']} with {r['best']}/14")

    # 2. E1 carryover on worst cases
    print("\n" + "=" * 70)
    print("E1 CARRYOVER ON 9/14 EVENTS vs 12+ EVENTS")
    print("-" * 50)

    worst_carryovers = []
    best_carryovers = []

    for r in results:
        sid = r['series']
        e1 = set(data[str(sid - 1)][0])
        max_carryover = 0
        for event in data[str(sid)]:
            carryover = len(e1 & set(event))
            max_carryover = max(max_carryover, carryover)

        if r['best'] == 9:
            worst_carryovers.append(max_carryover)
        elif r['best'] >= 12:
            best_carryovers.append(max_carryover)

    if worst_carryovers:
        print(f"9/14 events - Max E1 carryover: mean={sum(worst_carryovers)/len(worst_carryovers):.2f}")
        print(f"  Distribution: {Counter(worst_carryovers)}")
    if best_carryovers:
        print(f"12+/14 events - Max E1 carryover: mean={sum(best_carryovers)/len(best_carryovers):.2f}")
        print(f"  Distribution: {Counter(best_carryovers)}")

    # 3. Which rank positions fail most often?
    print("\n" + "=" * 70)
    print("POSITION FAILURE ANALYSIS")
    print("-" * 50)

    # For S1 (top-13 + rank16), which positions are typically NOT in the target?
    global_freq = Counter(n for events in data.values() for e in events for n in e)
    max_freq = max(global_freq.values())

    position_fails = {i: 0 for i in range(14)}
    position_total = 0

    for r in results:
        sid = r['series']
        pred = r['pred']
        s1 = set(pred['sets'][0])  # S1: top-13 + rank16

        for event in data[str(sid)]:
            event_set = set(event)
            position_total += 1
            for pos, num in enumerate(pred['ranked'][:14]):
                if num not in event_set:
                    position_fails[pos] += 1

    print(f"\nFailure rate by position in top-14 (S1 perspective):")
    for pos in range(14):
        fail_rate = position_fails[pos] / position_total
        expected = 1 - 14/25
        print(f"  Rank {pos+1:2d}: {fail_rate:.1%} fail (expected {expected:.1%})")

    # 4. Temporal patterns
    print("\n" + "=" * 70)
    print("TEMPORAL PATTERNS")
    print("-" * 50)

    # Rolling average
    window = 20
    rolling = []
    for i in range(len(results) - window + 1):
        chunk = results[i:i+window]
        avg = sum(r['best'] for r in chunk) / window
        rolling.append((chunk[0]['series'], avg))

    print(f"\nRolling {window}-series average:")
    print(f"  First 20: {rolling[0][1]:.2f}/14")
    print(f"  Last 20:  {rolling[-1][1]:.2f}/14")
    print(f"  Max:      {max(r[1] for r in rolling):.2f}/14 (Series {max(rolling, key=lambda x: x[1])[0]})")
    print(f"  Min:      {min(r[1] for r in rolling):.2f}/14 (Series {min(rolling, key=lambda x: x[1])[0]})")

    # 5. Event 6 vs Event 1 analysis
    print("\n" + "=" * 70)
    print("E1 vs E6 PREDICTIVE POWER")
    print("-" * 50)

    e1_wins = 0
    e6_wins = 0
    e1_e6_tie = 0

    for r in results:
        sid = r['series']
        e1_prev = set(data[str(sid - 1)][0])
        e6_prev = set(data[str(sid - 1)][5])

        e1_best = 0
        e6_best = 0
        for event in data[str(sid)]:
            event_set = set(event)
            e1_match = len(e1_prev & event_set)
            e6_match = len(e6_prev & event_set)
            e1_best = max(e1_best, e1_match)
            e6_best = max(e6_best, e6_match)

        if e1_best > e6_best:
            e1_wins += 1
        elif e6_best > e1_best:
            e6_wins += 1
        else:
            e1_e6_tie += 1

    total = e1_wins + e6_wins + e1_e6_tie
    print(f"E1 wins (higher max overlap): {e1_wins} ({e1_wins/total*100:.1f}%)")
    print(f"E6 wins: {e6_wins} ({e6_wins/total*100:.1f}%)")
    print(f"Ties: {e1_e6_tie} ({e1_e6_tie/total*100:.1f}%)")

    # 6. Per-set consistency
    print("\n" + "=" * 70)
    print("SET CONSISTENCY (Std Dev of Scores)")
    print("-" * 50)

    n_sets = 18  # 18-set multi-event strategy (E1+E3+E6+E7+#12+swaps)
    set_scores = {i: [] for i in range(1, n_sets + 1)}

    for r in results:
        for i, score in enumerate(r['set_bests'], 1):
            set_scores[i].append(score)

    import statistics
    labels = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12',
              'S13', 'S14', 'S15', 'S16', 'S17', 'S18']
    print(f"\n{'Set':<6} {'Mean':>8} {'StdDev':>8} {'CV':>8}")
    print("-" * 35)
    for i in range(1, n_sets + 1):
        scores = set_scores[i]
        mean = statistics.mean(scores)
        std = statistics.stdev(scores)
        cv = std / mean * 100
        print(f"{labels[i-1]:<6} {mean:>7.2f} {std:>7.2f} {cv:>7.1f}%")

if __name__ == "__main__":
    analyze_errors()
