#!/usr/bin/env python3
"""
S2 Replacement Monte Carlo Validation
======================================
Full statistical validation of 3 S2 replacement candidates vs baseline.

Candidates (all replace S2, S1/S3-S7 identical):
  1. BASELINE: S2 = E1 rank16 (top 13 + rank 16)
  2. SymDiff E4^E5: (E4 | E5) - (E4 & E5), fill/trim by recency freq
  3. Quint E1E3E4E5E7: 5-event consensus, top 14 by count then freq tiebreak
  4. E1&E5 Fusion: Intersection then union fill by freq

Tests performed:
  - Full 200-series backtest (2981-3180)
  - Bootstrap 10,000 iterations (95% CI)
  - Permutation test 5,000 iterations (p-values)
  - Cohen's d effect sizes
  - Series-level comparison (improved/same/degraded)
  - 12+ detail analysis (gained/lost series)
  - S7 safety check (preserve all S7 12+ contributions)
  - Rolling window stability (50-series windows)
  - L30 check (3151-3180)
  - Unique coverage analysis

Author: simulation-testing-expert
Date: 2026-01-30
"""

import json
import sys
import math
import random
from pathlib import Path
from collections import Counter
from datetime import datetime

# ============================================================================
# CONSTANTS
# ============================================================================
TOTAL = 25
PICK = 14
NUM_SETS = 7
START = 2981
END = 3180
N_BOOTSTRAP = 10_000
N_PERMUTATION = 5_000
RANDOM_SEED = 42

# ============================================================================
# DATA LOADING
# ============================================================================
def load_data():
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
    Weights: 3x for L10, 2x for L30, 1x for older series.
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
# SET BUILDERS -- S1, S3-S7 are IDENTICAL across all candidates
# ============================================================================
def build_common_sets(data, series_id, freq):
    """Build S1, S3, S4, S5, S6, S7 -- identical for all candidates."""
    prior = str(series_id - 1)
    prior_events = data[prior]

    event1 = set(prior_events[0])
    event2 = set(prior_events[1])
    event3 = set(prior_events[2])
    event4 = set(prior_events[3])
    event6 = set(prior_events[5])
    event7 = set(prior_events[6])

    # S1: E4 direct
    s1 = sorted(event4)

    # S3: E6 direct
    s3 = sorted(event6)

    # S4: E7 direct
    s4 = sorted(event7)

    # S5: E3&E7 fusion
    e3_e7_int = event3 & event7
    e3_e7_union = event3 | event7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]
    s5 = sorted(s5_numbers[:14])

    # S6: SymDiff E3^E7
    sym_diff = (event3 | event7) - (event3 & event7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6 = sorted(s6_numbers[:14])

    # S7: Quint E2E3E4E6E7
    quint_events = [event2, event3, event4, event6, event7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26),
                          key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    s7 = sorted(quint_ranked[:14])

    return s1, s3, s4, s5, s6, s7


# ============================================================================
# S2 CANDIDATE BUILDERS
# ============================================================================
def build_s2_baseline(data, series_id, freq):
    """BASELINE: E1 rank16 -- top 13 of E1-ranked + rank 16."""
    prior = str(series_id - 1)
    event1 = set(data[prior][0])
    max_freq = max(freq.values()) if freq else 1
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event1), -freq[n] / max_freq, n))
    return sorted(ranked[:13] + [ranked[15]])


def build_s2_symdiff_e4e5(data, series_id, freq):
    """SymDiff E4^E5: (E4 | E5) - (E4 & E5), fill/trim by recency freq."""
    prior = str(series_id - 1)
    event4 = set(data[prior][3])
    event5 = set(data[prior][4])
    sym_diff = (event4 | event5) - (event4 & event5)
    sd_numbers = list(sym_diff)
    if len(sd_numbers) < 14:
        fill = [n for n in range(1, 26) if n not in sd_numbers]
        fill.sort(key=lambda n: -freq.get(n, 0))
        sd_numbers += fill[:14 - len(sd_numbers)]
    elif len(sd_numbers) > 14:
        sd_numbers.sort(key=lambda n: (-freq.get(n, 0), n))
        sd_numbers = sd_numbers[:14]
    return sorted(sd_numbers[:14])


