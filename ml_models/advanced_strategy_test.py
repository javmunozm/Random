#!/usr/bin/env python3
"""
Advanced Strategy Test
======================
Testing Gemini's 5 new untested strategy ideas:
1. Quintuple-Event Fusion (5 events)
2. Recency-Weighted Event Construction
3. Conditional Overlap Strategy
4. Symmetric Difference Fusion
5. Performance-Weighted Hybrid Score
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
    """Three-event fusion."""
    in_all_3 = e1 & e2 & e3
    in_2 = ((e1 & e2) | (e1 & e3) | (e2 & e3)) - in_all_3
    in_1 = (e1 | e2 | e3) - in_all_3 - in_2

    result = list(in_all_3)
    result += sorted(in_2, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    if len(result) < 14:
        result += sorted(in_1, key=lambda n: -freq.get(n, 0))[:14 - len(result)]
    return sorted(result[:14])


def generate_quint_fusion(e1, e2, e3, e4, e5, freq):
    """Five-event fusion - prioritize numbers in most events."""
    all_events = [e1, e2, e3, e4, e5]

    # Count how many events each number appears in
    number_counts = Counter()
    for e in all_events:
        for n in e:
            number_counts[n] += 1

    # Sort by count (most events first), then by frequency
    ranked = sorted(range(1, 26),
                   key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


def generate_recency_event(data, series_id, event_idx, lookback=3, decay=0.5):
    """Create composite event from weighted average of last N series."""
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


def generate_conditional_overlap(events, freq):
    """Conditional strategy based on E1-E4 overlap."""
    e1, e4 = events[0], events[3]
    overlap = len(e1 & e4)

    if overlap >= 10:
        # High consensus - use E1&E4 fusion
        return generate_fusion(e1, e4, freq)
    else:
        # Coverage play - numbers NOT in E1 or E4
        union = e1 | e4
        outside = [n for n in range(1, 26) if n not in union]
        if len(outside) >= 14:
            return sorted(sorted(outside, key=lambda n: -freq.get(n, 0))[:14])
        else:
            # Fill with most frequent from union
            result = outside + sorted(union, key=lambda n: -freq.get(n, 0))[:14 - len(outside)]
            return sorted(result[:14])


def generate_symmetric_diff(e1, e2, freq):
    """Symmetric difference - prioritize disagreement."""
    sym_diff = (e1 | e2) - (e1 & e2)  # Numbers in one but not both
    intersection = e1 & e2

    if len(sym_diff) >= 14:
        return sorted(sorted(sym_diff, key=lambda n: -freq.get(n, 0))[:14])
    else:
        # Fill with intersection
        result = list(sym_diff) + sorted(intersection, key=lambda n: -freq.get(n, 0))[:14 - len(sym_diff)]
        return sorted(result[:14])


def generate_performance_weighted(data, series_id, events, freq, lookback=5):
    """Performance-weighted hybrid - feedback from own predictions."""
    # Calculate base scores
    tw_freq = Counter()
    series_list = sorted(int(s) for s in data.keys() if int(s) < series_id)
    for i, sid in enumerate(series_list[-50:]):  # Last 50 for time-weighted
        weight = 0.995 ** (len(series_list[-50:]) - 1 - i)
        for e in data[str(sid)]:
            for n in e:
                tw_freq[n] += weight

    # Performance bonus: numbers in sets that scored 12+ recently
    perf_bonus = Counter()
    for offset in range(1, lookback + 1):
        check_sid = series_id - offset
        if str(check_sid) not in data or str(check_sid - 1) not in data:
            continue

        # Recreate prediction for that series
        prior = data[str(check_sid - 1)]
        pred_events = [set(prior[i]) for i in range(7)]
        e3, e4, e6, e7 = pred_events[2], pred_events[3], pred_events[5], pred_events[6]

        # Simplified prediction sets
        pred_sets = [sorted(e4), sorted(e6), sorted(e7)]

        # Check which scored 12+
        actual = data[str(check_sid)]
        for ps in pred_sets:
            best = max(len(set(ps) & set(e)) for e in actual)
            if best >= 12:
                for n in ps:
                    perf_bonus[n] += 2.0

    # Combined score
    max_freq = max(freq.values()) if freq else 1
    max_tw = max(tw_freq.values()) if tw_freq else 1

    combined = {}
    for n in range(1, 26):
        combined[n] = (1.0 * freq.get(n, 0) / max_freq +
                      1.5 * tw_freq.get(n, 0) / max_tw +
                      2.0 * perf_bonus.get(n, 0))

    ranked = sorted(range(1, 26), key=lambda n: (-combined[n], n))
    return sorted(ranked[:14])


def generate_all_advanced(data, series_id):
    """Generate all advanced strategies."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)

    strategies = {}

    # Baseline (current S6)
    strategies["Current_S6_E3"] = sorted(e3)

    # 1. Quintuple-Event Fusions
    strategies["Quint_E1E3E4E6E7"] = generate_quint_fusion(e1, e3, e4, e6, e7, freq)
    strategies["Quint_E2E3E4E6E7"] = generate_quint_fusion(e2, e3, e4, e6, e7, freq)
    strategies["Quint_E1E2E4E6E7"] = generate_quint_fusion(e1, e2, e4, e6, e7, freq)
    strategies["Quint_E3E4E5E6E7"] = generate_quint_fusion(e3, e4, e5, e6, e7, freq)

    # 2. Recency-Weighted Events
    re1 = generate_recency_event(data, series_id, 0, lookback=3)
    re3 = generate_recency_event(data, series_id, 2, lookback=3)
    re4 = generate_recency_event(data, series_id, 3, lookback=3)
    re6 = generate_recency_event(data, series_id, 5, lookback=3)
    re7 = generate_recency_event(data, series_id, 6, lookback=3)

    strategies["Recency_E4"] = sorted(re4)
    strategies["Recency_E6"] = sorted(re6)
    strategies["Recency_E7"] = sorted(re7)
    strategies["Recency_Triple_E4E6E7"] = generate_triple_fusion(re4, re6, re7, freq)

    # 3. Conditional Overlap
    strategies["Conditional_E1E4"] = generate_conditional_overlap(events, freq)

    # Conditional with E4-E6
    e4_e6_overlap = len(e4 & e6)
    if e4_e6_overlap >= 10:
        strategies["Conditional_E4E6"] = generate_fusion(e4, e6, freq)
    else:
        outside = [n for n in range(1, 26) if n not in (e4 | e6)]
        if len(outside) >= 14:
            strategies["Conditional_E4E6"] = sorted(sorted(outside, key=lambda n: -freq.get(n, 0))[:14])
        else:
            result = outside + sorted(e4 | e6, key=lambda n: -freq.get(n, 0))[:14 - len(outside)]
            strategies["Conditional_E4E6"] = sorted(result[:14])

    # 4. Symmetric Difference Fusions
    strategies["SymDiff_E3E7"] = generate_symmetric_diff(e3, e7, freq)
    strategies["SymDiff_E4E6"] = generate_symmetric_diff(e4, e6, freq)
    strategies["SymDiff_E6E7"] = generate_symmetric_diff(e6, e7, freq)
    strategies["SymDiff_E4E7"] = generate_symmetric_diff(e4, e7, freq)

    # 5. Performance-Weighted Hybrid
    strategies["PerfWeighted"] = generate_performance_weighted(data, series_id, events, freq)

    return strategies


