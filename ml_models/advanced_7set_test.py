#!/usr/bin/env python3
"""
Advanced 7-Set Test
===================
Test full 7-set performance with advanced replacements:
- Quintuple fusions for S6
- Conditional overlap strategies
- Recency-weighted events
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


def generate_conditional_e1e4(events, freq):
    e1, e4 = events[0], events[3]
    overlap = len(e1 & e4)
    if overlap >= 10:
        return generate_fusion(e1, e4, freq)
    else:
        union = e1 | e4
        outside = [n for n in range(1, 26) if n not in union]
        if len(outside) >= 14:
            return sorted(sorted(outside, key=lambda n: -freq.get(n, 0))[:14])
        else:
            result = outside + sorted(union, key=lambda n: -freq.get(n, 0))[:14 - len(outside)]
            return sorted(result[:14])


def generate_recency_event(data, series_id, event_idx, lookback=3, decay=0.5):
    number_scores = Counter()
    weight = 1.0
    for offset in range(lookback):
        sid = str(series_id - 1 - offset)
        if sid not in data:
            break
        event = data[sid][event_idx]
        for n in event:
            number_scores[n] += weight
        weight *= decay
    ranked = sorted(range(1, 26), key=lambda n: (-number_scores[n], n))
    return set(ranked[:14])


def generate_7set(data, series_id, s6_strategy="E3", s7_strategy="E6E7"):
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

    # S6 - configurable
    s6_options = {
        "E3": sorted(e3),
        "Triple_E3E6E7": generate_triple_fusion(e3, e6, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Triple_E1E3E7": generate_triple_fusion(e1, e3, e7, freq),
        "Hybrid_Rank_E7": generate_fusion(rank_set, e7, freq),
        "Triple_E3E4E7": generate_triple_fusion(e3, e4, e7, freq),
        "Quint_E1E3E4E6E7": generate_quint_fusion(e1, e3, e4, e6, e7, freq),
        "Quint_E2E3E4E6E7": generate_quint_fusion(e2, e3, e4, e6, e7, freq),
        "Conditional_E1E4": generate_conditional_e1e4(events, freq),
    }
    sets.append(s6_options.get(s6_strategy, sorted(e3)))

    # S7 - configurable
    re4 = generate_recency_event(data, series_id, 3)
    re6 = generate_recency_event(data, series_id, 5)
    re7 = generate_recency_event(data, series_id, 6)

    s7_options = {
        "E6E7": generate_fusion(e6, e7, freq),
        "Triple_E3E6E7": generate_triple_fusion(e3, e6, e7, freq),
        "Triple_E4E6E7": generate_triple_fusion(e4, e6, e7, freq),
        "Hybrid_Rank_E7": generate_fusion(rank_set, e7, freq),
        "Triple_E1E3E7": generate_triple_fusion(e1, e3, e7, freq),
        "Quint_E1E3E4E6E7": generate_quint_fusion(e1, e3, e4, e6, e7, freq),
        "Quint_E2E3E4E6E7": generate_quint_fusion(e2, e3, e4, e6, e7, freq),
        "Recency_Triple": generate_triple_fusion(re4, re6, re7, freq),
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

    print("Advanced 7-Set Replacement Test")
    print("=" * 70)
    print()

    # Current configuration
    print("CURRENT 7-SET (S6=E3, S7=E6E7)")
    print("-" * 70)
    r = evaluate_7set(data, start, end, "E3", "E6E7")
    baseline_avg = r['avg']
    baseline_12 = r['at_12']
    baseline_11 = r['at_11']
    baseline_13 = r['at_13']
    print(f"Full:  avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, 13+={r['at_13']}, best={r['best']}")

    r_l30 = evaluate_7set(data, l30_start, l30_end, "E3", "E6E7")
    print(f"L30:   avg={r_l30['avg']:.2f}, 11+={r_l30['at_11']}, 12+={r_l30['at_12']}")

    # Test quintuple fusions as S6
    print("\n" + "=" * 70)
    print("TESTING QUINTUPLE FUSIONS AS S6 (S7 stays E6E7)")
    print("-" * 70)
    print(f"{'S6 Strategy':<25} {'Avg':<8} {'11+':<6} {'12+':<6} {'13+':<6} {'vs Base'}")
    print("-" * 70)

    s6_candidates = [
        "E3", "Quint_E1E3E4E6E7", "Quint_E2E3E4E6E7", "Conditional_E1E4",
        "Triple_E1E3E7", "Triple_E3E6E7"
    ]

    best_s6 = None
    best_s6_avg = 0

    for s6 in s6_candidates:
        r = evaluate_7set(data, start, end, s6, "E6E7")
        diff = r['avg'] - baseline_avg
        if r['avg'] > best_s6_avg:
            best_s6_avg = r['avg']
            best_s6 = (s6, r)
        print(f"{s6:<25} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6} {diff:+.2f}")

    # Test combined replacements with best S6
    print("\n" + "=" * 70)
    print("TESTING COMBINED S6+S7 REPLACEMENTS")
    print("-" * 70)
    print(f"{'S6':<20} {'S7':<20} {'Avg':<8} {'11+':<6} {'12+':<6} {'13+':<6} {'vs Base'}")
    print("-" * 70)

    best_combo = None
    best_12 = 0
    best_combo_avg = 0

    combos = [
        # Quintuple S6 + various S7
        ("Quint_E1E3E4E6E7", "E6E7"),
        ("Quint_E1E3E4E6E7", "Triple_E1E3E7"),
        ("Quint_E1E3E4E6E7", "Hybrid_Rank_E7"),
        ("Quint_E1E3E4E6E7", "Recency_Triple"),
        ("Quint_E2E3E4E6E7", "E6E7"),
        ("Quint_E2E3E4E6E7", "Triple_E1E3E7"),
        ("Quint_E2E3E4E6E7", "Quint_E1E3E4E6E7"),
        # Conditional S6 + various S7
        ("Conditional_E1E4", "E6E7"),
        ("Conditional_E1E4", "Quint_E1E3E4E6E7"),
        ("Conditional_E1E4", "Triple_E1E3E7"),
        # Previous best combinations
        ("Triple_E1E3E7", "Hybrid_Rank_E7"),
        ("Triple_E4E6E7", "Triple_E1E3E7"),
        ("Triple_E3E6E7", "Quint_E1E3E4E6E7"),
    ]

    for s6, s7 in combos:
        r = evaluate_7set(data, start, end, s6, s7)
        diff = r['avg'] - baseline_avg
        if r['at_12'] > best_12 or (r['at_12'] == best_12 and r['avg'] > best_combo_avg):
            best_12 = r['at_12']
            best_combo_avg = r['avg']
            best_combo = (s6, s7, r)
        print(f"{s6:<20} {s7:<20} {r['avg']:.2f}    {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6} {diff:+.2f}")

    # Best overall
    print("\n" + "=" * 70)
    print("BEST CONFIGURATION FOUND")
    print("-" * 70)

    if best_combo:
        s6, s7, r = best_combo
        print(f"\nS6: {s6}")
        print(f"S7: {s7}")
        print(f"\nFull: avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, 13+={r['at_13']}, best={r['best']}")
        print(f"Improvement vs baseline: avg {r['avg'] - baseline_avg:+.2f}, 11+ {r['at_11'] - baseline_11:+d}, 12+ {r['at_12'] - baseline_12:+d}, 13+ {r['at_13'] - baseline_13:+d}")

        # L30 validation
        r_l30 = evaluate_7set(data, l30_start, l30_end, s6, s7)
        print(f"\nL30: avg={r_l30['avg']:.2f}, 11+={r_l30['at_11']}, 12+={r_l30['at_12']}, best={r_l30['best']}")

    # Summary comparison
    print("\n" + "=" * 70)
    print("SUMMARY: TOP 3 CONFIGURATIONS")
    print("-" * 70)

    configs = [
        ("Current", "E3", "E6E7"),
        ("Best Triple", "Triple_E1E3E7", "Hybrid_Rank_E7"),
        ("Best Quint", "Quint_E1E3E4E6E7", "Triple_E1E3E7"),
    ]

    print(f"{'Config':<15} {'S6':<20} {'S7':<20} {'Avg':<8} {'12+':<6} {'L30 Avg'}")
    print("-" * 70)

    for name, s6, s7 in configs:
        r = evaluate_7set(data, start, end, s6, s7)
        r_l30 = evaluate_7set(data, l30_start, l30_end, s6, s7)
        print(f"{name:<15} {s6:<20} {s7:<20} {r['avg']:.2f}    {r['at_12']:<6} {r_l30['avg']:.2f}")


if __name__ == "__main__":
    main()
