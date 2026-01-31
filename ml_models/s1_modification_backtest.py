#!/usr/bin/env python3
"""
S1 Modification Backtest -- Monte Carlo & Statistical Validation
================================================================

Tests 7 S1 candidates against the full 200-series backtest (2981-3180).

Candidates:
  1. BASELINE       -- S1 = E4 direct copy (current production)
  2. E4+Force18     -- Copy E4, force #18 if absent (replace lowest-freq E4 num)
  3. E4+Force21     -- Same, force #21
  4. E4+Force23     -- Same, force #23
  5. E4_Top12+Div2  -- Top 12 E4 by recency-freq, fill 2 from E2/E5 not in E4
  6. E4&E5 Fusion   -- Intersection E4&E5, fill from union by freq
  7. E4_Trim11+Top3 -- 11 from E4, fill 3 with top recency-freq not in E4

Statistical outputs:
  - Full metrics table (avg, 11+, 12+, 13+, 14/14)
  - Per-set win counts (S1..S7)
  - Bootstrap 10k: 95% CI on avg and 12+ diffs vs baseline
  - Permutation test 5k: p-values
  - Cohen's d effect sizes
  - Series-level comparison: improved/same/degraded
  - S7 safety check: 12+ contribution NOT harmed
  - RECOMMEND / HOLD / REJECT per candidate

Author: simulation-testing-expert
Date: 2026-01-30
"""

import json
import sys
import math
import random
from pathlib import Path
from collections import Counter
from copy import deepcopy

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOTAL = 25
PICK = 14
NUM_SETS = 7
START = 2981
END = 3180

BOOTSTRAP_ITERS = 10_000
PERMUTATION_ITERS = 5_000
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    """Load data from JSON."""
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


# ---------------------------------------------------------------------------
# Recency-weighted frequency (exact copy from production_predictor.py)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Production predict (all 7 sets -- baseline S1)
# ---------------------------------------------------------------------------

def predict_production(data, series_id):
    """
    Exact copy of production predict -- returns list of 7 sorted sets.
    """
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No data for series {int(prior)}")

    event1 = set(data[prior][0])
    event2 = set(data[prior][1])
    event3 = set(data[prior][2])
    event4 = set(data[prior][3])
    event5 = set(data[prior][4])
    event6 = set(data[prior][5])
    event7 = set(data[prior][6])

    freq = get_recency_freq(data, series_id)
    max_freq = max(freq.values()) if freq else 1

    # E1 ranked
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event1), -freq[n] / max_freq, n))

    # E3&E7 fusion (S5)
    e3_e7_int = event3 & event7
    e3_e7_union = event3 | event7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # S6: SymDiff E3 xor E7
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
        sorted(event4),                           # S1: E4 direct
        sorted(ranked[:13] + [ranked[15]]),       # S2: rank16
        sorted(event6),                           # S3: E6 direct
        sorted(event7),                           # S4: E7 direct
        sorted(s5_numbers),                       # S5: E3&E7 fusion
        s6_numbers,                               # S6: SymDiff
        s7_numbers,                               # S7: Quint
    ]

    return sets, freq, event1, event2, event3, event4, event5, event6, event7


# ---------------------------------------------------------------------------
# S1 candidate generators
# ---------------------------------------------------------------------------

def candidate_baseline(event4, freq, **kw):
    """BASELINE: E4 direct copy."""
    return sorted(event4)


def _force_number(event4, freq, number):
    """Force a specific number into E4. If not present, drop lowest-freq E4 number."""
    s = set(event4)
    if number in s:
        return sorted(s)
    # Remove E4 member with lowest recency-freq
    worst = min(s, key=lambda n: (freq.get(n, 0), -n))
    s.discard(worst)
    s.add(number)
    return sorted(s)


def candidate_force18(event4, freq, **kw):
    """E4+Force18."""
    return _force_number(event4, freq, 18)


def candidate_force21(event4, freq, **kw):
    """E4+Force21."""
    return _force_number(event4, freq, 21)


def candidate_force23(event4, freq, **kw):
    """E4+Force23."""
    return _force_number(event4, freq, 23)


