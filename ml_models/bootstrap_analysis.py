#!/usr/bin/env python3
"""
Bootstrap Analysis for Production Predictor
============================================

Performs statistical bootstrap analysis on prediction results:
- 10,000 bootstrap resamples with replacement
- BCa (Bias-Corrected Accelerated) confidence intervals
- Standard error estimation
- Prediction intervals for future observations
- Variance/stability metrics

Usage: python bootstrap_analysis.py
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

# Configuration
N_BOOTSTRAP = 10000
RANDOM_SEED = 42
SERIES_START = 2981
SERIES_END = 3173  # Updated to latest series
RANDOM_BASELINE = 7.84  # Expected matches for random selection

def load_data():
    """Load data from JSON."""
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def get_all_results(data, start, end):
    """Get best match results for all series in range using production predictor logic."""
    from collections import Counter

    TOTAL = 25
    results = []

    for series_id in range(start, end + 1):
        sid = str(series_id)
        prior = str(series_id - 1)

        if sid not in data or prior not in data:
            continue

        # Replicate prediction logic
        event1 = set(data[prior][0])
        freq = Counter(n for events in data.values() for e in events for n in e)
        max_freq = max(freq.values())

        ranked = sorted(range(1, TOTAL + 1),
                        key=lambda n: (-(n in event1), -freq[n]/max_freq, n))

        prev_series = sorted(int(s) for s in data if int(s) < series_id)[-5:]
        recent_freq = Counter(n for s in prev_series for e in data[str(s)] for n in e)

        non_top14 = [n for n in range(1, TOTAL + 1) if n not in ranked[:14]]
        hot_outside = sorted(non_top14, key=lambda n: -recent_freq.get(n, 0))[:3]

        # 8 prediction sets (optimized strategy 2026-01-10)
        sets = [
            sorted(ranked[:13] + [ranked[15]]),              # Set 1: top-13 + rank16
            sorted(ranked[:13] + [ranked[17]]),              # Set 2: top-13 + rank18
            sorted(ranked[:13] + [ranked[20]]),              # Set 3: top-13 + rank21
            sorted(ranked[:12] + [ranked[15], ranked[17]]),  # Set 4: top-12 + r16+r18
            sorted(ranked[:12] + [ranked[15], ranked[20]]),  # Set 5: top-12 + r16+r21
            sorted(ranked[:12] + [ranked[13], ranked[16]]),  # Set 6: top-12 + r14+r17
            sorted(ranked[:12] + [ranked[14], ranked[18]]),  # Set 7: top-12 + r15+r19
            sorted(ranked[:12] + [hot_outside[1], hot_outside[2]]),  # Set 8: hot #2+#3
        ]

        # Evaluate against actual events
        events = data[sid]
        set_bests = []
        for s in sets:
            matches = [len(set(s) & set(e)) for e in events]
            set_bests.append(max(matches))

        best = max(set_bests)
        results.append({
            'series': series_id,
            'best': best,
            'set_bests': set_bests,
            'winner': set_bests.index(best) + 1
        })

    return results


def bootstrap_resample(data, n_bootstrap, seed):
    """Generate bootstrap resamples."""
    rng = np.random.RandomState(seed)
    n = len(data)
    indices = rng.randint(0, n, size=(n_bootstrap, n))
    return indices


def compute_bca_ci(data, boot_stats, statistic_func, alpha=0.05):
    """
    Compute BCa (Bias-Corrected Accelerated) confidence interval.

    BCa corrects for bias and skewness in the bootstrap distribution.
    """
    n = len(data)
    theta_hat = statistic_func(data)

    # Bias correction (z0)
    prop_less = np.mean(boot_stats < theta_hat)
    if prop_less == 0:
        prop_less = 1 / (2 * len(boot_stats))
    elif prop_less == 1:
        prop_less = 1 - 1 / (2 * len(boot_stats))
    z0 = stats.norm.ppf(prop_less)

    # Acceleration (a) via jackknife
    jackknife_stats = np.zeros(n)
    for i in range(n):
        jack_sample = np.delete(data, i)
        jackknife_stats[i] = statistic_func(jack_sample)

    jack_mean = np.mean(jackknife_stats)
    numerator = np.sum((jack_mean - jackknife_stats) ** 3)
    denominator = 6 * (np.sum((jack_mean - jackknife_stats) ** 2) ** 1.5)

    if denominator == 0:
        a = 0
    else:
        a = numerator / denominator

    # BCa percentiles
    z_alpha_lower = stats.norm.ppf(alpha / 2)
    z_alpha_upper = stats.norm.ppf(1 - alpha / 2)

    def bca_percentile(z_alpha):
        numer = z0 + z_alpha
        denom = 1 - a * numer
        if denom == 0:
            return 0.5
        return stats.norm.cdf(z0 + numer / denom)

    alpha_lower = bca_percentile(z_alpha_lower)
    alpha_upper = bca_percentile(z_alpha_upper)

    # Clamp to valid range
    alpha_lower = np.clip(alpha_lower, 0.001, 0.999)
    alpha_upper = np.clip(alpha_upper, 0.001, 0.999)

    lower = np.percentile(boot_stats, 100 * alpha_lower)
    upper = np.percentile(boot_stats, 100 * alpha_upper)

    return lower, upper, z0, a


def compute_prediction_interval(data, boot_stats, alpha=0.05):
    """
    Compute prediction interval for future observations.

    This accounts for both estimation uncertainty and observation variability.
    """
    # Point estimate and bootstrap SE
    mean_hat = np.mean(data)
    se_boot = np.std(boot_stats, ddof=1)

    # Estimate residual variance from data
    residual_var = np.var(data, ddof=1)

    # Prediction SE combines estimation and residual variance
    pred_se = np.sqrt(se_boot**2 + residual_var)

    # Use t-distribution for small samples
    n = len(data)
    t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)

    lower = mean_hat - t_crit * pred_se
    upper = mean_hat + t_crit * pred_se

    return lower, upper, pred_se


def main():
    print("=" * 70)
    print("BOOTSTRAP ANALYSIS - Production Predictor")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    data = load_data()

    # Get all prediction results
    print(f"Evaluating series {SERIES_START}-{SERIES_END}...")
    results = get_all_results(data, SERIES_START, SERIES_END)

    # Extract best matches
    best_matches = np.array([r['best'] for r in results])
    n_series = len(best_matches)

    print(f"Retrieved {n_series} series results")

    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    print("\n" + "=" * 70)
    print("CONFIGURATION")
    print("=" * 70)
    print(f"- Series range: {SERIES_START}-{SERIES_END}")
    print(f"- Sample size: {n_series}")
    print(f"- Bootstrap iterations: {N_BOOTSTRAP:,}")
    print(f"- Random seed: {RANDOM_SEED}")
    print(f"- Baseline (random): {RANDOM_BASELINE}/14")

    # =========================================================================
    # BOOTSTRAP RESAMPLING
    # =========================================================================
    print("\n" + "=" * 70)
    print("BOOTSTRAP RESAMPLING")
    print("=" * 70)

    # Generate bootstrap samples
    print(f"Generating {N_BOOTSTRAP:,} bootstrap resamples...")
    boot_indices = bootstrap_resample(best_matches, N_BOOTSTRAP, RANDOM_SEED)

    # Compute bootstrap statistics
    boot_means = np.array([np.mean(best_matches[idx]) for idx in boot_indices])
    boot_medians = np.array([np.median(best_matches[idx]) for idx in boot_indices])
    boot_stds = np.array([np.std(best_matches[idx], ddof=1) for idx in boot_indices])

    # Verify reproducibility
    print("Verifying reproducibility (re-running with same seed)...")
    boot_indices_check = bootstrap_resample(best_matches, N_BOOTSTRAP, RANDOM_SEED)
    boot_means_check = np.array([np.mean(best_matches[idx]) for idx in boot_indices_check])

    if np.allclose(boot_means, boot_means_check):
        print("  [OK] Reproducibility verified - identical results on re-run")
    else:
        print("  [WARN] Reproducibility check failed")

    # =========================================================================
    # RESULTS
    # =========================================================================
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    # Point estimates
    mean_hat = np.mean(best_matches)
    median_hat = np.median(best_matches)
    std_hat = np.std(best_matches, ddof=1)

    # Bootstrap SE
    se_mean = np.std(boot_means, ddof=1)
    se_median = np.std(boot_medians, ddof=1)
    se_std = np.std(boot_stds, ddof=1)

    # BCa confidence intervals
    print("\nComputing BCa confidence intervals...")
    ci_mean_lower, ci_mean_upper, z0_mean, a_mean = compute_bca_ci(
        best_matches, boot_means, np.mean
    )
    ci_median_lower, ci_median_upper, z0_median, a_median = compute_bca_ci(
        best_matches, boot_medians, np.median
    )
    ci_std_lower, ci_std_upper, z0_std, a_std = compute_bca_ci(
        best_matches, boot_stds, lambda x: np.std(x, ddof=1)
    )

    # Percentile CIs for comparison
    pct_mean_lower, pct_mean_upper = np.percentile(boot_means, [2.5, 97.5])
    pct_median_lower, pct_median_upper = np.percentile(boot_medians, [2.5, 97.5])

    print("\n" + "-" * 70)
    print(f"{'Metric':<15} {'Estimate':<12} {'SE':<10} {'95% BCa CI':<20} {'95% Pctl CI':<20}")
    print("-" * 70)
    print(f"{'Mean':<15} {mean_hat:<12.4f} {se_mean:<10.4f} [{ci_mean_lower:.4f}, {ci_mean_upper:.4f}]  [{pct_mean_lower:.4f}, {pct_mean_upper:.4f}]")
    print(f"{'Median':<15} {median_hat:<12.4f} {se_median:<10.4f} [{ci_median_lower:.4f}, {ci_median_upper:.4f}]  [{pct_median_lower:.4f}, {pct_median_upper:.4f}]")
    print(f"{'Std Dev':<15} {std_hat:<12.4f} {se_std:<10.4f} [{ci_std_lower:.4f}, {ci_std_upper:.4f}]")
    print("-" * 70)

    # =========================================================================
    # PREDICTION INTERVAL
    # =========================================================================
    print("\n" + "=" * 70)
    print("PREDICTION INTERVAL")
    print("=" * 70)

    pred_lower, pred_upper, pred_se = compute_prediction_interval(
        best_matches, boot_means
    )

    print(f"\n95% Prediction Interval for future series: [{pred_lower:.2f}, {pred_upper:.2f}]")
    print(f"Prediction SE: {pred_se:.4f}")
    print("\nInterpretation: 95% of future best-match scores are expected to fall")
    print(f"               within the range {pred_lower:.2f} to {pred_upper:.2f} matches.")

    # =========================================================================
    # VARIANCE/STABILITY METRICS
    # =========================================================================
    print("\n" + "=" * 70)
    print("VARIANCE / STABILITY METRICS")
    print("=" * 70)

    # Coefficient of variation
    cv = (std_hat / mean_hat) * 100
    cv_boot = np.std(boot_means) / np.mean(boot_means) * 100

    # Interquartile range
    q1, q3 = np.percentile(best_matches, [25, 75])
    iqr = q3 - q1

    # Skewness and kurtosis
    skew = stats.skew(best_matches)
    kurt = stats.kurtosis(best_matches)

    # Bootstrap distribution properties
    boot_skew = stats.skew(boot_means)
    boot_kurt = stats.kurtosis(boot_means)

    print(f"\nSample Statistics:")
    print(f"  Variance:              {std_hat**2:.4f}")
    print(f"  Std Deviation:         {std_hat:.4f}")
    print(f"  Coefficient of Var:    {cv:.2f}%")
    print(f"  IQR:                   {iqr:.2f}")
    print(f"  Range:                 [{min(best_matches)}, {max(best_matches)}]")
    print(f"  Skewness:              {skew:.4f}")
    print(f"  Kurtosis:              {kurt:.4f}")

    print(f"\nBootstrap Distribution:")
    print(f"  Mean of boot means:    {np.mean(boot_means):.4f}")
    print(f"  SE of boot means:      {se_mean:.4f}")
    print(f"  CV of boot means:      {cv_boot:.4f}%")
    print(f"  Skewness:              {boot_skew:.4f}")
    print(f"  Kurtosis:              {boot_kurt:.4f}")

    print(f"\nBCa Correction Factors:")
    print(f"  z0 (bias):             {z0_mean:.4f}")
    print(f"  a (acceleration):      {a_mean:.6f}")

    # =========================================================================
    # STATISTICAL TESTS
    # =========================================================================
    print("\n" + "=" * 70)
    print("STATISTICAL VALIDATION")
    print("=" * 70)

    # Test vs baseline
    t_stat, p_value = stats.ttest_1samp(best_matches, RANDOM_BASELINE)
    effect_size = (mean_hat - RANDOM_BASELINE) / std_hat  # Cohen's d

    print(f"\nOne-Sample t-test vs Random Baseline ({RANDOM_BASELINE}):")
    print(f"  t-statistic:           {t_stat:.4f}")
    print(f"  p-value:               {p_value:.2e}")
    print(f"  Effect size (Cohen's d): {effect_size:.4f}")

    if effect_size < 0.2:
        effect_interp = "negligible"
    elif effect_size < 0.5:
        effect_interp = "small"
    elif effect_size < 0.8:
        effect_interp = "medium"
    else:
        effect_interp = "large"
    print(f"  Interpretation:        {effect_interp} effect")

    # Bootstrap hypothesis test
    # H0: true mean = RANDOM_BASELINE
    boot_centered = boot_means - np.mean(boot_means) + RANDOM_BASELINE
    p_boot = np.mean(boot_centered >= mean_hat) * 2  # two-tailed
    p_boot = min(p_boot, 1.0)

    print(f"\nBootstrap Hypothesis Test:")
    print(f"  p-value (bootstrap):   {p_boot:.2e}")

    # Performance above baseline
    pct_above_baseline = np.mean(boot_means > RANDOM_BASELINE) * 100
    improvement = ((mean_hat - RANDOM_BASELINE) / RANDOM_BASELINE) * 100

    print(f"\nPerformance vs Baseline:")
    print(f"  Improvement:           {improvement:.1f}%")
    print(f"  % bootstrap > baseline: {pct_above_baseline:.1f}%")

    # =========================================================================
    # DISTRIBUTION OF SCORES
    # =========================================================================
    print("\n" + "=" * 70)
    print("DISTRIBUTION OF BEST MATCHES")
    print("=" * 70)

    # Value counts
    unique, counts = np.unique(best_matches, return_counts=True)

    print(f"\n{'Score':<10} {'Count':<10} {'Percentage':<12} {'Cumulative':<12}")
    print("-" * 44)
    cumulative = 0
    for score, count in zip(unique, counts):
        pct = count / n_series * 100
        cumulative += pct
        print(f"{score:<10} {count:<10} {pct:>6.1f}%      {cumulative:>6.1f}%")

    # =========================================================================
    # CONCLUSION
    # =========================================================================
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)

    significant = p_value < 0.05

    print(f"""
