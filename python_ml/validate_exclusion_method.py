#!/usr/bin/env python3
"""
Validate exclusion-based prediction method on historical data
Test if excluding least-frequent numbers successfully captures actual jackpots
"""

import json
from itertools import combinations
from collections import Counter

def analyze_and_predict_with_exclusion(target_series_id, lookback_series):
    """
    Use exclusion strategy to predict target series based on lookback data

    Args:
        target_series_id: Series to predict (e.g., 3151)
        lookback_series: List of series IDs to analyze (e.g., [3146, 3147, 3148, 3149, 3150])

    Returns:
        dict with prediction and validation results
    """
    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    # Count appearances in lookback series
    appearance_counter = Counter()
    total_events = 0

    for sid in lookback_series:
        for event in data[str(sid)]:
            total_events += 1
            for num in event:
                appearance_counter[num] += 1

    # Calculate appearance rates
    all_numbers = set(range(1, 26))
    number_frequencies = {num: appearance_counter.get(num, 0) / total_events for num in all_numbers}

    # Sort by frequency (ascending - least likely first)
    sorted_by_freq = sorted(number_frequencies.items(), key=lambda x: x[1])

    # Exclude bottom 4 numbers
    exclusion_list = [num for num, _ in sorted_by_freq[:4]]
    inclusion_pool = sorted([n for n in all_numbers if n not in exclusion_list])

    # Get actual results for target series
    actual_events = data[str(target_series_id)]

    # Check coverage: how many actual jackpots are in our predicted pool?
    coverage_results = []
    for i, actual_event in enumerate(actual_events, 1):
        actual_set = set(actual_event)
        predicted_set = set(inclusion_pool)

        overlap = actual_set & predicted_set
        coverage_pct = len(overlap) / 14 * 100

        # Check if this exact combination is in our pool
        exact_match = actual_set.issubset(predicted_set)

        coverage_results.append({
            'event': i,
            'actual': sorted(actual_event),
            'overlap': sorted(overlap),
            'coverage': len(overlap),
            'coverage_pct': coverage_pct,
            'exact_match': exact_match,
            'excluded_in_actual': sorted(actual_set - predicted_set)
        })

    return {
        'target_series': target_series_id,
        'lookback_series': lookback_series,
        'exclusion_list': exclusion_list,
        'inclusion_pool': inclusion_pool,
        'pool_size': len(inclusion_pool),
        'total_combinations': len(list(combinations(inclusion_pool, 14))),
        'coverage_results': coverage_results
    }

