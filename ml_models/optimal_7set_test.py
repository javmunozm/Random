#!/usr/bin/env python3
"""
Optimal 7-Set Configuration Test
================================
Find the best combination of all discovered strategies.
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
        "Triple_E3E6E7": generate_triple_fusion(e3, e6, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Hybrid_Rank_E7": generate_fusion(rank_set, e7, freq),
        "Quint_E1E3E4E6E7": generate_quint_fusion(e1, e3, e4, e6, e7, freq),
        "Quint_E2E3E4E6E7": generate_quint_fusion(e2, e3, e4, e6, e7, freq),
        "Quint_E2E4E5E6E7": generate_quint_fusion(e2, e4, e5, e6, e7, freq),
    }
    sets.append(s6_options.get(s6_strategy, sorted(e3)))

    # S7 strategies
    s7_options = {
        "E6E7": generate_fusion(e6, e7, freq),
        "Triple_E1E3E7": generate_triple_fusion(e1, e3, e7, freq),
        "Triple_E3E6E7": generate_triple_fusion(e3, e6, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Hybrid_Rank_E7": generate_fusion(rank_set, e7, freq),
        "Quint_E1E3E4E6E7": generate_quint_fusion(e1, e3, e4, e6, e7, freq),
        "Quint_E2E3E4E6E7": generate_quint_fusion(e2, e3, e4, e6, e7, freq),
        "Quint_E2E4E5E6E7": generate_quint_fusion(e2, e4, e5, e6, e7, freq),
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

    print("Optimal 7-Set Configuration Test")
    print("=" * 80)
    print()

    # Current baseline
    print("CURRENT BASELINE (S6=E3, S7=E6E7)")
    print("-" * 80)
    r = evaluate_7set(data, start, end, "E3", "E6E7")
    baseline = r
    print(f"Full:  avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, 13+={r['at_13']}, best={r['best']}")
    r_l30 = evaluate_7set(data, l30_start, l30_end, "E3", "E6E7")
    print(f"L30:   avg={r_l30['avg']:.2f}, 11+={r_l30['at_11']}, 12+={r_l30['at_12']}")

    # All candidate combinations
    print("\n" + "=" * 80)
    print("FULL COMBINATORIAL TEST")
    print("-" * 80)
    print(f"{'S6':<22} {'S7':<22} {'Avg':<8} {'11+':<6} {'12+':<6} {'13+':<6}")
    print("-" * 80)

    s6_candidates = ["E3", "Triple_E1E3E7", "Quint_E1E3E4E6E7", "Quint_E2E3E4E6E7"]
    s7_candidates = ["E6E7", "Triple_E1E3E7", "Hybrid_Rank_E7", "Quint_E1E3E4E6E7", "Quint_E2E3E4E6E7"]

    all_results = []

    for s6 in s6_candidates:
        for s7 in s7_candidates:
            r = evaluate_7set(data, start, end, s6, s7)
            r_l30 = evaluate_7set(data, l30_start, l30_end, s6, s7)
            all_results.append((s6, s7, r, r_l30))
            print(f"{s6:<22} {s7:<22} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    # Sort by 12+, then 13+, then avg
    all_results.sort(key=lambda x: (-x[2]['at_12'], -x[2]['at_13'], -x[2]['avg']))

    print("\n" + "=" * 80)
    print("TOP 10 CONFIGURATIONS (by 12+, then 13+, then avg)")
    print("-" * 80)
    print(f"{'Rank':<5} {'S6':<20} {'S7':<20} {'Avg':<8} {'12+':<6} {'13+':<6} {'L30 Avg':<8}")
    print("-" * 80)

    for i, (s6, s7, r, r_l30) in enumerate(all_results[:10], 1):
        diff_12 = r['at_12'] - baseline['at_12']
        diff_13 = r['at_13'] - baseline['at_13']
        print(f"{i:<5} {s6:<20} {s7:<20} {r['avg']:.2f}    {r['at_12']:<6} {r['at_13']:<6} {r_l30['avg']:.2f}")

    # Best configuration details
    print("\n" + "=" * 80)
    print("BEST CONFIGURATION DETAILS")
    print("-" * 80)

    best_s6, best_s7, best_r, best_l30 = all_results[0]
    print(f"\nS6: {best_s6}")
    print(f"S7: {best_s7}")
    print(f"\nFull (200 series):")
    print(f"  Average: {best_r['avg']:.2f}/14")
    print(f"  11+ hits: {best_r['at_11']} ({100*best_r['at_11']/200:.1f}%)")
    print(f"  12+ hits: {best_r['at_12']} ({100*best_r['at_12']/200:.1f}%)")
    print(f"  13+ hits: {best_r['at_13']} ({100*best_r['at_13']/200:.1f}%)")
    print(f"  Best: {best_r['best']}/14")
    print(f"\nL30 (recent):")
    print(f"  Average: {best_l30['avg']:.2f}/14")
    print(f"  11+ hits: {best_l30['at_11']} ({100*best_l30['at_11']/30:.1f}%)")
    print(f"  12+ hits: {best_l30['at_12']} ({100*best_l30['at_12']/30:.1f}%)")

    print(f"\nImprovement vs baseline:")
    print(f"  Avg: {best_r['avg'] - baseline['avg']:+.2f}")
    print(f"  11+: {best_r['at_11'] - baseline['at_11']:+d}")
    print(f"  12+: {best_r['at_12'] - baseline['at_12']:+d}")
    print(f"  13+: {best_r['at_13'] - baseline['at_13']:+d}")

    # Win distribution
    print(f"\nWin distribution by set:")
    print(f"  S1(E4)={best_r['wins'][0]} S2(rank16)={best_r['wins'][1]} S3(E6)={best_r['wins'][2]}")
    print(f"  S4(E7)={best_r['wins'][3]} S5(E3&E7)={best_r['wins'][4]} S6({best_s6})={best_r['wins'][5]} S7({best_s7})={best_r['wins'][6]}")

    # Additional analysis: overlap between S6 and S7
    print("\n" + "=" * 80)
    print("S6/S7 OVERLAP ANALYSIS FOR BEST CONFIG")
    print("-" * 80)

    # Check if using both Quint strategies causes overlap
    if "Quint" in best_s6 and "Quint" in best_s7:
        # Sample overlap check
        sample_sets = generate_7set(data, 3180, best_s6, best_s7)
        if sample_sets:
            s6_set = set(sample_sets[5])
            s7_set = set(sample_sets[6])
            overlap = len(s6_set & s7_set)
            print(f"Example (series 3181): S6 and S7 overlap by {overlap}/14 numbers")
            print(f"S6: {sample_sets[5]}")
            print(f"S7: {sample_sets[6]}")

    # Alternative: force diversity by using non-overlapping strategies
    print("\n" + "=" * 80)
    print("DIVERSE ALTERNATIVES (minimal S6/S7 overlap)")
    print("-" * 80)

    diverse_combos = [
        ("Quint_E2E3E4E6E7", "Triple_E1E3E7"),  # E2 quint vs E1 triple
        ("Quint_E1E3E4E6E7", "Triple_E4E6E7"),  # Different coverage
        ("Triple_E1E3E7", "Quint_E2E3E4E6E7"),  # Swap order
    ]

    print(f"{'S6':<22} {'S7':<22} {'Avg':<8} {'12+':<6} {'13+':<6} {'L30 Avg'}")
    print("-" * 80)

    for s6, s7 in diverse_combos:
        r = evaluate_7set(data, start, end, s6, s7)
        r_l30 = evaluate_7set(data, l30_start, l30_end, s6, s7)
        print(f"{s6:<22} {s7:<22} {r['avg']:.2f}    {r['at_12']:<6} {r['at_13']:<6} {r_l30['avg']:.2f}")


if __name__ == "__main__":
    main()
