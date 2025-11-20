#!/usr/bin/env python3
"""
Find jackpot for Series 3151 - determine how many tries needed
"""

import json
import random
from datetime import datetime


def load_series_data(file_path="full_series_data.json", min_series=2982):
    """Load and filter series data"""
    with open(file_path, 'r') as f:
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
    # Fallback
    return combination_to_tuple(random.sample(range(1, 26), 14))


def find_jackpot_unlimited(series_id, all_data):
    """Find jackpot with unlimited tries"""
    print(f"{'='*80}")
    print(f"FINDING JACKPOT FOR SERIES {series_id}")
    print(f"{'='*80}")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found in data")
        return None

    target_events = all_data[series_key]
    print(f"Target series has {len(target_events)} events")

    # Build exclusion set (exclude this series)
    exclusion_set = build_exclusion_set(all_data, exclude_series=series_id)
    print(f"Excluding {len(exclusion_set):,} historical combinations")
    print(f"Search space: {4457400 - len(exclusion_set):,} novel combinations")
    print()

    tries = 0
    best_match = 0
    start_time = datetime.now()

    print("Searching for jackpot (unlimited tries)...")

    while True:
        tries += 1

        # Generate novel combination
        combo = generate_novel_combination(exclusion_set)

        # Check against all events
        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if combo == event_tuple:
                # JACKPOT FOUND!
                elapsed = (datetime.now() - start_time).total_seconds()
                combo_str = ' '.join(f"{n:02d}" for n in combo)

                print(f"\n🎉 JACKPOT FOUND!")
                print(f"   Tries: {tries:,}")
                print(f"   Time: {elapsed:.1f} seconds")
                print(f"   Rate: {tries/elapsed:.0f} tries/sec")
                print(f"   Combination: {combo_str}")

                return {
                    'series_id': series_id,
                    'tries': tries,
                    'time_seconds': elapsed,
                    'rate': tries/elapsed,
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
    print("=" * 80)
    print("JACKPOT FINDER FOR SERIES 3151")
    print("=" * 80)
    print()
    print("Determining how many random tries needed to find 14/14 jackpot match")
    print("=" * 80)
    print()

    # Load data
    all_data = load_series_data(min_series=2982)
    print(f"✅ Loaded {len(all_data)} series (including 3151)")
    print()

    # Find jackpot for 3151
    result = find_jackpot_unlimited(3151, all_data)

    if result:
        print()
        print("=" * 80)
        print("FINAL RESULT")
        print("=" * 80)
        print()
        print(f"Series 3151 jackpot found after {result['tries']:,} tries")
        print(f"Time taken: {result['time_seconds']:.1f} seconds")
        print(f"Processing rate: {result['rate']:.0f} tries/second")
        print()

        combo_str = ' '.join(f"{n:02d}" for n in result['combination'])
        print(f"Jackpot combination: {combo_str}")
        print()

        # Save result
        output = {
            'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'series_id': 3151,
            'tries_to_jackpot': result['tries'],
            'time_seconds': result['time_seconds'],
            'processing_rate': result['rate'],
            'jackpot_combination': result['combination']
        }

        with open('series_3151_jackpot_tries.json', 'w') as f:
            json.dump(output, f, indent=2)

        print("📁 Results saved to: series_3151_jackpot_tries.json")
        print("=" * 80)


if __name__ == "__main__":
    main()
