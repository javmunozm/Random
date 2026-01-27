#!/usr/bin/env python3
"""
E5 Replacement Test
===================
Test replacing current sets with E5-inclusive strategies to capture #16.
Goal: Improve jackpot chance without losing too much 12+ rate.
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


def generate_quint_fusion(events, freq):
    number_counts = Counter()
    for e in events:
        for n in e:
            number_counts[n] += 1
    ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


def generate_7set(data, series_id, replacement=None):
    """Generate 7-set with optional replacement."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)
    max_freq = max(freq.values())

    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq[n]/max_freq, n))

    # E3&E7 fusion (S5)
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # Current S6: SymDiff E3⊕E7
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # Current S7: Quint E2E3E4E6E7
    s7_numbers = generate_quint_fusion([e2, e3, e4, e6, e7], freq)

    # E5-inclusive replacement options
    e5_options = {
        "Triple_E3E5E7": generate_triple_fusion(e3, e5, e7, freq),
        "E5_E7_fusion": generate_fusion(e5, e7, freq),
        "Quint_withE5": generate_quint_fusion([e3, e4, e5, e6, e7], freq),
        "Triple_E4E5E7": generate_triple_fusion(e4, e5, e7, freq),
        "E5_direct": sorted(e5),
    }

    # Base 7 sets
    sets = [
        ("S1 (E4)", sorted(e4)),
        ("S2 (rank16)", sorted(ranked[:13] + [ranked[15]])),
        ("S3 (E6)", sorted(e6)),
        ("S4 (E7)", sorted(e7)),
        ("S5 (E3&E7)", sorted(s5_numbers)),
        ("S6 (SymDiff)", s6_numbers),
        ("S7 (Quint)", s7_numbers),
    ]

    # Apply replacement if specified
    if replacement:
        slot, strategy = replacement
        if strategy in e5_options:
            sets[slot] = (f"S{slot+1} ({strategy})", e5_options[strategy])

    return sets


def evaluate_7set(data, start, end, replacement=None):
    """Evaluate full 7-set performance."""
    results = []
    wins = [0] * 7
    near_misses_captured = 0

    # Track specific near-miss series
    near_miss_series = {3061: 16, 3086: 1, 3098: 16}

    for sid in range(start, end + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue

        sets = generate_7set(data, sid, replacement)
        if not sets:
            continue

        actual = data[str(sid)]

        set_bests = []
        for _, s in sets:
            match = max(len(set(s) & set(e)) for e in actual)
            set_bests.append(match)

        best = max(set_bests)
        winner = set_bests.index(best)
        wins[winner] += 1
        results.append(best)

        # Check if we would have captured the near-miss
        if sid in near_miss_series:
            missing_num = near_miss_series[sid]
            for _, s in sets:
                if missing_num in s:
                    # Check if this set would have hit 14/14
                    for e in actual:
                        if len(set(s) & set(e)) == 14:
                            near_misses_captured += 1
                            break

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
        "at_14": sum(1 for r in results if r >= 14),
        "near_misses_captured": near_misses_captured,
    }


