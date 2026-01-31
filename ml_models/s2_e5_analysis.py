#!/usr/bin/env python3
"""
S2 Replacement Analysis: E5-based candidates
=============================================

Comprehensive analysis of whether S2 (E1 rank16) should be replaced with
an E5-based or E5-incorporating strategy.

Sections:
1. S2 Failure Pattern Analysis
2. E5 Potential Analysis
3. Candidate Generation
4. Quick Backtest (200-series)
5. Ranking

Uses recency-weighted frequency exactly as in production_predictor.py.
NO look-ahead bias.
"""

import json
import sys
from pathlib import Path
from collections import Counter
import statistics

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def get_recency_freq(data, series_id):
    """Recency-weighted frequency -- identical to production_predictor.py."""
    freq = Counter()
    prior_series = series_id - 1
    for sid_str, events in data.items():
        sid = int(sid_str)
        if sid >= series_id:
            continue
        age = prior_series - sid
        if age <= 10:
            weight = 3.0
        elif age <= 30:
            weight = 2.0
        else:
            weight = 1.0
        for event in events:
            for n in event:
                freq[n] += weight
    return freq


# =============================================================================
# PRODUCTION PREDICT (exact copy to ensure consistency)
# =============================================================================

TOTAL = 25
PICK = 14
NUM_SETS = 7


def predict_production(data, series_id):
    """Exact copy of production predict for baseline."""
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No data for series {int(prior)}")

    event1 = set(data[prior][0])
    event2 = set(data[prior][1])
    event3 = set(data[prior][2])
    event4 = set(data[prior][3])
    event5 = set(data[prior][4])  # E5 -- not used in production
    event6 = set(data[prior][5])
    event7 = set(data[prior][6])

    freq = get_recency_freq(data, series_id)
    max_freq = max(freq.values()) if freq else 1

    # E1 ranked
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event1), -freq[n]/max_freq, n))

    # E3&E7 fusion (S5)
    e3_e7_int = event3 & event7
    e3_e7_union = event3 | event7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # S6: Symmetric Difference E3^E7
    sym_diff = (event3 | event7) - (event3 & event7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # S7: Quint E2E3E4E6E7
    quint_events = [event2, event3, event4, event6, event7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26),
                         key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    sets = [
        sorted(event4),                              # S1: E4 direct
        sorted(ranked[:13] + [ranked[15]]),           # S2: rank16
        sorted(event6),                               # S3: E6 direct
        sorted(event7),                               # S4: E7 direct
        sorted(s5_numbers),                           # S5: E3&E7 fusion
        s6_numbers,                                   # S6: SymDiff E3^E7
        s7_numbers,                                   # S7: Quint E2E3E4E6E7
    ]

    return {
        "sets": sets,
        "event1": event1, "event2": event2, "event3": event3,
        "event4": event4, "event5": event5, "event6": event6, "event7": event7,
        "freq": freq, "ranked": ranked,
    }


# =============================================================================
# EVALUATION HELPERS
# =============================================================================

def score_set_vs_series(pred_set, data, series_id):
    """Best match of a single prediction set against all 7 events of a series."""
    sid = str(series_id)
    if sid not in data:
        return None
    events = data[sid]
    return max(len(set(pred_set) & set(e)) for e in events)


def full_evaluate(data, series_id, sets_7):
    """Evaluate 7-set prediction. Returns dict with per-set scores and best."""
    sid = str(series_id)
    if sid not in data:
        return None
    events = data[sid]
    set_bests = []
    set_best_events = []
    for s in sets_7:
        matches = [len(set(s) & set(e)) for e in events]
        best_ev = max(range(7), key=lambda i: matches[i])
        set_bests.append(max(matches))
        set_best_events.append(best_ev)
    best = max(set_bests)
    winner = set_bests.index(best) + 1
    return {
        "series": series_id,
        "set_bests": set_bests,
        "set_best_events": set_best_events,
        "best": best,
        "winner": winner,
    }


# =============================================================================
# CANDIDATE GENERATORS
# =============================================================================

def make_e5_direct(pred_info):
    """E5 direct copy."""
    return sorted(pred_info["event5"])


def make_e5_rank16(pred_info):
    """E5 rank16: top 13 by E5 membership + freq, then rank 16."""
    event5 = pred_info["event5"]
    freq = pred_info["freq"]
    max_freq = max(freq.values()) if freq else 1
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event5), -freq[n]/max_freq, n))
    return sorted(ranked[:13] + [ranked[15]])


