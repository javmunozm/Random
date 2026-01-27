#!/usr/bin/env python3
"""
Final 7-Set Configuration Test
==============================
Test Gemini's recommendation: Symmetric Difference E1&E2 paired with Quint.
Goal: Diversity + High 12+ rate = Best jackpot chance.
"""

import json
from pathlib import Path
from collections import Counter


def load_data():
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def generate_fusion(e1, e2, freq):
    intersection = e1 & e2
    union = e1 | e2
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def generate_triple_fusion(e1, e2, e3, freq):
    in_all_3 = e1 & e2 & e3
    in_2 = ((e1 & e2) | (e1 & e3) | (e2 & e3)) - in_all_3
    in_1 = (e1 | e2 | e3) - in_all_3 - in_2
    result = list(in_all_3)
    result += sorted(in_2, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    if len(result) < 14:
        result += sorted(in_1, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    return sorted(result[:14])


def generate_quint_fusion(e1, e2, e3, e4, e5, freq):
    all_events = [e1, e2, e3, e4, e5]
    number_counts = Counter()
    for e in all_events:
        for n in e:
            number_counts[n] += 1
    ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


def generate_symmetric_diff_hybrid(e1, e2, freq):
    """Symmetric difference of E1&E2, filled with high-frequency numbers."""
    sym_diff = (e1 | e2) - (e1 & e2)  # Numbers in one but not both
    result = list(sym_diff)

    if len(result) < 14:
        # Fill with highest frequency numbers not already included
        remaining = [n for n in range(1, 26) if n not in result]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        result += remaining[:14 - len(result)]

    return sorted(result[:14])


def generate_7set(data, series_id, s6_strategy, s7_strategy):
    """Generate 7-set with configurable S6 and S7."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)
    max_freq = max(freq.values())

    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq[n]/max_freq, n))
    rank_set = set(ranked[:14])

    # Fixed sets (S1-S5)
    sets = [
        sorted(e4),                                      # S1: E4 direct
        sorted(ranked[:13] + [ranked[15]]),              # S2: rank16
        sorted(e6),                                      # S3: E6 direct
        sorted(e7),                                      # S4: E7 direct
        generate_fusion(e3, e7, freq),                   # S5: E3&E7 fusion
    ]

    # S6 strategies
    s6_options = {
        "E3": sorted(e3),
        "Triple_E1E3E7": generate_triple_fusion(e1, e3, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Quint_E1E3E4E6E7": generate_quint_fusion(e1, e3, e4, e6, e7, freq),
        "Quint_E2E3E4E6E7": generate_quint_fusion(e2, e3, e4, e6, e7, freq),
        "SymDiff_E1E2": generate_symmetric_diff_hybrid(e1, e2, freq),
        "SymDiff_E4E6": generate_symmetric_diff_hybrid(e4, e6, freq),
        "SymDiff_E3E7": generate_symmetric_diff_hybrid(e3, e7, freq),
    }
    sets.append(s6_options.get(s6_strategy, sorted(e3)))

    # S7 strategies
    s7_options = {
        "E6E7": generate_fusion(e6, e7, freq),
        "Triple_E1E3E7": generate_triple_fusion(e1, e3, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Hybrid_Rank_E7": generate_fusion(rank_set, e7, freq),
        "Quint_E1E3E4E6E7": generate_quint_fusion(e1, e3, e4, e6, e7, freq),
        "Quint_E2E3E4E6E7": generate_quint_fusion(e2, e3, e4, e6, e7, freq),
        "SymDiff_E1E2": generate_symmetric_diff_hybrid(e1, e2, freq),
    }
    sets.append(s7_options.get(s7_strategy, generate_fusion(e6, e7, freq)))

    return sets


def evaluate_7set(data, start, end, s6_strategy, s7_strategy):
    """Evaluate full 7-set performance."""
    results = []
    wins = [0] * 7

    for sid in range(start, end + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue

        sets = generate_7set(data, sid, s6_strategy, s7_strategy)
        if not sets:
            continue

        actual = data[str(sid)]

        set_bests = []
        for s in sets:
            match = max(len(set(s) & set(e)) for e in actual)
            set_bests.append(match)

        best = max(set_bests)
        winner = set_bests.index(best)
        wins[winner] += 1
        results.append(best)

    if not results:
        return None

    n = len(results)
    return {
        "tested": n,
        "avg": sum(results) / n,
        "best": max(results),
        "worst": min(results),
        "wins": wins,
        "at_11": sum(1 for r in results if r >= 11),
        "at_12": sum(1 for r in results if r >= 12),
        "at_13": sum(1 for r in results if r >= 13),
    }


def main():
    data = load_data()
    start, end = 2981, 3180
    l30_start, l30_end = 3151, 3180

    print("Final 7-Set Configuration Test")
    print("=" * 85)
    print("Goal: Find optimal balance of 12+ hits and 13+ hits (diversity for jackpot)")
    print()

    # All candidates to test
    print("COMPREHENSIVE TEST")
    print("-" * 85)
    print(f"{'S6':<24} {'S7':<24} {'Avg':<8} {'11+':<6} {'12+':<6} {'13+':<6} {'L30':<8}")
    print("-" * 85)

    combos = [
        # Baseline
        ("E3", "E6E7"),
        # Best by 12+ (redundant)
        ("Quint_E1E3E4E6E7", "Quint_E2E3E4E6E7"),
        # Best by 13+ (diverse)
        ("Triple_E1E3E7", "Quint_E2E3E4E6E7"),
        ("Quint_E2E3E4E6E7", "Triple_E1E3E7"),
        # Gemini recommendation: SymDiff + Quint
        ("SymDiff_E1E2", "Quint_E2E3E4E6E7"),
        ("SymDiff_E4E6", "Quint_E2E3E4E6E7"),
        ("SymDiff_E3E7", "Quint_E2E3E4E6E7"),
        # Triple + Triple (max diversity)
        ("Triple_E1E3E7", "Triple_E4E6E7"),
        # Mixed approaches
        ("Triple_E1E3E7", "Hybrid_Rank_E7"),
        ("Quint_E1E3E4E6E7", "Triple_E1E3E7"),
        ("Triple_E4E6E7", "Quint_E1E3E4E6E7"),
        # SymDiff alternatives
        ("SymDiff_E1E2", "Triple_E1E3E7"),
        ("SymDiff_E4E6", "Triple_E4E6E7"),
    ]

    all_results = []

    for s6, s7 in combos:
        r = evaluate_7set(data, start, end, s6, s7)
        r_l30 = evaluate_7set(data, l30_start, l30_end, s6, s7)
        all_results.append((s6, s7, r, r_l30))
        print(f"{s6:<24} {s7:<24} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6} {r_l30['avg']:.2f}")

    # Rank by jackpot potential (weighted: 13+ x2, 12+ x1)
    all_results.sort(key=lambda x: (-2*x[2]['at_13'] - x[2]['at_12'], -x[2]['avg']))

    print("\n" + "=" * 85)
    print("RANKING BY JACKPOT POTENTIAL (13+ x2 + 12+ weighted)")
    print("-" * 85)
    print(f"{'Rank':<5} {'S6':<22} {'S7':<22} {'12+':<6} {'13+':<6} {'Score':<8}")
    print("-" * 85)

    baseline_r = evaluate_7set(data, start, end, "E3", "E6E7")

    for i, (s6, s7, r, r_l30) in enumerate(all_results[:10], 1):
        score = 2 * r['at_13'] + r['at_12']
        print(f"{i:<5} {s6:<22} {s7:<22} {r['at_12']:<6} {r['at_13']:<6} {score:<8}")

    # Best configuration
    print("\n" + "=" * 85)
    print("RECOMMENDED CONFIGURATION FOR JACKPOT")
    print("-" * 85)

    best_s6, best_s7, best_r, best_l30 = all_results[0]
    print(f"\nS6: {best_s6}")
    print(f"S7: {best_s7}")
    print(f"\nFull (200 series):")
    print(f"  12+ hits: {best_r['at_12']} (vs baseline {baseline_r['at_12']}, {best_r['at_12'] - baseline_r['at_12']:+d})")
    print(f"  13+ hits: {best_r['at_13']} (vs baseline {baseline_r['at_13']}, {best_r['at_13'] - baseline_r['at_13']:+d})")
    print(f"  Average: {best_r['avg']:.2f}/14")
    print(f"\nL30: avg={best_l30['avg']:.2f}, 12+={best_l30['at_12']}, 11+={best_l30['at_11']}")

    # Compare top 3 approaches
    print("\n" + "=" * 85)
    print("FINAL COMPARISON: TOP 3 STRATEGIES")
    print("-" * 85)
    print(f"{'Strategy':<50} {'12+':<8} {'13+':<8} {'L30 Avg':<10}")
    print("-" * 85)

    strategies = [
        ("Current (E3 + E6E7)", "E3", "E6E7"),
        ("Dual Quint (max 12+, redundant)", "Quint_E1E3E4E6E7", "Quint_E2E3E4E6E7"),
        ("Triple+Quint (max 13+, diverse)", "Triple_E1E3E7", "Quint_E2E3E4E6E7"),
    ]

    for name, s6, s7 in strategies:
        r = evaluate_7set(data, start, end, s6, s7)
        r_l30 = evaluate_7set(data, l30_start, l30_end, s6, s7)
        print(f"{name:<50} {r['at_12']:<8} {r['at_13']:<8} {r_l30['avg']:.2f}")


if __name__ == "__main__":
    main()
