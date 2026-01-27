#!/usr/bin/env python3
"""
Gemini Strategy Test
====================
Test Gemini's recommended untested strategies:
1. Three-event fusions (E3&E6&E7)
2. E2/E5 in fusions (E2&E4, E5&E6)
3. Difference fusions (E4-E6)+(E6-E4)
4. Anti-E4 set (numbers NOT in prior E4)
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
    """Two-event fusion."""
    intersection = e1 & e2
    union = e1 | e2
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def generate_triple_fusion(e1, e2, e3, freq):
    """Three-event fusion - prioritize numbers in all 3, then 2, then 1."""
    in_all_3 = e1 & e2 & e3
    in_2 = ((e1 & e2) | (e1 & e3) | (e2 & e3)) - in_all_3
    in_1 = (e1 | e2 | e3) - in_all_3 - in_2

    result = list(in_all_3)
    result += sorted(in_2, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    if len(result) < 14:
        result += sorted(in_1, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    return sorted(result[:14])


def generate_difference_fusion(e1, e2, freq):
    """Difference fusion - numbers unique to each event."""
    only_e1 = e1 - e2
    only_e2 = e2 - e1
    unique = only_e1 | only_e2

    if len(unique) >= 14:
        return sorted(sorted(unique, key=lambda n: -freq.get(n, 0))[:14])
    else:
        # Fill with intersection if needed
        intersection = e1 & e2
        result = list(unique) + sorted(intersection, key=lambda n: -freq.get(n, 0))[:14 - len(unique)]
        return sorted(result[:14])


def generate_anti_event(event, freq):
    """Anti-event - 14 numbers NOT in the event."""
    outside = [n for n in range(1, 26) if n not in event]
    return sorted(sorted(outside, key=lambda n: -freq.get(n, 0))[:14])


def generate_all_strategies(data, series_id):
    """Generate all test strategies for a series."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)

    strategies = {}

    # Current 7-set strategies (for comparison)
    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq[n], n))
    strategies["S1_E4"] = sorted(e4)
    strategies["S2_rank16"] = sorted(ranked[:13] + [ranked[15]])
    strategies["S3_E6"] = sorted(e6)
    strategies["S4_E7"] = sorted(e7)
    strategies["S5_E3E7"] = generate_fusion(e3, e7, freq)
    strategies["S6_E3"] = sorted(e3)
    strategies["S7_E6E7"] = generate_fusion(e6, e7, freq)

    # === GEMINI RECOMMENDED TESTS ===

    # 1. Three-event fusions
    strategies["Triple_E3E6E7"] = generate_triple_fusion(e3, e6, e7, freq)
    strategies["Triple_E4E6E7"] = generate_triple_fusion(e4, e6, e7, freq)
    strategies["Triple_E1E4E6"] = generate_triple_fusion(e1, e4, e6, freq)
    strategies["Triple_E1E6E7"] = generate_triple_fusion(e1, e6, e7, freq)

    # 2. E2/E5 in fusions
    strategies["Fusion_E2E4"] = generate_fusion(e2, e4, freq)
    strategies["Fusion_E2E6"] = generate_fusion(e2, e6, freq)
    strategies["Fusion_E2E7"] = generate_fusion(e2, e7, freq)
    strategies["Fusion_E5E6"] = generate_fusion(e5, e6, freq)
    strategies["Fusion_E5E7"] = generate_fusion(e5, e7, freq)
    strategies["Fusion_E4E5"] = generate_fusion(e4, e5, freq)

    # 3. Difference fusions
    strategies["Diff_E4E6"] = generate_difference_fusion(e4, e6, freq)
    strategies["Diff_E4E7"] = generate_difference_fusion(e4, e7, freq)
    strategies["Diff_E6E7"] = generate_difference_fusion(e6, e7, freq)
    strategies["Diff_E3E4"] = generate_difference_fusion(e3, e4, freq)

    # 4. Anti-event sets
    strategies["Anti_E4"] = generate_anti_event(e4, freq)
    strategies["Anti_E6"] = generate_anti_event(e6, freq)
    strategies["Anti_E7"] = generate_anti_event(e7, freq)
    strategies["Anti_E1"] = generate_anti_event(e1, freq)

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

    print("Gemini Strategy Test")
    print("=" * 70)
    print(f"Testing on {start}-{end} (200 series) and L30 ({l30_start}-{l30_end})")
    print()

    # Get all strategy names
    sample = generate_all_strategies(data, 3100)

    # Current 7-set strategies
    current_7 = ["S1_E4", "S2_rank16", "S3_E6", "S4_E7", "S5_E3E7", "S6_E3", "S7_E6E7"]

    # New test strategies
    triple_fusions = ["Triple_E3E6E7", "Triple_E4E6E7", "Triple_E1E4E6", "Triple_E1E6E7"]
    e2_e5_fusions = ["Fusion_E2E4", "Fusion_E2E6", "Fusion_E2E7", "Fusion_E5E6", "Fusion_E5E7", "Fusion_E4E5"]
    diff_fusions = ["Diff_E4E6", "Diff_E4E7", "Diff_E6E7", "Diff_E3E4"]
    anti_events = ["Anti_E4", "Anti_E6", "Anti_E7", "Anti_E1"]

    print("CURRENT 7-SET INDIVIDUAL PERFORMANCE")
    print("-" * 70)
    print(f"{'Strategy':<20} {'Avg':<8} {'Best':<6} {'11+':<6} {'12+':<6} {'13+':<6}")
    print("-" * 70)

    for name in current_7:
        r = evaluate_strategy(data, start, end, name)
        if r:
            print(f"{name:<20} {r['avg']:.2f}    {r['best']:<6} {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    print("\n" + "=" * 70)
    print("1. THREE-EVENT FUSIONS")
    print("-" * 70)
    print(f"{'Strategy':<20} {'Avg':<8} {'Best':<6} {'11+':<6} {'12+':<6} {'13+':<6}")
    print("-" * 70)

    for name in triple_fusions:
        r = evaluate_strategy(data, start, end, name)
        if r:
            print(f"{name:<20} {r['avg']:.2f}    {r['best']:<6} {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    print("\n" + "=" * 70)
    print("2. E2/E5 IN FUSIONS")
    print("-" * 70)
    print(f"{'Strategy':<20} {'Avg':<8} {'Best':<6} {'11+':<6} {'12+':<6} {'13+':<6}")
    print("-" * 70)

    for name in e2_e5_fusions:
        r = evaluate_strategy(data, start, end, name)
        if r:
            print(f"{name:<20} {r['avg']:.2f}    {r['best']:<6} {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    print("\n" + "=" * 70)
    print("3. DIFFERENCE FUSIONS")
    print("-" * 70)
    print(f"{'Strategy':<20} {'Avg':<8} {'Best':<6} {'11+':<6} {'12+':<6} {'13+':<6}")
    print("-" * 70)

    for name in diff_fusions:
        r = evaluate_strategy(data, start, end, name)
        if r:
            print(f"{name:<20} {r['avg']:.2f}    {r['best']:<6} {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    print("\n" + "=" * 70)
    print("4. ANTI-EVENT SETS (Contrarian)")
    print("-" * 70)
    print(f"{'Strategy':<20} {'Avg':<8} {'Best':<6} {'11+':<6} {'12+':<6} {'13+':<6}")
    print("-" * 70)

    for name in anti_events:
        r = evaluate_strategy(data, start, end, name)
        if r:
            print(f"{name:<20} {r['avg']:.2f}    {r['best']:<6} {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    # Find best performers from new strategies
    print("\n" + "=" * 70)
    print("TOP NEW STRATEGIES (sorted by 12+, then avg)")
    print("-" * 70)

    new_strategies = triple_fusions + e2_e5_fusions + diff_fusions + anti_events
    results = []
    for name in new_strategies:
        r = evaluate_strategy(data, start, end, name)
        if r:
            results.append((name, r))

    results.sort(key=lambda x: (-x[1]['at_12'], -x[1]['avg']))

    print(f"{'Rank':<5} {'Strategy':<20} {'Avg':<8} {'12+':<6} {'vs S6_E3'}")
    print("-" * 70)

    s6_result = evaluate_strategy(data, start, end, "S6_E3")
    s6_avg = s6_result['avg'] if s6_result else 0

    for i, (name, r) in enumerate(results[:10], 1):
        diff = r['avg'] - s6_avg
        print(f"{i:<5} {name:<20} {r['avg']:.2f}    {r['at_12']:<6} {diff:+.2f}")

    # L30 validation of top performers
    print("\n" + "=" * 70)
    print("L30 VALIDATION OF TOP 5 NEW STRATEGIES")
    print("-" * 70)

    for name, _ in results[:5]:
        r = evaluate_strategy(data, l30_start, l30_end, name)
        if r:
            print(f"{name:<20} L30: avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}")

    # Compare with S6 on L30
    s6_l30 = evaluate_strategy(data, l30_start, l30_end, "S6_E3")
    if s6_l30:
        print(f"\n{'S6_E3 (current)':<20} L30: avg={s6_l30['avg']:.2f}, 11+={s6_l30['at_11']}, 12+={s6_l30['at_12']}")


if __name__ == "__main__":
    main()
