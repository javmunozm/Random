#!/usr/bin/env python3
"""
Near-Miss Analysis (P1 Task)
============================
Analyze the 3 series that hit 13/14 to understand what prevented 14/14.
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


def generate_prediction(data, series_id):
    """Replicate production predictor logic."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    events = [set(data[prior][i]) for i in range(7)]
    e1, e2, e3, e4, e5, e6, e7 = events

    freq = Counter(n for ev in data.values() for e in ev for n in e)
    max_freq = max(freq.values())

    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -freq[n]/max_freq, n))

    # E3&E7 fusion
    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # SymDiff E3⊕E7
    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # Quint E2E3E4E6E7
    quint_events = [e2, e3, e4, e6, e7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26),
                         key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    sets = [
        ("S1 (E4)", sorted(e4)),
        ("S2 (rank16)", sorted(ranked[:13] + [ranked[15]])),
        ("S3 (E6)", sorted(e6)),
        ("S4 (E7)", sorted(e7)),
        ("S5 (E3&E7)", sorted(s5_numbers)),
        ("S6 (SymDiff)", s6_numbers),
        ("S7 (Quint)", s7_numbers),
    ]

    return sets, events


def analyze_near_misses(data, start, end):
    """Find and analyze all 13+ hits."""
    near_misses = []

    for sid in range(start, end + 1):
        if str(sid) not in data or str(sid - 1) not in data:
            continue

        result = generate_prediction(data, sid)
        if not result:
            continue

        sets, prior_events = result
        actual = data[str(sid)]

        for set_name, pred_set in sets:
            pred = set(pred_set)
            for event_idx, event in enumerate(actual):
                actual_set = set(event)
                match = len(pred & actual_set)

                if match >= 13:
                    missing = actual_set - pred
                    extra = pred - actual_set

                    near_misses.append({
                        "series": sid,
                        "set": set_name,
                        "event": f"E{event_idx + 1}",
                        "match": match,
                        "missing": sorted(missing),
                        "extra": sorted(extra),
                        "pred": pred_set,
                        "actual": sorted(actual_set),
                    })

    return near_misses


def main():
    data = load_data()
    start, end = 2981, 3180

    print("=" * 80)
    print("P1: NEAR-MISS ANALYSIS - What's Preventing 14/14?")
    print("=" * 80)
    print()

    near_misses = analyze_near_misses(data, start, end)

    print(f"Found {len(near_misses)} near-misses (13+ matches)")
    print()

    # Group by series
    by_series = {}
    for nm in near_misses:
        sid = nm["series"]
        if sid not in by_series:
            by_series[sid] = []
        by_series[sid].append(nm)

    print("-" * 80)
    print("DETAILED NEAR-MISS BREAKDOWN")
    print("-" * 80)

    missing_numbers = Counter()
    extra_numbers = Counter()
    winning_sets = Counter()
    winning_events = Counter()

    for sid, misses in sorted(by_series.items()):
        print(f"\n{'='*60}")
        print(f"SERIES {sid}")
        print(f"{'='*60}")

        for nm in misses:
            print(f"\n  {nm['set']} matched {nm['event']}: {nm['match']}/14")
            print(f"  Missing: {nm['missing']}")
            print(f"  Extra (wrong): {nm['extra']}")

            for n in nm["missing"]:
                missing_numbers[n] += 1
            for n in nm["extra"]:
                extra_numbers[n] += 1
            winning_sets[nm["set"]] += 1
            winning_events[nm["event"]] += 1

    # Summary statistics
    print("\n" + "=" * 80)
    print("NEAR-MISS STATISTICS")
    print("=" * 80)

    print("\n1. MISSING NUMBERS (what we needed but didn't predict)")
    print("-" * 40)
    for n, count in missing_numbers.most_common(10):
        print(f"   #{n:2d}: missed {count}x")

    print("\n2. EXTRA NUMBERS (what we predicted but shouldn't have)")
    print("-" * 40)
    for n, count in extra_numbers.most_common(10):
        print(f"   #{n:2d}: wrong {count}x")

    print("\n3. WHICH SETS ACHIEVED 13+?")
    print("-" * 40)
    for s, count in winning_sets.most_common():
        print(f"   {s}: {count}x")

    print("\n4. WHICH EVENTS WERE MATCHED?")
    print("-" * 40)
    for e, count in winning_events.most_common():
        print(f"   {e}: {count}x")

    # Actionable insights
    print("\n" + "=" * 80)
    print("ACTIONABLE INSIGHTS")
    print("=" * 80)

    if missing_numbers:
        top_missing = missing_numbers.most_common(3)
        print(f"\n1. TOP MISSING NUMBERS: {[n for n, _ in top_missing]}")
        print("   These numbers appear in 13+ events but we didn't predict them.")
        print("   Consider: Are these in prior events? Are they high-frequency?")

    if extra_numbers:
        top_extra = extra_numbers.most_common(3)
        print(f"\n2. TOP WRONG NUMBERS: {[n for n, _ in top_extra]}")
        print("   We predicted these but they weren't in the actual event.")
        print("   Consider: Should we deprioritize these?")

    # Check if missing numbers were in prior events
    print("\n3. WERE MISSING NUMBERS IN PRIOR SERIES?")
    print("-" * 40)

    for nm in near_misses:
        sid = nm["series"]
        prior = data[str(sid - 1)]
        prior_all = set(n for e in prior for n in e)

        for missing_n in nm["missing"]:
            in_prior = "YES" if missing_n in prior_all else "NO"
            prior_events = [f"E{i+1}" for i, e in enumerate(prior) if missing_n in e]
            print(f"   Series {sid}: #{missing_n} in prior? {in_prior} {prior_events if prior_events else ''}")


if __name__ == "__main__":
    main()