def validate_exclusion_on_multiple_series(test_range_start, test_range_end, lookback_count=5):
    """
    Validate exclusion method across multiple historical series

    Args:
        test_range_start: First series to test (e.g., 3147)
        test_range_end: Last series to test (e.g., 3151)
        lookback_count: Number of previous series to analyze (default: 5)
    """

    print("="*80)
    print("EXCLUSION METHOD VALIDATION - HISTORICAL TESTING")
    print("="*80)
    print(f"\nTesting on Series {test_range_start}-{test_range_end}")
    print(f"Using {lookback_count} series lookback for each prediction\n")

    all_results = []

    for target_id in range(test_range_start, test_range_end + 1):
        # Get lookback series (previous N series)
        lookback_series = list(range(target_id - lookback_count, target_id))

        print(f"\n{'='*80}")
        print(f"PREDICTING SERIES {target_id}")
        print(f"{'='*80}")
        print(f"Using lookback: {lookback_series}")

        result = analyze_and_predict_with_exclusion(target_id, lookback_series)

        print(f"\nExcluded numbers: {result['exclusion_list']}")
        print(f"Inclusion pool ({len(result['inclusion_pool'])} numbers): {result['inclusion_pool']}")
        print(f"Total combinations: {result['total_combinations']:,}")

        print(f"\nCoverage Results:")
        print(f"{'Event':<8} {'Coverage':<12} {'%':<8} {'Exact Match':<12} {'Excluded in Actual'}")
        print("-" * 80)

        exact_matches = 0
        total_coverage = []

        for cr in result['coverage_results']:
            exact_str = "✅ YES" if cr['exact_match'] else "❌ NO"
            excluded_str = str(cr['excluded_in_actual']) if cr['excluded_in_actual'] else "None"

            print(f"Event {cr['event']:<3} {cr['coverage']}/14{'':<7} {cr['coverage_pct']:>5.1f}%   {exact_str:<12} {excluded_str}")

            if cr['exact_match']:
                exact_matches += 1
            total_coverage.append(cr['coverage'])

        avg_coverage = sum(total_coverage) / len(total_coverage)
        avg_coverage_pct = avg_coverage / 14 * 100
        exact_match_rate = exact_matches / 7 * 100

        print(f"\nSummary for Series {target_id}:")
        print(f"  Average coverage: {avg_coverage:.1f}/14 ({avg_coverage_pct:.1f}%)")
        print(f"  Exact matches: {exact_matches}/7 ({exact_match_rate:.1f}%)")
        print(f"  Pool size: {len(result['inclusion_pool'])} numbers")
        print(f"  Space reduction: {(1 - result['total_combinations'] / 4457400) * 100:.1f}%")

        result['summary'] = {
            'avg_coverage': avg_coverage,
            'avg_coverage_pct': avg_coverage_pct,
            'exact_matches': exact_matches,
            'exact_match_rate': exact_match_rate
        }

        all_results.append(result)

    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL VALIDATION SUMMARY")
    print(f"{'='*80}\n")

    total_exact_matches = sum(r['summary']['exact_matches'] for r in all_results)
    total_events = len(all_results) * 7
    overall_exact_rate = total_exact_matches / total_events * 100

    avg_coverage_all = sum(r['summary']['avg_coverage'] for r in all_results) / len(all_results)
    avg_coverage_pct_all = avg_coverage_all / 14 * 100

    avg_pool_size = sum(len(r['inclusion_pool']) for r in all_results) / len(all_results)

    print(f"Series tested: {len(all_results)}")
    print(f"Total events: {total_events}")
    print(f"Total exact matches: {total_exact_matches}/{total_events} ({overall_exact_rate:.1f}%)")
    print(f"Average coverage: {avg_coverage_all:.1f}/14 ({avg_coverage_pct_all:.1f}%)")
    print(f"Average pool size: {avg_pool_size:.1f} numbers")
    print(f"Average space reduction: {(1 - (sum(r['total_combinations'] for r in all_results) / len(all_results)) / 4457400) * 100:.1f}%")

    # Detailed breakdown
    print(f"\n{'Series':<10} {'Exact Matches':<15} {'Avg Coverage':<15} {'Pool Size':<12}")
    print("-" * 80)
    for r in all_results:
        print(f"{r['target_series']:<10} {r['summary']['exact_matches']}/7 ({r['summary']['exact_match_rate']:>4.1f}%){'':<3} "
              f"{r['summary']['avg_coverage']:>4.1f}/14 ({r['summary']['avg_coverage_pct']:>4.1f}%){'':<2} {len(r['inclusion_pool'])}")

    # Save results
    with open('exclusion_validation_results.json', 'w') as f:
        json.dump({
            'test_range': f"{test_range_start}-{test_range_end}",
            'lookback_count': lookback_count,
            'overall_summary': {
                'total_exact_matches': total_exact_matches,
                'total_events': total_events,
                'overall_exact_rate': overall_exact_rate,
                'avg_coverage': avg_coverage_all,
                'avg_coverage_pct': avg_coverage_pct_all,
                'avg_pool_size': avg_pool_size
            },
            'detailed_results': all_results
        }, f, indent=2)

    print(f"\n📁 Results saved to: exclusion_validation_results.json")

    return all_results

if __name__ == '__main__':
    # Test on Series 3147-3151 (last 5 series)
    # Using 5-series lookback for each prediction
    validate_exclusion_on_multiple_series(3147, 3151, lookback_count=5)