def make_e1_e5_fusion(pred_info):
    """E1&E5 fusion: intersection + fill from union by freq."""
    e1 = pred_info["event1"]
    e5 = pred_info["event5"]
    freq = pred_info["freq"]
    intersection = e1 & e5
    union = e1 | e5
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def make_e4_e5_fusion(pred_info):
    """E4&E5 fusion: intersection + fill from union by freq."""
    e4 = pred_info["event4"]
    e5 = pred_info["event5"]
    freq = pred_info["freq"]
    intersection = e4 & e5
    union = e4 | e5
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def make_symdiff_e1_e5(pred_info):
    """SymDiff E1^E5: numbers in E1 OR E5 but not both."""
    e1 = pred_info["event1"]
    e5 = pred_info["event5"]
    freq = pred_info["freq"]
    sym_diff = (e1 | e5) - (e1 & e5)
    result = list(sym_diff)
    if len(result) < 14:
        remaining = [n for n in range(1, 26) if n not in result]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        result += remaining[:14 - len(result)]
    return sorted(result[:14])


def make_symdiff_e4_e5(pred_info):
    """SymDiff E4^E5: numbers in E4 OR E5 but not both."""
    e4 = pred_info["event4"]
    e5 = pred_info["event5"]
    freq = pred_info["freq"]
    sym_diff = (e4 | e5) - (e4 & e5)
    result = list(sym_diff)
    if len(result) < 14:
        remaining = [n for n in range(1, 26) if n not in result]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        result += remaining[:14 - len(result)]
    return sorted(result[:14])


def make_e5_e6_fusion(pred_info):
    """E5&E6 fusion: intersection + fill from union by freq."""
    e5 = pred_info["event5"]
    e6 = pred_info["event6"]
    freq = pred_info["freq"]
    intersection = e5 & e6
    union = e5 | e6
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def make_e5_e7_fusion(pred_info):
    """E5&E7 fusion: intersection + fill from union by freq."""
    e5 = pred_info["event5"]
    e7 = pred_info["event7"]
    freq = pred_info["freq"]
    intersection = e5 & e7
    union = e5 | e7
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def make_e3_e5_fusion(pred_info):
    """E3&E5 fusion: intersection + fill from union by freq."""
    e3 = pred_info["event3"]
    e5 = pred_info["event5"]
    freq = pred_info["freq"]
    intersection = e3 & e5
    union = e3 | e5
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    result = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(result[:14])


def make_quint_with_e5(pred_info):
    """Quint E1E3E4E5E7: 5-event consensus including E5, replacing E2 and E6."""
    events = [pred_info["event1"], pred_info["event3"], pred_info["event4"],
              pred_info["event5"], pred_info["event7"]]
    freq = pred_info["freq"]
    number_counts = Counter()
    for e in events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26),
                         key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(quint_ranked[:14])


def make_symdiff_e5_e7(pred_info):
    """SymDiff E5^E7: numbers in E5 OR E7 but not both."""
    e5 = pred_info["event5"]
    e7 = pred_info["event7"]
    freq = pred_info["freq"]
    sym_diff = (e5 | e7) - (e5 & e7)
    result = list(sym_diff)
    if len(result) < 14:
        remaining = [n for n in range(1, 26) if n not in result]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        result += remaining[:14 - len(result)]
    return sorted(result[:14])


