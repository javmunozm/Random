#!/usr/bin/env python3
"""
Enhanced Mandel-Style Jackpot Finder
Uses multiple elimination strategies to reduce search space:
1. Eliminate previously used combinations
2. Eliminate statistical outliers (number frequency constraints)
3. Eliminate pattern violations (based on historical patterns)
4. Use systematic coverage (Mandel's key strategy)
"""

import random
import json
from datetime import datetime
from collections import Counter
from itertools import combinations as iter_combinations

def load_all_series_data():
    """Load full series data from JSON file"""
    with open('full_series_data.json', 'r') as f:
        return json.load(f)

def combination_to_tuple(combination):
    """Convert combination to sorted tuple"""
    return tuple(sorted(combination))

def build_elimination_sets(all_data):
    """Build sets of combinations to eliminate"""
    print("Building elimination sets...")

    # 1. Previously used combinations
    used_combinations = set()
    for series_id, events in all_data.items():
        for event in events:
            used_combinations.add(combination_to_tuple(event))

    print(f"  ✓ Eliminating {len(used_combinations)} previously used combinations")

    # 2. Analyze number frequency patterns
    number_frequency = Counter()
    for events in all_data.values():
        for event in events:
            for number in event:
                number_frequency[number] += 1

    total_events = sum(len(events) for events in all_data.values())
    avg_per_event = {n: count / total_events for n, count in number_frequency.items()}

    # Numbers that appear significantly more/less than average
    hot_numbers = [n for n, freq in avg_per_event.items() if freq > 0.60]  # >60% of events
    cold_numbers = [n for n, freq in avg_per_event.items() if freq < 0.45]  # <45% of events

    print(f"  ✓ Hot numbers (>60%): {hot_numbers}")
    print(f"  ✓ Cold numbers (<45%): {cold_numbers}")

    return {
        'used_combinations': used_combinations,
        'hot_numbers': hot_numbers,
        'cold_numbers': cold_numbers,
        'number_frequency': number_frequency,
        'avg_per_event': avg_per_event
    }

def passes_statistical_constraints(combination, elimination_data):
    """Check if combination passes statistical constraints"""
    # Count hot/cold numbers in combination
    hot_count = sum(1 for n in combination if n in elimination_data['hot_numbers'])
    cold_count = sum(1 for n in combination if n in elimination_data['cold_numbers'])

    # Constraint: Don't allow too many cold numbers (unlikely to all appear together)
    if cold_count > 4:  # More than 4 cold numbers is suspicious
        return False

    # Constraint: Should have at least some hot numbers
    if hot_count == 0:  # No hot numbers at all is unlikely
        return False

    return True

def generate_constrained_random_combination(elimination_data):
    """Generate random combination that passes constraints"""
    max_attempts = 100
    for _ in range(max_attempts):
        combo = tuple(sorted(random.sample(range(1, 26), 14)))

        # Check if previously used
        if combo in elimination_data['used_combinations']:
            continue

        # Check statistical constraints
        if not passes_statistical_constraints(combo, elimination_data):
            continue

        return combo

    # Fallback: return pure random if can't find constrained one
    return tuple(sorted(random.sample(range(1, 26), 14)))

def mandel_systematic_search(target_events, elimination_data, max_tries=1000000):
    """
    Enhanced Mandel-style systematic search for jackpot
    Uses elimination and statistical constraints
    """
    print("\nStarting Mandel-enhanced systematic search...")

    tries = 0
    best_match = 0
    best_combination = None

    while tries < max_tries:
        tries += 1

        # Generate constrained combination
        combination = generate_constrained_random_combination(elimination_data)

        # Check against all events
        for event in target_events:
            event_tuple = combination_to_tuple(event)
            if combination == event_tuple:
                # JACKPOT!
                return tries, True, combination, 100.0

            # Track best match
            matches = len(set(combination) & set(event))
            match_pct = (matches / 14) * 100
            if match_pct > best_match:
                best_match = match_pct
                best_combination = combination

        # Progress
        if tries % 100000 == 0:
            print(f"  Progress: {tries:,} tries, best: {best_match:.2f}%")

    return tries, False, best_combination, best_match

