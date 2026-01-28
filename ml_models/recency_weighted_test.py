#!/usr/bin/env python3
"""
Recency-Weighted Predictor Test (2026-01-28)
=============================================

Tests whether weighting recent draws more heavily improves predictions.

Weighting schemes tested:
1. Baseline: All series weighted equally
2. Linear decay: Recent series get higher weight
3. Exponential decay: Strong recency bias
4. Window-based: Only use last N series for frequency
5. Tiered: 2x for L30, 1.5x for L60, 1x for rest

Compare against current 7-set baseline:
- Average: 10.61/14
- 12+ hits: 16
- 13+ hits: 3
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


def get_weighted_freq(current_series, scheme="uniform"):
    """
    Get frequency counter with different weighting schemes.

    Schemes:
    - uniform: All series equal weight (current baseline)
    - linear: Weight = (series - min_series) / range
    - exponential: Weight = exp(-decay * age)
    - window_30: Only use last 30 series
    - window_50: Only use last 50 series
    - tiered: 2x for L30, 1.5x for L60, 1x for rest
    """
    freq = Counter()

    all_series = sorted(int(s) for s in data.keys())
    min_series = min(all_series)
    max_series = current_series - 1  # Don't include current
    range_series = max_series - min_series if max_series > min_series else 1

    for sid_str, events in data.items():
        sid = int(sid_str)
        if sid >= current_series:
            continue  # Don't use future data

        age = max_series - sid  # How old is this series

        if scheme == "uniform":
            weight = 1.0
        elif scheme == "linear":
            # More recent = higher weight (0.1 to 1.0)
            weight = 0.1 + 0.9 * (sid - min_series) / range_series
        elif scheme == "exponential":
            # Exponential decay with age
            decay = 0.02  # Tune this
            weight = math.exp(-decay * age)
        elif scheme == "window_30":
            # Only use last 30 series
            if age > 30:
                continue
            weight = 1.0
        elif scheme == "window_50":
            # Only use last 50 series
            if age > 50:
                continue
            weight = 1.0
        elif scheme == "tiered":
            # 2x for L30, 1.5x for L60, 1x for rest
            if age <= 30:
                weight = 2.0
            elif age <= 60:
                weight = 1.5
            else:
                weight = 1.0
        elif scheme == "strong_recency":
            # Very strong recency: 3x for L10, 2x for L30, 1x for rest
            if age <= 10:
                weight = 3.0
            elif age <= 30:
                weight = 2.0
            else:
                weight = 1.0
        else:
            weight = 1.0

        for event in events:
            for n in event:
                freq[n] += weight

    return freq


def predict_with_scheme(series_id, scheme="uniform"):
    """Generate 7-set prediction with specified weighting scheme."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e2 = set(data[prior][1])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    # Get weighted frequency
    freq = get_weighted_freq(series_id, scheme)
    max_freq = max(freq.values()) if freq else 1

    # E1 ranked with weighted frequency
    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq.get(n, 0)/max_freq, n))

    # E3&E7 fusion
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq.get(n, 0))
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
        sorted(e4),                              # S1: E4 direct
        sorted(ranked[:13] + [ranked[15]]),      # S2: rank16
        sorted(e6),                              # S3: E6 direct
        sorted(e7),                              # S4: E7 direct
        sorted(s5_numbers),                      # S5: E3&E7 fusion
        s6_numbers,                              # S6: SymDiff E3⊕E7
        s7_numbers,                              # S7: Quint E2E3E4E6E7
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


def run_test(name, scheme):
    """Run full backtest for a weighting scheme."""
    bests = []
    for sid in range(START, END + 1):
        sets = predict_with_scheme(sid, scheme)
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
        "scheme": scheme,
        "tested": n,
        "avg": avg,
        "at_11": at_11,
        "at_12": at_12,
        "at_13": at_13,
    }


def main():
    print("=" * 70)
    print("RECENCY-WEIGHTED PREDICTOR TEST (2026-01-28)")
    print("=" * 70)
    print(f"Testing on series {START}-{END} ({END - START + 1} series)")
    print()
    print("Testing whether weighting recent draws improves predictions...")
    print()

    schemes = [
        ("Baseline (uniform)", "uniform"),
        ("Linear decay", "linear"),
        ("Exponential decay", "exponential"),
        ("Window L30 only", "window_30"),
        ("Window L50 only", "window_50"),
        ("Tiered (2x L30, 1.5x L60)", "tiered"),
        ("Strong recency (3x L10, 2x L30)", "strong_recency"),
    ]

    results = []
    for name, scheme in schemes:
        print(f"Testing: {name}...", end=" ", flush=True)
        result = run_test(name, scheme)
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

        # Format differences
        avg_str = f"({avg_diff:+.2f})" if r != baseline else ""
        d12_str = f"({d12_diff:+d})" if r != baseline and d12_diff != 0 else ""
        d13_str = f"({d13_diff:+d})" if r != baseline and d13_diff != 0 else ""

        print(f"{r['name']:<35} {r['avg']:>6.2f} {avg_str:>8} "
              f"{r['at_11']:>6} {r['at_12']:>4} {d12_str:>5} "
              f"{r['at_13']:>4} {d13_str:>5}")

    print()

    # Find best by 13+ then 12+ then avg
    best = max(results, key=lambda r: (r['at_13'], r['at_12'], r['avg']))

    print("ANALYSIS:")
    print("-" * 70)

    # Check if any scheme beats baseline
    improvements = [r for r in results[1:] if r['at_13'] > baseline['at_13'] or
                   (r['at_13'] == baseline['at_13'] and r['at_12'] > baseline['at_12'])]

    if improvements:
        best_imp = max(improvements, key=lambda r: (r['at_13'], r['at_12'], r['avg']))
        print(f"POTENTIAL IMPROVEMENT FOUND: {best_imp['name']}")
        print(f"  12+ delta: {best_imp['at_12'] - baseline['at_12']:+d}")
        print(f"  13+ delta: {best_imp['at_13'] - baseline['at_13']:+d}")
        print(f"  Avg delta: {best_imp['avg'] - baseline['avg']:+.3f}")
    else:
        print("No recency scheme improves over baseline.")
        print("This confirms: historical frequency is equally useful as recent frequency.")
        print("The data has no exploitable recency pattern.")

    print()
    print("RECOMMENDATION:")
    if best == baseline:
        print("  Keep current uniform weighting. Recency doesn't help.")
    else:
        print(f"  Consider: {best['name']} (but validate on new data first)")


if __name__ == "__main__":
    main()
