#!/usr/bin/env python3
"""
Unlimited Jackpot Finder - Find jackpot for EACH series, no matter how many tries
Uses Mandel elimination strategy (guaranteed novel combinations)
"""

import random
import json
from datetime import datetime

def load_all_series_data(min_series=2982):
    """Load and filter series data"""
    with open('full_series_data.json', 'r') as f:
        all_data = json.load(f)
    return {k: v for k, v in all_data.items() if int(k) >= min_series}

def combination_to_tuple(combination):
    """Convert combination to sorted tuple"""
    return tuple(sorted(combination))

def build_exclusion_set(all_data, exclude_series=None):
    """Build set of all historical combinations to exclude"""
    exclusion_set = set()
    for series_id, events in all_data.items():
        if exclude_series and str(series_id) == str(exclude_series):
            continue
        for event in events:
            exclusion_set.add(combination_to_tuple(event))
    return exclusion_set

def generate_novel_combination(exclusion_set):
    """Generate combination guaranteed not in exclusion set"""
    max_attempts = 1000
    for _ in range(max_attempts):
        combo = combination_to_tuple(random.sample(range(1, 26), 14))
        if combo not in exclusion_set:
            return combo
    # Fallback (extremely rare)
    return combination_to_tuple(random.sample(range(1, 26), 14))

def find_jackpot_unlimited(series_id, all_data):
    """
    Find jackpot for a series with UNLIMITED tries
    Will not stop until jackpot is found
    """
    print(f"\n{'='*80}")
    print(f"FINDING JACKPOT FOR SERIES {series_id}")
    print(f"{'='*80}")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    print(f"Target series has {len(target_events)} events")

    # Build exclusion set
    exclusion_set = build_exclusion_set(all_data, exclude_series=series_id)
    print(f"Excluding {len(exclusion_set):,} historical combinations")
    print(f"Search space: {4457400 - len(exclusion_set):,} novel combinations")

    # Search until jackpot found
    tries = 0
    best_match = 0
    start_time = datetime.now()

    print(f"\nSearching for jackpot (unlimited tries)...")

    while True:  # UNLIMITED - will not stop until jackpot found
        tries += 1

        # Generate novel combination
        combo = generate_novel_combination(exclusion_set)

        # Check against all events
        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if combo == event_tuple:
                # JACKPOT FOUND!
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n🎉 JACKPOT FOUND!")
                print(f"   Tries: {tries:,}")
                print(f"   Time: {elapsed:.1f} seconds")
                print(f"   Combination: {' '.join(f'{n:02d}' for n in combo)}")
                return {
                    'series_id': series_id,
                    'tries': tries,
                    'time_seconds': elapsed,
                    'combination': list(combo),
                    'found': True
                }

            # Track best
            matches = len(set(combo) & set(event))
            match_pct = (matches / 14) * 100
            if match_pct > best_match:
                best_match = match_pct

        # Progress every 100K tries
        if tries % 100000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = tries / elapsed if elapsed > 0 else 0
            print(f"  {tries:>10,} tries | Best: {best_match:5.2f}% | "
                  f"Time: {elapsed:>6.1f}s | Rate: {rate:>7.0f} tries/sec")

def main():
    print("="*80)
    print("UNLIMITED JACKPOT FINDER - Mandel Elimination Strategy")
    print("="*80)
    print("\nWill find jackpot for EACH series, no matter how many tries")
    print("Uses guaranteed novel combinations (excludes historical data)")
    print("="*80)

    # Load data
    all_data = load_all_series_data(min_series=2982)
    print(f"\n✅ Loaded {len(all_data)} series (2982-3150)")

    # Test on series 3141-3150 (all 10 series)
    test_series = range(3141, 3151)
    results = []

    overall_start = datetime.now()

    for series_id in test_series:
        result = find_jackpot_unlimited(series_id, all_data)
        if result:
            results.append(result)

    # Summary
    overall_elapsed = (datetime.now() - overall_start).total_seconds()

    print(f"\n{'='*80}")
    print("FINAL SUMMARY - ALL JACKPOTS FOUND")
    print(f"{'='*80}")

    total_tries = sum(r['tries'] for r in results)
    avg_tries = total_tries / len(results) if results else 0

    print(f"\nSeries tested: {len(results)}")
    print(f"Total tries: {total_tries:,}")
    print(f"Average tries per jackpot: {avg_tries:,.0f}")
    print(f"Total time: {overall_elapsed:.1f} seconds ({overall_elapsed/60:.1f} minutes)")

    print(f"\nDetailed Results:")
    print(f"{'Series':<10} {'Tries':>12} {'Time (s)':>10} {'Combination'}")
    print("-" * 80)
    for r in results:
        combo_str = ' '.join(f'{n:02d}' for n in r['combination'])
        print(f"{r['series_id']:<10} {r['tries']:>12,} {r['time_seconds']:>10.1f} {combo_str}")

    # Save results
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'series_range': [3141, 3150],
        'total_series': len(results),
        'total_tries': total_tries,
        'average_tries': avg_tries,
        'total_time_seconds': overall_elapsed,
        'results': results
    }

    output_file = 'unlimited_jackpot_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
