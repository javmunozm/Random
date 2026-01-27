#!/usr/bin/env python3
"""
Replacement Test
================
Test replacing S6 (E3) and S7 (E6&E7) with better strategies.
Compare full 7-set performance.
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


def time_weighted_freq(data, series_id, decay=0.995):
    freq = Counter()
    series_list = sorted(int(s) for s in data.keys() if int(s) < series_id)
    for i, sid in enumerate(series_list):
        weight = decay ** (len(series_list) - 1 - i)
        for e in data[str(sid)]:
            for n in e:
                freq[n] += weight
    return freq


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


def generate_7set(data, series_id, s6_strategy="E3", s7_strategy="E6E7"):
    """Generate 7-set with configurable S6 and S7."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)
    tw_freq = time_weighted_freq(data, series_id)
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

    # S6 - configurable
    s6_options = {
        "E3": sorted(e3),
        "Triple_E3E6E7": generate_triple_fusion(e3, e6, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Triple_E1E3E7": generate_triple_fusion(e1, e3, e7, freq),
        "Hybrid_Rank_E7": generate_fusion(rank_set, e7, freq),
        "Triple_E3E4E7": generate_triple_fusion(e3, e4, e7, freq),
    }
    sets.append(s6_options.get(s6_strategy, sorted(e3)))

    # S7 - configurable
    s7_options = {
        "E6E7": generate_fusion(e6, e7, freq),
        "Triple_E3E6E7": generate_triple_fusion(e3, e6, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Hybrid_Rank_E7": generate_fusion(rank_set, e7, freq),
        "Triple_E1E3E7": generate_triple_fusion(e1, e3, e7, freq),
    }
    sets.append(s7_options.get(s7_strategy, generate_fusion(e6, e7, freq)))

    return sets


def evaluate_7set(data, start, end, s6_strategy="E3", s7_strategy="E6E7"):
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

    print("7-Set Replacement Analysis")
    print("=" * 70)
    print()

    # Current configuration
    print("CURRENT 7-SET (S6=E3, S7=E6E7)")
    print("-" * 70)
    r = evaluate_7set(data, start, end, "E3", "E6E7")
    baseline_avg = r['avg']
    baseline_12 = r['at_12']
    baseline_11 = r['at_11']
    print(f"Full:  avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, 13+={r['at_13']}, best={r['best']}")
    print(f"Wins:  S1={r['wins'][0]} S2={r['wins'][1]} S3={r['wins'][2]} S4={r['wins'][3]} S5={r['wins'][4]} S6={r['wins'][5]} S7={r['wins'][6]}")

    r_l30 = evaluate_7set(data, l30_start, l30_end, "E3", "E6E7")
    print(f"L30:   avg={r_l30['avg']:.2f}, 11+={r_l30['at_11']}, 12+={r_l30['at_12']}")

    # Test different S6 replacements
    print("\n" + "=" * 70)
    print("TESTING S6 REPLACEMENTS (S7 stays E6E7)")
    print("-" * 70)
    print(f"{'S6 Strategy':<25} {'Avg':<8} {'11+':<6} {'12+':<6} {'13+':<6} {'vs Base'}")
    print("-" * 70)

    s6_candidates = ["E3", "Triple_E3E6E7", "Triple_E4E6E7", "Triple_E1E3E7", "Hybrid_Rank_E7", "Triple_E3E4E7"]

    s6_results = []
    for s6 in s6_candidates:
        r = evaluate_7set(data, start, end, s6, "E6E7")
        diff = r['avg'] - baseline_avg
        s6_results.append((s6, r, diff))
        print(f"{s6:<25} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6} {diff:+.2f}")

    # Test different S7 replacements
    print("\n" + "=" * 70)
    print("TESTING S7 REPLACEMENTS (S6 stays E3)")
    print("-" * 70)
    print(f"{'S7 Strategy':<25} {'Avg':<8} {'11+':<6} {'12+':<6} {'13+':<6} {'vs Base'}")
    print("-" * 70)

    s7_candidates = ["E6E7", "Triple_E3E6E7", "Triple_E4E6E7", "Hybrid_Rank_E7", "Triple_E1E3E7"]

    s7_results = []
    for s7 in s7_candidates:
        r = evaluate_7set(data, start, end, "E3", s7)
        diff = r['avg'] - baseline_avg
        s7_results.append((s7, r, diff))
        print(f"{s7:<25} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6} {diff:+.2f}")

    # Test combined replacements
    print("\n" + "=" * 70)
    print("TESTING COMBINED S6+S7 REPLACEMENTS")
    print("-" * 70)
    print(f"{'S6':<18} {'S7':<18} {'Avg':<8} {'11+':<6} {'12+':<6} {'vs Base'}")
    print("-" * 70)

    best_combo = None
    best_avg = 0

    combos = [
        ("Triple_E3E6E7", "Triple_E4E6E7"),
        ("Triple_E3E6E7", "Hybrid_Rank_E7"),
        ("Triple_E4E6E7", "Triple_E1E3E7"),
        ("Hybrid_Rank_E7", "Triple_E3E6E7"),
        ("Triple_E1E3E7", "Triple_E4E6E7"),
        ("Triple_E3E4E7", "Hybrid_Rank_E7"),
    ]

    for s6, s7 in combos:
        r = evaluate_7set(data, start, end, s6, s7)
        diff = r['avg'] - baseline_avg
        if r['avg'] > best_avg:
            best_avg = r['avg']
            best_combo = (s6, s7, r)
        print(f"{s6:<18} {s7:<18} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {diff:+.2f}")

    # Best overall
    print("\n" + "=" * 70)
    print("BEST CONFIGURATION FOUND")
    print("-" * 70)

    if best_combo:
        s6, s7, r = best_combo
        print(f"\nS6: {s6}")
        print(f"S7: {s7}")
        print(f"\nFull: avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, 13+={r['at_13']}")
        print(f"Improvement vs baseline: avg {r['avg'] - baseline_avg:+.2f}, 11+ {r['at_11'] - baseline_11:+d}, 12+ {r['at_12'] - baseline_12:+d}")

        # L30 validation
        r_l30 = evaluate_7set(data, l30_start, l30_end, s6, s7)
        print(f"\nL30: avg={r_l30['avg']:.2f}, 11+={r_l30['at_11']}, 12+={r_l30['at_12']}")


if __name__ == "__main__":
    main()
