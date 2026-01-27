#!/usr/bin/env python3
"""
Gemini Deep Analysis
====================
Extended testing based on Gemini's recommendations:
1. More triple fusions (E1E3E7, E3E4E7, E2E6E7, E5E6E7)
2. Meta-fusions (combine winning strategies)
3. 4-event fusions
4. Time-weighted fusions
5. Dynamic fusions (auto-select highest overlap events)
6. Hybrid rank/event fusions
"""

import json
from pathlib import Path
from collections import Counter
import math

def load_data():
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def time_weighted_freq(data, series_id, decay=0.99):
    """Calculate frequency with exponential decay for older series."""
    freq = Counter()
    series_list = sorted(int(s) for s in data.keys() if int(s) < series_id)

    for i, sid in enumerate(series_list):
        weight = decay ** (len(series_list) - 1 - i)  # Recent = higher weight
        for e in data[str(sid)]:
            for n in e:
                freq[n] += weight
    return freq


def generate_fusion(e1, e2, freq):
    """Two-event fusion."""
    intersection = e1 & e2
    union = e1 | e2
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def generate_triple_fusion(e1, e2, e3, freq):
    """Three-event fusion."""
    in_all_3 = e1 & e2 & e3
    in_2 = ((e1 & e2) | (e1 & e3) | (e2 & e3)) - in_all_3
    in_1 = (e1 | e2 | e3) - in_all_3 - in_2

    result = list(in_all_3)
    result += sorted(in_2, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    if len(result) < 14:
        result += sorted(in_1, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    return sorted(result[:14])


def generate_quad_fusion(e1, e2, e3, e4, freq):
    """Four-event fusion."""
    in_all_4 = e1 & e2 & e3 & e4
    in_3 = set()
    for combo in [(e1,e2,e3), (e1,e2,e4), (e1,e3,e4), (e2,e3,e4)]:
        in_3 |= (combo[0] & combo[1] & combo[2])
    in_3 -= in_all_4

    in_2 = set()
    for combo in [(e1,e2), (e1,e3), (e1,e4), (e2,e3), (e2,e4), (e3,e4)]:
        in_2 |= (combo[0] & combo[1])
    in_2 -= in_all_4
    in_2 -= in_3

    in_1 = (e1 | e2 | e3 | e4) - in_all_4 - in_3 - in_2

    result = list(in_all_4)
    result += sorted(in_3, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    if len(result) < 14:
        result += sorted(in_2, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    if len(result) < 14:
        result += sorted(in_1, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    return sorted(result[:14])


def generate_meta_fusion(set1, set2, freq):
    """Meta-fusion: combine two generated sets."""
    s1, s2 = set(set1), set(set2)
    intersection = s1 & s2
    union = s1 | s2
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def find_highest_overlap_pair(events):
    """Find the two events with highest overlap."""
    best_overlap = 0
    best_pair = (0, 1)
    for i in range(7):
        for j in range(i+1, 7):
            overlap = len(events[i] & events[j])
            if overlap > best_overlap:
                best_overlap = overlap
                best_pair = (i, j)
    return best_pair


def find_highest_overlap_triple(events):
    """Find the three events with highest combined overlap."""
    best_overlap = 0
    best_triple = (0, 1, 2)
    for i in range(7):
        for j in range(i+1, 7):
            for k in range(j+1, 7):
                # Sum of pairwise overlaps
                overlap = (len(events[i] & events[j]) +
                          len(events[i] & events[k]) +
                          len(events[j] & events[k]))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_triple = (i, j, k)
    return best_triple


def generate_all_strategies(data, series_id):
    """Generate all test strategies for a series."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)
    tw_freq = time_weighted_freq(data, series_id, decay=0.995)

    strategies = {}

    # Current best (for comparison)
    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq[n], n))
    strategies["Current_S6_E3"] = sorted(e3)
    strategies["Current_S5_E3E7"] = generate_fusion(e3, e7, freq)

    # === 1. MORE TRIPLE FUSIONS ===
    strategies["Triple_E1E3E7"] = generate_triple_fusion(e1, e3, e7, freq)
    strategies["Triple_E3E4E7"] = generate_triple_fusion(e3, e4, e7, freq)
    strategies["Triple_E2E6E7"] = generate_triple_fusion(e2, e6, e7, freq)
    strategies["Triple_E5E6E7"] = generate_triple_fusion(e5, e6, e7, freq)
    strategies["Triple_E1E3E4"] = generate_triple_fusion(e1, e3, e4, freq)
    strategies["Triple_E3E6E7"] = generate_triple_fusion(e3, e6, e7, freq)  # Previous winner
    strategies["Triple_E4E6E7"] = generate_triple_fusion(e4, e6, e7, freq)  # Previous winner

    # === 2. META-FUSIONS ===
    t1 = generate_triple_fusion(e3, e6, e7, freq)
    t2 = generate_triple_fusion(e4, e6, e7, freq)
    strategies["Meta_T3E6E7_T4E6E7"] = generate_meta_fusion(t1, t2, freq)

    t3 = generate_triple_fusion(e1, e3, e7, freq)
    strategies["Meta_T1E3E7_T3E6E7"] = generate_meta_fusion(t3, t1, freq)

    # === 3. QUAD FUSIONS ===
    strategies["Quad_E3E4E6E7"] = generate_quad_fusion(e3, e4, e6, e7, freq)
    strategies["Quad_E1E4E6E7"] = generate_quad_fusion(e1, e4, e6, e7, freq)
    strategies["Quad_E1E3E6E7"] = generate_quad_fusion(e1, e3, e6, e7, freq)
    strategies["Quad_E2E4E6E7"] = generate_quad_fusion(e2, e4, e6, e7, freq)

    # === 4. TIME-WEIGHTED FUSIONS ===
    strategies["Triple_E3E6E7_TW"] = generate_triple_fusion(e3, e6, e7, tw_freq)
    strategies["Triple_E4E6E7_TW"] = generate_triple_fusion(e4, e6, e7, tw_freq)
    strategies["Triple_E3E4E7_TW"] = generate_triple_fusion(e3, e4, e7, tw_freq)
    strategies["Fusion_E3E7_TW"] = generate_fusion(e3, e7, tw_freq)

    # === 5. DYNAMIC FUSIONS ===
    # Auto-select highest overlap pair/triple
    i, j = find_highest_overlap_pair(events)
    strategies["Dynamic_BestPair"] = generate_fusion(events[i], events[j], freq)

    i, j, k = find_highest_overlap_triple(events)
    strategies["Dynamic_BestTriple"] = generate_triple_fusion(events[i], events[j], events[k], freq)

    # === 6. HYBRID RANK/EVENT FUSIONS ===
    rank_set = set(ranked[:14])
    strategies["Hybrid_Rank_E7"] = generate_fusion(rank_set, e7, freq)
    strategies["Hybrid_Rank_E4"] = generate_fusion(rank_set, e4, freq)
    strategies["Hybrid_Rank_E6"] = generate_fusion(rank_set, e6, freq)

    # Rank + triple
    strategies["Hybrid_Rank_T367"] = generate_meta_fusion(ranked[:14], t1, freq)

    return strategies


def evaluate_strategy(data, start, end, strategy_name):
    """Evaluate a single strategy."""
    scores = []

    for sid in range(start, end + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue

        strategies = generate_all_strategies(data, sid)
        if not strategies or strategy_name not in strategies:
            continue

        pred = set(strategies[strategy_name])
        actual = data[str(sid)]
        best_match = max(len(pred & set(e)) for e in actual)
        scores.append(best_match)

    if not scores:
        return None

    n = len(scores)
    return {
        "tested": n,
        "avg": sum(scores) / n,
        "best": max(scores),
        "worst": min(scores),
        "at_11": sum(1 for s in scores if s >= 11),
        "at_12": sum(1 for s in scores if s >= 12),
        "at_13": sum(1 for s in scores if s >= 13),
    }


def main():
    data = load_data()
    start, end = 2981, 3180
    l30_start, l30_end = 3151, 3180

    print("Gemini Deep Analysis")
    print("=" * 70)
    print(f"Testing on {start}-{end} (200 series)")
    print()

    # Get all strategy names
    sample = generate_all_strategies(data, 3100)

    categories = {
        "BASELINE": ["Current_S6_E3", "Current_S5_E3E7"],
        "MORE TRIPLE FUSIONS": ["Triple_E1E3E7", "Triple_E3E4E7", "Triple_E2E6E7",
                                 "Triple_E5E6E7", "Triple_E1E3E4", "Triple_E3E6E7", "Triple_E4E6E7"],
        "META-FUSIONS": ["Meta_T3E6E7_T4E6E7", "Meta_T1E3E7_T3E6E7"],
        "QUAD FUSIONS": ["Quad_E3E4E6E7", "Quad_E1E4E6E7", "Quad_E1E3E6E7", "Quad_E2E4E6E7"],
        "TIME-WEIGHTED": ["Triple_E3E6E7_TW", "Triple_E4E6E7_TW", "Triple_E3E4E7_TW", "Fusion_E3E7_TW"],
        "DYNAMIC": ["Dynamic_BestPair", "Dynamic_BestTriple"],
        "HYBRID RANK/EVENT": ["Hybrid_Rank_E7", "Hybrid_Rank_E4", "Hybrid_Rank_E6", "Hybrid_Rank_T367"],
    }

    all_results = []

    for category, strategies in categories.items():
        print(f"\n{'=' * 70}")
        print(f"{category}")
        print("-" * 70)
        print(f"{'Strategy':<25} {'Avg':<8} {'Best':<6} {'11+':<6} {'12+':<6} {'13+':<6}")
        print("-" * 70)

        for name in strategies:
            r = evaluate_strategy(data, start, end, name)
            if r:
                all_results.append((name, r, category))
                print(f"{name:<25} {r['avg']:.2f}    {r['best']:<6} {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    # Overall ranking
    all_results.sort(key=lambda x: (-x[1]['at_12'], -x[1]['at_11'], -x[1]['avg']))

    print("\n" + "=" * 70)
    print("TOP 15 STRATEGIES OVERALL (by 12+, then 11+, then avg)")
    print("-" * 70)
    print(f"{'Rank':<5} {'Strategy':<25} {'Avg':<8} {'12+':<6} {'11+':<6} {'Category'}")
    print("-" * 70)

    for i, (name, r, cat) in enumerate(all_results[:15], 1):
        cat_short = cat[:15] + "..." if len(cat) > 15 else cat
        print(f"{i:<5} {name:<25} {r['avg']:.2f}    {r['at_12']:<6} {r['at_11']:<6} {cat_short}")

    # L30 validation of top 5
    print("\n" + "=" * 70)
    print("L30 VALIDATION OF TOP 5")
    print("-" * 70)

    for name, _, _ in all_results[:5]:
        r = evaluate_strategy(data, l30_start, l30_end, name)
        if r:
            print(f"{name:<25} L30: avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, best={r['best']}")

    # Compare best with current S6
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("-" * 70)

    best_name, best_r, best_cat = all_results[0]
    s6_r = evaluate_strategy(data, start, end, "Current_S6_E3")

    print(f"\nBest new strategy: {best_name} ({best_cat})")
    print(f"  Full: avg={best_r['avg']:.2f}, 12+={best_r['at_12']}, 11+={best_r['at_11']}")
    print(f"\nCurrent S6 (E3): avg={s6_r['avg']:.2f}, 12+={s6_r['at_12']}, 11+={s6_r['at_11']}")
    print(f"\nImprovement: avg {best_r['avg'] - s6_r['avg']:+.2f}, 12+ {best_r['at_12'] - s6_r['at_12']:+d}, 11+ {best_r['at_11'] - s6_r['at_11']:+d}")


if __name__ == "__main__":
    main()
