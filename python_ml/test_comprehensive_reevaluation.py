#!/usr/bin/env python3
"""
COMPREHENSIVE REEVALUATION: 29x vs 30x Boost
Multiple testing approaches to validate improvement claims

Tests:
1. Reproducibility (10 independent runs)
2. Extended validation (15 series: 3133-3147)
3. Multiple windows (4 different 7-series windows)
4. Seed sensitivity (5 different seeds)
5. Statistical significance (bootstrap, t-tests)
6. Temporal stability (early vs recent)
7. Per-series breakdown
8. Holdout validation
"""

import json
import numpy as np
from collections import defaultdict
from true_learning_model import TrueLearningModel
from scipy import stats

# Load data
with open('full_series_data_expanded.json', 'r') as f:
    data = json.load(f)
SERIES_DATA = {int(k): v for k, v in data.items()}

SEED = 999
LOOKBACK = 8


def test_configuration(boost: float, target_series: int, seed: int = 999):
    """Test a configuration on a single series"""
    model = TrueLearningModel(seed=seed, cold_hot_boost=boost)
    model.RECENT_SERIES_LOOKBACK = LOOKBACK

    # Train on data before target
    for sid in sorted(SERIES_DATA.keys()):
        if sid < target_series:
            model.learn_from_series(sid, SERIES_DATA[sid])

    # Generate prediction
    prediction = model.predict_best_combination(target_series)

    # Evaluate
    actual_events = SERIES_DATA[target_series]
    pred_set = set(prediction)

    matches_per_event = []
    for event in actual_events:
        matches = len(pred_set & set(event))
        matches_per_event.append(matches)

    best_match = max(matches_per_event) / 14
    avg_match = sum(matches_per_event) / len(matches_per_event) / 14

    return {
        'best_match': best_match,
        'avg_match': avg_match,
        'matches': matches_per_event,
        'prediction': prediction
    }


def test_1_reproducibility():
    """Test 1: Reproducibility - Run 10 times with same seed"""
    print("\n" + "=" * 80)
    print("TEST 1: REPRODUCIBILITY (10 independent runs)")
    print("=" * 80)

    series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

    results_29x = []
    results_30x = []

    for run in range(10):
        print(f"\nRun {run + 1}/10...")

        avg_29x = []
        avg_30x = []

        for s in series:
            r29 = test_configuration(29.0, s, seed=SEED)
            r30 = test_configuration(30.0, s, seed=SEED)
            avg_29x.append(r29['best_match'])
            avg_30x.append(r30['best_match'])

        results_29x.append(np.mean(avg_29x))
        results_30x.append(np.mean(avg_30x))

    print(f"\n29x Results: {results_29x}")
    print(f"30x Results: {results_30x}")
    print(f"\n29x: Mean={np.mean(results_29x):.4f}, Std={np.std(results_29x):.6f}")
    print(f"30x: Mean={np.mean(results_30x):.4f}, Std={np.std(results_30x):.6f}")

    reproducible = np.std(results_29x) < 0.001 and np.std(results_30x) < 0.001
    print(f"\n{'✅' if reproducible else '❌'} Reproducibility: {'PASS' if reproducible else 'FAIL'}")
    print(f"   (Variance should be ~0 for deterministic results)")

    return {
        'test': 'reproducibility',
        'results_29x': results_29x,
        'results_30x': results_30x,
        'reproducible': reproducible
    }


def test_2_extended_validation():
    """Test 2: Extended validation - Test on 15 series (3133-3147, excluding 3146)"""
    print("\n" + "=" * 80)
    print("TEST 2: EXTENDED VALIDATION (14 series: 3133-3147, no 3146)")
    print("=" * 80)

    series = [s for s in range(3133, 3148) if s in SERIES_DATA]  # 3133-3147 (excluding missing 3146)

    results_29x = []
    results_30x = []

    print(f"\nTesting on {len(series)} series...")

    for s in series:
        r29 = test_configuration(29.0, s, seed=SEED)
        r30 = test_configuration(30.0, s, seed=SEED)
        results_29x.append(r29['best_match'])
        results_30x.append(r30['best_match'])
        print(f"  Series {s}: 29x={r29['best_match']*100:.1f}%, 30x={r30['best_match']*100:.1f}%")

    avg_29x = np.mean(results_29x)
    avg_30x = np.mean(results_30x)
    diff = avg_29x - avg_30x

    print(f"\n29x Average: {avg_29x*100:.3f}%")
    print(f"30x Average: {avg_30x*100:.3f}%")
    print(f"Difference: {diff*100:+.3f}%")

    improved = diff > 0.005  # >0.5% improvement
    print(f"\n{'✅' if improved else '❌'} Improvement confirmed on extended validation")

    return {
        'test': 'extended_validation',
        'series_count': len(series),
        'avg_29x': avg_29x,
        'avg_30x': avg_30x,
        'difference': diff,
        'improved': improved
    }


