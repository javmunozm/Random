#!/usr/bin/env python3
"""
Gemini Advanced Analysis Test (2026-01-28)
==========================================

Tests strategies identified by Gemini evaluation:
1. Cross-series patterns ("Hit Hangover" - what happens after 12+ hits)
2. Delta prediction (predict corrections to E4 baseline)
3. Graph centrality (co-occurrence network analysis)

Baseline: 10.61 avg, 16 12+, 3 13+
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import math

# Load data
DATA_PATH = Path(__file__).parent.parent / "data" / "full_series_data.json"
data = json.loads(DATA_PATH.read_text())

TOTAL = 25
PICK = 14
START = 2981
END = 3180


def get_global_freq():
    """Get global frequency."""
    freq = Counter(n for events in data.values() for e in events for n in e)
    return freq


FREQ = get_global_freq()


# =============================================================================
# TEST 1: Cross-Series Patterns (Hit Hangover Analysis)
# =============================================================================

def analyze_hit_hangover():
    """Analyze what happens after 12+ hits."""
    print("=" * 70)
    print("TEST 1: CROSS-SERIES PATTERNS (Hit Hangover)")
    print("=" * 70)

    # First, identify all 12+ hit series using baseline predictor
    hit_series = []
    all_scores = []

    for sid in range(START, END + 1):
        score = evaluate_baseline(sid)
        if score:
            all_scores.append((sid, score))
            if score >= 12:
                hit_series.append(sid)

    print(f"Total series: {len(all_scores)}")
    print(f"12+ hits: {len(hit_series)}")
    print(f"Hit series: {hit_series}")
    print()

    # Analyze post-hit behavior
    post_hit_scores = []
    for hit_sid in hit_series:
        next_sid = hit_sid + 1
        if next_sid <= END:
            next_score = evaluate_baseline(next_sid)
            if next_score:
                post_hit_scores.append((hit_sid, next_score))

    print(f"Post-hit series analyzed: {len(post_hit_scores)}")

    if post_hit_scores:
        post_avg = sum(s[1] for s in post_hit_scores) / len(post_hit_scores)
        overall_avg = sum(s[1] for s in all_scores) / len(all_scores)

        print(f"Post-hit average: {post_avg:.2f}/14")
        print(f"Overall average: {overall_avg:.2f}/14")
        print(f"Difference: {post_avg - overall_avg:+.2f}")

        # Count 12+ in post-hit
        post_12plus = sum(1 for s in post_hit_scores if s[1] >= 12)
        print(f"12+ in post-hit series: {post_12plus}/{len(post_hit_scores)} ({100*post_12plus/len(post_hit_scores):.1f}%)")

        # Statistical significance (rough z-test)
        overall_12plus_rate = len(hit_series) / len(all_scores)
        expected = overall_12plus_rate * len(post_hit_scores)
        print(f"Expected 12+ (random): {expected:.1f}")

    print()
    return post_hit_scores


# =============================================================================
# TEST 2: Delta Prediction
# =============================================================================

def build_delta_model(series_id):
    """
    Build prediction by analyzing which numbers to ADD/REMOVE from E4.

    Strategy: E4 is ~55% accurate. We need to fix the ~45% errors.
    Analyze which numbers are frequently "wrong" and which are "missing".
    """
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e4 = set(data[prior][3])

    # Analyze historical error patterns
    # For each past series, see what was wrong in E4
    add_candidates = Counter()  # Numbers that should have been added
    remove_candidates = Counter()  # Numbers that should have been removed

    series_list = sorted(int(s) for s in data.keys())
    for sid in series_list:
        if sid >= series_id - 1:  # Don't use current or future
            break
        if sid < 2980:
            continue

        prior_sid = str(sid)
        current_sid = str(sid + 1)

        if prior_sid not in data or current_sid not in data:
            continue

        prior_e4 = set(data[prior_sid][3])
        actual_events = data[current_sid]

        # Find best matching event
        best_match = 0
        best_event = None
        for event in actual_events:
            match = len(prior_e4 & set(event))
            if match > best_match:
                best_match = match
                best_event = set(event)

        if best_event:
            # Numbers that were in E4 but shouldn't have been
            wrong_in_e4 = prior_e4 - best_event
            for n in wrong_in_e4:
                remove_candidates[n] += 1

            # Numbers that should have been in E4 but weren't
            missing_from_e4 = best_event - prior_e4
            for n in missing_from_e4:
                add_candidates[n] += 1

    # Build corrected E4
    # Remove top "wrong" numbers, add top "missing" numbers
    e4_list = list(e4)

    # Sort E4 numbers by how often they're wrong
    e4_sorted_by_wrong = sorted(e4_list, key=lambda n: -remove_candidates.get(n, 0))

    # Get top candidates to add
    not_in_e4 = [n for n in range(1, 26) if n not in e4]
    add_sorted = sorted(not_in_e4, key=lambda n: -add_candidates.get(n, 0))

    # Try different correction levels
    results = []
    for num_swaps in [0, 1, 2, 3, 4, 5, 6]:
        corrected = set(e4)
        # Remove worst
        for i in range(min(num_swaps, len(e4_sorted_by_wrong))):
            corrected.discard(e4_sorted_by_wrong[i])
        # Add best
        for i in range(min(num_swaps, len(add_sorted))):
            if len(corrected) < 14:
                corrected.add(add_sorted[i])

        # Ensure we have exactly 14
        while len(corrected) < 14:
            for n in add_sorted:
                if n not in corrected:
                    corrected.add(n)
                    break

        results.append((num_swaps, sorted(corrected)))

    return results


def test_delta_prediction():
    """Test delta prediction approach."""
    print("=" * 70)
    print("TEST 2: DELTA PREDICTION (Corrections to E4)")
    print("=" * 70)

    # Test each swap level
    swap_results = defaultdict(list)

    for sid in range(START, END + 1):
        corrections = build_delta_model(sid)
        if not corrections:
            continue

        actual_sid = str(sid)
        if actual_sid not in data:
            continue

        events = data[actual_sid]

        for num_swaps, corrected_set in corrections:
            # Evaluate corrected set
            matches = [len(set(corrected_set) & set(e)) for e in events]
            best = max(matches)
            swap_results[num_swaps].append(best)

    print(f"{'Swaps':<10} {'Avg':>8} {'11+':>6} {'12+':>6} {'13+':>6}")
    print("-" * 50)

    for num_swaps in sorted(swap_results.keys()):
        scores = swap_results[num_swaps]
        avg = sum(scores) / len(scores)
        at_11 = sum(1 for s in scores if s >= 11)
        at_12 = sum(1 for s in scores if s >= 12)
        at_13 = sum(1 for s in scores if s >= 13)
        print(f"{num_swaps:<10} {avg:>8.2f} {at_11:>6} {at_12:>6} {at_13:>6}")

    print()
    print("Note: 0 swaps = pure E4 copy")
    print()


# =============================================================================
# TEST 3: Graph Centrality Analysis
# =============================================================================

def build_cooccurrence_graph(max_series):
    """Build co-occurrence graph from historical data."""
    # Edge weights = how often two numbers appear together in same event
    edges = defaultdict(int)

    for sid_str, events in data.items():
        sid = int(sid_str)
        if sid >= max_series:
            continue

        for event in events:
            # All pairs in this event
            nums = list(event)
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    pair = tuple(sorted([nums[i], nums[j]]))
                    edges[pair] += 1

    return edges


def calculate_centrality(edges):
    """Calculate degree centrality for each number."""
    # Simple degree centrality: sum of edge weights
    centrality = Counter()
    for (n1, n2), weight in edges.items():
        centrality[n1] += weight
        centrality[n2] += weight
    return centrality


def predict_graph_centrality(series_id):
    """Predict using graph centrality - select most central numbers."""
    edges = build_cooccurrence_graph(series_id)
    centrality = calculate_centrality(edges)

    # Top 14 by centrality
    top_14 = sorted(range(1, 26), key=lambda n: -centrality.get(n, 0))[:14]
    return sorted(top_14)


def predict_hybrid_centrality(series_id):
    """Hybrid: E4 + centrality for tiebreaking."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e4 = set(data[prior][3])
    edges = build_cooccurrence_graph(series_id)
    centrality = calculate_centrality(edges)

    # E4 numbers + fill with highest centrality
    result = list(e4)
    remaining = sorted([n for n in range(1, 26) if n not in e4],
                       key=lambda n: -centrality.get(n, 0))

    # If E4 has 14, we're done
    # If less, fill with centrality
    while len(result) < 14 and remaining:
        result.append(remaining.pop(0))

    return sorted(result[:14])