def candidate_top12_div2(event4, freq, event2, event5, **kw):
    """
    E4_Top12+Diversity2:
    Take top 12 E4 numbers by recency-freq.
    Fill 2 slots from numbers in E2 or E5 but NOT in E4, ranked by freq.
    """
    e4_sorted = sorted(event4, key=lambda n: -freq.get(n, 0))
    top12 = set(e4_sorted[:12])
    # Diversity pool: in E2 or E5 but not in E4
    diversity_pool = ((event2 | event5) - event4)
    diversity_ranked = sorted(diversity_pool, key=lambda n: -freq.get(n, 0))
    fill = diversity_ranked[:2]
    result = top12 | set(fill)
    # If diversity pool had fewer than 2 members, fill from top freq not in result
    if len(result) < 14:
        extras = sorted([n for n in range(1, 26) if n not in result],
                        key=lambda n: -freq.get(n, 0))
        result = result | set(extras[:14 - len(result)])
    return sorted(result)[:14]


def candidate_e4e5_fusion(event4, freq, event5, **kw):
    """
    E4&E5 Fusion: Intersection of E4 and E5, fill remaining from union by freq.
    """
    intersection = event4 & event5
    union = event4 | event5
    remaining = sorted(union - intersection, key=lambda n: -freq.get(n, 0))
    nums = list(intersection) + remaining[:14 - len(intersection)]
    # If still < 14, fill from all by freq
    if len(nums) < 14:
        pool = sorted([n for n in range(1, 26) if n not in set(nums)],
                      key=lambda n: -freq.get(n, 0))
        nums += pool[:14 - len(nums)]
    return sorted(nums[:14])


def candidate_trim11_top3(event4, freq, **kw):
    """
    E4 Trimmed+TopFreq: Take 11 numbers from E4 (highest recency-freq),
    fill 3 with highest recency-freq numbers NOT in E4.
    """
    e4_sorted = sorted(event4, key=lambda n: -freq.get(n, 0))
    top11 = set(e4_sorted[:11])
    outside = sorted([n for n in range(1, 26) if n not in event4],
                     key=lambda n: -freq.get(n, 0))
    fill = outside[:3]
    result = top11 | set(fill)
    if len(result) < 14:
        extras = sorted([n for n in range(1, 26) if n not in result],
                        key=lambda n: -freq.get(n, 0))
        result = result | set(extras[:14 - len(result)])
    return sorted(result)[:14]


CANDIDATES = [
    ("BASELINE (E4 direct)", candidate_baseline),
    ("E4+Force18", candidate_force18),
    ("E4+Force21", candidate_force21),
    ("E4+Force23", candidate_force23),
    ("E4_Top12+Div2", candidate_top12_div2),
    ("E4&E5 Fusion", candidate_e4e5_fusion),
    ("E4_Trim11+Top3", candidate_trim11_top3),
]


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def evaluate_sets(prediction_sets, actual_events):
    """
    Evaluate one prediction: best-of-7-sets x 7-events.
    Returns (best_score, winner_index_0based, set_bests_list).
    """
    set_bests = []
    for s in prediction_sets:
        s_set = set(s)
        matches = [len(s_set & set(e)) for e in actual_events]
        set_bests.append(max(matches))
    best = max(set_bests)
    winner = set_bests.index(best)
    return best, winner, set_bests


def run_backtest(data, candidate_fn, candidate_name):
    """
    Run a candidate across 200 series, replacing only S1.
    Returns list of per-series result dicts.
    """
    results = []
    for series_id in range(START, END + 1):
        sid_str = str(series_id)
        if sid_str not in data:
            continue
        prior_str = str(series_id - 1)
        if prior_str not in data:
            continue

        # Get production sets (S1..S7) + context
        prod_sets, freq, e1, e2, e3, e4, e5, e6, e7 = predict_production(data, series_id)

        # Generate candidate S1
        new_s1 = candidate_fn(
            event4=set(data[prior_str][3]),
            freq=freq,
            event1=set(data[prior_str][0]),
            event2=set(data[prior_str][1]),
            event3=set(data[prior_str][2]),
            event5=set(data[prior_str][4]),
            event6=set(data[prior_str][5]),
            event7=set(data[prior_str][6]),
        )

        # Replace S1 only
        test_sets = deepcopy(prod_sets)
        test_sets[0] = new_s1

        actual_events = data[sid_str]
        best, winner, set_bests = evaluate_sets(test_sets, actual_events)

        results.append({
            "series": series_id,
            "best": best,
            "winner": winner,
            "set_bests": set_bests,
        })

    return results


# ---------------------------------------------------------------------------
# Metrics extraction
# ---------------------------------------------------------------------------

