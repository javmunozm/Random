#!/usr/bin/env python3
"""
Detailed Performance Analysis for Production Predictor
"""
import json
from collections import Counter
from pathlib import Path
import sys

# Import predictor functions
from production_predictor import predict, evaluate, latest, validate, load_data

def analyze():
    data = load_data()
    series_ids = sorted([int(s) for s in data.keys()])
    start, end = 2981, max(series_ids)

    # Full detailed validation
    results = []
    for sid in range(start, end + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue
        r = evaluate(data, sid)
        if r:
            results.append(r)

    print("=" * 70)
    print("SET-BY-SET PERFORMANCE ANALYSIS")
    print("=" * 70)

    n_sets = 12  # 12-set multi-event strategy (E1+E3+E6+E7)
    set_scores = {i: [] for i in range(1, n_sets + 1)}
    set_wins = Counter()
    set_at_12 = Counter()
    set_at_13 = Counter()
    set_at_14 = Counter()

    for r in results:
        for i, score in enumerate(r['set_bests'], 1):
            set_scores[i].append(score)
            if score >= 12:
                set_at_12[i] += 1
            if score >= 13:
                set_at_13[i] += 1
            if score == 14:
                set_at_14[i] += 1
        set_wins[r['winner']] += 1

    print()
    print(f"{'Set':<6} {'Wins':>6} {'Win%':>8} {'Avg':>8} {'12+':>6} {'13+':>6} {'14':>6}")
    print('-' * 50)
    labels = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12']
    for i in range(1, n_sets + 1):
        wins = set_wins[i]
        avg = sum(set_scores[i]) / len(set_scores[i]) if set_scores[i] else 0
        at_12 = set_at_12[i]
        at_13 = set_at_13[i]
        at_14 = set_at_14[i]
        pct = wins / len(results) * 100 if results else 0
        print(f'{labels[i-1]:<6} {wins:>6} {pct:>7.1f}% {avg:>7.2f} {at_12:>6} {at_13:>6} {at_14:>6}')

    print()
    print('Best match distribution:')
    bests = [r['best'] for r in results]
    dist = Counter(bests)
    for m in sorted(dist.keys(), reverse=True):
        pct = dist[m] / len(results) * 100
        print(f'  {m}/14: {dist[m]:>4} ({pct:>5.1f}%)')

    # E1 Carryover analysis
    print()
    print("=" * 70)
    print("E1 CARRYOVER ANALYSIS")
    print("=" * 70)

    carryover_counts = []
    for i, s in enumerate(series_ids[:-1]):
        next_s = str(series_ids[i+1])
        e1 = set(data[str(s)][0])
        for event in data[next_s]:
            carryover_counts.append(len(e1 & set(event)))

    print()
    print('E1 carryover distribution:')
    dist = Counter(carryover_counts)
    for c in sorted(dist.keys()):
        pct = dist[c] / len(carryover_counts) * 100
        bar = '#' * int(pct / 2)
        print(f'  {c:2d}: {dist[c]:>5} ({pct:>5.1f}%) {bar}')

    mean = sum(carryover_counts) / len(carryover_counts)
    expected = 14 * 14 / 25
    print(f'\nMean carryover: {mean:.2f}/14')
    print(f'Expected random: {expected:.2f}/14')
    print(f'Lift: {(mean - expected)/expected*100:+.1f}%')

    # Rank position analysis
    print()
    print("=" * 70)
    print("RANK POSITION APPEARANCE RATES")
    print("=" * 70)

    global_freq = Counter(n for events in data.values() for e in events for n in e)
    max_freq = max(global_freq.values())

    position_hits = {i: 0 for i in range(25)}
    position_count = 0

    for i, s in enumerate(series_ids[:-1]):
        next_s = str(series_ids[i+1])
        e1 = set(data[str(s)][0])
        ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -global_freq[n]/max_freq, n))

        for event in data[next_s]:
            event_set = set(event)
            position_count += 1
            for pos, num in enumerate(ranked):
                if num in event_set:
                    position_hits[pos] += 1

    print()
    print(f"{'Rank':<6} {'Hit Rate':>10} {'Expected':>10} {'Lift':>8}")
    print('-' * 40)
    expected = 14/25
    for pos in range(20):
        rate = position_hits[pos] / position_count
        lift = (rate - expected) / expected * 100
        print(f'{pos+1:>4}   {rate:>9.1%}   {expected:>9.1%}  {lift:>+7.1f}%')

    # When did 13/14 happen?
    print()
    print("=" * 70)
    print("13+ EVENTS ANALYSIS")
    print("=" * 70)
    for r in results:
        for i, score in enumerate(r['set_bests'], 1):
            if score >= 13:
                print(f"  Series {r['series']}: Set {i} ({labels[i-1]}) = {score}/14")

    # Series 3174 specific analysis
    print()
    print("=" * 70)
    print("SERIES 3174 ANALYSIS (Latest)")
    print("=" * 70)
    for r in results:
        if r['series'] == 3174:
            print(f"  Winner: S{r['winner']} with {r['best']}/14")
            print(f"  All sets: {r['set_bests']}")

if __name__ == "__main__":
    analyze()
