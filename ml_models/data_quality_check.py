#!/usr/bin/env python3
"""
Data Quality Validation (P2 Task)
=================================
Ensure dataset integrity before new experiments.
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


def validate_data(data):
    """Run comprehensive data quality checks."""
    issues = []
    warnings = []

    print("=" * 70)
    print("P2: DATA QUALITY VALIDATION")
    print("=" * 70)
    print()

    # 1. Basic structure checks
    print("1. STRUCTURE CHECKS")
    print("-" * 40)

    series_ids = sorted(int(s) for s in data.keys())
    print(f"   Total series: {len(series_ids)}")
    print(f"   Range: {min(series_ids)} - {max(series_ids)}")

    # Check for gaps
    expected = set(range(min(series_ids), max(series_ids) + 1))
    actual = set(series_ids)
    gaps = expected - actual
    if gaps:
        issues.append(f"Missing series: {sorted(gaps)}")
        print(f"   [ERROR] Missing series: {sorted(gaps)}")
    else:
        print(f"   [OK] No gaps in series sequence")

    # 2. Event structure checks
    print("\n2. EVENT STRUCTURE CHECKS")
    print("-" * 40)

    for sid in series_ids:
        events = data[str(sid)]

        # Check 7 events per series
        if len(events) != 7:
            issues.append(f"Series {sid}: {len(events)} events (expected 7)")

        for i, event in enumerate(events):
            # Check 14 numbers per event
            if len(event) != 14:
                issues.append(f"Series {sid} E{i+1}: {len(event)} numbers (expected 14)")

            # Check number range 1-25
            for n in event:
                if not (1 <= n <= 25):
                    issues.append(f"Series {sid} E{i+1}: invalid number {n}")

            # Check no duplicates within event
            if len(event) != len(set(event)):
                issues.append(f"Series {sid} E{i+1}: duplicate numbers")

    if not any("EVENT STRUCTURE" in str(i) for i in issues):
        print(f"   [OK] All series have 7 events with 14 unique numbers (1-25)")
    else:
        for issue in issues:
            if "E" in issue:
                print(f"   [ERROR] {issue}")

    # 3. Number distribution checks
    print("\n3. NUMBER DISTRIBUTION CHECKS")
    print("-" * 40)

    all_numbers = Counter()
    for sid in series_ids:
        for event in data[str(sid)]:
            for n in event:
                all_numbers[n] += 1

    total_draws = len(series_ids) * 7 * 14
    expected_per_number = total_draws / 25

    print(f"   Total draws: {total_draws}")
    print(f"   Expected per number: {expected_per_number:.1f}")

    # Check for significant deviations (>20% from expected)
    for n in range(1, 26):
        count = all_numbers[n]
        deviation = abs(count - expected_per_number) / expected_per_number
        if deviation > 0.20:
            warnings.append(f"#{n}: {count} occurrences ({deviation*100:.1f}% deviation)")

    if warnings:
        print(f"   [WARN] {len(warnings)} numbers with >20% deviation from expected:")
        for w in warnings[:5]:
            print(f"          {w}")
    else:
        print(f"   [OK] All numbers within normal distribution range")

    # Most/least frequent
    most = all_numbers.most_common(5)
    least = all_numbers.most_common()[-5:]
    print(f"\n   Most frequent:  {[(n, c) for n, c in most]}")
    print(f"   Least frequent: {[(n, c) for n, c in least]}")

    # 4. Duplicate event checks
    print("\n4. DUPLICATE EVENT CHECKS")
    print("-" * 40)

    all_events = []
    for sid in series_ids:
        for i, event in enumerate(data[str(sid)]):
            all_events.append((sid, i+1, tuple(sorted(event))))

    event_tuples = [e[2] for e in all_events]
    event_counts = Counter(event_tuples)
    duplicates = [(e, c) for e, c in event_counts.items() if c > 1]

    if duplicates:
        print(f"   [INFO] {len(duplicates)} event combinations appear multiple times")
        for event, count in duplicates[:3]:
            occurrences = [(s, e) for s, e, ev in all_events if ev == event]
            print(f"          {list(event)[:5]}... appears {count}x")
    else:
        print(f"   [OK] No duplicate events found")

    # 5. Temporal consistency
    print("\n5. TEMPORAL CONSISTENCY")
    print("-" * 40)

    # Check event-to-event overlap within series
    overlaps = []
    for sid in series_ids[:50]:  # Sample first 50
        events = [set(e) for e in data[str(sid)]]
        for i in range(6):
            overlap = len(events[i] & events[i+1])
            overlaps.append(overlap)

    avg_overlap = sum(overlaps) / len(overlaps)
    print(f"   Avg event-to-event overlap (within series): {avg_overlap:.2f}/14")

    # Check series-to-series overlap
    series_overlaps = []
    for i in range(len(series_ids) - 1):
        s1 = set(n for e in data[str(series_ids[i])] for n in e)
        s2 = set(n for e in data[str(series_ids[i+1])] for n in e)
        # Both should have ~25 unique numbers
        series_overlaps.append(len(s1 & s2))

    print(f"   Avg series-to-series number overlap: {sum(series_overlaps)/len(series_overlaps):.1f}/25")

    # 6. Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if issues:
        print(f"\n[ERRORS] {len(issues)} critical issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"\n[OK] No critical issues found")

    if warnings:
        print(f"\n[WARNINGS] {len(warnings)} warnings:")
        for w in warnings[:5]:
            print(f"   - {w}")
    else:
        print(f"\n[OK] No warnings")

    return len(issues) == 0


if __name__ == "__main__":
    data = load_data()
    is_valid = validate_data(data)
    print(f"\nData quality: {'PASS' if is_valid else 'FAIL'}")