def build_s2_quint_e1e3e4e5e7(data, series_id, freq):
    """Quint E1E3E4E5E7: 5-event consensus, top 14."""
    prior = str(series_id - 1)
    events = [set(data[prior][0]), set(data[prior][2]), set(data[prior][3]),
              set(data[prior][4]), set(data[prior][6])]
    counts = Counter(n for e in events for n in e)
    ranked = sorted(range(1, 26), key=lambda n: (-counts[n], -freq.get(n, 0), n))
    return sorted(ranked[:14])


def build_s2_e1e5_fusion(data, series_id, freq):
    """E1&E5 Fusion: intersection + union fill by freq."""
    prior = str(series_id - 1)
    event1 = set(data[prior][0])
    event5 = set(data[prior][4])
    intersection = event1 & event5
    union = event1 | event5
    remaining = sorted(union - intersection, key=lambda n: -freq[n])
    numbers = list(intersection) + remaining[:14 - len(intersection)]
    return sorted(numbers[:14])


# ============================================================================
# FULL EVALUATION ENGINE
# ============================================================================
def evaluate_series(data, series_id, sets_7):
    """Evaluate 7 sets against all 7 events. Returns per-set best matches."""
    sid = str(series_id)
    if sid not in data:
        return None
    events = data[sid]
    set_bests = []
    set_best_events = []
    for s in sets_7:
        matches = [len(set(s) & set(e)) for e in events]
        best_m = max(matches)
        best_e = matches.index(best_m)
        set_bests.append(best_m)
        set_best_events.append(best_e)
    overall_best = max(set_bests)
    winner = set_bests.index(overall_best)
    return {
        "series": series_id,
        "set_bests": set_bests,
        "set_best_events": set_best_events,
        "best": overall_best,
        "winner": winner,
    }


def run_backtest(data, s2_builder, start=START, end=END):
    """Run full backtest for a given S2 builder across [start, end]."""
    results = []
    for sid in range(start, end + 1):
        prior = str(sid - 1)
        if prior not in data or str(sid) not in data:
            continue
        freq = get_recency_freq(data, sid)
        s1, s3, s4, s5, s6, s7 = build_common_sets(data, sid, freq)
        s2 = s2_builder(data, sid, freq)
        sets_7 = [s1, s2, s3, s4, s5, s6, s7]
        r = evaluate_series(data, sid, sets_7)
        if r:
            r["s2_set"] = s2
            results.append(r)
    return results


# ============================================================================
# METRICS COMPUTATION
# ============================================================================
def compute_metrics(results):
    """Compute standard metrics from results."""
    n = len(results)
    bests = [r["best"] for r in results]
    wins = [0] * NUM_SETS
    for r in results:
        wins[r["winner"]] += 1

    return {
        "n": n,
        "avg": sum(bests) / n if n else 0,
        "best": max(bests) if bests else 0,
        "worst": min(bests) if bests else 0,
        "at_11": sum(1 for b in bests if b >= 11),
        "at_12": sum(1 for b in bests if b >= 12),
        "at_13": sum(1 for b in bests if b >= 13),
        "at_14": sum(1 for b in bests if b == 14),
        "wins": wins,
        "bests": bests,
    }