def main():
    data = load_data()
    start, end = 2981, 3180
    l30_start, l30_end = 3151, 3180

    print("=" * 80)
    print("E5 REPLACEMENT TEST")
    print("=" * 80)
    print()
    print("Goal: Replace one set with E5-inclusive strategy to capture #16")
    print("      while minimizing loss of 12+ rate")
    print()

    # Baseline
    print("CURRENT BASELINE (no replacement)")
    print("-" * 80)
    r = evaluate_7set(data, start, end, None)
    baseline = r
    print(f"Full:  avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, 13+={r['at_13']}, 14+={r['at_14']}")
    print(f"Wins:  {r['wins']}")

    r_l30 = evaluate_7set(data, l30_start, l30_end, None)
    print(f"L30:   avg={r_l30['avg']:.2f}, 11+={r_l30['at_11']}, 12+={r_l30['at_12']}")

    # Test replacing each slot with E5-inclusive strategies
    e5_strategies = ["Triple_E3E5E7", "E5_E7_fusion", "Quint_withE5", "Triple_E4E5E7"]
    slots_to_test = [5, 6]  # S6 and S7 (0-indexed: 5, 6)

    print("\n" + "=" * 80)
    print("REPLACEMENT TESTS")
    print("-" * 80)
    print(f"{'Slot':<8} {'Replacement':<20} {'Avg':<8} {'11+':<6} {'12+':<6} {'13+':<6} {'vs Base'}")
    print("-" * 80)

    all_results = []

    for slot in slots_to_test:
        for strategy in e5_strategies:
            r = evaluate_7set(data, start, end, (slot, strategy))
            r_l30 = evaluate_7set(data, l30_start, l30_end, (slot, strategy))
            diff_12 = r['at_12'] - baseline['at_12']
            diff_13 = r['at_13'] - baseline['at_13']

            all_results.append({
                "slot": f"S{slot+1}",
                "strategy": strategy,
                "full": r,
                "l30": r_l30,
                "diff_12": diff_12,
                "diff_13": diff_13,
            })

            marker = ""
            if diff_12 >= 0 and diff_13 > 0:
                marker = " <-- BETTER"
            elif diff_12 >= 0:
                marker = " (same 12+)"

            print(f"S{slot+1:<7} {strategy:<20} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6} 12+:{diff_12:+d} 13+:{diff_13:+d}{marker}")

    # Sort by improvement
    all_results.sort(key=lambda x: (-x['diff_13'], -x['diff_12'], -x['full']['avg']))

    print("\n" + "=" * 80)
    print("BEST REPLACEMENTS (sorted by 13+ improvement, then 12+)")
    print("-" * 80)

    for i, res in enumerate(all_results[:5], 1):
        r = res['full']
        r_l30 = res['l30']
        print(f"\n{i}. Replace {res['slot']} with {res['strategy']}")
        print(f"   Full: avg={r['avg']:.2f}, 12+={r['at_12']} ({res['diff_12']:+d}), 13+={r['at_13']} ({res['diff_13']:+d})")
        print(f"   L30:  avg={r_l30['avg']:.2f}, 12+={r_l30['at_12']}, 11+={r_l30['at_11']}")

    # Check if any replacement would have captured the near-misses
    print("\n" + "=" * 80)
    print("NEAR-MISS CAPTURE ANALYSIS")
    print("-" * 80)

    for sid in [3061, 3098]:
        print(f"\nSeries {sid} (missed #16):")
        prior = data[str(sid - 1)]
        e5 = set(prior[4])
        print(f"  #16 in prior E5: {'YES' if 16 in e5 else 'NO'}")

        # Check each E5-inclusive strategy
        for strategy in e5_strategies:
            sets = generate_7set(data, sid, (5, strategy))  # Replace S6
            for name, s in sets:
                if strategy in name:
                    has_16 = 16 in s
                    actual = data[str(sid)]
                    best_match = max(len(set(s) & set(e)) for e in actual)
                    print(f"  {strategy}: #16={has_16}, match={best_match}/14")

    # Final recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    best = all_results[0]
    if best['diff_12'] >= 0 or best['diff_13'] > 0:
        print(f"\nReplace {best['slot']} with {best['strategy']}")
        print(f"  12+ change: {best['diff_12']:+d}")
        print(f"  13+ change: {best['diff_13']:+d}")
        print(f"  L30 avg: {best['l30']['avg']:.2f}")

        if best['diff_12'] < 0:
            print(f"\n  WARNING: This reduces 12+ rate by {abs(best['diff_12'])}")
            print(f"  Trade-off: Better jackpot diversity vs. lower consistency")
    else:
        print("\nNo E5 replacement improves overall performance.")
        print("Current configuration remains optimal.")


if __name__ == "__main__":
    main()
