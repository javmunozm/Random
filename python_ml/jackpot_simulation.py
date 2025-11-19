#!/usr/bin/env python3
"""
Jackpot Simulation: Determine how many tries to hit perfect 14/14 match
Tests series 3141-3150 to understand jackpot difficulty
"""

import random
import json
from datetime import datetime

# Load all series data from JSON
def load_all_series_data():
    """Load full series data from JSON file"""
    with open('full_series_data.json', 'r') as f:
        return json.load(f)

# Load actual results for a series
def load_series_results(series_id, all_data=None):
    """Load all 7 events for a given series"""
    if all_data is None:
        all_data = load_all_series_data()

    series_key = str(series_id)
    if series_key not in all_data:
        return []

    events = all_data[series_key]
    # Ensure events are sorted
    return [sorted(event) for event in events]

# Generate random combination
def generate_random_combination():
    """Generate random 14 numbers from 1-25"""
    return sorted(random.sample(range(1, 26), 14))

# Check if combination matches any event exactly
def is_jackpot(combination, events):
    """Check if combination matches any of the 7 events perfectly (14/14)"""
    for event in events:
        if combination == event:
            return True
    return False

# Calculate match score
def calculate_match(combination, events):
    """Calculate best match percentage against all events"""
    best_match = 0
    for event in events:
        matches = len(set(combination) & set(event))
        match_pct = (matches / 14) * 100
        best_match = max(best_match, match_pct)
    return best_match

# Simulate tries to jackpot for one series
def simulate_tries_to_jackpot(series_id, max_tries=10000000, seed=None, all_data=None):
    """
    Simulate random tries until hitting jackpot (14/14 match)
    Returns: (tries, found, best_match_before_jackpot)
    """
    if seed is not None:
        random.seed(seed)

    print(f"\nSimulating Series {series_id}...")
    events = load_series_results(series_id, all_data)

    if len(events) != 7:
        print(f"WARNING: Series {series_id} has {len(events)} events (expected 7)")
        return None, False, 0

    tries = 0
    best_match_overall = 0

    # Show progress every 10K tries
    while tries < max_tries:
        tries += 1
        combination = generate_random_combination()

        # Calculate match before checking jackpot
        match_score = calculate_match(combination, events)
        best_match_overall = max(best_match_overall, match_score)

        # Check for jackpot
        if is_jackpot(combination, events):
            print(f"✅ JACKPOT! Found in {tries:,} tries")
            return tries, True, best_match_overall

        # Progress indicator
        if tries % 100000 == 0:
            print(f"  Progress: {tries:,} tries, best match so far: {best_match_overall:.2f}%")

    print(f"❌ No jackpot found in {max_tries:,} tries (best: {best_match_overall:.2f}%)")
    return max_tries, False, best_match_overall

# Test GA-optimized combination
def test_ga_combination(series_id, all_data=None):
    """Test the GA-optimized combination (seed 331) against a series"""
    ga_combination = [1, 2, 4, 5, 6, 8, 9, 10, 12, 14, 16, 20, 21, 22]
    events = load_series_results(series_id, all_data)

    # Check if jackpot
    is_jp = is_jackpot(ga_combination, events)

    # Calculate match
    match_score = calculate_match(ga_combination, events)

    return {
        'series_id': series_id,
        'combination': ga_combination,
        'is_jackpot': is_jp,
        'match_score': match_score
    }

# Main simulation
def main():
    print("="*80)
    print("JACKPOT SIMULATION: Series 3141-3150")
    print("="*80)
    print("\nObjective: Determine how many random tries to hit 14/14 perfect match")
    print("GA Combination (Seed 331): 01 02 04 05 06 08 09 10 12 14 16 20 21 22")
    print("\nNote: With C(25,14) = 4,457,400 possible combinations,")
    print("      expected tries to jackpot = ~635,000 per event (4,457,400 / 7)")
    print("="*80)

    results = []
    series_range = range(3141, 3151)  # 3141-3150

    # Load all data once
    print("\nLoading series data...")
    all_data = load_all_series_data()
    print(f"✅ Loaded data for {len(all_data)} series")

    # Test each series
    for series_id in series_range:
        print(f"\n{'='*80}")
        print(f"SERIES {series_id}")
        print(f"{'='*80}")

        # Test GA combination first
        ga_result = test_ga_combination(series_id, all_data)
        print(f"\nGA Combination Test:")
        print(f"  Match Score: {ga_result['match_score']:.2f}%")
        print(f"  Jackpot: {'YES! 🎉' if ga_result['is_jackpot'] else 'No'}")

        # Random simulation
        print(f"\nRandom Simulation (max 1,000,000 tries):")
        tries, found, best_match = simulate_tries_to_jackpot(
            series_id,
            max_tries=1000000,  # Limit to 1M to keep reasonable runtime
            seed=series_id,  # Use series_id as seed for reproducibility
            all_data=all_data
        )

        result = {
            'series_id': series_id,
            'random_tries': tries,
            'random_found': found,
            'random_best_match': best_match,
            'ga_match': ga_result['match_score'],
            'ga_jackpot': ga_result['is_jackpot']
        }
        results.append(result)

        print(f"\nSeries {series_id} Summary:")
        print(f"  Random: {tries:,} tries ({'JACKPOT!' if found else f'best {best_match:.2f}%'})")
        print(f"  GA: {ga_result['match_score']:.2f}% ({'JACKPOT!' if ga_result['is_jackpot'] else 'no jackpot'})")

    # Save results
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'series_range': [3141, 3150],
        'total_combinations_possible': 4457400,
        'expected_tries_per_event': 636771,  # 4,457,400 / 7
        'ga_combination': [1, 2, 4, 5, 6, 8, 9, 10, 12, 14, 16, 20, 21, 22],
        'results': results,
        'summary': {
            'total_series': len(results),
            'random_jackpots': sum(1 for r in results if r['random_found']),
            'ga_jackpots': sum(1 for r in results if r['ga_jackpot']),
            'avg_random_tries': sum(r['random_tries'] for r in results) / len(results),
            'avg_random_best_match': sum(r['random_best_match'] for r in results) / len(results),
            'avg_ga_match': sum(r['ga_match'] for r in results) / len(results)
        }
    }

    output_file = 'jackpot_simulation_3141_3150.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"\nTotal Series Tested: {len(results)}")
    print(f"Random Jackpots Found: {output['summary']['random_jackpots']}")
    print(f"GA Jackpots Found: {output['summary']['ga_jackpots']}")
    print(f"Avg Random Tries: {output['summary']['avg_random_tries']:,.0f}")
    print(f"Avg Random Best Match: {output['summary']['avg_random_best_match']:.2f}%")
    print(f"Avg GA Match: {output['summary']['avg_ga_match']:.2f}%")

    print(f"\n📁 Results saved to: {output_file}")
    print("="*80)

    # Create detailed report
    print("\nDETAILED RESULTS:")
    print("-" * 80)
    print(f"{'Series':<10} {'Random Tries':<15} {'Random Found':<15} {'Random Best':<15} {'GA Match':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['series_id']:<10} {r['random_tries']:>14,} {str(r['random_found']):<15} "
              f"{r['random_best_match']:>13.2f}% {r['ga_match']:>9.2f}%")
    print("-" * 80)

if __name__ == "__main__":
    main()