def compare_search_strategies(series_id, all_data):
    """
    Compare three strategies:
    1. Pure random (baseline)
    2. Simple elimination (exclude used only)
    3. Enhanced Mandel (multiple constraints)
    """
    print(f"\n{'='*80}")
    print(f"TESTING SERIES {series_id}")
    print(f"{'='*80}")

    # Get target events
    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found in data")
        return None

    target_events = all_data[series_key]
    print(f"Target series has {len(target_events)} events")

    # Build elimination data (excluding target series)
    training_data = {k: v for k, v in all_data.items() if k != series_key}
    elimination_data = build_elimination_sets(training_data)

    max_tries_per_method = 1000000

    results = {}

    # Strategy 1: Pure Random (baseline)
    print(f"\n🎲 Strategy 1: Pure Random")
    random.seed(series_id)
    pure_random_tries, pure_found, _, pure_best = pure_random_search(
        target_events, max_tries_per_method
    )
    results['pure_random'] = {
        'tries': pure_random_tries,
        'found': pure_found,
        'best_match': pure_best
    }
    print(f"  Result: {'JACKPOT!' if pure_found else f'Best {pure_best:.2f}%'} in {pure_random_tries:,} tries")

    # Strategy 2: Simple Elimination
    print(f"\n🚫 Strategy 2: Simple Elimination (exclude {len(elimination_data['used_combinations'])} used)")
    random.seed(series_id)
    simple_tries, simple_found, _, simple_best = simple_elimination_search(
        target_events, elimination_data['used_combinations'], max_tries_per_method
    )
    results['simple_elimination'] = {
        'tries': simple_tries,
        'found': simple_found,
        'best_match': simple_best
    }
    print(f"  Result: {'JACKPOT!' if simple_found else f'Best {simple_best:.2f}%'} in {simple_tries:,} tries")

    # Strategy 3: Enhanced Mandel
    print(f"\n🎯 Strategy 3: Enhanced Mandel (constraints + elimination)")
    random.seed(series_id)
    mandel_tries, mandel_found, _, mandel_best = mandel_systematic_search(
        target_events, elimination_data, max_tries_per_method
    )
    results['enhanced_mandel'] = {
        'tries': mandel_tries,
        'found': mandel_found,
        'best_match': mandel_best
    }
    print(f"  Result: {'JACKPOT!' if mandel_found else f'Best {mandel_best:.2f}%'} in {mandel_tries:,} tries")

    # Compare
    print(f"\n📊 COMPARISON:")
    print(f"  Pure Random:        {results['pure_random']['tries']:>10,} tries")
    print(f"  Simple Elimination: {results['simple_elimination']['tries']:>10,} tries")
    print(f"  Enhanced Mandel:    {results['enhanced_mandel']['tries']:>10,} tries")

    if results['enhanced_mandel']['found']:
        improvement_vs_random = (results['pure_random']['tries'] / results['enhanced_mandel']['tries'])
        improvement_vs_simple = (results['simple_elimination']['tries'] / results['enhanced_mandel']['tries'])
        print(f"\n  Enhanced Mandel vs Pure Random: {improvement_vs_random:.2f}x faster")
        print(f"  Enhanced Mandel vs Simple:      {improvement_vs_simple:.2f}x faster")

    return results

def pure_random_search(target_events, max_tries):
    """Pure random search - baseline"""
    tries = 0
    best_match = 0
    best_combo = None

    while tries < max_tries:
        tries += 1
        combo = tuple(sorted(random.sample(range(1, 26), 14)))

        for event in target_events:
            event_tuple = combination_to_tuple(event)
            if combo == event_tuple:
                return tries, True, combo, 100.0

            matches = len(set(combo) & set(event))
            match_pct = (matches / 14) * 100
            if match_pct > best_match:
                best_match = match_pct
                best_combo = combo

        if tries % 100000 == 0:
            print(f"  Progress: {tries:,} tries, best: {best_match:.2f}%")

    return tries, False, best_combo, best_match

def simple_elimination_search(target_events, used_combinations, max_tries):
    """Search with simple elimination of used combinations"""
    tries = 0
    best_match = 0
    best_combo = None

    while tries < max_tries:
        tries += 1
        combo = tuple(sorted(random.sample(range(1, 26), 14)))

        # Skip if used before
        if combo in used_combinations:
            continue

        for event in target_events:
            event_tuple = combination_to_tuple(event)
            if combo == event_tuple:
                return tries, True, combo, 100.0

            matches = len(set(combo) & set(event))
            match_pct = (matches / 14) * 100
            if match_pct > best_match:
                best_match = match_pct
                best_combo = combo

        if tries % 100000 == 0:
            print(f"  Progress: {tries:,} tries, best: {best_match:.2f}%")

    return tries, False, best_combo, best_match

def main():
    print("="*80)
    print("ENHANCED MANDEL-STYLE JACKPOT FINDER")
    print("="*80)
    print("\nStrategies tested:")
    print("  1. Pure Random (baseline)")
    print("  2. Simple Elimination (exclude previously used)")
    print("  3. Enhanced Mandel (elimination + statistical constraints)")
    print("="*80)

    # Load data
    all_data = load_all_series_data()
    print(f"\n✅ Loaded {len(all_data)} series")

    # Test on series 3141-3150 (same as jackpot simulation)
    test_series = range(3141, 3151)

    all_results = []

    for series_id in test_series:
        result = compare_search_strategies(series_id, all_data)
        if result:
            all_results.append({
                'series_id': series_id,
                **result
            })

    # Summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")

    pure_wins = sum(1 for r in all_results if r['pure_random']['found'])
    simple_wins = sum(1 for r in all_results if r['simple_elimination']['found'])
    mandel_wins = sum(1 for r in all_results if r['enhanced_mandel']['found'])

    print(f"\nJackpots found (out of {len(all_results)} series):")
    print(f"  Pure Random:        {pure_wins}")
    print(f"  Simple Elimination: {simple_wins}")
    print(f"  Enhanced Mandel:    {mandel_wins}")

    if mandel_wins > 0:
        mandel_avg = sum(r['enhanced_mandel']['tries'] for r in all_results if r['enhanced_mandel']['found']) / mandel_wins
        print(f"\nEnhanced Mandel average tries (when found): {mandel_avg:,.0f}")

    # Save results
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'series_tested': list(test_series),
        'results': all_results,
        'summary': {
            'pure_random_jackpots': pure_wins,
            'simple_elimination_jackpots': simple_wins,
            'enhanced_mandel_jackpots': mandel_wins
        }
    }

    output_file = 'mandel_enhanced_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
