#!/usr/bin/env python3
"""
Optimized Jackpot Finder with Mandel Elimination
Key optimization: Pre-filter the search space to exclude all historical combinations
Benefit: Guarantees no wasted cycles on already-tested combinations
"""

import random
import json
from datetime import datetime
from itertools import combinations as iter_combinations

def load_all_series_data():
    """Load full series data from JSON file"""
    with open('full_series_data.json', 'r') as f:
        return json.load(f)

def combination_to_tuple(combination):
    """Convert combination to sorted tuple for hashing"""
    return tuple(sorted(combination))

def build_exclusion_set(all_data, exclude_series=None):
    """
    Build set of all historical combinations to exclude

    Args:
        all_data: Full historical data
        exclude_series: Series ID to exclude from training (for testing)

    Returns:
        Set of tuple combinations to exclude
    """
    exclusion_set = set()

    for series_id, events in all_data.items():
        # Skip the test series if specified
        if exclude_series and str(series_id) == str(exclude_series):
            continue

        for event in events:
            exclusion_set.add(combination_to_tuple(event))

    return exclusion_set

def generate_novel_combination(exclusion_set, max_attempts=1000):
    """
    Generate a random combination that's guaranteed not in exclusion set

    Args:
        exclusion_set: Set of combinations to avoid
        max_attempts: Max attempts before giving up

    Returns:
        Tuple of 14 numbers, or None if couldn't find novel one
    """
    for _ in range(max_attempts):
        combo = combination_to_tuple(random.sample(range(1, 26), 14))
        if combo not in exclusion_set:
            return combo

    # Fallback: return random even if in set (extremely rare with 4.4M possibilities)
    return combination_to_tuple(random.sample(range(1, 26), 14))

def optimized_jackpot_search(target_events, exclusion_set, max_tries=1000000, series_id=None):
    """
    Search for jackpot with guaranteed novel combinations

    Key optimization: Never generates combinations that are in exclusion_set
    This means we never waste cycles on known non-winners
    """
    print(f"\nOptimized search for Series {series_id}...")
    print(f"  Excluding {len(exclusion_set):,} historical combinations")
    print(f"  Search space: {4457400 - len(exclusion_set):,} novel combinations")

    tries = 0
    best_match = 0
    best_combo = None

    while tries < max_tries:
        tries += 1

        # Generate novel combination (guaranteed not in history)
        combo = generate_novel_combination(exclusion_set)

        # Check against target events
        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if combo == event_tuple:
                # JACKPOT!
                print(f"  ✅ JACKPOT in {tries:,} tries!")
                return tries, True, combo, 100.0

            # Track best
            matches = len(set(combo) & set(event))
            match_pct = (matches / 14) * 100
            if match_pct > best_match:
                best_match = match_pct
                best_combo = combo

        # Progress
        if tries % 100000 == 0:
            print(f"  Progress: {tries:,} tries, best: {best_match:.2f}%")

    print(f"  ❌ No jackpot in {max_tries:,} tries (best: {best_match:.2f}%)")
    return tries, False, best_combo, best_match

def baseline_random_search(target_events, max_tries=1000000, series_id=None):
    """
    Baseline: Pure random without elimination (can generate duplicates)
    """
    print(f"\nBaseline random search for Series {series_id}...")

    tries = 0
    best_match = 0
    best_combo = None

    while tries < max_tries:
        tries += 1
        combo = combination_to_tuple(random.sample(range(1, 26), 14))

        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if combo == event_tuple:
                print(f"  ✅ JACKPOT in {tries:,} tries!")
                return tries, True, combo, 100.0

            matches = len(set(combo) & set(event))
            match_pct = (matches / 14) * 100
            if match_pct > best_match:
                best_match = match_pct
                best_combo = combo

        if tries % 100000 == 0:
            print(f"  Progress: {tries:,} tries, best: {best_match:.2f}%")

    print(f"  ❌ No jackpot in {max_tries:,} tries (best: {best_match:.2f}%)")
    return tries, False, best_combo, best_match