def make_hex_quint_e5(pred_info):
    """Hex with E5: 6-event consensus E1E2E3E4E5E7 (replaces E6 with E5)."""
    events = [pred_info["event1"], pred_info["event2"], pred_info["event3"],
              pred_info["event4"], pred_info["event5"], pred_info["event7"]]
    freq = pred_info["freq"]
    number_counts = Counter()
    for e in events:
        for n in e:
            number_counts[n] += 1
    ranked = sorted(range(1, 26),
                   key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


# =============================================================================
# SECTION 1: S2 FAILURE PATTERN ANALYSIS
# =============================================================================

def s2_failure_analysis(data, start=2981, end=3180):
    print("\n" + "=" * 80)
    print("SECTION 1: S2 FAILURE PATTERN ANALYSIS")
    print("=" * 80)

    s2_scores = []
    s2_wins = []
    s2_win_scores = []
    s2_unique_wins = []  # series where S2 is strictly best
    s2_missing_at_11 = []
    all_results = []

    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        result = full_evaluate(data, sid, pred_info["sets"])
        if result is None:
            continue

        all_results.append(result)
        s2_score = result["set_bests"][1]  # S2 is index 1
        s2_scores.append(s2_score)

        if result["winner"] == 2:  # S2 wins
            s2_wins.append(sid)
            s2_win_scores.append(s2_score)

        # Check if S2 is strictly best (no tie)
        other_bests = [result["set_bests"][i] for i in range(7) if i != 1]
        if s2_score > max(other_bests):
            s2_unique_wins.append(sid)

        # When S2 scores 11+, which numbers missing?
        if s2_score >= 11:
            s2_set = pred_info["sets"][1]
            sid_str = str(sid)
            if sid_str in data:
                events = data[sid_str]
                best_ev_idx = result["set_best_events"][1]
                target = set(events[best_ev_idx])
                pred = set(s2_set)
                missing = target - pred
                wrong = pred - target
                s2_missing_at_11.append({
                    "series": sid, "score": s2_score,
                    "missing": sorted(missing), "wrong": sorted(wrong),
                    "event": best_ev_idx + 1
                })

    # -- 1a: Score distribution --
    print("\n1a) S2 Per-Set Score Distribution:")
    score_dist = Counter(s2_scores)
    for sc in sorted(score_dist.keys()):
        bar = "#" * score_dist[sc]
        print(f"  {sc:2d}/14: {score_dist[sc]:3d} ({100*score_dist[sc]/len(s2_scores):5.1f}%) {bar}")
    print(f"  Mean: {statistics.mean(s2_scores):.2f}, Median: {statistics.median(s2_scores):.1f}")
    print(f"  Std:  {statistics.stdev(s2_scores):.2f}")

    # -- 1b: When S2 wins, what scores? --
    print(f"\n1b) S2 Wins: {len(s2_wins)} series (wins = is best set)")
    if s2_win_scores:
        win_dist = Counter(s2_win_scores)
        for sc in sorted(win_dist.keys()):
            print(f"  Wins at {sc}/14: {win_dist[sc]}")
    print(f"  Unique wins (strictly best): {len(s2_unique_wins)}")
    if s2_unique_wins:
        print(f"  Series: {s2_unique_wins}")

    # -- 1c: When S2 scores 11+, what's missing? --
    print(f"\n1c) S2 at 11+ ({len(s2_missing_at_11)} cases):")
    missing_counter = Counter()
    for item in s2_missing_at_11:
        for m in item["missing"]:
            missing_counter[m] += 1
        if item["score"] >= 12:
            print(f"  Series {item['series']}: {item['score']}/14 vs E{item['event']}, "
                  f"missing={item['missing']}, wrong={item['wrong']}")
    if missing_counter:
        print(f"  Most frequently missing numbers at 11+:")
        for num, cnt in missing_counter.most_common(10):
            print(f"    #{num:2d}: missed {cnt}x")

    # -- 1d: S2 overlap with other sets --
    print(f"\n1d) S2 Overlap with Other Sets (avg over {len(all_results)} series):")
    overlap_sums = [0.0] * 7
    unique_counts = []
    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        if str(sid) not in data:
            continue
        sets = pred_info["sets"]
        s2_set = set(sets[1])
        for i in range(7):
            overlap_sums[i] += len(s2_set & set(sets[i]))
        # Numbers in S2 not in ANY other set
        other_union = set()
        for i in range(7):
            if i != 1:
                other_union |= set(sets[i])
        unique_to_s2 = s2_set - other_union
        unique_counts.append(len(unique_to_s2))

    n_series = len(all_results)
    labels = ["S1(E4)", "S2(rank16)", "S3(E6)", "S4(E7)", "S5(E3&E7)", "S6(SymDiff)", "S7(Quint)"]
    for i in range(7):
        print(f"  S2 vs {labels[i]}: avg overlap = {overlap_sums[i]/n_series:.2f}/14")
    print(f"  S2 unique numbers (not in any other set): avg = {statistics.mean(unique_counts):.2f}, "
          f"min = {min(unique_counts)}, max = {max(unique_counts)}")

    # -- 1e: Series that would lose best score if S2 removed --
    print(f"\n1e) Impact of Removing S2:")
    would_lose = 0
    lose_details = []
    for result in all_results:
        s2_score = result["set_bests"][1]
        other_best = max(result["set_bests"][i] for i in range(7) if i != 1)
        if s2_score > other_best:
            would_lose += 1
            lose_details.append({
                "series": result["series"],
                "s2_score": s2_score,
                "next_best": other_best,
            })
    print(f"  Series that would lose best score: {would_lose}/{n_series} ({100*would_lose/n_series:.1f}%)")
    for d in lose_details:
        print(f"    Series {d['series']}: would drop from {d['s2_score']} to {d['next_best']}")

    # Check 12+ impact
    s2_12plus = []
    for result in all_results:
        if result["set_bests"][1] >= 12:
            other_max = max(result["set_bests"][i] for i in range(7) if i != 1)
            if other_max < 12:
                s2_12plus.append(result["series"])
    print(f"  12+ hits that ONLY S2 achieves: {len(s2_12plus)}")
    if s2_12plus:
        print(f"    Series: {s2_12plus}")

    # L30 and L10 breakdown
    l30_start = end - 29
    l10_start = end - 9
    l30_scores = [r["set_bests"][1] for r in all_results if r["series"] >= l30_start]
    l10_scores = [r["set_bests"][1] for r in all_results if r["series"] >= l10_start]
    l30_wins = sum(1 for r in all_results if r["series"] >= l30_start and r["winner"] == 2)
    l10_wins = sum(1 for r in all_results if r["series"] >= l10_start and r["winner"] == 2)

    print(f"\n  L30 S2 avg: {statistics.mean(l30_scores):.2f}, wins: {l30_wins}")
    print(f"  L10 S2 avg: {statistics.mean(l10_scores):.2f}, wins: {l10_wins}")

    return all_results


# =============================================================================
# SECTION 2: E5 POTENTIAL ANALYSIS
# =============================================================================

def e5_potential_analysis(data, start=2981, end=3180):
    print("\n" + "=" * 80)
    print("SECTION 2: E5 POTENTIAL ANALYSIS")
    print("=" * 80)

    # -- 2a: E5 pairwise overlap with all events --
    print("\n2a) E5 Pairwise Overlap with Each Event (avg over series):")
    overlap_sums = {f"E{i+1}": 0.0 for i in range(7)}
    n_counted = 0
    for sid in range(start, end + 1):
        prior = str(sid - 1)
        if prior not in data:
            continue
        n_counted += 1
        e5 = set(data[prior][4])
        for i in range(7):
            if i == 4:
                continue
            ei = set(data[prior][i])
            overlap_sums[f"E{i+1}"] += len(e5 & ei)

    for name, total in sorted(overlap_sums.items()):
        if name == "E5":
            continue
        print(f"  E5 vs {name}: avg overlap = {total/n_counted:.2f}/14")

    # Also compute all pairwise for comparison
    print("\n  (For comparison -- all pairwise event overlaps):")
    pairs = []
    for i in range(7):
        for j in range(i+1, 7):
            total = 0
            for sid in range(start, end + 1):
                prior = str(sid - 1)
                if prior not in data:
                    continue
                total += len(set(data[prior][i]) & set(data[prior][j]))
            pairs.append((f"E{i+1}-E{j+1}", total / n_counted))
    pairs.sort(key=lambda x: x[1])
    for name, avg in pairs:
        marker = " <-- involves E5" if "E5" in name else ""
        print(f"  {name}: {avg:.2f}{marker}")

    # -- 2b: E5 direct copy per-set performance --
    print("\n2b) E5 Direct Copy -- Per-Set Performance:")
    e5_scores = []
    e5_12plus = 0
    e5_11plus = 0
    for sid in range(start, end + 1):
        prior = str(sid - 1)
        if prior not in data or str(sid) not in data:
            continue
        e5 = sorted(data[prior][4])
        score = score_set_vs_series(e5, data, sid)
        if score is not None:
            e5_scores.append(score)
            if score >= 12:
                e5_12plus += 1
            if score >= 11:
                e5_11plus += 1

    if e5_scores:
        print(f"  E5 direct avg: {statistics.mean(e5_scores):.2f}/14")
        print(f"  E5 direct 11+: {e5_11plus} ({100*e5_11plus/len(e5_scores):.1f}%)")
        print(f"  E5 direct 12+: {e5_12plus} ({100*e5_12plus/len(e5_scores):.1f}%)")
        print(f"  Score distribution:")
        dist = Counter(e5_scores)
        for sc in sorted(dist.keys()):
            print(f"    {sc:2d}/14: {dist[sc]:3d} ({100*dist[sc]/len(e5_scores):5.1f}%)")

    # -- 2c: E5 overlap with each existing set S1-S7 --
    print(f"\n2c) E5 Overlap with Each Existing Set (avg):")
    set_overlap_sums = [0.0] * 7
    n_valid = 0
    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        if str(sid) not in data:
            continue
        n_valid += 1
        e5 = pred_info["event5"]
        for i in range(7):
            set_overlap_sums[i] += len(e5 & set(pred_info["sets"][i]))

    labels = ["S1(E4)", "S2(rank16)", "S3(E6)", "S4(E7)", "S5(E3&E7)", "S6(SymDiff)", "S7(Quint)"]
    for i in range(7):
        print(f"  E5 vs {labels[i]}: avg overlap = {set_overlap_sums[i]/n_valid:.2f}/14")

    # -- 2d: Unique numbers E5 provides --
    print(f"\n2d) E5 Unique Numbers (not in any S1-S7):")
    e5_unique_counts = []
    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        if str(sid) not in data:
            continue
        e5 = pred_info["event5"]
        all_sets_union = set()
        for s in pred_info["sets"]:
            all_sets_union |= set(s)
        unique = e5 - all_sets_union
        e5_unique_counts.append(len(unique))

    if e5_unique_counts:
        print(f"  Avg unique E5 numbers: {statistics.mean(e5_unique_counts):.2f}")
        print(f"  Min: {min(e5_unique_counts)}, Max: {max(e5_unique_counts)}")
        print(f"  Distribution: {Counter(e5_unique_counts)}")

    # -- 2e: E5 score distribution --
    print(f"\n2e) E5 Score Distribution across 200 series:")
    # (Already done in 2b above, but let's add per-event breakdown)
    e5_per_event = [[] for _ in range(7)]
    for sid in range(start, end + 1):
        prior = str(sid - 1)
        sid_str = str(sid)
        if prior not in data or sid_str not in data:
            continue
        e5 = set(data[prior][4])
        events = data[sid_str]
        for ei in range(7):
            e5_per_event[ei].append(len(e5 & set(events[ei])))

    print(f"  E5 (prior) vs each event in target series:")
    for ei in range(7):
        scores = e5_per_event[ei]
        if scores:
            # E5 predicting its own next value (E5->E5 persistence)
            marker = " <-- E5->E5 self-persistence" if ei == 4 else ""
            print(f"    vs E{ei+1}: avg = {statistics.mean(scores):.2f}{marker}")


# =============================================================================
# SECTION 3 & 4: CANDIDATE GENERATION + BACKTEST
# =============================================================================

def run_backtest(data, start, end, candidate_fn, candidate_name):
    """Run 200-series backtest replacing S2 with candidate."""
    results = []
    s2_slot_scores = []
    s2_slot_12plus = 0
    s7_12plus_preserved = 0
    s7_12plus_total = 0
    unique_coverage_sum = 0
    n_valid = 0

    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        if str(sid) not in data:
            continue

        n_valid += 1
        # Build modified sets: replace S2 (index 1)
        candidate_set = candidate_fn(pred_info)
        modified_sets = list(pred_info["sets"])
        modified_sets[1] = candidate_set

        result = full_evaluate(data, sid, modified_sets)
        if result is None:
            continue
        results.append(result)

        s2_score = result["set_bests"][1]
        s2_slot_scores.append(s2_score)
        if s2_score >= 12:
            s2_slot_12plus += 1

        # S7 12+ tracking
        s7_score = result["set_bests"][6]
        if s7_score >= 12:
            s7_12plus_total += 1

        # Unique coverage
        other_union = set()
        for i in range(7):
            if i != 1:
                other_union |= set(modified_sets[i])
        unique = set(candidate_set) - other_union
        unique_coverage_sum += len(unique)

    if not results:
        return None

    bests = [r["best"] for r in results]
    n = len(results)
    wins = [0] * 7
    for r in results:
        wins[r["winner"] - 1] += 1

    at_11 = sum(1 for b in bests if b >= 11)
    at_12 = sum(1 for b in bests if b >= 12)
    at_13 = sum(1 for b in bests if b >= 13)
    at_14 = sum(1 for b in bests if b == 14)

    return {
        "name": candidate_name,
        "n": n,
        "avg": sum(bests) / n,
        "best": max(bests),
        "worst": min(bests),
        "at_11": at_11,
        "at_12": at_12,
        "at_13": at_13,
        "at_14": at_14,
        "wins": wins,
        "s2_slot_avg": statistics.mean(s2_slot_scores),
        "s2_slot_12plus": s2_slot_12plus,
        "s2_slot_11plus": sum(1 for s in s2_slot_scores if s >= 11),
        "s7_12plus": s7_12plus_total,
        "unique_coverage_avg": unique_coverage_sum / n,
        "s2_slot_dist": Counter(s2_slot_scores),
    }


def backtest_all_candidates(data, start=2981, end=3180):
    print("\n" + "=" * 80)
    print("SECTION 3 & 4: CANDIDATE GENERATION + BACKTEST")
    print("=" * 80)

    candidates = [
        (make_e5_direct,       "E5 direct"),
        (make_e5_rank16,       "E5 rank16"),
        (make_e1_e5_fusion,    "E1&E5 fusion"),
        (make_e4_e5_fusion,    "E4&E5 fusion"),
        (make_symdiff_e1_e5,   "SymDiff E1^E5"),
        (make_symdiff_e4_e5,   "SymDiff E4^E5"),
        (make_e5_e6_fusion,    "E5&E6 fusion"),
        (make_e5_e7_fusion,    "E5&E7 fusion"),
        (make_e3_e5_fusion,    "E3&E5 fusion"),
        (make_quint_with_e5,   "Quint E1E3E4E5E7"),
        (make_symdiff_e5_e7,   "SymDiff E5^E7"),
        (make_hex_quint_e5,    "Hex E1E2E3E4E5E7"),
    ]

    # Baseline (current production)
    print("\nRunning baseline (current production S2=rank16)...")
    baseline_fn = lambda pred_info: pred_info["sets"][1]  # Keep S2 as-is
    baseline = run_backtest(data, start, end, baseline_fn, "BASELINE (S2=rank16)")
    print(f"  Baseline: avg={baseline['avg']:.2f}, 11+={baseline['at_11']}, "
          f"12+={baseline['at_12']}, 13+={baseline['at_13']}, 14={baseline['at_14']}")
    print(f"  S2-slot: avg={baseline['s2_slot_avg']:.2f}, 12+={baseline['s2_slot_12plus']}, "
          f"wins={baseline['wins'][1]}")
    print(f"  S7 12+: {baseline['s7_12plus']}")

    all_results = [baseline]

    print("\nRunning candidates...")
    for fn, name in candidates:
        r = run_backtest(data, start, end, fn, name)
        all_results.append(r)
        delta_12 = r["at_12"] - baseline["at_12"]
        delta_13 = r["at_13"] - baseline["at_13"]
        sign_12 = "+" if delta_12 >= 0 else ""
        sign_13 = "+" if delta_13 >= 0 else ""
        print(f"  {name:22s}: avg={r['avg']:.2f} ({r['avg']-baseline['avg']:+.2f}), "
              f"11+={r['at_11']}, 12+={r['at_12']} ({sign_12}{delta_12}), "
              f"13+={r['at_13']} ({sign_13}{delta_13}), "
              f"S2-wins={r['wins'][1]}, S2-12+={r['s2_slot_12plus']}, "
              f"uniq={r['unique_coverage_avg']:.1f}")

    return all_results, baseline


# =============================================================================
# SECTION 5: RANKING
# =============================================================================

def rank_candidates(all_results, baseline):
    print("\n" + "=" * 80)
    print("SECTION 5: RANKING")
    print("=" * 80)

    # Sort by: 12+ (desc), unique coverage (desc), avg (desc)
    candidates = [r for r in all_results if r["name"] != "BASELINE (S2=rank16)"]
    candidates.sort(key=lambda r: (-r["at_12"], -r["unique_coverage_avg"], -r["avg"]))

    print(f"\n{'Rank':<5} {'Candidate':22s} {'Avg':>6} {'11+':>4} {'12+':>4} {'13+':>4} "
          f"{'S2w':>4} {'S2-12+':>6} {'Uniq':>5} {'S7-12+':>6}")
    print("-" * 88)
    print(f"{'---':<5} {'BASELINE (S2=rank16)':22s} {baseline['avg']:>6.2f} "
          f"{baseline['at_11']:>4} {baseline['at_12']:>4} {baseline['at_13']:>4} "
          f"{baseline['wins'][1]:>4} {baseline['s2_slot_12plus']:>6} "
          f"{baseline['unique_coverage_avg']:>5.1f} {baseline['s7_12plus']:>6}")
    print("-" * 88)

    for rank, r in enumerate(candidates, 1):
        d12 = r["at_12"] - baseline["at_12"]
        d13 = r["at_13"] - baseline["at_13"]
        marker = " ***" if d12 > 0 or d13 > 0 else ""
        print(f"#{rank:<4} {r['name']:22s} {r['avg']:>6.2f} "
              f"{r['at_11']:>4} {r['at_12']:>4} {r['at_13']:>4} "
              f"{r['wins'][1]:>4} {r['s2_slot_12plus']:>6} "
              f"{r['unique_coverage_avg']:>5.1f} {r['s7_12plus']:>6}{marker}")

    # Top 3 detailed
    print("\n" + "=" * 80)
    print("TOP 3 CANDIDATES FOR FULL MONTE CARLO")
    print("=" * 80)
    for rank, r in enumerate(candidates[:3], 1):
        print(f"\n--- #{rank}: {r['name']} ---")
        print(f"  System avg: {r['avg']:.2f} (delta: {r['avg']-baseline['avg']:+.2f})")
        print(f"  11+ hits:   {r['at_11']} (delta: {r['at_11']-baseline['at_11']:+d})")
        print(f"  12+ hits:   {r['at_12']} (delta: {r['at_12']-baseline['at_12']:+d})")
        print(f"  13+ hits:   {r['at_13']} (delta: {r['at_13']-baseline['at_13']:+d})")
        print(f"  S2-slot wins: {r['wins'][1]} (baseline: {baseline['wins'][1]})")
        print(f"  S2-slot 12+:  {r['s2_slot_12plus']} (baseline: {baseline['s2_slot_12plus']})")
        print(f"  Unique coverage: {r['unique_coverage_avg']:.2f} (baseline: {baseline['unique_coverage_avg']:.2f})")
        print(f"  S7 12+ preserved: {r['s7_12plus']} (baseline: {baseline['s7_12plus']})")
        print(f"  S2-slot score distribution:")
        for sc in sorted(r["s2_slot_dist"].keys()):
            cnt = r["s2_slot_dist"][sc]
            print(f"    {sc:2d}/14: {cnt:3d} ({100*cnt/r['n']:5.1f}%)")

    # Critical check: does any candidate beat baseline at 13+?
    print("\n" + "=" * 80)
    print("CRITICAL ANALYSIS")
    print("=" * 80)
    any_13_improvement = any(r["at_13"] > baseline["at_13"] for r in candidates)
    any_12_improvement = any(r["at_12"] > baseline["at_12"] for r in candidates)
    print(f"  Any candidate improves 12+? {'YES' if any_12_improvement else 'NO'}")
    print(f"  Any candidate improves 13+? {'YES' if any_13_improvement else 'NO'}")

    if any_12_improvement:
        improvers_12 = [r for r in candidates if r["at_12"] > baseline["at_12"]]
        print(f"  12+ improvers: {[r['name'] for r in improvers_12]}")
    if any_13_improvement:
        improvers_13 = [r for r in candidates if r["at_13"] > baseline["at_13"]]
        print(f"  13+ improvers: {[r['name'] for r in improvers_13]}")

    # S7 preservation check
    s7_losers = [r for r in candidates if r["s7_12plus"] < baseline["s7_12plus"]]
    if s7_losers:
        print(f"  WARNING: These candidates reduce S7's 12+ count: "
              f"{[(r['name'], r['s7_12plus']) for r in s7_losers]}")
    else:
        print(f"  S7 12+ preserved across all candidates.")

    # Final recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    best = candidates[0]
    if best["at_12"] > baseline["at_12"]:
        print(f"  RECOMMEND: Replace S2 with {best['name']}")
        print(f"  Rationale: +{best['at_12']-baseline['at_12']} at 12+, "
              f"unique coverage {best['unique_coverage_avg']:.1f}")
    elif best["at_13"] > baseline["at_13"]:
        print(f"  RECOMMEND: Replace S2 with {best['name']}")
        print(f"  Rationale: +{best['at_13']-baseline['at_13']} at 13+")
    elif best["at_12"] == baseline["at_12"] and best["unique_coverage_avg"] > baseline["unique_coverage_avg"] + 0.5:
        print(f"  TENTATIVE: {best['name']} matches 12+ but adds coverage")
        print(f"  Needs Monte Carlo validation.")
    else:
        print(f"  NO REPLACEMENT RECOMMENDED. S2 is not clearly outperformed.")
        print(f"  Best candidate ({best['name']}) shows 12+={best['at_12']} vs baseline {baseline['at_12']}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("S2 Replacement Analysis: E5-based Candidates")
    print("=" * 80)
    print(f"Pool: {TOTAL} numbers, pick {PICK}")
    print(f"Sets: {NUM_SETS}")
    print(f"Using recency-weighted frequency (no look-ahead bias)")

    data = load_data()

    # Determine range
    all_sids = sorted(int(s) for s in data.keys())
    start = 2981
    end = all_sids[-1]
    print(f"Series range: {start}-{end} ({end - start + 1} series)")

    # Section 1
    all_results = s2_failure_analysis(data, start, end)

    # Section 2
    e5_potential_analysis(data, start, end)

    # Sections 3 & 4
    backtest_results, baseline = backtest_all_candidates(data, start, end)

    # Section 5
    rank_candidates(backtest_results, baseline)


def deep_dive_symdiff_e4_e5(data, start=2981, end=3180):
    """Deep dive on the SymDiff E4^E5 candidate -- the winner."""
    print("\n" + "=" * 80)
    print("DEEP DIVE: SymDiff E4^E5")
    print("=" * 80)

    # Track per-series: baseline vs candidate at system level
    baseline_12plus = []
    candidate_12plus = []
    gained_12 = []
    lost_12 = []
    gained_13 = []
    lost_13 = []

    # Per-set comparison at S2 slot only
    s2_baseline_scores = []
    s2_candidate_scores = []
    s2_improved = 0
    s2_worsened = 0
    s2_same = 0

    # SymDiff size distribution
    symdiff_sizes = []

    # L30 and L10 breakdown
    l30_start = end - 29
    l10_start = end - 9

    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        if str(sid) not in data:
            continue

        # Baseline
        baseline_result = full_evaluate(data, sid, pred_info["sets"])
        if baseline_result is None:
            continue

        # Candidate
        candidate_set = make_symdiff_e4_e5(pred_info)
        modified_sets = list(pred_info["sets"])
        modified_sets[1] = candidate_set
        candidate_result = full_evaluate(data, sid, modified_sets)

        b_best = baseline_result["best"]
        c_best = candidate_result["best"]

        b_s2 = baseline_result["set_bests"][1]
        c_s2 = candidate_result["set_bests"][1]
        s2_baseline_scores.append(b_s2)
        s2_candidate_scores.append(c_s2)

        if c_s2 > b_s2:
            s2_improved += 1
        elif c_s2 < b_s2:
            s2_worsened += 1
        else:
            s2_same += 1

        # System-level 12+ tracking
        if c_best >= 12 and b_best < 12:
            gained_12.append(sid)
        if c_best < 12 and b_best >= 12:
            lost_12.append(sid)
        if c_best >= 13 and b_best < 13:
            gained_13.append(sid)
        if c_best < 13 and b_best >= 13:
            lost_13.append(sid)

        if b_best >= 12:
            baseline_12plus.append(sid)
        if c_best >= 12:
            candidate_12plus.append(sid)

        # SymDiff size
        e4 = pred_info["event4"]
        e5 = pred_info["event5"]
        sd = (e4 | e5) - (e4 & e5)
        symdiff_sizes.append(len(sd))

    print(f"\n  S2-slot comparison (per-set, not system):")
    print(f"    Improved: {s2_improved} series")
    print(f"    Worsened: {s2_worsened} series")
    print(f"    Same:     {s2_same} series")
    print(f"    Baseline S2 avg: {statistics.mean(s2_baseline_scores):.2f}")
    print(f"    Candidate S2 avg: {statistics.mean(s2_candidate_scores):.2f}")

    print(f"\n  System-level 12+ changes:")
    print(f"    Gained 12+: {len(gained_12)} series: {gained_12}")
    print(f"    Lost 12+:   {len(lost_12)} series: {lost_12}")
    print(f"    Net 12+ change: {len(gained_12) - len(lost_12):+d}")

    print(f"\n  System-level 13+ changes:")
    print(f"    Gained 13+: {len(gained_13)} series: {gained_13}")
    print(f"    Lost 13+:   {len(lost_13)} series: {lost_13}")
    print(f"    Net 13+ change: {len(gained_13) - len(lost_13):+d}")

    print(f"\n  SymDiff E4^E5 size distribution:")
    size_dist = Counter(symdiff_sizes)
    for sz in sorted(size_dist.keys()):
        print(f"    {sz} numbers: {size_dist[sz]} series ({100*size_dist[sz]/len(symdiff_sizes):.1f}%)")
    print(f"    Mean size: {statistics.mean(symdiff_sizes):.1f}")

    # L30 and L10 comparison
    l30_b_scores = []
    l30_c_scores = []
    l10_b_scores = []
    l10_c_scores = []
    l30_b_12 = 0
    l30_c_12 = 0
    l10_b_12 = 0
    l10_c_12 = 0

    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        if str(sid) not in data:
            continue

        baseline_result = full_evaluate(data, sid, pred_info["sets"])
        candidate_set = make_symdiff_e4_e5(pred_info)
        modified_sets = list(pred_info["sets"])
        modified_sets[1] = candidate_set
        candidate_result = full_evaluate(data, sid, modified_sets)

        if baseline_result is None or candidate_result is None:
            continue

        if sid >= l30_start:
            l30_b_scores.append(baseline_result["best"])
            l30_c_scores.append(candidate_result["best"])
            if baseline_result["best"] >= 12:
                l30_b_12 += 1
            if candidate_result["best"] >= 12:
                l30_c_12 += 1
        if sid >= l10_start:
            l10_b_scores.append(baseline_result["best"])
            l10_c_scores.append(candidate_result["best"])
            if baseline_result["best"] >= 12:
                l10_b_12 += 1
            if candidate_result["best"] >= 12:
                l10_c_12 += 1

    print(f"\n  L30 comparison (series {l30_start}-{end}):")
    print(f"    Baseline avg: {statistics.mean(l30_b_scores):.2f}, 12+: {l30_b_12}")
    print(f"    Candidate avg: {statistics.mean(l30_c_scores):.2f}, 12+: {l30_c_12}")

    print(f"\n  L10 comparison (series {l10_start}-{end}):")
    print(f"    Baseline avg: {statistics.mean(l10_b_scores):.2f}, 12+: {l10_b_12}")
    print(f"    Candidate avg: {statistics.mean(l10_c_scores):.2f}, 12+: {l10_c_12}")

    # Detail: which series produce the 12+ hits for candidate?
    print(f"\n  All 12+ series with SymDiff E4^E5:")
    for sid in range(start, end + 1):
        try:
            pred_info = predict_production(data, sid)
        except ValueError:
            continue
        if str(sid) not in data:
            continue
        candidate_set = make_symdiff_e4_e5(pred_info)
        modified_sets = list(pred_info["sets"])
        modified_sets[1] = candidate_set
        result = full_evaluate(data, sid, modified_sets)
        if result and result["best"] >= 12:
            winner_idx = result["winner"] - 1
            labels = ["S1(E4)", "S2(SymDiff)", "S3(E6)", "S4(E7)", "S5(E3&E7)", "S6(SymDiff37)", "S7(Quint)"]
            scores_str = " ".join(f"{labels[i]}={result['set_bests'][i]}" for i in range(7))
            in_baseline = "Y" if sid in baseline_12plus else "N"
            print(f"    Series {sid}: {result['best']}/14 by {labels[winner_idx]} | "
                  f"was12+={in_baseline} | {scores_str}")


def main():
    print("S2 Replacement Analysis: E5-based Candidates")
    print("=" * 80)
    print(f"Pool: {TOTAL} numbers, pick {PICK}")
    print(f"Sets: {NUM_SETS}")
    print(f"Using recency-weighted frequency (no look-ahead bias)")

    data = load_data()

    all_sids = sorted(int(s) for s in data.keys())
    start = 2981
    end = all_sids[-1]
    print(f"Series range: {start}-{end} ({end - start + 1} series)")

    # Section 1
    all_results = s2_failure_analysis(data, start, end)

    # Section 2
    e5_potential_analysis(data, start, end)

    # Sections 3 & 4
    backtest_results, baseline = backtest_all_candidates(data, start, end)

    # Section 5
    rank_candidates(backtest_results, baseline)

    # Deep dive on winner
    deep_dive_symdiff_e4_e5(data, start, end)


if __name__ == "__main__":
    main()
