#!/usr/bin/env python3
"""Pure random baseline - no ML, no bias, just uniform random selection"""
import json
import random
from datetime import datetime

def load_all_series_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def build_exclusion_set(all_series_data, before_series_id):
    exclusion_set = set()
    for sid_str, events in all_series_data.items():
        if int(sid_str) < before_series_id:
            for event in events:
                exclusion_set.add(tuple(sorted(event)))
    return exclusion_set

def pure_random_search(series_id, all_data, exclusion_set):
    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    while True:
        combo = tuple(sorted(random.sample(range(1, 26), 14)))
        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)
        unique_tries += 1

        if unique_tries % 50000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  {unique_tries:,} tries | {elapsed:.1f}s | {unique_tries/elapsed:.0f}/sec")

        for event_num, target in enumerate(target_tuples, 1):
            if combo == target:
                elapsed = (datetime.now() - start_time).total_seconds()
                return {
                    'series_id': series_id,
                    'tries': unique_tries,
                    'time_seconds': elapsed,
                    'event_number': event_num,
                    'combination': list(combo)
                }

def main():
    print("PURE RANDOM BASELINE - Series 3128-3151")
    all_data = load_all_series_data()
    results = []

    for series_id in range(3128, 3152):
        print(f"\nSeries {series_id}:")
        exclusion_set = build_exclusion_set(all_data, series_id)
        result = pure_random_search(series_id, all_data, exclusion_set)
        results.append(result)
        print(f"  FOUND in {result['tries']:,} tries ({result['time_seconds']:.1f}s)")

    avg_tries = sum(r['tries'] for r in results) / len(results)
    output = {
        'method': 'Pure Random Baseline',
        'average_tries': avg_tries,
        'results': results
    }

    with open('pure_random_baseline_3128_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nAverage: {avg_tries:,.0f} tries")
    print("BASELINE COMPLETE")

if __name__ == '__main__':
    main()