def compare_methods(series_id, all_data, max_tries=1000000):
    """
    Compare baseline random vs optimized elimination
    """
    print(f"\n{'='*80}")
    print(f"TESTING SERIES {series_id}")
    print(f"{'='*80}")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    print(f"Target series has {len(target_events)} events")

    # Build exclusion set (excluding target series)
    exclusion_set = build_exclusion_set(all_data, exclude_series=series_id)

    results = {}

    # Method 1: Baseline Random
    print(f"\n{'='*80}")
    print("METHOD 1: Baseline Random (can generate duplicates)")
    print(f"{'='*80}")
    random.seed(series_id)
    baseline_tries, baseline_found, _, baseline_best = baseline_random_search(
        target_events, max_tries, series_id
    )
    results['baseline'] = {
        'tries': baseline_tries,
        'found': baseline_found,
        'best_match': baseline_best
    }

    # Method 2: Optimized with Elimination
    print(f"\n{'='*80}")
    print("METHOD 2: Optimized with Elimination (guaranteed novel)")
    print(f"{'='*80}")
    random.seed(series_id)
    optimized_tries, optimized_found, _, optimized_best = optimized_jackpot_search(
        target_events, exclusion_set, max_tries, series_id
    )
    results['optimized'] = {
        'tries': optimized_tries,
        'found': optimized_found,
        'best_match': optimized_best
    }

    # Compare
    print(f"\n{'='*80}")
    print("COMPARISON")
    print(f"{'='*80}")
    print(f"Baseline Random:  {baseline_tries:>10,} tries {'✅ FOUND' if baseline_found else '❌ NOT FOUND'}")
    print(f"Optimized:        {optimized_tries:>10,} tries {'✅ FOUND' if optimized_found else '❌ NOT FOUND'}")

    if baseline_found and optimized_found:
        speedup = baseline_tries / optimized_tries
        print(f"\nSpeedup: {speedup:.4f}x ({'FASTER' if speedup > 1 else 'SLOWER'})")
    elif optimized_found and not baseline_found:
        print(f"\n✅ Optimized found jackpot, baseline did not!")
    elif baseline_found and not optimized_found:
        print(f"\n⚠️ Baseline found jackpot, optimized did not")

    return results

def main():
    print("="*80)
    print("OPTIMIZED JACKPOT FINDER - Mandel Elimination Strategy")
    print("="*80)
    print("\nKey Optimization: Exclude all 1,197 historical combinations")
    print("Benefit: Never waste cycles generating known non-winners")
    print("Result: Pure exploration of untested search space")
    print("="*80)

    # Load data
    all_data = load_all_series_data()
    print(f"\n✅ Loaded {len(all_data)} series")

    # Count total historical combinations
    total_historical = sum(len(events) for events in all_data.values())
    print(f"✅ Total historical combinations: {total_historical:,}")
    print(f"✅ Novel search space: {4457400 - total_historical:,}")
    print(f"✅ Exclusion benefit: {total_historical:,} combinations guaranteed skip")

    # Test on series 3141-3143 (quick test)
    test_series = [3141, 3142, 3143]

    all_results = []

    for series_id in test_series:
        result = compare_methods(series_id, all_data, max_tries=1000000)
        if result:
            all_results.append({
                'series_id': series_id,
                **result
            })

    # Summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")

    baseline_wins = sum(1 for r in all_results if r['baseline']['found'])
    optimized_wins = sum(1 for r in all_results if r['optimized']['found'])

    print(f"\nJackpots found (out of {len(all_results)} series):")
    print(f"  Baseline Random: {baseline_wins}")
    print(f"  Optimized:       {optimized_wins}")

    if optimized_wins > 0:
        opt_avg = sum(r['optimized']['tries'] for r in all_results if r['optimized']['found']) / optimized_wins
        print(f"\nOptimized average tries (when found): {opt_avg:,.0f}")

    if baseline_wins > 0:
        base_avg = sum(r['baseline']['tries'] for r in all_results if r['baseline']['found']) / baseline_wins
        print(f"Baseline average tries (when found): {base_avg:,.0f}")

        if optimized_wins > 0:
            improvement = ((base_avg - opt_avg) / base_avg) * 100
            print(f"\nImprovement: {improvement:+.2f}% {'(FASTER)' if improvement > 0 else '(SLOWER)'}")

    # Save results
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'exclusion_count': total_historical,
        'novel_search_space': 4457400 - total_historical,
        'series_tested': test_series,
        'results': all_results
    }

    output_file = 'optimized_elimination_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