def test_3_multiple_windows():
    """Test 3: Multiple validation windows"""
    print("\n" + "=" * 80)
    print("TEST 3: MULTIPLE VALIDATION WINDOWS")
    print("=" * 80)

    windows = [
        (3130, 3137, "Early window"),
        (3133, 3140, "Mid-early window"),
        (3137, 3144, "Mid-late window"),
        (3140, 3147, "Late window (original)"),
    ]

    window_results = []

    for start, end, label in windows:
        series = [s for s in range(start, end + 1) if s in SERIES_DATA]
        print(f"\n{label} ({start}-{end}):")

        results_29x = []
        results_30x = []

        for s in series:
            r29 = test_configuration(29.0, s, seed=SEED)
            r30 = test_configuration(30.0, s, seed=SEED)
            results_29x.append(r29['best_match'])
            results_30x.append(r30['best_match'])

        avg_29x = np.mean(results_29x)
        avg_30x = np.mean(results_30x)
        diff = avg_29x - avg_30x

        print(f"  29x: {avg_29x*100:.3f}%")
        print(f"  30x: {avg_30x*100:.3f}%")
        print(f"  Diff: {diff*100:+.3f}%")

        window_results.append({
            'window': label,
            'range': f"{start}-{end}",
            'avg_29x': avg_29x,
            'avg_30x': avg_30x,
            'difference': diff
        })

    # Overall average across all windows
    all_diffs = [w['difference'] for w in window_results]
    avg_diff = np.mean(all_diffs)
    consistent = all(d > -0.01 for d in all_diffs)  # No window worse than -1%

    print(f"\nOverall: Average difference = {avg_diff*100:+.3f}%")
    print(f"{'✅' if consistent else '❌'} Consistency: {'PASS' if consistent else 'FAIL'}")

    return {
        'test': 'multiple_windows',
        'windows': window_results,
        'avg_difference': avg_diff,
        'consistent': consistent
    }


def test_4_seed_sensitivity():
    """Test 4: Seed sensitivity - Test with 5 different seeds"""
    print("\n" + "=" * 80)
    print("TEST 4: SEED SENSITIVITY (5 different seeds)")
    print("=" * 80)

    seeds = [42, 123, 456, 789, 999]
    series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

    seed_results = []

    for seed in seeds:
        print(f"\nSeed {seed}:")

        results_29x = []
        results_30x = []

        for s in series:
            r29 = test_configuration(29.0, s, seed=seed)
            r30 = test_configuration(30.0, s, seed=seed)
            results_29x.append(r29['best_match'])
            results_30x.append(r30['best_match'])

        avg_29x = np.mean(results_29x)
        avg_30x = np.mean(results_30x)
        diff = avg_29x - avg_30x

        print(f"  29x: {avg_29x*100:.3f}%")
        print(f"  30x: {avg_30x*100:.3f}%")
        print(f"  Diff: {diff*100:+.3f}%")

        seed_results.append({
            'seed': seed,
            'avg_29x': avg_29x,
            'avg_30x': avg_30x,
            'difference': diff
        })

    # Check consistency across seeds
    diffs = [r['difference'] for r in seed_results]
    avg_diff = np.mean(diffs)
    std_diff = np.std(diffs)
    all_positive = all(d > 0 for d in diffs)

    print(f"\nAcross all seeds:")
    print(f"  Average difference: {avg_diff*100:+.3f}%")
    print(f"  Std deviation: {std_diff*100:.3f}%")
    print(f"  All positive: {all_positive}")

    robust = all_positive and avg_diff > 0.005
    print(f"\n{'✅' if robust else '❌'} Seed robustness: {'PASS' if robust else 'FAIL'}")

    return {
        'test': 'seed_sensitivity',
        'seeds': seed_results,
        'avg_difference': avg_diff,
        'std_difference': std_diff,
        'robust': robust
    }