def compute_metrics(results):
    """Extract summary metrics from a list of result dicts."""
    n = len(results)
    bests = [r["best"] for r in results]
    avg = sum(bests) / n
    wins = [0] * NUM_SETS
    for r in results:
        wins[r["winner"]] += 1
    at_11 = sum(1 for b in bests if b >= 11)
    at_12 = sum(1 for b in bests if b >= 12)
    at_13 = sum(1 for b in bests if b >= 13)
    at_14 = sum(1 for b in bests if b == 14)

    # S7 12+ contribution: count series where S7 set_bests >= 12
    s7_at12 = sum(1 for r in results if r["set_bests"][6] >= 12)

    return {
        "n": n,
        "avg": avg,
        "best": max(bests),
        "worst": min(bests),
        "at_11": at_11,
        "at_12": at_12,
        "at_13": at_13,
        "at_14": at_14,
        "wins": wins,
        "bests": bests,
        "s7_at12": s7_at12,
    }


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------

def bootstrap_ci(baseline_bests, test_bests, n_boot=BOOTSTRAP_ITERS, seed=RANDOM_SEED):
    """
    Bootstrap 95% CI for difference in mean and difference in 12+ count.
    Returns dict with avg_diff_ci, at12_diff_ci.
    """
    rng = random.Random(seed)
    n = len(baseline_bests)
    assert len(test_bests) == n

    avg_diffs = []
    at12_diffs = []

    for _ in range(n_boot):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        b_sample = [baseline_bests[i] for i in indices]
        t_sample = [test_bests[i] for i in indices]

        b_avg = sum(b_sample) / n
        t_avg = sum(t_sample) / n
        avg_diffs.append(t_avg - b_avg)

        b_12 = sum(1 for x in b_sample if x >= 12)
        t_12 = sum(1 for x in t_sample if x >= 12)
        at12_diffs.append(t_12 - b_12)

    avg_diffs.sort()
    at12_diffs.sort()

    lo = int(n_boot * 0.025)
    hi = int(n_boot * 0.975)

    return {
        "avg_diff_mean": sum(avg_diffs) / n_boot,
        "avg_diff_ci": (avg_diffs[lo], avg_diffs[hi]),
        "at12_diff_mean": sum(at12_diffs) / n_boot,
        "at12_diff_ci": (at12_diffs[lo], at12_diffs[hi]),
    }


def permutation_test(baseline_bests, test_bests, n_perm=PERMUTATION_ITERS, seed=RANDOM_SEED):
    """
    Two-sided permutation test for difference in mean and 12+ count.
    Returns p-values.
    """
    rng = random.Random(seed + 1)
    n = len(baseline_bests)
    assert len(test_bests) == n

    obs_avg_diff = sum(test_bests) / n - sum(baseline_bests) / n
    obs_12_diff = (sum(1 for x in test_bests if x >= 12)
                   - sum(1 for x in baseline_bests if x >= 12))

    count_avg = 0
    count_12 = 0

    pooled = list(zip(baseline_bests, test_bests))

    for _ in range(n_perm):
        perm_b = []
        perm_t = []
        for b, t in pooled:
            if rng.random() < 0.5:
                perm_b.append(b)
                perm_t.append(t)
            else:
                perm_b.append(t)
                perm_t.append(b)

        d_avg = sum(perm_t) / n - sum(perm_b) / n
        d_12 = (sum(1 for x in perm_t if x >= 12)
                - sum(1 for x in perm_b if x >= 12))

        if abs(d_avg) >= abs(obs_avg_diff):
            count_avg += 1
        if abs(d_12) >= abs(obs_12_diff):
            count_12 += 1

    return {
        "p_avg": (count_avg + 1) / (n_perm + 1),
        "p_12": (count_12 + 1) / (n_perm + 1),
    }


def cohens_d(baseline_bests, test_bests):
    """Cohen's d for paired samples."""
    n = len(baseline_bests)
    diffs = [test_bests[i] - baseline_bests[i] for i in range(n)]
    mean_d = sum(diffs) / n
    var_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1) if n > 1 else 0
    sd_d = math.sqrt(var_d) if var_d > 0 else 1e-9
    return mean_d / sd_d


def series_comparison(baseline_bests, test_bests):
    """Count series improved, same, degraded."""
    improved = same = degraded = 0
    for b, t in zip(baseline_bests, test_bests):
        if t > b:
            improved += 1
        elif t < b:
            degraded += 1
        else:
            same += 1
    return improved, same, degraded


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------

