#!/usr/bin/env python3
"""
E3 and E7 Breakthrough Analysis
===============================

Analyze the specific 12+ events for E3 and E7:
- E3: 12/14 in Series 2998 (matched E7), 12/14 in Series 3134 (matched E4)
- E7: 12/14 in Series 3004 (matched E3), 12/14 in Series 3072 (matched E5)

Questions:
1. What were the prior series event numbers (prediction)?
2. What were the actual winning numbers?
3. Exact match breakdown
4. What 2 numbers were missing?
5. Do E3/E7 hits overlap with E1/E6 hits?
6. Would adding S11 (E3) and S12 (E7) increase ceiling or just diversify?
"""

import json
from pathlib import Path
from collections import Counter


def load_data():
    """Load data from JSON."""
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def analyze_12plus_event(data, series_id, event_idx, event_name, matched_event_name):
    """Analyze a specific 12+ event in detail."""
    prior = str(series_id - 1)
    current = str(series_id)

    print(f"\n{'='*70}")
    print(f"Series {series_id}: {event_name} hit 12/14 (matched {matched_event_name})")
    print(f"{'='*70}")

    # Prior event (what was used for prediction)
    prior_event = set(data[prior][event_idx])
    print(f"\nPrior Series {series_id - 1} {event_name}: {sorted(prior_event)}")

    # Find which event gave 12/14
    current_events = data[current]
    best_match = 0
    best_event_idx = -1

    for i, event in enumerate(current_events):
        matches = len(prior_event & set(event))
        if matches > best_match:
            best_match = matches
            best_event_idx = i

    actual_winning = set(current_events[best_event_idx])
    print(f"Actual Series {series_id} E{best_event_idx + 1}: {sorted(actual_winning)}")

    # Match breakdown
    matched = prior_event & actual_winning
    missed = prior_event - actual_winning
    extra_in_actual = actual_winning - prior_event

    print(f"\nMatch breakdown:")
    print(f"  Matched ({len(matched)}/14): {sorted(matched)}")
    print(f"  Predicted but NOT in actual ({len(missed)}): {sorted(missed)}")
    print(f"  In actual but NOT predicted ({len(extra_in_actual)}): {sorted(extra_in_actual)}")

    return {
        "series": series_id,
        "event_predicted": event_name,
        "prior_numbers": sorted(prior_event),
        "matched_event": f"E{best_event_idx + 1}",
        "actual_numbers": sorted(actual_winning),
        "matches": best_match,
        "matched_numbers": sorted(matched),
        "missed_numbers": sorted(missed),
        "extra_numbers": sorted(extra_in_actual)
    }


def find_all_12plus_events(data, start=2981, end=None):
    """Find all 12+ events for all event types (E1-E7)."""
    if end is None:
        end = max(int(s) for s in data.keys())

    results_by_event = {f"E{i+1}": [] for i in range(7)}

    for series_id in range(start, end + 1):
        prior = str(series_id - 1)
        current = str(series_id)

        if prior not in data or current not in data:
            continue

        current_events = data[current]

        for event_idx in range(7):
            prior_event = set(data[prior][event_idx])

            for i, actual_event in enumerate(current_events):
                matches = len(prior_event & set(actual_event))
                if matches >= 12:
                    results_by_event[f"E{event_idx + 1}"].append({
                        "series": series_id,
                        "matches": matches,
                        "matched_event": f"E{i + 1}"
                    })

    return results_by_event


def analyze_overlap(data, start=2981, end=None):
    """Analyze overlap between E1/E6 and E3/E7 wins."""
    if end is None:
        end = max(int(s) for s in data.keys())

    # Track which series each event type wins
    e1_wins = []
    e3_wins = []
    e6_wins = []
    e7_wins = []

    for series_id in range(start, end + 1):
        prior = str(series_id - 1)
        current = str(series_id)

        if prior not in data or current not in data:
            continue

        current_events = data[current]

        # Check each prior event type
        for event_idx, wins_list in [(0, e1_wins), (2, e3_wins), (5, e6_wins), (6, e7_wins)]:
            prior_event = set(data[prior][event_idx])
            best_match = max(len(prior_event & set(e)) for e in current_events)
            if best_match >= 11:  # Track 11+ for win analysis
                wins_list.append((series_id, best_match))

    return e1_wins, e3_wins, e6_wins, e7_wins