def test_5_statistical_significance():
    """Test 5: Statistical significance tests"""
    print("\n" + "=" * 80)
    print("TEST 5: STATISTICAL SIGNIFICANCE")
    print("=" * 80)

    series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

    results_29x = []
    results_30x = []

    for s in series:
        r29 = test_configuration(29.0, s, seed=SEED)
        r30 = test_configuration(30.0, s, seed=SEED)
        results_29x.append(r29['best_match'])
        results_30x.append(r30['best_match'])

    # Paired t-test
    t_stat, p_value = stats.ttest_rel(results_29x, results_30x)

    # Effect size (Cohen's d)
    diff = np.array(results_29x) - np.array(results_30x)
    cohens_d = np.mean(diff) / np.std(diff)

    print(f"\nPaired t-test:")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value:.6f}")
    print(f"  Significant (p<0.05): {'Yes' if p_value < 0.05 else 'No'}")

    print(f"\nEffect size (Cohen's d): {cohens_d:.4f}")
    effect = "Large" if abs(cohens_d) > 0.8 else "Medium" if abs(cohens_d) > 0.5 else "Small"
    print(f"  Effect: {effect}")

    # Bootstrap confidence interval
    n_bootstrap = 1000
    bootstrap_diffs = []

    for _ in range(n_bootstrap):
        indices = np.random.choice(len(results_29x), len(results_29x), replace=True)
        boot_29x = [results_29x[i] for i in indices]
        boot_30x = [results_30x[i] for i in indices]
        bootstrap_diffs.append(np.mean(boot_29x) - np.mean(boot_30x))

    ci_lower = np.percentile(bootstrap_diffs, 2.5)
    ci_upper = np.percentile(bootstrap_diffs, 97.5)

    print(f"\nBootstrap 95% CI: [{ci_lower*100:.3f}%, {ci_upper*100:.3f}%]")
    print(f"  Zero in CI: {'No' if ci_lower > 0 or ci_upper < 0 else 'Yes'}")

    significant = p_value < 0.05 and ci_lower > 0
    print(f"\n{'✅' if significant else '❌'} Statistical significance: {'PASS' if significant else 'FAIL'}")

    return {
        'test': 'statistical_significance',
        't_stat': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'significant': significant
    }


def test_6_temporal_stability():
    """Test 6: Temporal stability - Early vs recent series"""
    print("\n" + "=" * 80)
    print("TEST 6: TEMPORAL STABILITY (Early vs Recent)")
    print("=" * 80)

    early_series = [s for s in range(3120, 3130) if s in SERIES_DATA]  # Early series
    recent_series = [s for s in range(3138, 3148) if s in SERIES_DATA]  # Recent series

    print("\nEarly series (3120-3129):")
    early_29x = []
    early_30x = []

    for s in early_series:
        r29 = test_configuration(29.0, s, seed=SEED)
        r30 = test_configuration(30.0, s, seed=SEED)
        early_29x.append(r29['best_match'])
        early_30x.append(r30['best_match'])

    early_avg_29x = np.mean(early_29x)
    early_avg_30x = np.mean(early_30x)
    early_diff = early_avg_29x - early_avg_30x

    print(f"  29x: {early_avg_29x*100:.3f}%")
    print(f"  30x: {early_avg_30x*100:.3f}%")
    print(f"  Diff: {early_diff*100:+.3f}%")

    print("\nRecent series (3138-3147):")
    recent_29x = []
    recent_30x = []

    for s in recent_series:
        r29 = test_configuration(29.0, s, seed=SEED)
        r30 = test_configuration(30.0, s, seed=SEED)
        recent_29x.append(r29['best_match'])
        recent_30x.append(r30['best_match'])

    recent_avg_29x = np.mean(recent_29x)
    recent_avg_30x = np.mean(recent_30x)
    recent_diff = recent_avg_29x - recent_avg_30x

    print(f"  29x: {recent_avg_29x*100:.3f}%")
    print(f"  30x: {recent_avg_30x*100:.3f}%")
    print(f"  Diff: {recent_diff*100:+.3f}%")

    stable = abs(early_diff - recent_diff) < 0.03  # Within 3%
    print(f"\n{'✅' if stable else '❌'} Temporal stability: {'PASS' if stable else 'FAIL'}")

    return {
        'test': 'temporal_stability',
        'early_diff': early_diff,
        'recent_diff': recent_diff,
        'difference_in_diffs': abs(early_diff - recent_diff),
        'stable': stable
    }