# ============================================================================
# BOOTSTRAP CONFIDENCE INTERVALS
# ============================================================================
def bootstrap_ci(baseline_bests, candidate_bests, n_iter=N_BOOTSTRAP, seed=RANDOM_SEED):
    """Bootstrap 95% CI on differences: avg, 12+, 13+."""
    rng = random.Random(seed)
    n = len(baseline_bests)
    assert n == len(candidate_bests)

    diffs_avg = []
    diffs_12 = []
    diffs_13 = []

    for _ in range(n_iter):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        b_sample = [baseline_bests[i] for i in idx]
        c_sample = [candidate_bests[i] for i in idx]

        b_avg = sum(b_sample) / n
        c_avg = sum(c_sample) / n
        diffs_avg.append(c_avg - b_avg)

        b_12 = sum(1 for x in b_sample if x >= 12)
        c_12 = sum(1 for x in c_sample if x >= 12)
        diffs_12.append(c_12 - b_12)

        b_13 = sum(1 for x in b_sample if x >= 13)
        c_13 = sum(1 for x in c_sample if x >= 13)
        diffs_13.append(c_13 - b_13)

    def ci_95(vals):
        s = sorted(vals)
        lo = s[int(0.025 * len(s))]
        hi = s[int(0.975 * len(s))]
        mean = sum(vals) / len(vals)
        return mean, lo, hi

    return {
        "avg": ci_95(diffs_avg),
        "12+": ci_95(diffs_12),
        "13+": ci_95(diffs_13),
    }


# ============================================================================
# PERMUTATION TEST
# ============================================================================
def permutation_test(baseline_bests, candidate_bests, n_iter=N_PERMUTATION, seed=RANDOM_SEED):
    """Two-sided permutation test for avg, 11+, 12+, 13+."""
    rng = random.Random(seed)
    n = len(baseline_bests)

    # Observed differences
    obs_avg = sum(candidate_bests) / n - sum(baseline_bests) / n
    obs_11 = (sum(1 for x in candidate_bests if x >= 11) -
              sum(1 for x in baseline_bests if x >= 11))
    obs_12 = (sum(1 for x in candidate_bests if x >= 12) -
              sum(1 for x in baseline_bests if x >= 12))
    obs_13 = (sum(1 for x in candidate_bests if x >= 13) -
              sum(1 for x in baseline_bests if x >= 13))

    count_avg = 0
    count_11 = 0
    count_12 = 0
    count_13 = 0

    for _ in range(n_iter):
        # Randomly swap baseline/candidate labels
        perm_base = []
        perm_cand = []
        for i in range(n):
            if rng.random() < 0.5:
                perm_base.append(baseline_bests[i])
                perm_cand.append(candidate_bests[i])
            else:
                perm_base.append(candidate_bests[i])
                perm_cand.append(baseline_bests[i])

        d_avg = sum(perm_cand) / n - sum(perm_base) / n
        d_11 = (sum(1 for x in perm_cand if x >= 11) -
                sum(1 for x in perm_base if x >= 11))
        d_12 = (sum(1 for x in perm_cand if x >= 12) -
                sum(1 for x in perm_base if x >= 12))
        d_13 = (sum(1 for x in perm_cand if x >= 13) -
                sum(1 for x in perm_base if x >= 13))

        if abs(d_avg) >= abs(obs_avg):
            count_avg += 1
        if abs(d_11) >= abs(obs_11):
            count_11 += 1
        if abs(d_12) >= abs(obs_12):
            count_12 += 1
        if abs(d_13) >= abs(obs_13):
            count_13 += 1

    return {
        "avg": {"obs": obs_avg, "p": (count_avg + 1) / (n_iter + 1)},
        "11+": {"obs": obs_11, "p": (count_11 + 1) / (n_iter + 1)},
        "12+": {"obs": obs_12, "p": (count_12 + 1) / (n_iter + 1)},
        "13+": {"obs": obs_13, "p": (count_13 + 1) / (n_iter + 1)},
    }


# ============================================================================
# COHEN'S D
# ============================================================================
def cohens_d(baseline_bests, candidate_bests):
    """Cohen's d effect size on per-series best scores."""
    n = len(baseline_bests)
    diffs = [candidate_bests[i] - baseline_bests[i] for i in range(n)]
    mean_d = sum(diffs) / n
    var_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    sd_d = math.sqrt(var_d) if var_d > 0 else 1e-10
    return mean_d / sd_d


