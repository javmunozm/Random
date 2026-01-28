#!/usr/bin/env python3
"""
Test Gemini-Suggested Improvements (2026-01-28)
================================================

Tests 4 strategies identified by Gemini analysis:
1. SymDiff(E4, E7) - Use best event in symmetric difference
2. Weighted Quint - Weight events by historical performance
3. E5 Quint - Replace E2 with unused E5 in consensus
4. Winner's Echo - Dynamic set based on previous series winner

Compare against current 7-set baseline:
- Average: 10.61/14
- 12+ hits: 16
- 13+ hits: 3
"""

import json
from pathlib import Path
from collections import Counter

# Load data
DATA_PATH = Path(__file__).parent.parent / "data" / "full_series_data.json"
data = json.loads(DATA_PATH.read_text())

TOTAL = 25
PICK = 14
START = 2981
END = 3180


def get_global_freq():
    """Get global number frequency."""
    freq = Counter(n for events in data.values() for e in events for n in e)
    return freq


FREQ = get_global_freq()


def predict_baseline(series_id):
    """Current 7-set strategy (baseline)."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e2 = set(data[prior][1])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    # E1 ranked
    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -FREQ[n], n))

    # E3&E7 fusion
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -FREQ[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # S6: SymDiff E3 XOR E7
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -FREQ.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # S7: Quint E2E3E4E6E7
    quint_events = [e2, e3, e4, e6, e7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -FREQ.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    return [
        sorted(e4),                              # S1: E4 direct
        sorted(ranked[:13] + [ranked[15]]),      # S2: rank16
        sorted(e6),                              # S3: E6 direct
        sorted(e7),                              # S4: E7 direct
        sorted(s5_numbers),                      # S5: E3&E7 fusion
        s6_numbers,                              # S6: SymDiff E3⊕E7
        s7_numbers,                              # S7: Quint E2E3E4E6E7
    ]


def predict_symdiff_e4e7(series_id):
    """Test 1: Replace S6 with SymDiff(E4, E7)."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e2 = set(data[prior][1])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -FREQ[n], n))

    # E3&E7 fusion
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -FREQ[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # NEW: SymDiff E4 XOR E7 (instead of E3 XOR E7)
    sym_diff = (e4 | e7) - (e4 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -FREQ.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # Quint E2E3E4E6E7
    quint_events = [e2, e3, e4, e6, e7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -FREQ.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    return [
        sorted(e4),
        sorted(ranked[:13] + [ranked[15]]),
        sorted(e6),
        sorted(e7),
        sorted(s5_numbers),
        s6_numbers,  # Changed
        s7_numbers,
    ]


def predict_weighted_quint(series_id):
    """Test 2: Weighted Quint consensus."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e2 = set(data[prior][1])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -FREQ[n], n))

    # E3&E7 fusion
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -FREQ[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # SymDiff E3 XOR E7
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -FREQ.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # NEW: Weighted Quint (E4=1.5, E6=1.2, E7=1.1, E3=1.0, E2=0.8)
    weights = {
        'e4': 1.5,
        'e6': 1.2,
        'e7': 1.1,
        'e3': 1.0,
        'e2': 0.8,
    }
    number_counts = Counter()
    for n in e4:
        number_counts[n] += weights['e4']
    for n in e6:
        number_counts[n] += weights['e6']
    for n in e7:
        number_counts[n] += weights['e7']
    for n in e3:
        number_counts[n] += weights['e3']
    for n in e2:
        number_counts[n] += weights['e2']

    quint_ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -FREQ.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    return [
        sorted(e4),
        sorted(ranked[:13] + [ranked[15]]),
        sorted(e6),
        sorted(e7),
        sorted(s5_numbers),
        s6_numbers,
        s7_numbers,  # Changed
    ]


def predict_e5_quint(series_id):
    """Test 3: Replace E2 with E5 in Quint."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e5 = set(data[prior][4])  # E5 now used
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -FREQ[n], n))

    # E3&E7 fusion
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -FREQ[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # SymDiff E3 XOR E7
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -FREQ.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # NEW: Quint E3E4E5E6E7 (replace E2 with E5)
    quint_events = [e3, e4, e5, e6, e7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -FREQ.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    return [
        sorted(e4),
        sorted(ranked[:13] + [ranked[15]]),
        sorted(e6),
        sorted(e7),
        sorted(s5_numbers),
        s6_numbers,
        s7_numbers,  # Changed
    ]


def evaluate(series_id, sets):
    """Evaluate prediction sets against actual results."""
    sid = str(series_id)
    if sid not in data:
        return None

    events = data[sid]
    set_bests = []
    for s in sets:
        matches = [len(set(s) & set(e)) for e in events]
        set_bests.append(max(matches))

    return max(set_bests)


def run_test(name, predict_func):
    """Run full backtest for a prediction function."""
    bests = []
    for sid in range(START, END + 1):
        sets = predict_func(sid)
        if sets:
            best = evaluate(sid, sets)
            if best:
                bests.append(best)

    n = len(bests)
    avg = sum(bests) / n
    at_11 = sum(1 for b in bests if b >= 11)
    at_12 = sum(1 for b in bests if b >= 12)
    at_13 = sum(1 for b in bests if b >= 13)

    return {
        "name": name,
        "tested": n,
        "avg": avg,
        "at_11": at_11,
        "at_12": at_12,
        "at_13": at_13,
    }


def main():
    print("=" * 70)
    print("GEMINI IMPROVEMENT TEST (2026-01-28)")
    print("=" * 70)
    print(f"Testing on series {START}-{END} ({END - START + 1} series)")
    print()

    tests = [
        ("Baseline (current 7-set)", predict_baseline),
        ("Test 1: SymDiff(E4,E7)", predict_symdiff_e4e7),
        ("Test 2: Weighted Quint", predict_weighted_quint),
        ("Test 3: E5 Quint", predict_e5_quint),
    ]

    results = []
    for name, func in tests:
        result = run_test(name, func)
        results.append(result)
        print(f"{name}")
        print(f"  Average: {result['avg']:.2f}/14")
        print(f"  11+: {result['at_11']}, 12+: {result['at_12']}, 13+: {result['at_13']}")
        print()

    # Summary comparison
    print("=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print(f"{'Strategy':<30} {'Avg':>8} {'11+':>6} {'12+':>6} {'13+':>6}")
    print("-" * 70)

    baseline = results[0]
    for r in results:
        avg_diff = r['avg'] - baseline['avg']
        d12_diff = r['at_12'] - baseline['at_12']
        d13_diff = r['at_13'] - baseline['at_13']

        diff_str = f"({avg_diff:+.2f})" if r != baseline else ""
        d12_str = f"({d12_diff:+d})" if r != baseline and d12_diff != 0 else ""
        d13_str = f"({d13_diff:+d})" if r != baseline and d13_diff != 0 else ""

        print(f"{r['name']:<30} {r['avg']:>6.2f} {diff_str:>8} "
              f"{r['at_11']:>6} {r['at_12']:>4} {d12_str:>5} "
              f"{r['at_13']:>4} {d13_str:>5}")

    print()
    print("RECOMMENDATION:")

    # Find best by 13+ then 12+ then avg
    best = max(results[1:], key=lambda r: (r['at_13'], r['at_12'], r['avg']))
    if best['at_13'] > baseline['at_13'] or best['at_12'] > baseline['at_12']:
        print(f"  POTENTIAL IMPROVEMENT: {best['name']}")
        print(f"  12+ delta: {best['at_12'] - baseline['at_12']:+d}")
        print(f"  13+ delta: {best['at_13'] - baseline['at_13']:+d}")
    else:
        print("  No improvement over baseline. Current 7-set strategy is optimal.")


if __name__ == "__main__":
    main()
