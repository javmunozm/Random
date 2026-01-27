#!/usr/bin/env python3
"""
Event Fusion Opportunities (P3 Task)
====================================
Explore new event combinations with E2, E4, E5 (underutilized).
Based on P1 finding: #16 was in E5 both times it was missed.
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


def generate_all_strategies(data, series_id):
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)

    strategies = {}

    # Current S6 and S7 (baseline)
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    strategies["Current_S6_SymDiff"] = sorted(s6_numbers[:14])
    strategies["Current_S7_Quint_noE5"] = generate_quint_fusion([e2, e3, e4, e6, e7], freq)

    # E5-inclusive strategies (based on P1 finding)
    strategies["Quint_withE5"] = generate_quint_fusion([e3, e4, e5, e6, e7], freq)
    strategies["Quint_E1E3E5E6E7"] = generate_quint_fusion([e1, e3, e5, e6, e7], freq)
    strategies["Quint_E2E3E5E6E7"] = generate_quint_fusion([e2, e3, e5, e6, e7], freq)

    # E5 direct and fusions
    strategies["E5_direct"] = sorted(e5)
    strategies["E5_E6_fusion"] = generate_fusion(e5, e6, freq)
    strategies["E5_E7_fusion"] = generate_fusion(e5, e7, freq)
    strategies["Triple_E3E5E7"] = generate_triple_fusion(e3, e5, e7, freq)
    strategies["Triple_E4E5E6"] = generate_triple_fusion(e4, e5, e6, freq)

    # E2 strategies
    strategies["E2_direct"] = sorted(e2)
    strategies["E2_E4_fusion"] = generate_fusion(e2, e4, freq)
    strategies["E2_E6_fusion"] = generate_fusion(e2, e6, freq)
    strategies["Triple_E2E4E6"] = generate_triple_fusion(e2, e4, e6, freq)

    # SymDiff variants including E5
    sym_diff_e5e7 = (e5 | e7) - (e5 & e7)
    s_e5e7 = list(sym_diff_e5e7)
    if len(s_e5e7) < 14:
        remaining = [n for n in range(1, 26) if n not in s_e5e7]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s_e5e7 += remaining[:14 - len(s_e5e7)]
    strategies["SymDiff_E5E7"] = sorted(s_e5e7[:14])

    return strategies


def evaluate_strategy(data, start, end, strategy_name):
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
        "at_11": sum(1 for s in scores if s >= 11),
        "at_12": sum(1 for s in scores if s >= 12),
        "at_13": sum(1 for s in scores if s >= 13),
    }


def main():
    data = load_data()
    start, end = 2981, 3180
    l30_start, l30_end = 3151, 3180

    print("=" * 75)
    print("P3: EVENT FUSION OPPORTUNITIES (E2, E4, E5 Underutilized)")
    print("=" * 75)
    print()
    print("Based on P1 finding: #16 was in E5 both times it was missed for 14/14")
    print()

    # Get strategy names
    sample = generate_all_strategies(data, 3100)

    categories = {
        "CURRENT (BASELINE)": ["Current_S6_SymDiff", "Current_S7_Quint_noE5"],
        "E5-INCLUSIVE QUINTS": ["Quint_withE5", "Quint_E1E3E5E6E7", "Quint_E2E3E5E6E7"],
        "E5 DIRECT & FUSIONS": ["E5_direct", "E5_E6_fusion", "E5_E7_fusion",
                                "Triple_E3E5E7", "Triple_E4E5E6"],
        "E2 STRATEGIES": ["E2_direct", "E2_E4_fusion", "E2_E6_fusion", "Triple_E2E4E6"],
        "SYMDIFF WITH E5": ["SymDiff_E5E7"],
    }

    all_results = []

    for category, strategies in categories.items():
        print(f"\n{category}")
        print("-" * 75)
        print(f"{'Strategy':<25} {'Avg':<8} {'Best':<6} {'11+':<6} {'12+':<6} {'13+':<6}")
        print("-" * 75)

        for name in strategies:
            r = evaluate_strategy(data, start, end, name)
            if r:
                all_results.append((name, r, category))
                print(f"{name:<25} {r['avg']:.2f}    {r['best']:<6} {r['at_11']:<6} {r['at_12']:<6} {r['at_13']:<6}")

    # Ranking
    all_results.sort(key=lambda x: (-x[1]['at_12'], -x[1]['at_13'], -x[1]['avg']))

    print("\n" + "=" * 75)
    print("RANKING (by 12+, then 13+, then avg)")
    print("-" * 75)
    print(f"{'Rank':<5} {'Strategy':<25} {'Avg':<8} {'12+':<6} {'13+':<6}")
    print("-" * 75)

    baseline = evaluate_strategy(data, start, end, "Current_S7_Quint_noE5")

    for i, (name, r, cat) in enumerate(all_results[:10], 1):
        diff = r['avg'] - baseline['avg']
        marker = " <-- CURRENT" if "Current" in name else ""
        print(f"{i:<5} {name:<25} {r['avg']:.2f}    {r['at_12']:<6} {r['at_13']:<6} {marker}")

    # L30 validation of top E5-inclusive strategies
    print("\n" + "=" * 75)
    print("L30 VALIDATION OF E5-INCLUSIVE STRATEGIES")
    print("-" * 75)

    e5_strategies = ["Current_S7_Quint_noE5", "Quint_withE5", "Triple_E3E5E7", "SymDiff_E5E7"]
    for name in e5_strategies:
        r = evaluate_strategy(data, l30_start, l30_end, name)
        if r:
            print(f"{name:<25} L30: avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}")

    # Would E5 have captured #16?
    print("\n" + "=" * 75)
    print("WOULD E5 STRATEGIES HAVE CAPTURED THE MISSING #16?")
    print("-" * 75)

    for sid in [3061, 3098]:  # Series where #16 was missed
        prior = data[str(sid - 1)]
        e5 = set(prior[4])
        print(f"   Series {sid}: #16 in prior E5? {'YES' if 16 in e5 else 'NO'}")

        if 16 in e5:
            # Check if E5-inclusive strategies would have had #16
            strategies = generate_all_strategies(data, sid)
            for strat in ["Quint_withE5", "Triple_E3E5E7", "E5_E7_fusion"]:
                if strat in strategies:
                    has_16 = 16 in strategies[strat]
                    print(f"      {strat}: #16 included? {'YES' if has_16 else 'NO'}")

    # Recommendation
    print("\n" + "=" * 75)
    print("RECOMMENDATION")
    print("=" * 75)

    best_e5 = None
    for name, r, cat in all_results:
        if "E5" in name or "withE5" in name:
            best_e5 = (name, r)
            break

    if best_e5:
        print(f"\nBest E5-inclusive strategy: {best_e5[0]}")
        print(f"   12+ hits: {best_e5[1]['at_12']} (vs current {baseline['at_12']})")
        print(f"   13+ hits: {best_e5[1]['at_13']} (vs current {baseline['at_13']})")
        print(f"   Average: {best_e5[1]['avg']:.2f} (vs current {baseline['avg']:.2f})")


if __name__ == "__main__":
    main()