# ============================================================================
# SERIES-LEVEL COMPARISON
# ============================================================================
def series_comparison(baseline_results, candidate_results):
    """Per-series improved/same/degraded counts + detail for 12+ changes."""
    improved = []
    same = []
    degraded = []
    gained_12 = []
    lost_12 = []

    for br, cr in zip(baseline_results, candidate_results):
        sid = br["series"]
        b = br["best"]
        c = cr["best"]
        if c > b:
            improved.append((sid, b, c))
        elif c < b:
            degraded.append((sid, b, c))
        else:
            same.append((sid, b, c))

        # 12+ changes
        if c >= 12 and b < 12:
            gained_12.append((sid, b, c))
        elif b >= 12 and c < 12:
            lost_12.append((sid, b, c))

    gained_13 = [(sid, b, c) for sid, b, c in improved + same + degraded
                 if c >= 13 and b < 13]
    lost_13 = [(sid, b, c) for sid, b, c in improved + same + degraded
               if b >= 13 and c < 13]

    # Recompute gained/lost 13 cleanly
    gained_13 = []
    lost_13 = []
    for br, cr in zip(baseline_results, candidate_results):
        sid = br["series"]
        b = br["best"]
        c = cr["best"]
        if c >= 13 and b < 13:
            gained_13.append((sid, b, c))
        if b >= 13 and c < 13:
            lost_13.append((sid, b, c))

    return {
        "improved": improved,
        "same": same,
        "degraded": degraded,
        "gained_12": gained_12,
        "lost_12": lost_12,
        "gained_13": gained_13,
        "lost_13": lost_13,
    }


# ============================================================================
# S7 SAFETY CHECK
# ============================================================================
def s7_safety_check(data, baseline_results, candidate_results):
    """
    Check that ALL series where S7 contributed to 12+ are preserved.
    S7 is index 6 in the sets.
    """
    s7_12plus_baseline = []
    s7_12plus_candidate = []

    for br in baseline_results:
        # Check if S7 (index 6) achieves 12+ in baseline
        if br["set_bests"][6] >= 12:
            s7_12plus_baseline.append(br["series"])

    for cr in candidate_results:
        if cr["set_bests"][6] >= 12:
            s7_12plus_candidate.append(cr["series"])

    # Also check: any series where baseline best came from S7 at 12+
    s7_critical_baseline = []
    for br in baseline_results:
        if br["winner"] == 6 and br["best"] >= 12:
            s7_critical_baseline.append(br["series"])

    # Are all S7 12+ series preserved in candidate?
    lost = [s for s in s7_12plus_baseline if s not in s7_12plus_candidate]

    return {
        "s7_12plus_baseline": s7_12plus_baseline,
        "s7_12plus_candidate": s7_12plus_candidate,
        "s7_critical_wins_baseline": s7_critical_baseline,
        "s7_lost": lost,
        "safe": len(lost) == 0,
    }


# ============================================================================
# ROLLING WINDOW STABILITY
# ============================================================================
def rolling_window(results, window_size=50):
    """Compute avg and 12+ for non-overlapping windows."""
    windows = []
    for i in range(0, len(results), window_size):
        chunk = results[i:i + window_size]
        if len(chunk) < window_size // 2:
            continue
        bests = [r["best"] for r in chunk]
        avg = sum(bests) / len(bests)
        at_12 = sum(1 for b in bests if b >= 12)
        start_s = chunk[0]["series"]
        end_s = chunk[-1]["series"]
        windows.append({
            "label": f"W{len(windows)+1} ({start_s}-{end_s})",
            "n": len(chunk),
            "avg": avg,
            "at_12": at_12,
        })
    return windows


# ============================================================================
# UNIQUE COVERAGE
# ============================================================================
def unique_coverage(data, baseline_results, candidate_results):
    """Mean count of numbers in new S2 NOT in any S1,S3-S7."""
    unique_counts = []
    for br, cr in zip(baseline_results, candidate_results):
        # S2 is at index 1, other sets are at 0, 2, 3, 4, 5, 6
        # But we need the actual sets -- reconstruct from the evaluation
        # We stored s2_set in the results
        new_s2 = set(cr.get("s2_set", []))
        old_s2 = set(br.get("s2_set", []))

        # For unique coverage: numbers in new S2 not in S1,S3-S7
        # S1,S3-S7 are the same across baseline and candidate
        # We need to reconstruct them -- but since they're identical,
        # we can compute from the baseline prediction
        sid = br["series"]
        prior = str(sid - 1)
        if prior not in data:
            continue
        freq = get_recency_freq(data, sid)
        s1, s3, s4, s5, s6, s7 = build_common_sets(data, sid, freq)
        other_numbers = set(s1) | set(s3) | set(s4) | set(s5) | set(s6) | set(s7)
        unique_new = new_s2 - other_numbers
        unique_old = old_s2 - other_numbers
        unique_counts.append((len(unique_new), len(unique_old)))

    avg_new = sum(u[0] for u in unique_counts) / len(unique_counts)
    avg_old = sum(u[1] for u in unique_counts) / len(unique_counts)
    return avg_new, avg_old


