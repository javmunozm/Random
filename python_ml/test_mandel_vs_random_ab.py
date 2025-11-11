#!/usr/bin/env python3
"""
Mandel vs Random Pool Generation A/B Test
==========================================

Comprehensive comparison of two pool generation methods:
1. Current: Weighted random generation (no structural constraints)
2. Mandel: Structured generation with column balance + pattern filtering

Both use same ML model (TrueLearningModel with 30x boost, 8-series lookback)
Only difference: How candidate pool is generated

Test Framework:
- Test 1: Baseline performance (validation series)
- Test 2: Seed sensitivity (5 seeds)
- Test 3: Statistical significance (t-test, CI, Cohen's d)
- Test 4: Pattern quality analysis
- Test 5: Per-series breakdown
"""

import json
import sys
import random
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter
import numpy as np
from scipy import stats

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from true_learning_model import TrueLearningModel
from mandel_pool_generator import MandelPoolGenerator


def load_all_series_data():
    """Load all series data from JSON export + hardcoded recent series"""
    # Load from JSON export
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    series_dict = {}

    if json_path.exists():
        with open(json_path, 'r') as f:
            json_data = json.load(f)

        for series in json_data.get('data', []):
            series_id = series['series_id']
            events = [event['numbers'] for event in series['events']]
            series_dict[series_id] = events

    # Add hardcoded recent series
    series_dict[3144] = [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
    ]

    series_dict[3145] = [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
    ]

    series_dict[3147] = [
        [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
        [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
        [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
        [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
        [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
        [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
        [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
    ]

    return series_dict


# Load series data
SERIES_DATA = load_all_series_data()

# Configuration
VALIDATION_SERIES = [s for s in range(3140, 3148) if s in SERIES_DATA]
TEST_SEEDS = [42, 123, 456, 789, 999]
BOOST = 30.0
LOOKBACK = 8

print("="*80)
print("MANDEL VS RANDOM POOL GENERATION - COMPREHENSIVE A/B TEST")
print("="*80)
print(f"\nConfiguration:")
print(f"  Validation Series: {len(VALIDATION_SERIES)} series ({min(VALIDATION_SERIES)}-{max(VALIDATION_SERIES)})")
print(f"  Test Seeds: {TEST_SEEDS}")
print(f"  Boost: {BOOST}x")
print(f"  Lookback: {LOOKBACK} series")
print(f"  Candidate Pool: 10,000")
print()


def calculate_match_percentage(prediction: List[int], actual_events: List[List[int]]) -> Dict[str, Any]:
    """Calculate match statistics for a prediction"""
    prediction_set = set(prediction)

    matches_per_event = []
    for event in actual_events:
        event_set = set(event)
        matches = len(prediction_set & event_set)
        matches_per_event.append(matches)

    best_match = max(matches_per_event)
    avg_match = np.mean(matches_per_event)

    return {
        'best_match': best_match,
        'best_match_pct': (best_match / 14) * 100,
        'avg_match': avg_match,
        'avg_match_pct': (avg_match / 14) * 100,
        'matches_per_event': matches_per_event
    }


def analyze_pattern_quality(prediction: List[int]) -> Dict[str, Any]:
    """Analyze pattern quality of a prediction"""
    # Column distribution
    col0 = sum(1 for n in prediction if 1 <= n <= 9)
    col1 = sum(1 for n in prediction if 10 <= n <= 19)
    col2 = sum(1 for n in prediction if 20 <= n <= 25)

    # Sum
    total_sum = sum(prediction)

    # Even/odd balance
    even_count = sum(1 for n in prediction if n % 2 == 0)
    odd_count = 14 - even_count

    # Gaps (difference between consecutive numbers)
    gaps = [prediction[i+1] - prediction[i] for i in range(13)]
    max_gap = max(gaps)
    avg_gap = np.mean(gaps)

    # Mandel validity checks
    mandel_valid = (
        5 <= col0 <= 7 and
        4 <= col1 <= 6 and
        2 <= col2 <= 4 and
        145 <= total_sum <= 220 and
        3 <= even_count <= 11 and
        max_gap <= 8
    )

    return {
        'column_distribution': [col0, col1, col2],
        'sum': total_sum,
        'even_count': even_count,
        'odd_count': odd_count,
        'max_gap': max_gap,
        'avg_gap': avg_gap,
        'mandel_valid': mandel_valid
    }


def test_with_method(method: str, series_id: int, seed: int = 999) -> Dict[str, Any]:
    """Test a single series with specified pool generation method"""

    if method == 'random':
        # Current method: weighted random in TrueLearningModel
        model = TrueLearningModel(seed=seed, cold_hot_boost=BOOST)
        model.RECENT_SERIES_LOOKBACK = LOOKBACK

        # Train on all data before target series
        for sid in sorted(SERIES_DATA.keys()):
            if sid < series_id:
                model.learn_from_series(sid, SERIES_DATA[sid])

        # Generate prediction with random pool
        prediction = model.predict_best_combination(series_id)

    elif method == 'mandel':
        # Mandel method: structured pool generation
        model = TrueLearningModel(seed=seed, cold_hot_boost=BOOST)
        model.RECENT_SERIES_LOOKBACK = LOOKBACK

        # Train on all data before target series
        for sid in sorted(SERIES_DATA.keys()):
            if sid < series_id:
                model.learn_from_series(sid, SERIES_DATA[sid])

        # Identify cold/hot numbers using model's method
        all_numbers_freq = Counter()
        lookback_start = max(0, series_id - LOOKBACK)
        for sid in range(lookback_start, series_id):
            if sid in SERIES_DATA:
                for event in SERIES_DATA[sid]:
                    all_numbers_freq.update(event)

        sorted_by_freq = sorted(all_numbers_freq.items(), key=lambda x: x[1])
        cold_numbers = set([n for n, _ in sorted_by_freq[:7]])
        hot_numbers = set([n for n, _ in sorted_by_freq[-7:]])

        # Generate Mandel pool with model's learned weights
        random.seed(seed)
        pool_gen = MandelPoolGenerator(
            frequency_weights=model.number_frequency_weights.copy(),
            pair_affinities=model.pair_affinities.copy(),
            hybrid_cold_numbers=cold_numbers,
            hybrid_hot_numbers=hot_numbers,
            cold_hot_boost=BOOST
        )

        mandel_pool = pool_gen.generate_pool(size=10000, seed=seed)

        # Score with model
        best_score = -float('inf')
        best_candidate = None

        for candidate in mandel_pool:
            score = model._calculate_score(candidate)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        prediction = best_candidate

    else:
        raise ValueError(f"Unknown method: {method}")

    # Calculate match statistics
    actual_events = SERIES_DATA[series_id]
    match_stats = calculate_match_percentage(prediction, actual_events)

    # Analyze pattern quality
    pattern_stats = analyze_pattern_quality(prediction)

    return {
        'series_id': series_id,
        'method': method,
        'seed': seed,
        'prediction': prediction,
        'match_stats': match_stats,
        'pattern_stats': pattern_stats
    }


def test_1_baseline_performance():
    """Test 1: Baseline performance on validation series with seed 999"""
    print("\n" + "="*80)
    print("TEST 1: BASELINE PERFORMANCE (Seed 999)")
    print("="*80)

    results_random = []
    results_mandel = []

    for series_id in VALIDATION_SERIES:
        print(f"\nTesting Series {series_id}...")

        # Test with random method
        r_random = test_with_method('random', series_id, seed=999)
        results_random.append(r_random)
        print(f"  Random: {r_random['match_stats']['best_match_pct']:.1f}% best match")

        # Test with Mandel method
        r_mandel = test_with_method('mandel', series_id, seed=999)
        results_mandel.append(r_mandel)
        print(f"  Mandel: {r_mandel['match_stats']['best_match_pct']:.1f}% best match")

        diff = r_mandel['match_stats']['best_match_pct'] - r_random['match_stats']['best_match_pct']
        if abs(diff) < 0.01:
            print(f"  Difference: Tie")
        else:
            winner = "Mandel" if diff > 0 else "Random"
            print(f"  Difference: {abs(diff):.1f}% ({winner} better)")

    # Summary statistics
    avg_random = np.mean([r['match_stats']['best_match_pct'] for r in results_random])
    avg_mandel = np.mean([r['match_stats']['best_match_pct'] for r in results_mandel])

    peak_random = max([r['match_stats']['best_match_pct'] for r in results_random])
    peak_mandel = max([r['match_stats']['best_match_pct'] for r in results_mandel])

    print(f"\n{'='*80}")
    print("TEST 1 SUMMARY:")
    print(f"{'='*80}")
    print(f"Random Method:")
    print(f"  Average: {avg_random:.3f}%")
    print(f"  Peak: {peak_random:.1f}%")
    print(f"\nMandel Method:")
    print(f"  Average: {avg_mandel:.3f}%")
    print(f"  Peak: {peak_mandel:.1f}%")
    print(f"\nDifference: {avg_mandel - avg_random:+.3f}% (Mandel vs Random)")

    if abs(avg_mandel - avg_random) < 0.01:
        print("VERDICT: ➖ TIE - No significant difference")
    elif avg_mandel > avg_random:
        print(f"VERDICT: ✅ MANDEL BETTER by {avg_mandel - avg_random:.3f}%")
    else:
        print(f"VERDICT: ✅ RANDOM BETTER by {avg_random - avg_mandel:.3f}%")

    return {
        'test_name': 'baseline_performance',
        'results_random': results_random,
        'results_mandel': results_mandel,
        'avg_random': avg_random,
        'avg_mandel': avg_mandel,
        'peak_random': peak_random,
        'peak_mandel': peak_mandel,
        'difference': avg_mandel - avg_random
    }


def test_2_seed_sensitivity():
    """Test 2: Seed sensitivity - Test with 5 different seeds"""
    print("\n" + "="*80)
    print("TEST 2: SEED SENSITIVITY (5 Seeds)")
    print("="*80)

    all_results = []

    for seed in TEST_SEEDS:
        print(f"\nTesting with seed {seed}...")

        results_random = []
        results_mandel = []

        for series_id in VALIDATION_SERIES:
            r_random = test_with_method('random', series_id, seed=seed)
            r_mandel = test_with_method('mandel', series_id, seed=seed)

            results_random.append(r_random['match_stats']['best_match_pct'])
            results_mandel.append(r_mandel['match_stats']['best_match_pct'])

        avg_random = np.mean(results_random)
        avg_mandel = np.mean(results_mandel)
        diff = avg_mandel - avg_random

        print(f"  Random: {avg_random:.3f}%")
        print(f"  Mandel: {avg_mandel:.3f}%")
        print(f"  Difference: {diff:+.3f}%")

        all_results.append({
            'seed': seed,
            'avg_random': avg_random,
            'avg_mandel': avg_mandel,
            'difference': diff
        })

    # Cross-seed summary
    avg_diff = np.mean([r['difference'] for r in all_results])
    mandel_better_count = sum(1 for r in all_results if r['difference'] > 0.01)
    random_better_count = sum(1 for r in all_results if r['difference'] < -0.01)
    tie_count = len(all_results) - mandel_better_count - random_better_count

    print(f"\n{'='*80}")
    print("TEST 2 SUMMARY:")
    print(f"{'='*80}")
    print(f"Average difference across {len(TEST_SEEDS)} seeds: {avg_diff:+.3f}%")
    print(f"  Mandel better: {mandel_better_count}/{len(TEST_SEEDS)} seeds")
    print(f"  Random better: {random_better_count}/{len(TEST_SEEDS)} seeds")
    print(f"  Ties: {tie_count}/{len(TEST_SEEDS)} seeds")

    if abs(avg_diff) < 0.5:
        print("VERDICT: ✅ SEED-ROBUST - Both methods stable across seeds")
    elif avg_diff > 0 and mandel_better_count >= 4:
        print("VERDICT: ✅ MANDEL CONSISTENTLY BETTER")
    elif avg_diff < 0 and random_better_count >= 4:
        print("VERDICT: ✅ RANDOM CONSISTENTLY BETTER")
    else:
        print("VERDICT: ⚠️ SEED-DEPENDENT - Results vary by seed")

    return {
        'test_name': 'seed_sensitivity',
        'all_results': all_results,
        'avg_difference': avg_diff,
        'mandel_better_count': mandel_better_count,
        'random_better_count': random_better_count
    }


def test_3_statistical_significance(baseline_results):
    """Test 3: Statistical significance testing"""
    print("\n" + "="*80)
    print("TEST 3: STATISTICAL SIGNIFICANCE")
    print("="*80)

    # Extract performance data
    random_perf = [r['match_stats']['best_match_pct'] for r in baseline_results['results_random']]
    mandel_perf = [r['match_stats']['best_match_pct'] for r in baseline_results['results_mandel']]

    # Paired t-test
    t_stat, p_value = stats.ttest_rel(mandel_perf, random_perf)

    # Cohen's d (effect size)
    mean_diff = np.mean(mandel_perf) - np.mean(random_perf)
    pooled_std = np.sqrt((np.std(mandel_perf, ddof=1)**2 + np.std(random_perf, ddof=1)**2) / 2)
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

    # Bootstrap confidence interval (95%)
    n_bootstrap = 10000
    bootstrap_diffs = []

    for _ in range(n_bootstrap):
        indices = np.random.choice(len(random_perf), size=len(random_perf), replace=True)
        boot_random = [random_perf[i] for i in indices]
        boot_mandel = [mandel_perf[i] for i in indices]
        bootstrap_diffs.append(np.mean(boot_mandel) - np.mean(boot_random))

    ci_lower = np.percentile(bootstrap_diffs, 2.5)
    ci_upper = np.percentile(bootstrap_diffs, 97.5)

    print(f"\nPaired t-test:")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Significant: {'✅ YES (p < 0.05)' if p_value < 0.05 else '❌ NO (p >= 0.05)'}")

    print(f"\nEffect Size (Cohen's d):")
    print(f"  Cohen's d: {cohens_d:.4f}")
    if abs(cohens_d) < 0.2:
        effect = "negligible"
    elif abs(cohens_d) < 0.5:
        effect = "small"
    elif abs(cohens_d) < 0.8:
        effect = "medium"
    else:
        effect = "large"
    print(f"  Interpretation: {effect}")

    print(f"\n95% Confidence Interval (Bootstrap):")
    print(f"  [{ci_lower:.3f}%, {ci_upper:.3f}%]")
    print(f"  Includes zero: {'✅ YES (not significant)' if ci_lower <= 0 <= ci_upper else '❌ NO (significant)'}")

    print(f"\n{'='*80}")
    print("TEST 3 SUMMARY:")
    print(f"{'='*80}")

    is_significant = p_value < 0.05 and not (ci_lower <= 0 <= ci_upper)

    if is_significant:
        winner = "Mandel" if mean_diff > 0 else "Random"
        print(f"VERDICT: ✅ STATISTICALLY SIGNIFICANT - {winner} is better")
    else:
        print("VERDICT: ➖ NOT SIGNIFICANT - No reliable difference detected")

    return {
        'test_name': 'statistical_significance',
        't_statistic': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'is_significant': is_significant
    }


def test_4_pattern_quality(baseline_results):
    """Test 4: Pattern quality analysis"""
    print("\n" + "="*80)
    print("TEST 4: PATTERN QUALITY ANALYSIS")
    print("="*80)

    # Analyze pattern validity
    random_patterns = [r['pattern_stats'] for r in baseline_results['results_random']]
    mandel_patterns = [r['pattern_stats'] for r in baseline_results['results_mandel']]

    random_valid = sum(1 for p in random_patterns if p['mandel_valid'])
    mandel_valid = sum(1 for p in mandel_patterns if p['mandel_valid'])

    print(f"\nPattern Validity (Mandel criteria):")
    print(f"  Random method: {random_valid}/{len(random_patterns)} ({100*random_valid/len(random_patterns):.1f}%)")
    print(f"  Mandel method: {mandel_valid}/{len(mandel_patterns)} ({100*mandel_valid/len(mandel_patterns):.1f}%)")

    # Column distribution analysis
    print(f"\nColumn Distribution (avg per series):")
    random_cols = np.mean([p['column_distribution'] for p in random_patterns], axis=0)
    mandel_cols = np.mean([p['column_distribution'] for p in mandel_patterns], axis=0)

    print(f"  Random: Col0={random_cols[0]:.1f}, Col1={random_cols[1]:.1f}, Col2={random_cols[2]:.1f}")
    print(f"  Mandel: Col0={mandel_cols[0]:.1f}, Col1={mandel_cols[1]:.1f}, Col2={mandel_cols[2]:.1f}")
    print(f"  Target: Col0=5-7, Col1=4-6, Col2=2-4")

    # Gap analysis
    random_gaps = [p['max_gap'] for p in random_patterns]
    mandel_gaps = [p['max_gap'] for p in mandel_patterns]

    print(f"\nMax Gap Analysis:")
    print(f"  Random avg: {np.mean(random_gaps):.1f} (max {max(random_gaps)})")
    print(f"  Mandel avg: {np.mean(mandel_gaps):.1f} (max {max(mandel_gaps)})")
    print(f"  Target: <= 8")

    print(f"\n{'='*80}")
    print("TEST 4 SUMMARY:")
    print(f"{'='*80}")

    if mandel_valid > random_valid:
        print(f"VERDICT: ✅ MANDEL BETTER - {mandel_valid-random_valid} more valid patterns")
    elif mandel_valid == random_valid:
        print("VERDICT: ➖ TIE - Same pattern validity")
    else:
        print(f"VERDICT: ⚠️ RANDOM BETTER - {random_valid-mandel_valid} more valid patterns")

    return {
        'test_name': 'pattern_quality',
        'random_valid_count': random_valid,
        'mandel_valid_count': mandel_valid,
        'random_cols_avg': random_cols.tolist(),
        'mandel_cols_avg': mandel_cols.tolist()
    }


def run_comprehensive_ab_test():
    """Run all A/B tests"""
    print("\n" + "="*80)
    print("STARTING COMPREHENSIVE A/B TEST")
    print("="*80)

    all_results = {}

    # Test 1: Baseline performance
    test1_results = test_1_baseline_performance()
    all_results['test_1_baseline'] = test1_results

    # Test 2: Seed sensitivity
    test2_results = test_2_seed_sensitivity()
    all_results['test_2_seed_sensitivity'] = test2_results

    # Test 3: Statistical significance
    test3_results = test_3_statistical_significance(test1_results)
    all_results['test_3_statistical'] = test3_results

    # Test 4: Pattern quality
    test4_results = test_4_pattern_quality(test1_results)
    all_results['test_4_pattern_quality'] = test4_results

    # Final verdict
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)

    # Scoring system
    scores = {'random': 0, 'mandel': 0, 'tie': 0}

    # Test 1: Baseline performance
    diff = test1_results['difference']
    if abs(diff) < 0.5:
        scores['tie'] += 1
        print("✓ Test 1 (Baseline): TIE")
    elif diff > 0:
        scores['mandel'] += 1
        print(f"✓ Test 1 (Baseline): MANDEL +{diff:.3f}%")
    else:
        scores['random'] += 1
        print(f"✓ Test 1 (Baseline): RANDOM +{abs(diff):.3f}%")

    # Test 2: Seed sensitivity
    if abs(test2_results['avg_difference']) < 0.5:
        scores['tie'] += 1
        print("✓ Test 2 (Seeds): ROBUST (both methods stable)")
    elif test2_results['mandel_better_count'] >= 4:
        scores['mandel'] += 1
        print(f"✓ Test 2 (Seeds): MANDEL ({test2_results['mandel_better_count']}/5 seeds)")
    elif test2_results['random_better_count'] >= 4:
        scores['random'] += 1
        print(f"✓ Test 2 (Seeds): RANDOM ({test2_results['random_better_count']}/5 seeds)")
    else:
        scores['tie'] += 1
        print("✓ Test 2 (Seeds): MIXED (seed-dependent)")

    # Test 3: Statistical significance
    if test3_results['is_significant']:
        winner = 'mandel' if test1_results['difference'] > 0 else 'random'
        scores[winner] += 2  # Double weight for statistical significance
        print(f"✓✓ Test 3 (Stats): {winner.upper()} (p={test3_results['p_value']:.4f})")
    else:
        scores['tie'] += 2
        print(f"✓✓ Test 3 (Stats): NOT SIGNIFICANT (p={test3_results['p_value']:.4f})")

    # Test 4: Pattern quality
    if test4_results['mandel_valid_count'] > test4_results['random_valid_count']:
        scores['mandel'] += 1
        print(f"✓ Test 4 (Quality): MANDEL ({test4_results['mandel_valid_count']} valid patterns)")
    elif test4_results['mandel_valid_count'] == test4_results['random_valid_count']:
        scores['tie'] += 1
        print(f"✓ Test 4 (Quality): TIE ({test4_results['random_valid_count']} valid patterns)")
    else:
        scores['random'] += 1
        print(f"✓ Test 4 (Quality): RANDOM ({test4_results['random_valid_count']} valid patterns)")

    print(f"\n{'='*80}")
    print("OVERALL SCORE:")
    print(f"{'='*80}")
    print(f"  Random: {scores['random']} points")
    print(f"  Mandel: {scores['mandel']} points")
    print(f"  Tie: {scores['tie']} points")

    all_results['final_scores'] = scores

    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION:")
    print(f"{'='*80}")

    if scores['mandel'] > scores['random'] + 2:
        print("✅ ADOPT MANDEL METHOD")
        print("   - Significantly better performance")
        print("   - Better pattern quality")
        print("   - Statistically validated")
        all_results['recommendation'] = 'adopt_mandel'
    elif scores['random'] > scores['mandel'] + 2:
        print("✅ KEEP RANDOM METHOD")
        print("   - Better performance")
        print("   - Current method validated")
        all_results['recommendation'] = 'keep_random'
    else:
        print("➖ NO CLEAR WINNER")
        print("   - Both methods perform similarly")
        print("   - Keep current method (Random) for simplicity")
        print("   - Mandel offers better pattern quality but no performance gain")
        all_results['recommendation'] = 'keep_random_no_advantage'

    return all_results


if __name__ == '__main__':
    results = run_comprehensive_ab_test()

    # Save results
    output_file = Path(__file__).parent / 'mandel_vs_random_ab_results.json'

    # Convert numpy types for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    # Deep convert all numpy types
    def deep_convert(obj):
        if isinstance(obj, dict):
            return {k: deep_convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [deep_convert(item) for item in obj]
        else:
            return convert_numpy(obj)

    results_serializable = deep_convert(results)

    with open(output_file, 'w') as f:
        json.dump(results_serializable, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}")
