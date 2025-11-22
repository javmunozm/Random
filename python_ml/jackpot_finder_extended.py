#!/usr/bin/env python3
"""
Extended Jackpot Finder - Series 3100-3152
Finds all jackpots via random generation with 1M tries limit per event
"""

import json
import random
from datetime import datetime

def find_all_jackpots_extended(start_series=3100, end_series=3152, max_tries=1000000):
    """Find jackpots for series range 3100-3152"""

    # Load data
    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    all_jackpots = []
    total_events = 0
    found_count = 0
    not_found_count = 0

    print("=" * 80)
    print(f"EXTENDED JACKPOT FINDER - Series {start_series}-{end_series}")
    print(f"Finding ALL jackpots with random generation")
    print(f"Max tries per event: {max_tries:,}")
    print("=" * 80)
    print()

    for series_id in range(start_series, end_series + 1):
        series_key = str(series_id)

        if series_key not in data:
            print(f"Series {series_id}: NOT IN DATASET - skipping")
            continue

        actual_events = data[series_key]
        series_found = 0
        series_tries = []

        for event_idx, event in enumerate(actual_events, 1):
            total_events += 1
            event_set = set(event)
            found = False

            for try_num in range(1, max_tries + 1):
                # Generate random combination
                prediction = sorted(random.sample(range(1, 26), 14))

                # Check if jackpot
                if set(prediction) == event_set:
                    found = True
                    found_count += 1
                    series_found += 1
                    series_tries.append(try_num)

                    all_jackpots.append({
                        'series': series_id,
                        'event': event_idx,
                        'tries': try_num,
                        'combination': event,
                        'prediction': prediction
                    })
                    break

            if not found:
                not_found_count += 1
                all_jackpots.append({
                    'series': series_id,
                    'event': event_idx,
                    'tries': None,
                    'combination': event,
                    'prediction': None
                })

        # Print series summary
        if series_tries:
            avg_tries = sum(series_tries) // len(series_tries)
            print(f"Series {series_id}: {series_found}/7 jackpots found, Avg tries: {avg_tries:,}")
        else:
            print(f"Series {series_id}: 0/7 found")

    print()
    print("=" * 80)
    print("EXTENDED ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Total events searched: {total_events}")
    print(f"Jackpots found: {found_count} ({found_count/total_events*100:.1f}%)")
    print(f"Jackpots not found: {not_found_count} ({not_found_count/total_events*100:.1f}%)")

    # Calculate statistics for found jackpots
    found_tries = [jp['tries'] for jp in all_jackpots if jp['tries'] is not None]
    if found_tries:
        print()
        print("STATISTICS (Found Jackpots):")
        print(f"  Minimum: {min(found_tries):,} tries")
        print(f"  Maximum: {max(found_tries):,} tries")
        print(f"  Average: {sum(found_tries) // len(found_tries):,} tries")
        print(f"  Median: {sorted(found_tries)[len(found_tries)//2]:,} tries")

    # Save results
    results = {
        'date': datetime.now().isoformat(),
        'series_range': f"{start_series}-{end_series}",
        'total_events': total_events,
        'found': found_count,
        'not_found': not_found_count,
        'max_tries_limit': max_tries,
        'jackpots': all_jackpots,
        'statistics': {
            'min_tries': min(found_tries) if found_tries else None,
            'max_tries': max(found_tries) if found_tries else None,
            'avg_tries': sum(found_tries) // len(found_tries) if found_tries else None,
            'median_tries': sorted(found_tries)[len(found_tries)//2] if found_tries else None
        }
    }

    output_file = f'jackpot_finder_extended_{start_series}_{end_series}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"📁 Results saved to: {output_file}")
    print("=" * 80)

    return results

if __name__ == '__main__':
    find_all_jackpots_extended(3100, 3152, max_tries=1000000)
