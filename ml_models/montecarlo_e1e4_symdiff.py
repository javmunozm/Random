#!/usr/bin/env python3
"""
Monte Carlo Validation: E1^E4 SymDiff Replacement
==================================================
simulation-testing-expert | 2026-01-29

Tests whether replacing S5 (E3&E7 fusion) or S7 (Quint) with E1^E4 SymDiff
is a statistically significant improvement over the current 7-set strategy.

Methods:
1. Full 200-series backtest (observed statistics)
2. Bootstrap resampling (10,000 iterations) for confidence intervals
3. Permutation test (5,000 iterations) for null-hypothesis p-value
4. Cohen's d effect size
5. L30 window analysis (series 3151-3180)

Key question: Is the reported +4 at 12+ (14->18) real or noise?
"""

import json
import sys
import time
import random
import numpy as np
from pathlib import Path
from collections import Counter

# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load data from JSON."""
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


# ============================================================================
# RECENCY-WEIGHTED FREQUENCY (exact copy from production_predictor.py)
# ============================================================================

def get_recency_freq(data, series_id):
    """
    Get recency-weighted frequency for tiebreaking.
    Only uses data from series BEFORE the target (no look-ahead bias).
    Weights: 3x for L10, 2x for L30, 1x for older.
    """
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


# ============================================================================
# SET CONSTRUCTION FUNCTIONS
# ============================================================================

def build_s1_e4(prior_events, freq):
    """S1: E4 direct copy."""
    return sorted(prior_events[3])


def build_s2_rank16(prior_events, freq):
    """S2: E1-based, top 13 + rank 16."""
    event1 = set(prior_events[0])
    max_freq = max(freq.values()) if freq else 1
    ranked = sorted(range(1, 26),
                    key=lambda n: (-(n in event1), -freq[n] / max_freq, n))
    return sorted(ranked[:13] + [ranked[15]])


def build_s3_e6(prior_events, freq):
    """S3: E6 direct copy."""
    return sorted(prior_events[5])


def build_s4_e7(prior_events, freq):
    """S4: E7 direct copy."""
    return sorted(prior_events[6])


def build_s5_e3e7_fusion(prior_events, freq):
    """S5: E3 & E7 fusion (intersection + fill from union by freq)."""
    event3 = set(prior_events[2])
    event7 = set(prior_events[6])

    e3_e7_int = event3 & event7
    e3_e7_union = event3 | event7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]
    return sorted(s5_numbers[:14])


def build_s6_symdiff_e3e7(prior_events, freq):
    """S6: Symmetric Difference E3 xor E7."""
    event3 = set(prior_events[2])
    event7 = set(prior_events[6])

    sym_diff = (event3 | event7) - (event3 & event7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    return sorted(s6_numbers[:14])


def build_s7_quint(prior_events, freq):
    """S7: Quint E2E3E4E6E7 (5-event consensus)."""
    quint_events = [set(prior_events[1]), set(prior_events[2]),
                    set(prior_events[3]), set(prior_events[5]),
                    set(prior_events[6])]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26),
                          key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    return sorted(quint_ranked[:14])


def build_symdiff_e1e4(prior_events, freq):
    """CANDIDATE: E1 ^ E4 SymDiff (numbers in E1 OR E4 but NOT both)."""
    event1 = set(prior_events[0])
    event4 = set(prior_events[3])

    sym_diff = (event1 | event4) - (event1 & event4)
    sd_numbers = list(sym_diff)

    if len(sd_numbers) < 14:
        # Fill from E1 union E4 highest-freq numbers not already in set
        fill_pool = [n for n in range(1, 26) if n not in sym_diff]
        fill_pool.sort(key=lambda n: -freq.get(n, 0))
        sd_numbers += fill_pool[:14 - len(sd_numbers)]
    elif len(sd_numbers) > 14:
        # Trim by removing lowest-frequency numbers
        sd_numbers.sort(key=lambda n: (-freq.get(n, 0), n))
        sd_numbers = sd_numbers[:14]

    return sorted(sd_numbers[:14])


# ============================================================================
# STRATEGY BUILDERS
# ============================================================================