# ============================================================================
# L30 CHECK
# ============================================================================
def l30_metrics(results, l30_start=3151, l30_end=3180):
    """Extract L30 performance."""
    l30 = [r for r in results if l30_start <= r["series"] <= l30_end]
    if not l30:
        return None
    return compute_metrics(l30)


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 80)
    print("S2 REPLACEMENT MONTE CARLO VALIDATION")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Series range: {START}-{END}")
    print(f"Bootstrap iterations: {N_BOOTSTRAP:,}")
    print(f"Permutation iterations: {N_PERMUTATION:,}")
    print(f"Random seed: {RANDOM_SEED}")
    print()

    data = load_data()

    # ========================================================================
    # 1. RUN ALL BACKTESTS
    # ========================================================================
    candidates = {
        "BASELINE (E1 rank16)": build_s2_baseline,
        "SymDiff E4^E5": build_s2_symdiff_e4e5,
        "Quint E1E3E4E5E7": build_s2_quint_e1e3e4e5e7,
        "E1&E5 Fusion": build_s2_e1e5_fusion,
    }

    print("Running backtests...")
    all_results = {}
    all_metrics = {}
    for name, builder in candidates.items():
        print(f"  {name}...", end=" ", flush=True)
        results = run_backtest(data, builder)
        all_results[name] = results
        m = compute_metrics(results)
        all_metrics[name] = m
        print(f"done ({m['n']} series, avg={m['avg']:.2f})")

    baseline_name = "BASELINE (E1 rank16)"
    baseline_results = all_results[baseline_name]
    baseline_metrics = all_metrics[baseline_name]
    baseline_bests = baseline_metrics["bests"]

    # ========================================================================
    # 2. FULL METRICS TABLE
    # ========================================================================
    print()
    print("=" * 80)
    print("1. FULL METRICS TABLE")
    print("=" * 80)
    print()
    header = f"{'Strategy':<25} {'Avg':>7} {'Best':>5} {'Worst':>6} {'11+':>5} {'12+':>5} {'13+':>5} {'14/14':>6}"
    print(header)
    print("-" * 80)
    for name in candidates:
        m = all_metrics[name]
        diff_avg = m["avg"] - baseline_metrics["avg"]
        diff_12 = m["at_12"] - baseline_metrics["at_12"]
        diff_13 = m["at_13"] - baseline_metrics["at_13"]
        diff_str = ""
        if name != baseline_name:
            diff_str = f"  (avg {diff_avg:+.2f}, 12+ {diff_12:+d}, 13+ {diff_13:+d})"
        print(f"{name:<25} {m['avg']:>7.2f} {m['best']:>5d} {m['worst']:>6d} "
              f"{m['at_11']:>5d} {m['at_12']:>5d} {m['at_13']:>5d} {m['at_14']:>6d}{diff_str}")

    # ========================================================================
    # 3. PER-SET WIN COUNTS
    # ========================================================================
    print()
    print("=" * 80)
    print("2. PER-SET WIN COUNTS")
    print("=" * 80)
    print()
    set_labels = ["S1(E4)", "S2(*)", "S3(E6)", "S4(E7)", "S5(E3&E7)", "S6(SymDiff)", "S7(Quint)"]
    header = f"{'Strategy':<25} " + " ".join(f"{l:>12}" for l in set_labels) + f" {'S7 delta':>10}"
    print(header)
    print("-" * 120)
    for name in candidates:
        m = all_metrics[name]
        w = m["wins"]
        s7_delta = w[6] - baseline_metrics["wins"][6]
        cols = " ".join(f"{x:>12d}" for x in w)
        print(f"{name:<25} {cols} {s7_delta:>+10d}")

    # ========================================================================
    # 4-6. STATISTICAL TESTS (per candidate)
    # ========================================================================
    for name in candidates:
        if name == baseline_name:
            continue

        cand_results = all_results[name]
        cand_metrics = all_metrics[name]
        cand_bests = cand_metrics["bests"]

        print()
        print("=" * 80)
        print(f"CANDIDATE: {name}")
        print("=" * 80)

        # ====================================================================
        # 4. BOOTSTRAP CI
        # ====================================================================
        print()
        print("--- 3. Bootstrap 95% CI (10,000 iterations) ---")
        boot = bootstrap_ci(baseline_bests, cand_bests)
        for metric, (mean, lo, hi) in boot.items():
            sig = "*" if (lo > 0 or hi < 0) else ""
            print(f"  {metric:>4} diff:  mean={mean:+.3f}  95% CI=[{lo:+.3f}, {hi:+.3f}] {sig}")

        # ====================================================================
        # 5. PERMUTATION TEST
        # ====================================================================
        print()
        print("--- 4. Permutation Test (5,000 iterations) ---")
        perm = permutation_test(baseline_bests, cand_bests)
        for metric, vals in perm.items():
            sig = "***" if vals["p"] < 0.001 else ("**" if vals["p"] < 0.01 else ("*" if vals["p"] < 0.05 else ""))
            print(f"  {metric:>4}:  obs_diff={vals['obs']:+.2f}  p={vals['p']:.4f} {sig}")

        # ====================================================================
        # 6. COHEN'S D
        # ====================================================================
        print()
        d = cohens_d(baseline_bests, cand_bests)
        magnitude = ("negligible" if abs(d) < 0.2 else
                     "small" if abs(d) < 0.5 else
                     "medium" if abs(d) < 0.8 else "large")
        print(f"--- 5. Cohen's d = {d:+.4f} ({magnitude}) ---")

        # ====================================================================
        # 7. SERIES-LEVEL COMPARISON
        # ====================================================================
        print()
        print("--- 6. Series-Level Comparison ---")
        comp = series_comparison(baseline_results, cand_results)
        print(f"  Improved:  {len(comp['improved']):>4}")
        print(f"  Same:      {len(comp['same']):>4}")
        print(f"  Degraded:  {len(comp['degraded']):>4}")
        if comp["improved"]:
            print(f"  Improved series: ", end="")
            for sid, b, c in comp["improved"][:20]:
                print(f"{sid}({b}->{c})", end=" ")
            if len(comp["improved"]) > 20:
                print(f"... +{len(comp['improved'])-20} more", end="")
            print()
        if comp["degraded"]:
            print(f"  Degraded series: ", end="")
            for sid, b, c in comp["degraded"][:20]:
                print(f"{sid}({b}->{c})", end=" ")
            if len(comp["degraded"]) > 20:
                print(f"... +{len(comp['degraded'])-20} more", end="")
            print()

        # ====================================================================
        # 8. 12+ DETAIL ANALYSIS
        # ====================================================================
        print()
        print("--- 7. 12+ Detail Analysis ---")
        print(f"  Gained 12+ ({len(comp['gained_12'])}):")
        for sid, b, c in comp["gained_12"]:
            print(f"    Series {sid}: {b} -> {c} (+{c - b})")
        print(f"  Lost 12+ ({len(comp['lost_12'])}):")
        for sid, b, c in comp["lost_12"]:
            print(f"    Series {sid}: {b} -> {c} ({c - b})")
        net_12 = len(comp["gained_12"]) - len(comp["lost_12"])
        print(f"  NET 12+ change: {net_12:+d}")
        print()
        print(f"  Gained 13+ ({len(comp['gained_13'])}):")
        for sid, b, c in comp["gained_13"]:
            print(f"    Series {sid}: {b} -> {c} (+{c - b})")
        print(f"  Lost 13+ ({len(comp['lost_13'])}):")
        for sid, b, c in comp["lost_13"]:
            print(f"    Series {sid}: {b} -> {c} ({c - b})")
        net_13 = len(comp["gained_13"]) - len(comp["lost_13"])
        print(f"  NET 13+ change: {net_13:+d}")

        # ====================================================================
        # 9. S7 SAFETY CHECK
        # ====================================================================
        print()
        print("--- 8. S7 Safety Check ---")
        s7_check = s7_safety_check(data, baseline_results, cand_results)
        print(f"  S7 12+ series (baseline): {s7_check['s7_12plus_baseline']}")
        print(f"  S7 12+ series (candidate): {s7_check['s7_12plus_candidate']}")
        print(f"  S7 critical wins (baseline): {s7_check['s7_critical_wins_baseline']}")
        print(f"  S7 series lost: {s7_check['s7_lost']}")
        print(f"  SAFE: {'YES' if s7_check['safe'] else '*** NO -- S7 REGRESSION ***'}")

        # ====================================================================
        # 10. ROLLING WINDOW STABILITY
        # ====================================================================
        print()
        print("--- 9. Rolling Window Stability (50-series windows) ---")
        base_windows = rolling_window(baseline_results)
        cand_windows = rolling_window(cand_results)
        print(f"  {'Window':<25} {'Base avg':>9} {'Cand avg':>9} {'Diff':>7} {'Base 12+':>9} {'Cand 12+':>9} {'Diff':>6}")
        print(f"  {'-'*75}")
        for bw, cw in zip(base_windows, cand_windows):
            d_avg = cw["avg"] - bw["avg"]
            d_12 = cw["at_12"] - bw["at_12"]
            print(f"  {bw['label']:<25} {bw['avg']:>9.2f} {cw['avg']:>9.2f} {d_avg:>+7.2f} "
                  f"{bw['at_12']:>9d} {cw['at_12']:>9d} {d_12:>+6d}")

        # ====================================================================
        # 11. L30 CHECK
        # ====================================================================
        print()
        print("--- 10. L30 Check (3151-3180) ---")
        base_l30 = l30_metrics(baseline_results)
        cand_l30 = l30_metrics(cand_results)
        if base_l30 and cand_l30:
            print(f"  {'Metric':<10} {'Baseline':>10} {'Candidate':>12} {'Diff':>8}")
            print(f"  {'-'*42}")
            print(f"  {'Avg':<10} {base_l30['avg']:>10.2f} {cand_l30['avg']:>12.2f} {cand_l30['avg']-base_l30['avg']:>+8.2f}")
            print(f"  {'11+':<10} {base_l30['at_11']:>10d} {cand_l30['at_11']:>12d} {cand_l30['at_11']-base_l30['at_11']:>+8d}")
            print(f"  {'12+':<10} {base_l30['at_12']:>10d} {cand_l30['at_12']:>12d} {cand_l30['at_12']-base_l30['at_12']:>+8d}")
            print(f"  {'13+':<10} {base_l30['at_13']:>10d} {cand_l30['at_13']:>12d} {cand_l30['at_13']-base_l30['at_13']:>+8d}")
            if cand_l30['avg'] < 10.5:
                print(f"  *** WARNING: L30 avg {cand_l30['avg']:.2f} < 10.5 threshold ***")
        else:
            print("  Could not compute L30 metrics.")

        # ====================================================================
        # 12. UNIQUE COVERAGE
        # ====================================================================
        print()
        print("--- 11. Unique Coverage ---")
        avg_new_unique, avg_old_unique = unique_coverage(data, baseline_results, cand_results)
        print(f"  Mean unique numbers in S2 not in S1,S3-S7:")
        print(f"    Baseline S2: {avg_old_unique:.2f}")
        print(f"    Candidate S2: {avg_new_unique:.2f}")
        print(f"    Diff: {avg_new_unique - avg_old_unique:+.2f}")

    # ========================================================================
    # FINAL RECOMMENDATIONS
    # ========================================================================
    print()
    print("=" * 80)
    print("FINAL RECOMMENDATIONS")
    print("=" * 80)

    for name in candidates:
        if name == baseline_name:
            continue

        m = all_metrics[name]
        diff_avg = m["avg"] - baseline_metrics["avg"]
        diff_12 = m["at_12"] - baseline_metrics["at_12"]
        diff_13 = m["at_13"] - baseline_metrics["at_13"]

        cand_bests = m["bests"]
        comp = series_comparison(baseline_results, all_results[name])

        boot = bootstrap_ci(baseline_bests, cand_bests)
        perm = permutation_test(baseline_bests, cand_bests)
        d = cohens_d(baseline_bests, cand_bests)

        cand_l30 = l30_metrics(all_results[name])
        base_l30 = l30_metrics(baseline_results)

        s7_check = s7_safety_check(data, baseline_results, all_results[name])

        # Decision logic
        red_flags = []
        green_flags = []

        # Red flag checks
        if diff_avg > 1.05:
            red_flags.append(f"avg improvement {diff_avg:+.2f} > 10% -- possible bug")
        if cand_l30 and cand_l30["avg"] < 10.5:
            red_flags.append(f"L30 avg {cand_l30['avg']:.2f} < 10.5")
        if not s7_check["safe"]:
            red_flags.append(f"S7 lost 12+ in series: {s7_check['s7_lost']}")
        if len(comp["lost_12"]) > 0:
            red_flags.append(f"Lost {len(comp['lost_12'])} existing 12+ series")
        if diff_avg < -0.10:
            red_flags.append(f"avg DECREASED by {diff_avg:.2f}")

        # Green flags
        if diff_12 > 0 and len(comp["lost_12"]) == 0:
            green_flags.append(f"+{diff_12} net 12+ with ZERO losses")
        if diff_13 > 0:
            green_flags.append(f"+{diff_13} net 13+")
        if boot["12+"][1] > 0:
            green_flags.append("12+ bootstrap CI entirely positive")
        if perm["12+"]["p"] < 0.05:
            green_flags.append(f"12+ permutation p={perm['12+']['p']:.4f} (significant)")
        if cand_l30 and base_l30 and cand_l30["avg"] >= base_l30["avg"]:
            green_flags.append(f"L30 avg maintained or improved")
        if s7_check["safe"]:
            green_flags.append("S7 all 12+ series preserved")

        # Verdict
        if red_flags and any("bug" in f or "S7 lost" in f or "DECREASED" in f for f in red_flags):
            verdict = "REJECT"
        elif diff_12 >= 3 and len(comp["lost_12"]) == 0 and s7_check["safe"]:
            verdict = "RECOMMEND"
        elif diff_12 >= 1 and len(comp["lost_12"]) == 0:
            verdict = "RECOMMEND (marginal)"
        elif diff_12 > 0 and len(comp["lost_12"]) > 0:
            verdict = "HOLD (tradeoff)"
        elif diff_12 == 0 and diff_avg >= 0:
            verdict = "HOLD (neutral)"
        else:
            verdict = "REJECT"

        print()
        print(f"--- {name} ---")
        print(f"  Verdict: *** {verdict} ***")
        print(f"  avg diff: {diff_avg:+.2f}  |  12+ diff: {diff_12:+d}  |  13+ diff: {diff_13:+d}")
        print(f"  12+ gained: {len(comp['gained_12'])}  |  12+ lost: {len(comp['lost_12'])}  |  Net: {diff_12:+d}")
        print(f"  Cohen's d: {d:+.4f}")
        if cand_l30:
            print(f"  L30 avg: {cand_l30['avg']:.2f} (baseline: {base_l30['avg']:.2f})")
        print(f"  S7 safe: {'YES' if s7_check['safe'] else 'NO'}")
        if green_flags:
            print(f"  GREEN: {'; '.join(green_flags)}")
        if red_flags:
            print(f"  RED:   {'; '.join(red_flags)}")

    print()
    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)


if __name__ == "__main__":
    main()
