#!/usr/bin/env python3
"""
Event Breakthrough Analysis
===========================
Analyze E2-E7 for breakthrough potential similar to E6's 13/14 achievement.

Key questions:
1. What score would each event achieve if used directly (like S9)?
2. Which events have highest ceiling (12+, 13+)?
3. Which events correlate with E1 vs independently predictive?
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import statistics

def load_data():
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def analyze_event_carryover(data, event_idx):
    """Analyze carryover for a specific event (0-indexed)."""
    series_list = sorted(int(s) for s in data.keys())

    carryovers = []
    best_matches = []
    scores_12plus = []
    scores_13plus = []

    for i, sid in enumerate(series_list[1:], 1):
        prev_sid = series_list[i-1]

        # Prior event numbers (what we'd predict with)
        prior_event = set(data[str(prev_sid)][event_idx])

        # Current series all events (what we match against)
        current_events = data[str(sid)]

        # Best match across all 7 events
        matches = [len(prior_event & set(e)) for e in current_events]
        best = max(matches)
        best_event_idx = matches.index(best)

        carryovers.append(best)
        best_matches.append({
            'series': sid,
            'score': best,
            'matched_event': best_event_idx + 1,
            'prior_event': sorted(prior_event),
            'actual': sorted(current_events[best_event_idx])
        })

        if best >= 12:
            scores_12plus.append({'series': sid, 'score': best, 'event': best_event_idx + 1})
        if best >= 13:
            scores_13plus.append({'series': sid, 'score': best, 'event': best_event_idx + 1})

    return {
        'event': event_idx + 1,
        'n': len(carryovers),
        'mean': statistics.mean(carryovers),
        'std': statistics.stdev(carryovers),
        'min': min(carryovers),
        'max': max(carryovers),
        'at_11plus': sum(1 for c in carryovers if c >= 11),
        'at_12plus': sum(1 for c in carryovers if c >= 12),
        'at_13plus': sum(1 for c in carryovers if c >= 13),
        'at_14': sum(1 for c in carryovers if c == 14),
        'scores_12plus': scores_12plus,
        'scores_13plus': scores_13plus,
        'distribution': Counter(carryovers),
        'best_matches': best_matches
    }


def analyze_event_independence(data):
    """Check how independent each event is from E1."""
    series_list = sorted(int(s) for s in data.keys())

    correlations = defaultdict(list)

    for i, sid in enumerate(series_list[1:], 1):
        prev_sid = series_list[i-1]
        prior_events = data[str(prev_sid)]
        e1 = set(prior_events[0])

        for event_idx in range(1, 7):  # E2-E7
            other = set(prior_events[event_idx])
            overlap = len(e1 & other)
            correlations[event_idx + 1].append(overlap)

    results = {}
    for event, overlaps in correlations.items():
        results[event] = {
            'mean_overlap_with_e1': statistics.mean(overlaps),
            'std': statistics.stdev(overlaps),
            'min': min(overlaps),
            'max': max(overlaps)
        }
    return results


def find_breakthrough_events(data):
    """Find which events to watch for 13+ scores."""
    series_list = sorted(int(s) for s in data.keys())

    # Track which event achieved the best score for each series
    event_wins = defaultdict(int)
    event_scores = defaultdict(list)

    for i, sid in enumerate(series_list[1:], 1):
        prev_sid = series_list[i-1]
        prior_events = data[str(prev_sid)]
        current_events = data[str(sid)]

        best_overall = 0
        best_event = 0

        for event_idx in range(7):
            prior = set(prior_events[event_idx])
            matches = [len(prior & set(e)) for e in current_events]
            best = max(matches)
            event_scores[event_idx + 1].append(best)

            if best > best_overall:
                best_overall = best
                best_event = event_idx + 1

        event_wins[best_event] += 1

    return event_wins, event_scores


def main():
    data = load_data()

    print("=" * 80)
    print("EVENT BREAKTHROUGH ANALYSIS (E1-E7)")
    print("=" * 80)
    print(f"Data: {len(data)} series")
    print()

    # Analyze each event
    print("=" * 80)
    print("DIRECT EVENT COPY PERFORMANCE (like S9 uses E6)")
    print("=" * 80)
    print()
    print(f"{'Event':<8} {'Mean':>8} {'Std':>6} {'Min':>5} {'Max':>5} {'11+':>6} {'12+':>6} {'13+':>6} {'14/14':>6}")
    print("-" * 80)

    all_results = {}
    for event_idx in range(7):
        r = analyze_event_carryover(data, event_idx)
        all_results[event_idx + 1] = r
        print(f"E{r['event']:<7} {r['mean']:>8.2f} {r['std']:>6.2f} {r['min']:>5} {r['max']:>5} "
              f"{r['at_11plus']:>6} {r['at_12plus']:>6} {r['at_13plus']:>6} {r['at_14']:>6}")

    print("-" * 80)
    print()

    # Find breakthrough events (12+ and 13+)
    print("=" * 80)
    print("12+ SCORE DETAILS BY EVENT")
    print("=" * 80)

    for event_idx in range(7):
        r = all_results[event_idx + 1]
        if r['scores_12plus']:
            print(f"\nE{event_idx + 1}: {len(r['scores_12plus'])} occurrences")
            for s in r['scores_12plus']:
                print(f"  Series {s['series']}: {s['score']}/14 (matched E{s['event']})")

    print()
    print("=" * 80)
    print("13+ SCORE DETAILS BY EVENT")
    print("=" * 80)

    for event_idx in range(7):
        r = all_results[event_idx + 1]
        if r['scores_13plus']:
            print(f"\nE{event_idx + 1}: {len(r['scores_13plus'])} occurrences")
            for s in r['scores_13plus']:
                print(f"  Series {s['series']}: {s['score']}/14 (matched E{s['event']})")

    # Independence analysis
    print()
    print("=" * 80)
    print("EVENT INDEPENDENCE FROM E1")
    print("=" * 80)
    print("(Lower overlap = more independent, more diversification value)")
    print()

    independence = analyze_event_independence(data)
    print(f"{'Event':<8} {'Mean Overlap':>14} {'Std':>8} {'Min':>6} {'Max':>6}")
    print("-" * 50)
    for event, stats in sorted(independence.items()):
        print(f"E{event:<7} {stats['mean_overlap_with_e1']:>14.2f} {stats['std']:>8.2f} "
              f"{stats['min']:>6} {stats['max']:>6}")

    # Win rate analysis
    print()
    print("=" * 80)
    print("BEST EVENT WIN RATES")
    print("=" * 80)
    print("(Which event achieves highest score most often)")
    print()

    event_wins, event_scores = find_breakthrough_events(data)
    total = sum(event_wins.values())

    print(f"{'Event':<8} {'Wins':>8} {'Rate':>10} {'Avg Score':>12}")
    print("-" * 50)
    for event in range(1, 8):
        wins = event_wins[event]
        avg = statistics.mean(event_scores[event])
        print(f"E{event:<7} {wins:>8} {wins/total*100:>9.1f}% {avg:>12.2f}")

    # Breakthrough potential ranking
    print()
    print("=" * 80)
    print("BREAKTHROUGH POTENTIAL RANKING")
    print("=" * 80)
    print()

    # Score events by breakthrough potential
    # Weight: 13+ count * 100 + 12+ count * 10 + 11+ count + mean
    scored = []
    for event_idx in range(7):
        r = all_results[event_idx + 1]
        score = r['at_13plus'] * 100 + r['at_12plus'] * 10 + r['at_11plus'] * 0.1 + r['mean']
        scored.append((event_idx + 1, score, r))

    scored.sort(key=lambda x: -x[1])

    print(f"{'Rank':<6} {'Event':<8} {'Score':>10} {'13+':>6} {'12+':>6} {'Mean':>8} {'Recommendation'}")
    print("-" * 80)

    for rank, (event, score, r) in enumerate(scored, 1):
        if event == 1:
            rec = "BASELINE (S1-S8)"
        elif event == 6:
            rec = "IMPLEMENTED (S9)"
        elif r['at_13plus'] > 0:
            rec = "HIGH PRIORITY - Add as set"
        elif r['at_12plus'] > 0:
            rec = "MEDIUM - Consider adding"
        else:
            rec = "LOW - No 12+ scores"

        print(f"#{rank:<5} E{event:<7} {score:>10.1f} {r['at_13plus']:>6} {r['at_12plus']:>6} {r['mean']:>8.2f} {rec}")

    # Detailed recommendations
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    # Find events with breakthrough potential not yet implemented
    new_candidates = []
    for event_idx in range(7):
        r = all_results[event_idx + 1]
        if event_idx == 0:  # E1 is baseline
            continue
        if event_idx == 5:  # E6 already implemented
            continue
        if r['at_12plus'] > 0:
            new_candidates.append((event_idx + 1, r))

    if new_candidates:
        print("Events with 12+ potential not yet in strategy:")
        for event, r in new_candidates:
            print(f"  - E{event}: {r['at_12plus']}x 12+, {r['at_13plus']}x 13+, avg {r['mean']:.2f}/14")
        print()
        print("Suggested new sets:")
        for i, (event, r) in enumerate(new_candidates):
            print(f"  S{11+i}: E{event} directly (copy prior E{event})")
    else:
        print("No additional events show breakthrough potential beyond E1 and E6.")

    print()

    # Save results
    output = {
        'event_stats': {str(k): {
            'mean': v['mean'],
            'max': v['max'],
            'at_11plus': v['at_11plus'],
            'at_12plus': v['at_12plus'],
            'at_13plus': v['at_13plus'],
            'scores_12plus': v['scores_12plus'],
            'scores_13plus': v['scores_13plus']
        } for k, v in all_results.items()},
        'independence': independence,
        'win_rates': {str(k): v for k, v in event_wins.items()},
        'ranking': [(e, s) for e, s, _ in scored]
    }

    out_path = Path(__file__).parent / "event_breakthrough_results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
