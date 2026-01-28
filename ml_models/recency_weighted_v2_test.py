#!/usr/bin/env python3
"""
Recency-Weighted Predictor Test v2 (2026-01-28)
================================================

Tests recency weighting using SAME methodology as production predictor.
Production uses global frequency (all data) for tiebreaking.
This test compares uniform vs recency-weighted tiebreaking.

Key insight: The frequency is only used for TIEBREAKING, not primary selection.
Direct event copies (E4, E6, E7) are unaffected by frequency weighting.
Only affects: rank16 ordering, fusion fills, SymDiff fills, Quint tiebreaks.
"""

import json
from pathlib import Path
from collections import Counter
import math

# Load data
DATA_PATH = Path(__file__).parent.parent / "data" / "full_series_data.json"
data = json.loads(DATA_PATH.read_text())

TOTAL = 25
PICK = 14
START = 2981
END = 3180


def get_global_freq():
    """Get global frequency (matches production predictor)."""
    freq = Counter(n for events in data.values() for e in events for n in e)
    return freq


def get_recency_freq(current_series, scheme="strong"):
    """Get recency-weighted frequency."""
    freq = Counter()

    for sid_str, events in data.items():
        sid = int(sid_str)
        age = current_series - 1 - sid  # How old relative to prior series

        if scheme == "strong":
            # 3x for L10, 2x for L30, 1x for rest
            if age < 0:
                weight = 1.0  # Future data gets normal weight (matches prod)
            elif age <= 10:
                weight = 3.0
            elif age <= 30:
                weight = 2.0
            else:
                weight = 1.0
        elif scheme == "moderate":
            # 2x for L30, 1.5x for L60, 1x for rest
            if age < 0:
                weight = 1.0
            elif age <= 30:
                weight = 2.0
            elif age <= 60:
                weight = 1.5
            else:
                weight = 1.0
        elif scheme == "mild":
            # 1.5x for L30, 1x for rest
            if age < 0:
                weight = 1.0
            elif age <= 30:
                weight = 1.5
            else:
                weight = 1.0
        else:
            weight = 1.0

        for event in events:
            for n in event:
                freq[n] += weight

    return freq


# Global frequency (production baseline)
GLOBAL_FREQ = get_global_freq()


def predict_baseline(series_id):
    """Production predictor baseline (uses global freq)."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e2 = set(data[prior][1])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    freq = GLOBAL_FREQ
    max_freq = max(freq.values())

    # E1 ranked
    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq[n]/max_freq, n))

    # E3&E7 fusion
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # S6: SymDiff E3 XOR E7
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # S7: Quint E2E3E4E6E7
    quint_events = [e2, e3, e4, e6, e7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    return [
        sorted(e4),
        sorted(ranked[:13] + [ranked[15]]),
        sorted(e6),
        sorted(e7),
        sorted(s5_numbers),
        s6_numbers,
        s7_numbers,
    ]


def predict_recency(series_id, scheme="strong"):
    """Recency-weighted predictor."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e2 = set(data[prior][1])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    # Use recency-weighted frequency
    freq = get_recency_freq(series_id, scheme)
    max_freq = max(freq.values()) if freq else 1

    # E1 ranked with recency
    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq.get(n, 0)/max_freq, n))

    # E3&E7 fusion with recency
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq.get(n, 0))
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # S6: SymDiff with recency fill
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # S7: Quint with recency tiebreak
    quint_events = [e2, e3, e4, e6, e7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26), key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    return [
        sorted(e4),
        sorted(ranked[:13] + [ranked[15]]),
        sorted(e6),
        sorted(e7),
        sorted(s5_numbers),
        s6_numbers,
        s7_numbers,
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


def run_test(name, predict_func, scheme=None):
    """Run full backtest."""
    bests = []
    for sid in range(START, END + 1):
        if scheme:
            sets = predict_func(sid, scheme)
        else:
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
    print("RECENCY-WEIGHTED PREDICTOR TEST v2 (2026-01-28)")
    print("=" * 70)
    print(f"Testing on series {START}-{END} ({END - START + 1} series)")
    print()
    print("Uses same methodology as production predictor (global freq baseline)")
    print("Tests whether recency-weighted tiebreaking improves results")
    print()

    results = []

    # Baseline
    print("Testing: Baseline (global freq)...", end=" ", flush=True)
    result = run_test("Baseline (global freq)", predict_baseline)
    results.append(result)
    print(f"avg={result['avg']:.2f}, 12+={result['at_12']}, 13+={result['at_13']}")

    # Recency schemes
    schemes = [
        ("Mild (1.5x L30)", "mild"),
        ("Moderate (2x L30, 1.5x L60)", "moderate"),
        ("Strong (3x L10, 2x L30)", "strong"),
    ]

    for name, scheme in schemes:
        print(f"Testing: {name}...", end=" ", flush=True)
        result = run_test(name, predict_recency, scheme)
        results.append(result)
        print(f"avg={result['avg']:.2f}, 12+={result['at_12']}, 13+={result['at_13']}")

    print()
    print("=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print(f"{'Scheme':<35} {'Avg':>8} {'11+':>6} {'12+':>6} {'13+':>6}")
    print("-" * 70)

    baseline = results[0]
    for r in results:
        avg_diff = r['avg'] - baseline['avg']
        d12_diff = r['at_12'] - baseline['at_12']
        d13_diff = r['at_13'] - baseline['at_13']

        avg_str = f"({avg_diff:+.2f})" if r != baseline else ""
        d12_str = f"({d12_diff:+d})" if r != baseline and d12_diff != 0 else ""
        d13_str = f"({d13_diff:+d})" if r != baseline and d13_diff != 0 else ""

        print(f"{r['name']:<35} {r['avg']:>6.2f} {avg_str:>8} "
              f"{r['at_11']:>6} {r['at_12']:>4} {d12_str:>5} "
              f"{r['at_13']:>4} {d13_str:>5}")

    print()
    print("ANALYSIS:")
    print("-" * 70)

    # Find best
    best = max(results, key=lambda r: (r['at_13'], r['at_12'], r['avg']))

    if best != baseline:
        print(f"BEST SCHEME: {best['name']}")
        print(f"  12+ delta: {best['at_12'] - baseline['at_12']:+d}")
        print(f"  13+ delta: {best['at_13'] - baseline['at_13']:+d}")
        print(f"  Avg delta: {best['avg'] - baseline['avg']:+.3f}")

        if best['at_13'] > baseline['at_13'] or best['at_12'] > baseline['at_12']:
            print()
            print("RECOMMENDATION: Consider implementing recency weighting")
        else:
            print()
            print("RECOMMENDATION: Improvement is marginal, keep baseline")
    else:
        print("Baseline is still best. Recency weighting doesn't help.")


if __name__ == "__main__":
    main()