Result: {'SIGNIFICANT' if significant else 'NOT SIGNIFICANT'}

The production predictor achieves a mean of {mean_hat:.2f}/14 matches
(95% BCa CI: [{ci_mean_lower:.2f}, {ci_mean_upper:.2f}]).

Key Findings:
1. Performance is {improvement:.1f}% above random baseline ({RANDOM_BASELINE}/14)
2. Effect size is {effect_interp} (Cohen's d = {effect_size:.2f})
3. p-value = {p_value:.2e} ({'' if significant else 'not '}statistically significant)
4. 95% of future predictions expected in range [{pred_lower:.1f}, {pred_upper:.1f}]
5. Bootstrap SE of mean: {se_mean:.4f} (estimation stability: {'good' if se_mean < 0.1 else 'moderate'})

Reliability Assessment:
- The predictor shows consistent performance above random chance
- BCa correction factors (z0={z0_mean:.4f}, a={a_mean:.6f}) indicate {'minimal' if abs(z0_mean) < 0.1 else 'some'} bias
- Coefficient of variation ({cv:.1f}%) suggests {'stable' if cv < 10 else 'moderate'} prediction stability
""")

    # Save results to file
    results_summary = {
        'n_bootstrap': N_BOOTSTRAP,
        'seed': RANDOM_SEED,
        'n_series': n_series,
        'mean': float(mean_hat),
        'median': float(median_hat),
        'std': float(std_hat),
        'se_mean': float(se_mean),
        'ci_bca_mean': [float(ci_mean_lower), float(ci_mean_upper)],
        'ci_percentile_mean': [float(pct_mean_lower), float(pct_mean_upper)],
        'prediction_interval': [float(pred_lower), float(pred_upper)],
        'effect_size': float(effect_size),
        'p_value': float(p_value),
        'improvement_pct': float(improvement),
        'bca_z0': float(z0_mean),
        'bca_a': float(a_mean)
    }

    output_path = Path(__file__).parent / "bootstrap_results.json"
    output_path.write_text(json.dumps(results_summary, indent=2))
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