def recommend(name, metrics, baseline_metrics, boot, perm, effect_d, imp, same, deg):
    """
    RECOMMEND / HOLD / REJECT for a candidate.

    RECOMMEND: significant improvement in 12+ or 13+ WITHOUT degrading avg or S7.
    HOLD:      neutral or marginal, needs more data.
    REJECT:    degraded or no benefit.
    """
    avg_diff = metrics["avg"] - baseline_metrics["avg"]
    at12_diff = metrics["at_12"] - baseline_metrics["at_12"]
    at13_diff = metrics["at_13"] - baseline_metrics["at_13"]
    s7_harm = metrics["s7_at12"] < baseline_metrics["s7_at12"]

    # Red flag: S7 12+ harmed
    if s7_harm:
        return "REJECT", f"S7 12+ contribution harmed ({baseline_metrics['s7_at12']} -> {metrics['s7_at12']})"

    # Significant avg degradation
    if avg_diff < -0.10 and perm["p_avg"] < 0.10:
        return "REJECT", f"Avg degraded by {avg_diff:.3f} (p={perm['p_avg']:.3f})"

    # Strong 12+ improvement
    if at12_diff >= 2 and perm["p_12"] < 0.10:
        return "RECOMMEND", f"12+ improved by {at12_diff} (p={perm['p_12']:.3f})"

    # Any 13+ improvement (rare, valuable)
    if at13_diff > 0 and avg_diff >= -0.05:
        return "RECOMMEND", f"13+ improved by {at13_diff}, avg diff {avg_diff:+.3f}"

    # Moderate 12+ improvement but not significant
    if at12_diff > 0 and avg_diff >= -0.03:
        return "HOLD", f"12+ improved by {at12_diff} but p={perm['p_12']:.3f}"

    # Degradation (even if 12+ neutral)
    if deg > imp and perm["p_avg"] < 0.20:
        return "REJECT", f"More degraded ({deg}) than improved ({imp}) series"

    # Neutral
    if at12_diff == 0 and abs(avg_diff) < 0.03:
        return "HOLD", "No meaningful change"

    # Default
    if avg_diff < -0.03:
        return "REJECT", f"Avg degraded by {avg_diff:.3f}"

    return "HOLD", f"Avg diff {avg_diff:+.3f}, 12+ diff {at12_diff:+d}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("S1 MODIFICATION BACKTEST -- Monte Carlo & Statistical Validation")
    print("=" * 80)
    print(f"Series range: {START}-{END} (200 series)")
    print(f"Bootstrap iterations: {BOOTSTRAP_ITERS:,}")
    print(f"Permutation iterations: {PERMUTATION_ITERS:,}")
    print(f"Random seed: {RANDOM_SEED}")
    print()

    data = load_data()
    print(f"Loaded {len(data)} series from data file.")
    print()

    # ------------------------------------------------------------------
    # Run all candidates
    # ------------------------------------------------------------------
    all_results = {}
    all_metrics = {}

    for name, fn in CANDIDATES:
        print(f"  Running: {name} ...", end="", flush=True)
        results = run_backtest(data, fn, name)
        metrics = compute_metrics(results)
        all_results[name] = results
        all_metrics[name] = metrics
        print(f" avg={metrics['avg']:.2f}, 12+={metrics['at_12']}, 13+={metrics['at_13']}")

    baseline_name = CANDIDATES[0][0]
    baseline_metrics = all_metrics[baseline_name]
    baseline_bests = baseline_metrics["bests"]

    # ------------------------------------------------------------------
    # Section 1: Full Metrics Table
    # ------------------------------------------------------------------
    print()
    print("=" * 80)
    print("SECTION 1: FULL METRICS TABLE")
    print("=" * 80)
    print()
    header = f"{'Candidate':<22} {'Avg':>6} {'Best':>5} {'Worst':>6} {'11+':>5} {'12+':>5} {'13+':>5} {'14/14':>6}"
    print(header)
    print("-" * len(header))
    for name, _ in CANDIDATES:
        m = all_metrics[name]
        marker = " <-- baseline" if name == baseline_name else ""
        print(f"{name:<22} {m['avg']:>6.2f} {m['best']:>5d} {m['worst']:>6d} "
              f"{m['at_11']:>5d} {m['at_12']:>5d} {m['at_13']:>5d} {m['at_14']:>6d}{marker}")

    # ------------------------------------------------------------------
    # Section 2: Per-Set Win Counts
    # ------------------------------------------------------------------
    print()
    print("=" * 80)
    print("SECTION 2: PER-SET WIN COUNTS")
    print("=" * 80)
    print()
    labels = ["S1(E4)", "S2(rk16)", "S3(E6)", "S4(E7)", "S5(E3E7)", "S6(Sym)", "S7(Qnt)"]
    header2 = f"{'Candidate':<22} " + " ".join(f"{l:>9}" for l in labels)
    print(header2)
    print("-" * len(header2))
    for name, _ in CANDIDATES:
        m = all_metrics[name]
        w = m["wins"]
        row = f"{name:<22} " + " ".join(f"{w[i]:>9}" for i in range(NUM_SETS))
        print(row)

    # ------------------------------------------------------------------
    # Section 3-6: Statistical Comparison vs Baseline
    # ------------------------------------------------------------------
    print()
    print("=" * 80)
    print("SECTION 3: BOOTSTRAP 95% CI (10,000 iterations)")
    print("=" * 80)
    print()
    print(f"{'Candidate':<22} {'Avg Diff':>9} {'95% CI Avg':>18} {'12+ Diff':>9} {'95% CI 12+':>16}")
    print("-" * 78)

    boot_results = {}
    for name, _ in CANDIDATES[1:]:
        test_bests = all_metrics[name]["bests"]
        boot = bootstrap_ci(baseline_bests, test_bests)
        boot_results[name] = boot
        print(f"{name:<22} {boot['avg_diff_mean']:>+9.3f} "
              f"[{boot['avg_diff_ci'][0]:>+7.3f}, {boot['avg_diff_ci'][1]:>+7.3f}] "
              f"{boot['at12_diff_mean']:>+9.1f} "
              f"[{boot['at12_diff_ci'][0]:>+6.0f}, {boot['at12_diff_ci'][1]:>+6.0f}]")

    print()
    print("=" * 80)
    print("SECTION 4: PERMUTATION TEST (5,000 iterations)")
    print("=" * 80)
    print()
    print(f"{'Candidate':<22} {'p(avg)':>8} {'p(12+)':>8} {'Sig(avg)':>10} {'Sig(12+)':>10}")
    print("-" * 62)

    perm_results = {}
    for name, _ in CANDIDATES[1:]:
        test_bests = all_metrics[name]["bests"]
        perm = permutation_test(baseline_bests, test_bests)
        perm_results[name] = perm
        sig_a = "YES" if perm["p_avg"] < 0.05 else ("marginal" if perm["p_avg"] < 0.10 else "no")
        sig_12 = "YES" if perm["p_12"] < 0.05 else ("marginal" if perm["p_12"] < 0.10 else "no")
        print(f"{name:<22} {perm['p_avg']:>8.4f} {perm['p_12']:>8.4f} {sig_a:>10} {sig_12:>10}")

    print()
    print("=" * 80)
    print("SECTION 5: EFFECT SIZES (Cohen's d)")
    print("=" * 80)
    print()
    print(f"{'Candidate':<22} {'Cohen d':>8} {'Interpretation':>16}")
    print("-" * 50)

    effect_results = {}
    for name, _ in CANDIDATES[1:]:
        test_bests = all_metrics[name]["bests"]
        d = cohens_d(baseline_bests, test_bests)
        effect_results[name] = d
        if abs(d) < 0.2:
            interp = "negligible"
        elif abs(d) < 0.5:
            interp = "small"
        elif abs(d) < 0.8:
            interp = "medium"
        else:
            interp = "large"
        print(f"{name:<22} {d:>+8.3f} {interp:>16}")

    print()
    print("=" * 80)
    print("SECTION 6: SERIES-LEVEL COMPARISON vs BASELINE")
    print("=" * 80)
    print()
    print(f"{'Candidate':<22} {'Improved':>9} {'Same':>6} {'Degraded':>9} {'Net':>5}")
    print("-" * 55)

    comparison_results = {}
    for name, _ in CANDIDATES[1:]:
        test_bests = all_metrics[name]["bests"]
        imp, same, deg = series_comparison(baseline_bests, test_bests)
        comparison_results[name] = (imp, same, deg)
        net = imp - deg
        print(f"{name:<22} {imp:>9} {same:>6} {deg:>9} {net:>+5d}")

    # ------------------------------------------------------------------
    # Section 7: S7 Safety Check
    # ------------------------------------------------------------------
    print()
    print("=" * 80)
    print("SECTION 7: S7 12+ SAFETY CHECK")
    print("=" * 80)
    print()
    print(f"Baseline S7 12+ contribution: {baseline_metrics['s7_at12']}")
    print()
    print(f"{'Candidate':<22} {'S7 at12':>8} {'Change':>8} {'Status':>10}")
    print("-" * 52)

    for name, _ in CANDIDATES[1:]:
        m = all_metrics[name]
        diff = m["s7_at12"] - baseline_metrics["s7_at12"]
        status = "SAFE" if diff >= 0 else "HARMED"
        print(f"{name:<22} {m['s7_at12']:>8} {diff:>+8d} {status:>10}")

    # ------------------------------------------------------------------
    # Section 8: Score Distribution (S1 only)
    # ------------------------------------------------------------------
    print()
    print("=" * 80)
    print("SECTION 8: S1 SCORE DISTRIBUTION (S1 set only, not best-of-7)")
    print("=" * 80)
    print()
    # For each candidate, show the distribution of S1's score (index 0 in set_bests)
    header_d = f"{'Candidate':<22} " + " ".join(f"{'=' + str(s):>5}" for s in range(7, 15))
    print(header_d)
    print("-" * len(header_d))

    for name, _ in CANDIDATES:
        results = all_results[name]
        dist = Counter()
        for r in results:
            dist[r["set_bests"][0]] += 1
        row = f"{name:<22} " + " ".join(f"{dist.get(s, 0):>5}" for s in range(7, 15))
        print(row)

    # ------------------------------------------------------------------
    # Section 9: Final Recommendations
    # ------------------------------------------------------------------
    print()
    print("=" * 80)
    print("SECTION 9: FINAL RECOMMENDATIONS")
    print("=" * 80)
    print()

    for name, _ in CANDIDATES[1:]:
        m = all_metrics[name]
        boot = boot_results[name]
        perm = perm_results[name]
        d = effect_results[name]
        imp, same, deg = comparison_results[name]

        verdict, reason = recommend(name, m, baseline_metrics, boot, perm, d, imp, same, deg)

        avg_diff = m["avg"] - baseline_metrics["avg"]
        at12_diff = m["at_12"] - baseline_metrics["at_12"]
        at13_diff = m["at_13"] - baseline_metrics["at_13"]

        icon = {"RECOMMEND": ">>>", "HOLD": "---", "REJECT": "XXX"}[verdict]

        print(f"  [{icon}] {name}")
        print(f"        Verdict:  {verdict}")
        print(f"        Reason:   {reason}")
        print(f"        Avg diff: {avg_diff:+.3f} | 12+ diff: {at12_diff:+d} | 13+ diff: {at13_diff:+d}")
        print(f"        Cohen's d: {d:+.3f} | p(avg): {perm['p_avg']:.4f} | p(12+): {perm['p_12']:.4f}")
        print(f"        Series: +{imp} / ={same} / -{deg}")
        print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Baseline: avg={baseline_metrics['avg']:.2f}, 12+={baseline_metrics['at_12']}, "
          f"13+={baseline_metrics['at_13']}, 14/14={baseline_metrics['at_14']}")
    print()

    rec_count = sum(1 for name, _ in CANDIDATES[1:]
                    if recommend(name, all_metrics[name], baseline_metrics,
                                 boot_results[name], perm_results[name],
                                 effect_results[name],
                                 *comparison_results[name])[0] == "RECOMMEND")
    hold_count = sum(1 for name, _ in CANDIDATES[1:]
                     if recommend(name, all_metrics[name], baseline_metrics,
                                  boot_results[name], perm_results[name],
                                  effect_results[name],
                                  *comparison_results[name])[0] == "HOLD")
    reject_count = sum(1 for name, _ in CANDIDATES[1:]
                       if recommend(name, all_metrics[name], baseline_metrics,
                                    boot_results[name], perm_results[name],
                                    effect_results[name],
                                    *comparison_results[name])[0] == "REJECT")

    print(f"  RECOMMEND: {rec_count}")
    print(f"  HOLD:      {hold_count}")
    print(f"  REJECT:    {reject_count}")
    print()
    print("NOTE: With N=200, statistical power is limited. Any candidate with")
    print("p > 0.10 should be considered noise unless 12+/13+ improvement is large.")
    print()
    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)


if __name__ == "__main__":
    main()