def build_baseline_sets(prior_events, freq):
    """Build the current 7-set strategy (BASELINE)."""
    return [
        build_s1_e4(prior_events, freq),        # S1
        build_s2_rank16(prior_events, freq),     # S2
        build_s3_e6(prior_events, freq),         # S3
        build_s4_e7(prior_events, freq),         # S4
        build_s5_e3e7_fusion(prior_events, freq),# S5
        build_s6_symdiff_e3e7(prior_events, freq),# S6
        build_s7_quint(prior_events, freq),      # S7
    ]


def build_candidate1_sets(prior_events, freq):
    """CANDIDATE 1: Replace S5 (E3&E7 fusion) with E1^E4 SymDiff."""
    return [
        build_s1_e4(prior_events, freq),        # S1
        build_s2_rank16(prior_events, freq),     # S2
        build_s3_e6(prior_events, freq),         # S3
        build_s4_e7(prior_events, freq),         # S4
        build_symdiff_e1e4(prior_events, freq),  # S5 REPLACED
        build_s6_symdiff_e3e7(prior_events, freq),# S6
        build_s7_quint(prior_events, freq),      # S7
    ]


def build_candidate2_sets(prior_events, freq):
    """CANDIDATE 2: Replace S7 (Quint) with E1^E4 SymDiff."""
    return [
        build_s1_e4(prior_events, freq),        # S1
        build_s2_rank16(prior_events, freq),     # S2
        build_s3_e6(prior_events, freq),         # S3
        build_s4_e7(prior_events, freq),         # S4
        build_s5_e3e7_fusion(prior_events, freq),# S5
        build_s6_symdiff_e3e7(prior_events, freq),# S6
        build_symdiff_e1e4(prior_events, freq),  # S7 REPLACED
    ]


# ============================================================================
# SCORING
# ============================================================================

def score_series(prediction_sets, actual_events):
    """
    Score: best match across all sets x all events.
    Returns (best_score, per_set_bests).
    """
    set_bests = []
    for s in prediction_sets:
        s_set = set(s)
        matches = [len(s_set & set(e)) for e in actual_events]
        set_bests.append(max(matches))
    return max(set_bests), set_bests


# ============================================================================
# FULL BACKTEST
# ============================================================================

def run_backtest(data, strategy_builder, start=2981, end=3180):
    """
    Run full backtest for a strategy.
    Returns list of (series_id, best_score, per_set_bests) tuples.
    """
    results = []
    for sid in range(start, end + 1):
        prior_key = str(sid - 1)
        current_key = str(sid)
        if prior_key not in data or current_key not in data:
            continue

        prior_events = data[prior_key]
        actual_events = data[current_key]
        freq = get_recency_freq(data, sid)

        prediction_sets = strategy_builder(prior_events, freq)
        best, set_bests = score_series(prediction_sets, actual_events)
        results.append((sid, best, set_bests))

    return results


def compute_metrics(results):
    """Compute summary metrics from backtest results."""
    scores = [r[1] for r in results]
    n = len(scores)
    return {
        "n": n,
        "avg": np.mean(scores),
        "std": np.std(scores, ddof=1),
        "best": max(scores),
        "worst": min(scores),
        "at_11": sum(1 for s in scores if s >= 11),
        "at_12": sum(1 for s in scores if s >= 12),
        "at_13": sum(1 for s in scores if s >= 13),
        "at_14": sum(1 for s in scores if s == 14),
    }


def compute_metrics_from_scores(scores):
    """Compute metrics from a list of scores."""
    n = len(scores)
    return {
        "n": n,
        "avg": np.mean(scores),
        "std": np.std(scores, ddof=1),
        "at_11": sum(1 for s in scores if s >= 11),
        "at_12": sum(1 for s in scores if s >= 12),
        "at_13": sum(1 for s in scores if s >= 13),
        "at_14": sum(1 for s in scores if s == 14),
    }


# ============================================================================
# BOOTSTRAP MONTE CARLO
# ============================================================================

