#!/usr/bin/env python3
"""
Hex Fusion Test
===============
Testing 6-event (hex) fusions for maximum consensus.
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
    """5-event fusion - prioritize numbers in most events."""
    all_events = [e1, e2, e3, e4, e5]
    number_counts = Counter()
    for e in all_events:
        for n in e:
            number_counts[n] += 1
    ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


def generate_hex_fusion(e1, e2, e3, e4, e5, e6, freq):
    """6-event fusion - prioritize numbers in most events."""
    all_events = [e1, e2, e3, e4, e5, e6]
    number_counts = Counter()
    for e in all_events:
        for n in e:
            number_counts[n] += 1
    ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


def generate_sept_fusion(events, freq):
    """7-event fusion - all events."""
    number_counts = Counter()
    for e in events:
        for n in e:
            number_counts[n] += 1
    ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


def generate_all_strategies(data, series_id):
    """Generate all fusion strategies."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)

    strategies = {}

    # Baseline
    strategies["Baseline_E3"] = sorted(e3)

    # Current best quint fusions
    strategies["Quint_E1E3E4E6E7"] = generate_quint_fusion(e1, e3, e4, e6, e7, freq)
    strategies["Quint_E2E3E4E6E7"] = generate_quint_fusion(e2, e3, e4, e6, e7, freq)

    # New quint with E5
    strategies["Quint_E3E4E5E6E7"] = generate_quint_fusion(e3, e4, e5, e6, e7, freq)
    strategies["Quint_E1E2E3E5E7"] = generate_quint_fusion(e1, e2, e3, e5, e7, freq)
    strategies["Quint_E1E3E5E6E7"] = generate_quint_fusion(e1, e3, e5, e6, e7, freq)
    strategies["Quint_E2E4E5E6E7"] = generate_quint_fusion(e2, e4, e5, e6, e7, freq)

    # 6-event (Hex) fusions
    strategies["Hex_E1E2E3E4E6E7"] = generate_hex_fusion(e1, e2, e3, e4, e6, e7, freq)  # Exclude E5
    strategies["Hex_E2E3E4E5E6E7"] = generate_hex_fusion(e2, e3, e4, e5, e6, e7, freq)  # Exclude E1
    strategies["Hex_E1E3E4E5E6E7"] = generate_hex_fusion(e1, e3, e4, e5, e6, e7, freq)  # Exclude E2
    strategies["Hex_E1E2E4E5E6E7"] = generate_hex_fusion(e1, e2, e4, e5, e6, e7, freq)  # Exclude E3
    strategies["Hex_E1E2E3E5E6E7"] = generate_hex_fusion(e1, e2, e3, e5, e6, e7, freq)  # Exclude E4
    strategies["Hex_E1E2E3E4E5E7"] = generate_hex_fusion(e1, e2, e3, e4, e5, e7, freq)  # Exclude E6
    strategies["Hex_E1E2E3E4E5E6"] = generate_hex_fusion(e1, e2, e3, e4, e5, e6, freq)  # Exclude E7

    # 7-event (Sept) fusion - all events
    strategies["Sept_All"] = generate_sept_fusion(events, freq)

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

    print("Hex Fusion Test (5, 6, 7 Event Fusions)")
    print("=" * 70)
    print(f"Testing on {start}-{end} (200 series)")
    print()

    categories = {
        "BASELINE": ["Baseline_E3"],
        "QUINT (5-event) - Previous Best": ["Quint_E1E3E4E6E7", "Quint_E2E3E4E6E7"],
        "QUINT (5-event) - New with E5": ["Quint_E3E4E5E6E7", "Quint_E1E2E3E5E7",
                                           "Quint_E1E3E5E6E7", "Quint_E2E4E5E6E7"],
        "HEX (6-event)": ["Hex_E1E2E3E4E6E7", "Hex_E2E3E4E5E6E7", "Hex_E1E3E4E5E6E7",
                          "Hex_E1E2E4E5E6E7", "Hex_E1E2E3E5E6E7", "Hex_E1E2E3E4E5E7", "Hex_E1E2E3E4E5E6"],
        "SEPT (7-event)": ["Sept_All"],
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
    print("OVERALL RANKING (by 12+, then 11+, then avg)")
    print("-" * 70)
    print(f"{'Rank':<5} {'Strategy':<25} {'Avg':<8} {'12+':<6} {'11+':<6} {'13+':<6}")
    print("-" * 70)

    for i, (name, r, _) in enumerate(all_results[:15], 1):
        print(f"{i:<5} {name:<25} {r['avg']:.2f}    {r['at_12']:<6} {r['at_11']:<6} {r['at_13']:<6}")

    # L30 validation of top 5
    print("\n" + "=" * 70)
    print("L30 VALIDATION (series 3151-3180)")
    print("-" * 70)

    for name, _, _ in all_results[:6]:
        r = evaluate_strategy(data, l30_start, l30_end, name)
        if r:
            print(f"{name:<25} L30: avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, best={r['best']}")


if __name__ == "__main__":
    main()