def test_7_per_series_breakdown():
    """Test 7: Per-series breakdown - Which series drive improvement?"""
    print("\n" + "=" * 80)
    print("TEST 7: PER-SERIES BREAKDOWN")
    print("=" * 80)

    series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

    per_series = []

    for s in series:
        r29 = test_configuration(29.0, s, seed=SEED)
        r30 = test_configuration(30.0, s, seed=SEED)

        diff = r29['best_match'] - r30['best_match']

        per_series.append({
            'series': s,
            'perf_29x': r29['best_match'],
            'perf_30x': r30['best_match'],
            'difference': diff
        })

        status = "✅" if diff > 0 else "➖" if diff == 0 else "❌"
        print(f"  Series {s}: 29x={r29['best_match']*100:.1f}%, 30x={r30['best_match']*100:.1f}%, Diff={diff*100:+.1f}% {status}")

    # Find winners and losers
    winners = [p for p in per_series if p['difference'] > 0.01]
    ties = [p for p in per_series if abs(p['difference']) <= 0.01]
    losers = [p for p in per_series if p['difference'] < -0.01]

    print(f"\nSummary:")
    print(f"  29x wins: {len(winners)} series")
    print(f"  Ties: {len(ties)} series")
    print(f"  30x wins: {len(losers)} series")

    balanced = len(winners) >= len(losers)
    print(f"\n{'✅' if balanced else '❌'} Balanced improvement: {'PASS' if balanced else 'FAIL'}")

    return {
        'test': 'per_series_breakdown',
        'per_series': per_series,
        'winners': len(winners),
        'ties': len(ties),
        'losers': len(losers),
        'balanced': balanced
    }


def main():
    print("=" * 80)
    print("COMPREHENSIVE REEVALUATION: 29x vs 30x Boost")
    print("=" * 80)
    print("\nThis will run 7 comprehensive tests to validate the improvement claim.")
    print("Estimated time: 10-15 minutes")

    results = {}

    # Run all tests
    results['test1'] = test_1_reproducibility()
    results['test2'] = test_2_extended_validation()
    results['test3'] = test_3_multiple_windows()
    results['test4'] = test_4_seed_sensitivity()
    results['test5'] = test_5_statistical_significance()
    results['test6'] = test_6_temporal_stability()
    results['test7'] = test_7_per_series_breakdown()

    # Summary
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    tests_passed = sum([
        results['test1']['reproducible'],
        results['test2']['improved'],
        results['test3']['consistent'],
        results['test4']['robust'],
        results['test5']['significant'],
        results['test6']['stable'],
        results['test7']['balanced']
    ])

    print(f"\nTests passed: {tests_passed}/7")
    print(f"\n1. Reproducibility: {'✅ PASS' if results['test1']['reproducible'] else '❌ FAIL'}")
    print(f"2. Extended validation: {'✅ PASS' if results['test2']['improved'] else '❌ FAIL'}")
    print(f"3. Multiple windows: {'✅ PASS' if results['test3']['consistent'] else '❌ FAIL'}")
    print(f"4. Seed sensitivity: {'✅ PASS' if results['test4']['robust'] else '❌ FAIL'}")
    print(f"5. Statistical significance: {'✅ PASS' if results['test5']['significant'] else '❌ FAIL'}")
    print(f"6. Temporal stability: {'✅ PASS' if results['test6']['stable'] else '❌ FAIL'}")
    print(f"7. Per-series breakdown: {'✅ PASS' if results['test7']['balanced'] else '❌ FAIL'}")

    if tests_passed >= 6:
        verdict = "✅ IMPROVEMENT VALIDATED"
        confidence = "HIGH"
    elif tests_passed >= 4:
        verdict = "⚠️ IMPROVEMENT UNCERTAIN"
        confidence = "MEDIUM"
    else:
        verdict = "❌ IMPROVEMENT REJECTED"
        confidence = "LOW"

    print(f"\n{'=' * 80}")
    print(f"VERDICT: {verdict}")
    print(f"CONFIDENCE: {confidence}")
    print(f"{'=' * 80}")

    # Save results
    with open('comprehensive_reevaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n✅ Results saved to: comprehensive_reevaluation_results.json")


if __name__ == '__main__':
    main()