def bootstrap_test(baseline_scores, candidate_scores, n_iter=10000, seed=42):
    """
    Bootstrap resampling test.
    Resample 200 series WITH replacement, compute metrics for both,
    record differences.
    """
    rng = np.random.RandomState(seed)
    n = len(baseline_scores)
    assert len(candidate_scores) == n

    baseline_arr = np.array(baseline_scores)
    candidate_arr = np.array(candidate_scores)

    diffs_avg = []
    diffs_12 = []
    diffs_13 = []
    diffs_11 = []

    for _ in range(n_iter):
        idx = rng.randint(0, n, size=n)
        b_sample = baseline_arr[idx]
        c_sample = candidate_arr[idx]

        b_avg = np.mean(b_sample)
        c_avg = np.mean(c_sample)
        diffs_avg.append(c_avg - b_avg)

        b_11 = np.sum(b_sample >= 11)
        c_11 = np.sum(c_sample >= 11)
        diffs_11.append(c_11 - b_11)

        b_12 = np.sum(b_sample >= 12)
        c_12 = np.sum(c_sample >= 12)
        diffs_12.append(c_12 - b_12)

        b_13 = np.sum(b_sample >= 13)
        c_13 = np.sum(c_sample >= 13)
        diffs_13.append(c_13 - b_13)

    diffs_avg = np.array(diffs_avg)
    diffs_11 = np.array(diffs_11)
    diffs_12 = np.array(diffs_12)
    diffs_13 = np.array(diffs_13)

    def summarize(diffs, label):
        ci_lo = np.percentile(diffs, 2.5)
        ci_hi = np.percentile(diffs, 97.5)
        mean_diff = np.mean(diffs)
        # P-value: proportion of samples where candidate is WORSE or equal
        p_worse = np.mean(diffs <= 0)
        return {
            "label": label,
            "mean": mean_diff,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "p_worse_or_equal": p_worse,
        }

    return {
        "avg": summarize(diffs_avg, "Average Score"),
        "at_11": summarize(diffs_11, "11+ Count"),
        "at_12": summarize(diffs_12, "12+ Count"),
        "at_13": summarize(diffs_13, "13+ Count"),
        "raw_diffs_avg": diffs_avg,
        "raw_diffs_12": diffs_12,
    }


# ============================================================================
# PERMUTATION TEST
# ============================================================================

def permutation_test(baseline_scores, candidate_scores, n_iter=5000, seed=123):
    """
    Permutation test: under H0 (no difference), randomly swap each series's
    scores between baseline and candidate.
    Returns p-value for each metric.
    """
    rng = np.random.RandomState(seed)
    n = len(baseline_scores)
    baseline_arr = np.array(baseline_scores)
    candidate_arr = np.array(candidate_scores)

    # Observed differences
    obs_diff_avg = np.mean(candidate_arr) - np.mean(baseline_arr)
    obs_diff_12 = np.sum(candidate_arr >= 12) - np.sum(baseline_arr >= 12)
    obs_diff_13 = np.sum(candidate_arr >= 13) - np.sum(baseline_arr >= 13)
    obs_diff_11 = np.sum(candidate_arr >= 11) - np.sum(baseline_arr >= 11)

    count_avg = 0
    count_12 = 0
    count_13 = 0
    count_11 = 0

    for _ in range(n_iter):
        # Randomly swap each pair with 50% probability
        swap = rng.random(n) > 0.5
        perm_b = np.where(swap, candidate_arr, baseline_arr)
        perm_c = np.where(swap, baseline_arr, candidate_arr)

        d_avg = np.mean(perm_c) - np.mean(perm_b)
        d_12 = np.sum(perm_c >= 12) - np.sum(perm_b >= 12)
        d_13 = np.sum(perm_c >= 13) - np.sum(perm_b >= 13)
        d_11 = np.sum(perm_c >= 11) - np.sum(perm_b >= 11)

        if d_avg >= obs_diff_avg:
            count_avg += 1
        if d_12 >= obs_diff_12:
            count_12 += 1
        if d_13 >= obs_diff_13:
            count_13 += 1
        if d_11 >= obs_diff_11:
            count_11 += 1

    return {
        "avg": {"observed": obs_diff_avg, "p_value": count_avg / n_iter},
        "at_11": {"observed": obs_diff_11, "p_value": count_11 / n_iter},
        "at_12": {"observed": obs_diff_12, "p_value": count_12 / n_iter},
        "at_13": {"observed": obs_diff_13, "p_value": count_13 / n_iter},
    }


# ============================================================================
# EFFECT SIZE
# ============================================================================

def cohens_d(baseline_scores, candidate_scores):
    """Cohen's d effect size for paired samples."""
    b = np.array(baseline_scores, dtype=float)
    c = np.array(candidate_scores, dtype=float)
    diff = c - b
    d = np.mean(diff) / np.std(diff, ddof=1) if np.std(diff, ddof=1) > 0 else 0
    return d