def evaluate_strategy(data, start, end, strategy_name):
    """Evaluate a single strategy."""
    scores = []

    for sid in range(start, end + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue

        strategies = generate_all_advanced(data, sid)
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

    print("Advanced Strategy Test (Gemini 5 New Ideas)")
    print("=" * 70)
    print(f"Testing on {start}-{end} (200 series)")
    print()

    categories = {
        "BASELINE": ["Current_S6_E3"],
        "1. QUINTUPLE-EVENT FUSIONS": [
            "Quint_E1E3E4E6E7", "Quint_E2E3E4E6E7",
            "Quint_E1E2E4E6E7", "Quint_E3E4E5E6E7"
        ],
        "2. RECENCY-WEIGHTED EVENTS": [
            "Recency_E4", "Recency_E6", "Recency_E7", "Recency_Triple_E4E6E7"
        ],
        "3. CONDITIONAL OVERLAP": ["Conditional_E1E4", "Conditional_E4E6"],
        "4. SYMMETRIC DIFFERENCE": [
            "SymDiff_E3E7", "SymDiff_E4E6", "SymDiff_E6E7", "SymDiff_E4E7"
        ],
        "5. PERFORMANCE-WEIGHTED": ["PerfWeighted"],
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
    print(f"{'Rank':<5} {'Strategy':<25} {'Avg':<8} {'12+':<6} {'11+':<6}")
    print("-" * 70)

    baseline = evaluate_strategy(data, start, end, "Current_S6_E3")
    baseline_avg = baseline['avg'] if baseline else 0

    for i, (name, r, cat) in enumerate(all_results, 1):
        diff = r['avg'] - baseline_avg
        print(f"{i:<5} {name:<25} {r['avg']:.2f}    {r['at_12']:<6} {r['at_11']:<6} ({diff:+.2f})")

    # L30 validation of top 5
    print("\n" + "=" * 70)
    print("L30 VALIDATION (series 3151-3180)")
    print("-" * 70)

    for name, _, _ in all_results[:5]:
        r = evaluate_strategy(data, l30_start, l30_end, name)
        if r:
            print(f"{name:<25} L30: avg={r['avg']:.2f}, 11+={r['at_11']}, 12+={r['at_12']}, best={r['best']}")

    # Compare with baseline
    r_base_l30 = evaluate_strategy(data, l30_start, l30_end, "Current_S6_E3")
    if r_base_l30:
        print(f"\n{'Current_S6_E3 (baseline)':<25} L30: avg={r_base_l30['avg']:.2f}, 11+={r_base_l30['at_11']}, 12+={r_base_l30['at_12']}")


if __name__ == "__main__":
    main()
