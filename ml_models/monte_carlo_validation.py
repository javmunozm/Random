#!/usr/bin/env python3
"""
Monte Carlo Validation for Production Predictor
================================================

Validates the 8-set hedge strategy against random baseline.

Statistical Methods:
- Hypergeometric distribution for random baseline (7.84/14)
- t-test for significance
- Cohen's d for effect size
- 95% confidence intervals
"""

import json
import numpy as np
from scipy import stats
from pathlib import Path
from collections import Counter
from datetime import datetime

# Import production predictor functions
from production_predictor import load_data, predict, evaluate, validate, latest

# Constants
TOTAL = 25
PICK = 14
BASELINE = PICK * PICK / TOTAL  # 7.84


class MonteCarloValidator:
    """Monte Carlo validation for production predictor."""

    def __init__(self, data, seed=42):
        self.data = data
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Theoretical baseline: E[X] = n*K/N = 14*14/25 = 7.84
        self.baseline_mean = PICK * PICK / TOTAL
        # Variance: n*K*(N-K)*(N-n) / (N^2*(N-1))
        self.baseline_var = PICK * PICK * (TOTAL-PICK) * (TOTAL-PICK) / (TOTAL**2 * (TOTAL-1))
        self.baseline_std = np.sqrt(self.baseline_var)

    def simulate_random(self, series_ids, n_sims=10000):
        """Simulate random selection performance."""
        print(f"\nSimulating {n_sims:,} random trials...")

        all_matches = []
        sim_avgs = []

        for sim in range(n_sims):
            if sim % 1000 == 0:
                print(f"  {sim:,}/{n_sims:,}", end='\r')

            sim_matches = []
            for sid in series_ids:
                events = self.data[str(sid)]
                # Random 14-number selection
                pred = set(self.rng.choice(range(1, TOTAL+1), size=PICK, replace=False))
                best = max(len(pred & set(e)) for e in events)
                sim_matches.append(best)
                all_matches.append(best)

            sim_avgs.append(np.mean(sim_matches))

        print(f"  {n_sims:,}/{n_sims:,} done")

        return np.array(all_matches), np.array(sim_avgs)

    def get_prediction_results(self, start, end):
        """Get actual prediction results from production predictor."""
        results = []
        for sid in range(start, end + 1):
            r = evaluate(self.data, sid)
            if r:
                results.append(r['best'])
        return np.array(results)

    def run_validation(self, start=2981, end=None, n_sims=10000):
        """Run full Monte Carlo validation."""
        if end is None:
            end = latest(self.data)

        series_ids = [sid for sid in range(start, end+1) if str(sid) in self.data]
        n_series = len(series_ids)

        print("=" * 70)
        print("MONTE CARLO VALIDATION - Production Predictor (12-Set)")
        print("=" * 70)
        print(f"Series range: {start}-{end} ({n_series} series)")
        print(f"Simulations:  {n_sims:,}")
        print(f"Seed:         {self.seed}")
        print(f"Baseline:     {self.baseline_mean:.2f}/14 (random)")

        # Get actual prediction results
        print("\nGetting prediction results...")
        pred_results = self.get_prediction_results(start, end)
        pred_mean = np.mean(pred_results)
        pred_std = np.std(pred_results)

        print(f"  Prediction mean: {pred_mean:.2f}/14")
        print(f"  Prediction std:  {pred_std:.2f}")

        # Simulate random baseline
        rand_matches, rand_avgs = self.simulate_random(series_ids, n_sims)
        rand_mean = np.mean(rand_matches)
        rand_std = np.std(rand_matches)

        # Statistical tests
        # t-test: Is prediction significantly better than baseline?
        t_stat, p_value = stats.ttest_1samp(pred_results, self.baseline_mean)

        # Cohen's d effect size
        pooled_std = np.sqrt((pred_std**2 + self.baseline_std**2) / 2)
        cohens_d = (pred_mean - self.baseline_mean) / pooled_std if pooled_std > 0 else 0

        # 95% confidence interval
        sem = stats.sem(pred_results)
        ci_low, ci_high = stats.t.interval(0.95, df=len(pred_results)-1,
                                            loc=pred_mean, scale=sem)

        # Percentile rank in random distribution
        percentile = stats.percentileofscore(rand_avgs, pred_mean)

        # Improvement
        improvement = pred_mean - self.baseline_mean
        improvement_pct = improvement / self.baseline_mean * 100

        # Effect size interpretation
        if abs(cohens_d) < 0.2:
            effect = "negligible"
        elif abs(cohens_d) < 0.5:
            effect = "small"
        elif abs(cohens_d) < 0.8:
            effect = "medium"
        else:
            effect = "large"

        # Match distribution
        pred_dist = Counter(pred_results)
        rand_dist = Counter(rand_matches)

        # Print results
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        print(f"\n{'METRIC':<25} {'PREDICTION':<15} {'RANDOM':<15} {'BASELINE'}")
        print("-" * 70)
        print(f"{'Mean':<25} {pred_mean:<15.4f} {rand_mean:<15.4f} {self.baseline_mean:.4f}")
        print(f"{'Std Dev':<25} {pred_std:<15.4f} {rand_std:<15.4f} {self.baseline_std:.4f}")
        print(f"{'Min':<25} {min(pred_results):<15d} {min(rand_matches):<15d}")
        print(f"{'Max':<25} {max(pred_results):<15d} {max(rand_matches):<15d}")

        print(f"\n{'STATISTICAL TESTS'}")
        print("-" * 70)
        print(f"{'Improvement':<25} +{improvement:.4f} ({improvement_pct:+.1f}%)")
        print(f"{'t-statistic':<25} {t_stat:.4f}")
        print(f"{'p-value':<25} {p_value:.2e}")
        print(f"{'Cohens d':<25} {cohens_d:.4f} ({effect.upper()})")
        print(f"{'95% CI':<25} [{ci_low:.4f}, {ci_high:.4f}]")
        print(f"{'Percentile vs random':<25} {percentile:.1f}%")

        print(f"\n{'MATCH DISTRIBUTION'}")
        print("-" * 70)
        print(f"{'Matches':<10} {'Prediction':<15} {'Random (sim)':<15} {'Pct Diff'}")
        for m in range(max(max(pred_dist.keys()), 14), min(min(pred_dist.keys()) if pred_dist else 0, 5) - 1, -1):
            p_count = pred_dist.get(m, 0)
            r_count = rand_dist.get(m, 0)
            p_pct = p_count / len(pred_results) * 100 if len(pred_results) > 0 else 0
            r_pct = r_count / len(rand_matches) * 100 if len(rand_matches) > 0 else 0
            diff = p_pct - r_pct
            if p_count > 0 or r_count > 0:
                print(f"{m:>2}/14      {p_count:>4} ({p_pct:>5.1f}%)    {r_count:>6} ({r_pct:>5.1f}%)   {diff:>+6.1f}%")

        print("\n" + "=" * 70)
        print("CONCLUSION")
        print("=" * 70)

        if p_value < 0.001:
            sig = "*** HIGHLY SIGNIFICANT (p < 0.001) ***"
        elif p_value < 0.01:
            sig = "** SIGNIFICANT (p < 0.01) **"
        elif p_value < 0.05:
            sig = "* SIGNIFICANT (p < 0.05) *"
        else:
            sig = "NOT SIGNIFICANT (p >= 0.05)"

        print(f"\n{sig}")
        print(f"\nThe production predictor achieves {pred_mean:.2f}/14 average,")
        print(f"which is +{improvement:.2f} ({improvement_pct:.1f}%) above the {self.baseline_mean:.2f} random baseline.")
        print(f"Effect size is {effect} (Cohen's d = {cohens_d:.2f}).")

        if percentile >= 99:
            print(f"Performance is in the top {100-percentile:.1f}% of random simulations.")

        # Build results dict
        results = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'series_range': [start, end],
                'n_series': n_series,
                'n_simulations': n_sims,
                'seed': self.seed
            },
            'prediction': {
                'mean': float(pred_mean),
                'std': float(pred_std),
                'min': int(min(pred_results)),
                'max': int(max(pred_results)),
                'ci_95': [float(ci_low), float(ci_high)],
                'distribution': {str(k): int(v) for k, v in pred_dist.items()}
            },
            'random_baseline': {
                'theoretical_mean': float(self.baseline_mean),
                'theoretical_std': float(self.baseline_std),
                'simulated_mean': float(rand_mean),
                'simulated_std': float(rand_std)
            },
            'statistics': {
                'improvement': float(improvement),
                'improvement_pct': float(improvement_pct),
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'cohens_d': float(cohens_d),
                'effect_size': effect,
                'percentile_rank': float(percentile),
                'significant_001': bool(p_value < 0.001),
                'significant_005': bool(p_value < 0.05)
            }
        }

        return results


def main():
    """Run Monte Carlo validation."""
    import argparse

    parser = argparse.ArgumentParser(description='Monte Carlo Validation')
    parser.add_argument('-n', '--sims', type=int, default=10000, help='Simulations (default: 10000)')
    parser.add_argument('-s', '--seed', type=int, default=42, help='Random seed (default: 42)')
    parser.add_argument('--start', type=int, default=2981, help='Start series (default: 2981)')
    parser.add_argument('--end', type=int, default=None, help='End series (default: latest)')
    parser.add_argument('-o', '--output', type=str, default=None, help='Output JSON file')

    args = parser.parse_args()

    data = load_data()
    validator = MonteCarloValidator(data, seed=args.seed)
    results = validator.run_validation(start=args.start, end=args.end, n_sims=args.sims)

    # Save results
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(__file__).parent / 'monte_carlo_results.json'

    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {out_path}")


if __name__ == '__main__':
    main()