# ============================================================================
# PER-SERIES COMPARISON
# ============================================================================

def series_level_comparison(baseline_results, candidate_results):
    """Compare at series level: how many improved, same, degraded."""
    improved = 0
    same = 0
    degraded = 0
    flip_details = {"improved": [], "degraded": []}

    for (sid_b, score_b, _), (sid_c, score_c, _) in zip(baseline_results, candidate_results):
        assert sid_b == sid_c
        if score_c > score_b:
            improved += 1
            flip_details["improved"].append((sid_b, score_b, score_c))
        elif score_c < score_b:
            degraded += 1
            flip_details["degraded"].append((sid_b, score_b, score_c))
        else:
            same += 1

    return improved, same, degraded, flip_details


# ============================================================================
# OVERLAP ANALYSIS
# ============================================================================

def overlap_analysis(data, start=2981, end=3180):
    """Analyze how much E1^E4 SymDiff overlaps with existing sets."""
    overlaps = {f"S{i+1}": [] for i in range(7)}
    overlaps["E1E4_SD"] = []  # self-check sizes

    for sid in range(start, end + 1):
        prior_key = str(sid - 1)
        if prior_key not in data:
            continue

        prior_events = data[prior_key]
        freq = get_recency_freq(data, sid)

        baseline = build_baseline_sets(prior_events, freq)
        e1e4_sd = set(build_symdiff_e1e4(prior_events, freq))
        overlaps["E1E4_SD"].append(len(e1e4_sd))

        for i, s in enumerate(baseline):
            overlaps[f"S{i+1}"].append(len(e1e4_sd & set(s)))

    result = {}
    for key, vals in overlaps.items():
        result[key] = {
            "mean": np.mean(vals),
            "min": min(vals),
            "max": max(vals),
        }
    return result


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 78)
    print("MONTE CARLO VALIDATION: E1^E4 SymDiff Replacement")
    print("simulation-testing-expert | 2026-01-29")
    print("=" * 78)

    data = load_data()
    print(f"\nData loaded: {len(data)} series")

    # ---- STEP 1: Full backtest ----
    print("\n" + "-" * 78)
    print("STEP 1: Full Backtest (200 series, 2981-3180)")
    print("-" * 78)

    t0 = time.time()
    baseline_results = run_backtest(data, build_baseline_sets)
    t1 = time.time()
    print(f"  Baseline computed in {t1-t0:.1f}s")

    cand1_results = run_backtest(data, build_candidate1_sets)
    t2 = time.time()
    print(f"  Candidate 1 (replace S5) computed in {t2-t1:.1f}s")

    cand2_results = run_backtest(data, build_candidate2_sets)
    t3 = time.time()
    print(f"  Candidate 2 (replace S7) computed in {t3-t2:.1f}s")

    baseline_metrics = compute_metrics(baseline_results)
    cand1_metrics = compute_metrics(cand1_results)
    cand2_metrics = compute_metrics(cand2_results)

    baseline_scores = [r[1] for r in baseline_results]
    cand1_scores = [r[1] for r in cand1_results]
    cand2_scores = [r[1] for r in cand2_results]

    print(f"\n  {'Metric':<12} {'Baseline':>10} {'Cand1(S5)':>10} {'Diff1':>8} {'Cand2(S7)':>10} {'Diff2':>8}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*8} {'-'*10} {'-'*8}")
    for key, label in [("avg", "Average"), ("at_11", "11+"),
                       ("at_12", "12+"), ("at_13", "13+"), ("at_14", "14/14")]:
        b = baseline_metrics[key]
        c1 = cand1_metrics[key]
        c2 = cand2_metrics[key]
        if key == "avg":
            print(f"  {label:<12} {b:>10.2f} {c1:>10.2f} {c1-b:>+8.2f} {c2:>10.2f} {c2-b:>+8.2f}")
        else:
            print(f"  {label:<12} {b:>10d} {c1:>10d} {c1-b:>+8d} {c2:>10d} {c2-b:>+8d}")

    # Score distributions
    print(f"\n  Score Distribution:")
    for score in range(8, 15):
        b_ct = sum(1 for s in baseline_scores if s == score)
        c1_ct = sum(1 for s in cand1_scores if s == score)
        c2_ct = sum(1 for s in cand2_scores if s == score)
        if b_ct > 0 or c1_ct > 0 or c2_ct > 0:
            print(f"    {score:>2}/14: Baseline={b_ct:>3}  Cand1={c1_ct:>3}  Cand2={c2_ct:>3}")

    # ---- STEP 2: Series-level comparison ----
    print(f"\n" + "-" * 78)
    print("STEP 2: Series-Level Comparison")
    print("-" * 78)

    for label, cand_results in [("Candidate 1 (replace S5)", cand1_results),
                                ("Candidate 2 (replace S7)", cand2_results)]:
        improved, same, degraded, flip_details = series_level_comparison(
            baseline_results, cand_results)
        print(f"\n  {label}:")
        print(f"    Improved: {improved} series")
        print(f"    Same:     {same} series")
        print(f"    Degraded: {degraded} series")
        if flip_details["improved"]:
            print(f"    Improved series: ", end="")
            for sid, sb, sc in flip_details["improved"][:10]:
                print(f"{sid}({sb}->{sc})", end=" ")
            if len(flip_details["improved"]) > 10:
                print(f"... +{len(flip_details['improved'])-10} more")
            else:
                print()
        if flip_details["degraded"]:
            print(f"    Degraded series: ", end="")
            for sid, sb, sc in flip_details["degraded"][:10]:
                print(f"{sid}({sb}->{sc})", end=" ")
            if len(flip_details["degraded"]) > 10:
                print(f"... +{len(flip_details['degraded'])-10} more")
            else:
                print()

    # ---- STEP 3: L30 Analysis ----
    print(f"\n" + "-" * 78)
    print("STEP 3: L30 Window Analysis (series 3151-3180)")
    print("-" * 78)

    l30_baseline = [r for r in baseline_results if r[0] >= 3151]
    l30_cand1 = [r for r in cand1_results if r[0] >= 3151]
    l30_cand2 = [r for r in cand2_results if r[0] >= 3151]

    l30_b_scores = [r[1] for r in l30_baseline]
    l30_c1_scores = [r[1] for r in l30_cand1]
    l30_c2_scores = [r[1] for r in l30_cand2]

    l30_b = compute_metrics_from_scores(l30_b_scores)
    l30_c1 = compute_metrics_from_scores(l30_c1_scores)
    l30_c2 = compute_metrics_from_scores(l30_c2_scores)

    print(f"\n  {'Metric':<12} {'Baseline':>10} {'Cand1(S5)':>10} {'Diff1':>8} {'Cand2(S7)':>10} {'Diff2':>8}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*8} {'-'*10} {'-'*8}")
    for key, label in [("avg", "Average"), ("at_11", "11+"),
                       ("at_12", "12+"), ("at_13", "13+")]:
        b = l30_b[key]
        c1 = l30_c1[key]
        c2 = l30_c2[key]
        if key == "avg":
            print(f"  {label:<12} {b:>10.2f} {c1:>10.2f} {c1-b:>+8.2f} {c2:>10.2f} {c2-b:>+8.2f}")
        else:
            print(f"  {label:<12} {b:>10d} {c1:>10d} {c1-b:>+8d} {c2:>10d} {c2-b:>+8d}")

    # ---- STEP 4: Rolling window stability ----
    print(f"\n" + "-" * 78)
    print("STEP 4: Rolling Window Stability (50-series windows)")
    print("-" * 78)

    windows = [
        ("W1: 2981-3030", 2981, 3030),
        ("W2: 3031-3080", 3031, 3080),
        ("W3: 3081-3130", 3081, 3130),
        ("W4: 3131-3180", 3131, 3180),
    ]

    print(f"\n  {'Window':<18} {'B avg':>7} {'C1 avg':>7} {'Diff':>7} | {'B 12+':>5} {'C1 12+':>6} {'Diff':>5}")
    print(f"  {'-'*18} {'-'*7} {'-'*7} {'-'*7} | {'-'*5} {'-'*6} {'-'*5}")

    for wname, ws, we in windows:
        w_b = [r[1] for r in baseline_results if ws <= r[0] <= we]
        w_c1 = [r[1] for r in cand1_results if ws <= r[0] <= we]
        b_avg = np.mean(w_b) if w_b else 0
        c1_avg = np.mean(w_c1) if w_c1 else 0
        b_12 = sum(1 for s in w_b if s >= 12)
        c1_12 = sum(1 for s in w_c1 if s >= 12)
        print(f"  {wname:<18} {b_avg:>7.2f} {c1_avg:>7.2f} {c1_avg-b_avg:>+7.2f} | {b_12:>5d} {c1_12:>6d} {c1_12-b_12:>+5d}")

    # ---- STEP 5: Overlap analysis ----
    print(f"\n" + "-" * 78)
    print("STEP 5: Overlap Analysis (E1^E4 SymDiff vs existing sets)")
    print("-" * 78)

    overlap = overlap_analysis(data)
    print(f"\n  E1^E4 SymDiff size: avg={overlap['E1E4_SD']['mean']:.1f}, "
          f"min={overlap['E1E4_SD']['min']}, max={overlap['E1E4_SD']['max']}")
    print(f"\n  {'Overlap with':<15} {'Mean':>6} {'Min':>5} {'Max':>5}")
    print(f"  {'-'*15} {'-'*6} {'-'*5} {'-'*5}")
    for i in range(7):
        key = f"S{i+1}"
        labels = ["S1(E4)", "S2(rank16)", "S3(E6)", "S4(E7)",
                  "S5(E3&E7)", "S6(SD_E3E7)", "S7(Quint)"]
        o = overlap[key]
        print(f"  {labels[i]:<15} {o['mean']:>6.1f} {o['min']:>5d} {o['max']:>5d}")

    # ---- STEP 6: Bootstrap Monte Carlo ----
    print(f"\n" + "-" * 78)
    print("STEP 6: Bootstrap Monte Carlo (10,000 iterations)")
    print("-" * 78)

    for label, cand_scores in [("CANDIDATE 1 (replace S5 with E1^E4 SD)", cand1_scores),
                                ("CANDIDATE 2 (replace S7 with E1^E4 SD)", cand2_scores)]:
        print(f"\n  --- {label} ---")
        t0 = time.time()
        boot = bootstrap_test(baseline_scores, cand_scores, n_iter=10000)
        t1 = time.time()
        print(f"  Computed in {t1-t0:.1f}s")

        print(f"\n  {'Metric':<15} {'Mean Diff':>10} {'95% CI Lo':>10} {'95% CI Hi':>10} {'P(worse)':>10}")
        print(f"  {'-'*15} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
        for key in ["avg", "at_11", "at_12", "at_13"]:
            r = boot[key]
            if key == "avg":
                print(f"  {r['label']:<15} {r['mean']:>+10.4f} {r['ci_lo']:>+10.4f} {r['ci_hi']:>+10.4f} {r['p_worse_or_equal']:>10.4f}")
            else:
                print(f"  {r['label']:<15} {r['mean']:>+10.2f} {r['ci_lo']:>+10.1f} {r['ci_hi']:>+10.1f} {r['p_worse_or_equal']:>10.4f}")

        # Cohen's d
        d = cohens_d(baseline_scores, cand_scores)
        print(f"\n  Cohen's d: {d:+.4f}", end="")
        if abs(d) < 0.2:
            print(" (negligible)")
        elif abs(d) < 0.5:
            print(" (small)")
        elif abs(d) < 0.8:
            print(" (medium)")
        else:
            print(" (large)")

    # ---- STEP 7: Permutation Test ----
    print(f"\n" + "-" * 78)
    print("STEP 7: Permutation Test (5,000 iterations)")
    print("-" * 78)

    for label, cand_scores_p in [("CANDIDATE 1 (replace S5)", cand1_scores),
                                  ("CANDIDATE 2 (replace S7)", cand2_scores)]:
        print(f"\n  --- {label} ---")
        t0 = time.time()
        perm = permutation_test(baseline_scores, cand_scores_p, n_iter=5000)
        t1 = time.time()
        print(f"  Computed in {t1-t0:.1f}s")

        print(f"\n  {'Metric':<15} {'Observed':>10} {'P-value':>10} {'Significant':>12}")
        print(f"  {'-'*15} {'-'*10} {'-'*10} {'-'*12}")
        for key, label_m in [("avg", "Average"), ("at_11", "11+"),
                             ("at_12", "12+"), ("at_13", "13+")]:
            r = perm[key]
            sig = "YES" if r["p_value"] < 0.05 else "NO"
            if key == "avg":
                print(f"  {label_m:<15} {r['observed']:>+10.4f} {r['p_value']:>10.4f} {sig:>12}")
            else:
                print(f"  {label_m:<15} {r['observed']:>+10d} {r['p_value']:>10.4f} {sig:>12}")

    # ---- STEP 8: Per-set contribution ----
    print(f"\n" + "-" * 78)
    print("STEP 8: Per-Set Win Contribution Analysis")
    print("-" * 78)

    def count_wins(results):
        wins = [0] * 7
        for sid, best, set_bests in results:
            winner_idx = set_bests.index(max(set_bests))
            wins[winner_idx] += 1
        return wins

    b_wins = count_wins(baseline_results)
    c1_wins = count_wins(cand1_results)
    c2_wins = count_wins(cand2_results)

    labels = ["S1(E4)", "S2(rank16)", "S3(E6)", "S4(E7)",
              "S5/E1E4SD", "S6(SD_E3E7)", "S7/E1E4SD"]

    print(f"\n  {'Set':<14} {'Baseline':>9} {'Cand1':>7} {'Diff1':>7} {'Cand2':>7} {'Diff2':>7}")
    print(f"  {'-'*14} {'-'*9} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")

    b_labels = ["S1(E4)", "S2(rank16)", "S3(E6)", "S4(E7)",
                "S5(E3&E7)", "S6(SD_E3E7)", "S7(Quint)"]
    c1_labels = ["S1(E4)", "S2(rank16)", "S3(E6)", "S4(E7)",
                 "*E1E4_SD*", "S6(SD_E3E7)", "S7(Quint)"]
    c2_labels = ["S1(E4)", "S2(rank16)", "S3(E6)", "S4(E7)",
                 "S5(E3&E7)", "S6(SD_E3E7)", "*E1E4_SD*"]

    for i in range(7):
        lbl = b_labels[i]
        if i == 4:
            lbl = "S5 slot"
        elif i == 6:
            lbl = "S7 slot"
        print(f"  {lbl:<14} {b_wins[i]:>9} {c1_wins[i]:>7} {c1_wins[i]-b_wins[i]:>+7} {c2_wins[i]:>7} {c2_wins[i]-b_wins[i]:>+7}")

    # ---- STEP 9: Unique contribution analysis ----
    print(f"\n" + "-" * 78)
    print("STEP 9: Unique Contribution - Series where E1^E4 SD is the SOLE winner")
    print("-" * 78)

    for label, cand_results, slot_idx in [
        ("Candidate 1 (S5 slot)", cand1_results, 4),
        ("Candidate 2 (S7 slot)", cand2_results, 6)]:

        sole_winner_series = []
        for (sid_b, score_b, sb_bests), (sid_c, score_c, sc_bests) in zip(
                baseline_results, cand_results):
            # E1E4_SD is the sole winner if it has the best score AND
            # no other set matches that score
            if score_c > score_b:
                # The improvement came from the new set
                if sc_bests[slot_idx] == score_c:
                    # Check if E1E4_SD is the only one at this score
                    others_at_max = sum(1 for j, s in enumerate(sc_bests)
                                        if j != slot_idx and s == score_c)
                    sole_winner_series.append(
                        (sid_c, score_b, score_c, others_at_max))

        print(f"\n  {label}:")
        print(f"  Series where E1^E4 SD uniquely improved the best score: {len(sole_winner_series)}")
        for sid, sb, sc, others in sole_winner_series:
            co_winners = f"(+{others} ties)" if others > 0 else "(sole)"
            print(f"    Series {sid}: {sb} -> {sc} {co_winners}")

    # ---- FINAL VERDICT ----
    print(f"\n" + "=" * 78)
    print("FINAL VERDICT")
    print("=" * 78)

    obs_diff_avg_c1 = cand1_metrics["avg"] - baseline_metrics["avg"]
    obs_diff_12_c1 = cand1_metrics["at_12"] - baseline_metrics["at_12"]

    # Run quick bootstrap for p-values to use in verdict
    boot_c1 = bootstrap_test(baseline_scores, cand1_scores, n_iter=10000)
    perm_c1 = permutation_test(baseline_scores, cand1_scores, n_iter=5000)

    print(f"""
  CANDIDATE 1: Replace S5 (E3&E7 fusion) with E1^E4 SymDiff
  -----------------------------------------------------------
  Observed avg difference:  {obs_diff_avg_c1:+.4f}
  Observed 12+ difference:  {obs_diff_12_c1:+d}
  Bootstrap 95% CI (avg):   [{boot_c1['avg']['ci_lo']:+.4f}, {boot_c1['avg']['ci_hi']:+.4f}]
  Bootstrap 95% CI (12+):   [{boot_c1['at_12']['ci_lo']:+.1f}, {boot_c1['at_12']['ci_hi']:+.1f}]
  Bootstrap P(worse|equal): {boot_c1['avg']['p_worse_or_equal']:.4f} (avg), {boot_c1['at_12']['p_worse_or_equal']:.4f} (12+)
  Permutation P-value:      {perm_c1['avg']['p_value']:.4f} (avg), {perm_c1['at_12']['p_value']:.4f} (12+)
  Cohen's d:                {cohens_d(baseline_scores, cand1_scores):+.4f}
""")

    obs_diff_avg_c2 = cand2_metrics["avg"] - baseline_metrics["avg"]
    obs_diff_12_c2 = cand2_metrics["at_12"] - baseline_metrics["at_12"]

    boot_c2 = bootstrap_test(baseline_scores, cand2_scores, n_iter=10000)
    perm_c2 = permutation_test(baseline_scores, cand2_scores, n_iter=5000)

    print(f"""
  CANDIDATE 2: Replace S7 (Quint) with E1^E4 SymDiff
  -----------------------------------------------------------
  Observed avg difference:  {obs_diff_avg_c2:+.4f}
  Observed 12+ difference:  {obs_diff_12_c2:+d}
  Bootstrap 95% CI (avg):   [{boot_c2['avg']['ci_lo']:+.4f}, {boot_c2['avg']['ci_hi']:+.4f}]
  Bootstrap 95% CI (12+):   [{boot_c2['at_12']['ci_lo']:+.1f}, {boot_c2['at_12']['ci_hi']:+.1f}]
  Bootstrap P(worse|equal): {boot_c2['avg']['p_worse_or_equal']:.4f} (avg), {boot_c2['at_12']['p_worse_or_equal']:.4f} (12+)
  Permutation P-value:      {perm_c2['avg']['p_value']:.4f} (avg), {perm_c2['at_12']['p_value']:.4f} (12+)
  Cohen's d:                {cohens_d(baseline_scores, cand2_scores):+.4f}
""")

    # Decision logic
    sig_threshold = 0.05
    c1_avg_sig = perm_c1['avg']['p_value'] < sig_threshold
    c1_12_sig = perm_c1['at_12']['p_value'] < sig_threshold
    c2_avg_sig = perm_c2['avg']['p_value'] < sig_threshold
    c2_12_sig = perm_c2['at_12']['p_value'] < sig_threshold

    c1_direction = obs_diff_avg_c1 > 0
    c2_direction = obs_diff_avg_c2 > 0

    print("  DECISION:")
    print()

    for label, avg_sig, t12_sig, direction, diff_avg, diff_12 in [
        ("Candidate 1 (replace S5)", c1_avg_sig, c1_12_sig, c1_direction, obs_diff_avg_c1, obs_diff_12_c1),
        ("Candidate 2 (replace S7)", c2_avg_sig, c2_12_sig, c2_direction, obs_diff_avg_c2, obs_diff_12_c2)]:

        if avg_sig and direction:
            verdict = "RECOMMEND (statistically significant improvement)"
        elif t12_sig and diff_12 > 0:
            verdict = "RECOMMEND (significant 12+ improvement)"
        elif direction and diff_12 > 0:
            verdict = "WEAK RECOMMEND (positive direction, not significant)"
        elif not direction:
            verdict = "REJECT (negative direction)"
        else:
            verdict = "REJECT (no significant improvement)"

        print(f"  {label}: {verdict}")

    print(f"\n  NOTE: Statistical significance threshold: p < {sig_threshold}")
    print(f"  With 200 series, detecting a +4 at 12+ (7% to 9%) requires")
    print(f"  much larger samples for statistical power. The test is underpowered")
    print(f"  for rare-event differences at this sample size.")


if __name__ == "__main__":
    main()