def test_graph_centrality():
    """Test graph centrality approach."""
    print("=" * 70)
    print("TEST 3: GRAPH CENTRALITY (Co-occurrence Network)")
    print("=" * 70)

    strategies = [
        ("Pure centrality (top 14)", predict_graph_centrality),
        ("Hybrid (E4 + centrality)", predict_hybrid_centrality),
    ]

    for name, func in strategies:
        scores = []
        for sid in range(START, END + 1):
            pred = func(sid)
            if pred:
                actual_sid = str(sid)
                if actual_sid in data:
                    events = data[actual_sid]
                    matches = [len(set(pred) & set(e)) for e in events]
                    scores.append(max(matches))

        if scores:
            avg = sum(scores) / len(scores)
            at_11 = sum(1 for s in scores if s >= 11)
            at_12 = sum(1 for s in scores if s >= 12)
            at_13 = sum(1 for s in scores if s >= 13)
            print(f"{name}")
            print(f"  Avg: {avg:.2f}, 11+: {at_11}, 12+: {at_12}, 13+: {at_13}")
            print()


# =============================================================================
# BASELINE
# =============================================================================

def predict_baseline(series_id):
    """Current 7-set baseline."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    e1 = set(data[prior][0])
    e2 = set(data[prior][1])
    e3 = set(data[prior][2])
    e4 = set(data[prior][3])
    e6 = set(data[prior][5])
    e7 = set(data[prior][6])

    max_freq = max(FREQ.values())
    ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -FREQ[n]/max_freq, n))

    e3_e7_int = e3 & e7
    e3_e7_union = e3 | e7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -FREQ[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    sym_diff = (e3 | e7) - (e3 & e7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -FREQ.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

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
        s6_numbers,
        s7_numbers,
    ]


def evaluate_baseline(series_id):
    """Evaluate baseline prediction."""
    sets = predict_baseline(series_id)
    if not sets:
        return None

    actual_sid = str(series_id)
    if actual_sid not in data:
        return None

    events = data[actual_sid]
    set_bests = []
    for s in sets:
        matches = [len(set(s) & set(e)) for e in events]
        set_bests.append(max(matches))

    return max(set_bests)


def main():
    print("=" * 70)
    print("GEMINI ADVANCED ANALYSIS TEST (2026-01-28)")
    print("=" * 70)
    print(f"Testing on series {START}-{END} ({END - START + 1} series)")
    print(f"Baseline: 10.61 avg, 16 12+, 3 13+")
    print()

    # Test 1: Hit Hangover
    analyze_hit_hangover()

    # Test 2: Delta Prediction
    test_delta_prediction()

    # Test 3: Graph Centrality
    test_graph_centrality()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Compare all results against baseline: 10.61 avg, 16 12+, 3 13+")


if __name__ == "__main__":
    main()
