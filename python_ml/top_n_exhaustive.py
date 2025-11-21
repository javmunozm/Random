#!/usr/bin/env python3
"""Top-N exhaustive search - test different pool sizes"""
import json
import random
from itertools import combinations
from collections import Counter
from datetime import datetime

def load_all_series_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def get_top_n_numbers(all_data, training_ids, n):
    counter = Counter()
    for sid in training_ids:
        for event in all_data[str(sid)]:
            for num in event:
                counter[num] += 1
    return [num for num, _ in counter.most_common(n)]

def search_top_n(series_id, all_data, top_n):
    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    start_time = datetime.now()

    for tries, combo in enumerate(combinations(top_n, 14), 1):
        if tries % 10000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  {tries:,} combos | {elapsed:.1f}s")

        for event_num, target in enumerate(target_tuples, 1):
            if combo == target:
                elapsed = (datetime.now() - start_time).total_seconds()
                return {
                    'series_id': series_id,
                    'pool_size': len(top_n),
                    'tries': tries,
                    'time_seconds': elapsed,
                    'event_number': event_num,
                    'found': True
                }

    elapsed = (datetime.now() - start_time).total_seconds()
    return {
        'series_id': series_id,
        'pool_size': len(top_n),
        'tries': tries,
        'time_seconds': elapsed,
        'found': False
    }

def main():
    print("TOP-N EXHAUSTIVE SEARCH")
    all_data = load_all_series_data()
    test_pools = [16, 18, 20, 22]

    for pool_size in test_pools:
        print(f"\n{'='*60}")
        print(f"TESTING POOL SIZE: {pool_size}")
        print(f"{'='*60}")
        results = []

        for series_id in range(3128, 3152):
            training_ids = [sid for sid in map(int, all_data.keys()) if sid < series_id]
            top_n = get_top_n_numbers(all_data, training_ids, pool_size)

            print(f"\nSeries {series_id} (pool={pool_size}):")
            result = search_top_n(series_id, all_data, top_n)
            results.append(result)

            if result['found']:
                print(f"  FOUND in {result['tries']:,} tries")
            else:
                print(f"  NOT FOUND (checked all {result['tries']:,} combos)")

        found_count = sum(1 for r in results if r['found'])
        avg_tries = sum(r['tries'] for r in results if r['found']) / max(found_count, 1)

        output = {
            'method': f'Top-{pool_size} Exhaustive',
            'pool_size': pool_size,
            'found_rate': found_count / len(results),
            'average_tries': avg_tries,
            'results': results
        }

        with open(f'top_{pool_size}_exhaustive_3128_3151.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nPool {pool_size}: {found_count}/24 found, avg {avg_tries:,.0f} tries")

if __name__ == '__main__':
    main()