def main():
    data = load_data()

    print("="*70)
    print("E3 and E7 Breakthrough Analysis")
    print("="*70)

    # First, find ALL 12+ events for all event types
    print("\n" + "="*70)
    print("Part 1: All 12+ Events by Event Type")
    print("="*70)

    results_by_event = find_all_12plus_events(data)

    for event_name, results in results_by_event.items():
        if results:
            print(f"\n{event_name}: {len(results)} hits at 12+")
            for r in results:
                print(f"  Series {r['series']}: {r['matches']}/14 (matched {r['matched_event']})")
        else:
            print(f"\n{event_name}: 0 hits at 12+")

    # Part 2: Detailed analysis of reported E3/E7 breakthroughs
    print("\n" + "="*70)
    print("Part 2: Detailed Breakdown of Reported E3/E7 Hits")
    print("="*70)

    # E3 hits
    e3_2998 = analyze_12plus_event(data, 2998, 2, "E3", "E7")
    e3_3134 = analyze_12plus_event(data, 3134, 2, "E3", "E4")

    # E7 hits
    e7_3004 = analyze_12plus_event(data, 3004, 6, "E7", "E3")
    e7_3072 = analyze_12plus_event(data, 3072, 6, "E7", "E5")

    # Part 3: Compare with E1 and E6 on the same series
    print("\n" + "="*70)
    print("Part 3: E1/E6 Performance on Same Series (E3/E7 12+ hits)")
    print("="*70)

    for series_id in [2998, 3004, 3072, 3134]:
        prior = str(series_id - 1)
        current = str(series_id)

        e1_prior = set(data[prior][0])  # E1
        e6_prior = set(data[prior][5])  # E6
        e3_prior = set(data[prior][2])  # E3
        e7_prior = set(data[prior][6])  # E7

        current_events = data[current]

        e1_best = max(len(e1_prior & set(e)) for e in current_events)
        e6_best = max(len(e6_prior & set(e)) for e in current_events)
        e3_best = max(len(e3_prior & set(e)) for e in current_events)
        e7_best = max(len(e7_prior & set(e)) for e in current_events)

        print(f"\nSeries {series_id}:")
        print(f"  E1: {e1_best}/14")
        print(f"  E3: {e3_best}/14")
        print(f"  E6: {e6_best}/14")
        print(f"  E7: {e7_best}/14")
        print(f"  Winner: E3={e3_best}, E7={e7_best}, E1={e1_best}, E6={e6_best}")

    # Part 4: Full overlap analysis
    print("\n" + "="*70)
    print("Part 4: Win Overlap Analysis (11+ matches)")
    print("="*70)

    e1_wins, e3_wins, e6_wins, e7_wins = analyze_overlap(data)

    e1_series = set(w[0] for w in e1_wins)
    e3_series = set(w[0] for w in e3_wins)
    e6_series = set(w[0] for w in e6_wins)
    e7_series = set(w[0] for w in e7_wins)

    print(f"\n11+ hit counts:")
    print(f"  E1: {len(e1_wins)} series")
    print(f"  E3: {len(e3_wins)} series")
    print(f"  E6: {len(e6_wins)} series")
    print(f"  E7: {len(e7_wins)} series")

    # Overlap analysis
    e1_e3_overlap = e1_series & e3_series
    e1_e7_overlap = e1_series & e7_series
    e6_e3_overlap = e6_series & e3_series
    e6_e7_overlap = e6_series & e7_series
    e3_e7_overlap = e3_series & e7_series

    # Independence from E1/E6
    e3_unique = e3_series - e1_series - e6_series
    e7_unique = e7_series - e1_series - e6_series

    print(f"\nOverlap:")
    print(f"  E1 & E3: {len(e1_e3_overlap)} shared series")
    print(f"  E1 & E7: {len(e1_e7_overlap)} shared series")
    print(f"  E6 & E3: {len(e6_e3_overlap)} shared series")
    print(f"  E6 & E7: {len(e6_e7_overlap)} shared series")
    print(f"  E3 & E7: {len(e3_e7_overlap)} shared series")

    print(f"\nIndependent wins (not captured by E1 or E6):")
    print(f"  E3 unique: {len(e3_unique)} series")
    print(f"  E7 unique: {len(e7_unique)} series")

    if e3_unique:
        print(f"    E3 unique series: {sorted(e3_unique)[:10]}{'...' if len(e3_unique) > 10 else ''}")
    if e7_unique:
        print(f"    E7 unique series: {sorted(e7_unique)[:10]}{'...' if len(e7_unique) > 10 else ''}")

    # Part 5: Would S11/S12 increase ceiling?
    print("\n" + "="*70)
    print("Part 5: Ceiling Analysis - Would S11 (E3) and S12 (E7) Help?")
    print("="*70)

    # Find max score across E1, E3, E6, E7 for each series
    end = max(int(s) for s in data.keys())

    e1_max_scores = []
    e1_e6_max_scores = []
    e1_e6_e3_e7_max_scores = []
    e3_alone_scores = []
    e7_alone_scores = []

    for series_id in range(2981, end + 1):
        prior = str(series_id - 1)
        current = str(series_id)

        if prior not in data or current not in data:
            continue

        current_events = data[current]

        e1_prior = set(data[prior][0])
        e3_prior = set(data[prior][2])
        e6_prior = set(data[prior][5])
        e7_prior = set(data[prior][6])

        e1_best = max(len(e1_prior & set(e)) for e in current_events)
        e3_best = max(len(e3_prior & set(e)) for e in current_events)
        e6_best = max(len(e6_prior & set(e)) for e in current_events)
        e7_best = max(len(e7_prior & set(e)) for e in current_events)

        e1_max_scores.append(e1_best)
        e1_e6_max_scores.append(max(e1_best, e6_best))
        e1_e6_e3_e7_max_scores.append(max(e1_best, e3_best, e6_best, e7_best))
        e3_alone_scores.append(e3_best)
        e7_alone_scores.append(e7_best)

    n = len(e1_max_scores)

    print(f"\nAverage best match across {n} series:")
    print(f"  E1 only:           {sum(e1_max_scores)/n:.2f}/14")
    print(f"  E1 + E6:           {sum(e1_e6_max_scores)/n:.2f}/14")
    print(f"  E1 + E3 + E6 + E7: {sum(e1_e6_e3_e7_max_scores)/n:.2f}/14")

    print(f"\nStandalone averages:")
    print(f"  E3 alone:          {sum(e3_alone_scores)/n:.2f}/14")
    print(f"  E7 alone:          {sum(e7_alone_scores)/n:.2f}/14")

    # Count 12+ and 13+ for each configuration
    e1_12plus = sum(1 for s in e1_max_scores if s >= 12)
    e1_e6_12plus = sum(1 for s in e1_e6_max_scores if s >= 12)
    e1_e6_e3_e7_12plus = sum(1 for s in e1_e6_e3_e7_max_scores if s >= 12)

    e1_13plus = sum(1 for s in e1_max_scores if s >= 13)
    e1_e6_13plus = sum(1 for s in e1_e6_max_scores if s >= 13)
    e1_e6_e3_e7_13plus = sum(1 for s in e1_e6_e3_e7_max_scores if s >= 13)

    print(f"\n12+ hit counts:")
    print(f"  E1 only:           {e1_12plus}")
    print(f"  E1 + E6:           {e1_e6_12plus}")
    print(f"  E1 + E3 + E6 + E7: {e1_e6_e3_e7_12plus}")

    print(f"\n13+ hit counts:")
    print(f"  E1 only:           {e1_13plus}")
    print(f"  E1 + E6:           {e1_e6_13plus}")
    print(f"  E1 + E3 + E6 + E7: {e1_e6_e3_e7_13plus}")

    # Find specific series where E3/E7 improved over E1/E6
    improved_series = []
    for i, series_id in enumerate(range(2981, 2981 + n)):
        e1_e6 = e1_e6_max_scores[i]
        e1_e6_e3_e7 = e1_e6_e3_e7_max_scores[i]
        if e1_e6_e3_e7 > e1_e6:
            improved_series.append((series_id, e1_e6, e1_e6_e3_e7))

    print(f"\nSeries where E3/E7 improved over E1/E6: {len(improved_series)}")
    if improved_series:
        print("  Top improvements:")
        for sid, old, new in sorted(improved_series, key=lambda x: x[2] - x[1], reverse=True)[:10]:
            print(f"    Series {sid}: E1/E6={old}/14 -> E1/E3/E6/E7={new}/14 (+{new-old})")

    # Final recommendation
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)

    avg_improvement = sum(e1_e6_e3_e7_max_scores)/n - sum(e1_e6_max_scores)/n

    print(f"\n1. Average improvement from adding E3+E7: +{avg_improvement:.3f}/14")
    print(f"2. Series with improvement: {len(improved_series)}/{n} ({100*len(improved_series)/n:.1f}%)")
    print(f"3. E3 unique 11+ wins (not E1/E6): {len(e3_unique)}")
    print(f"4. E7 unique 11+ wins (not E1/E6): {len(e7_unique)}")
    print(f"5. Additional 12+ from E3/E7: {e1_e6_e3_e7_12plus - e1_e6_12plus}")
    print(f"6. Additional 13+ from E3/E7: {e1_e6_e3_e7_13plus - e1_e6_13plus}")

    if e1_e6_e3_e7_13plus > e1_e6_13plus or e1_e6_e3_e7_12plus > e1_e6_12plus:
        print("\nRECOMMENDATION: Add S11 (E3) and S12 (E7) - they increase ceiling!")
    elif len(improved_series) > 0.1 * n:
        print("\nRECOMMENDATION: Add S11 (E3) and S12 (E7) - significant diversification")
    else:
        print("\nRECOMMENDATION: E3/E7 add marginal value, consider if 12-set is acceptable")


if __name__ == "__main__":
    main()
