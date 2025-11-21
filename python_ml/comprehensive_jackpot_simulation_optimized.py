#!/usr/bin/env python3
"""Optimized comprehensive jackpot simulation - all models, all series
Reduced max_tries to prevent hanging on slow models"""

import json
import random
from itertools import combinations
from collections import Counter
from datetime import datetime

MAX_TRIES_PER_MODEL = 1000000  # Reduced from 2M to 1M

def load_all_series_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def build_exclusion_set(all_data, before_series_id):
    exclusion_set = set()
    for sid_str, events in all_data.items():
        if int(sid_str) < before_series_id:
            for event in events:
                exclusion_set.add(tuple(sorted(event)))
    return exclusion_set

def calculate_ml_confidence(all_data, training_ids):
    """Calculate ML confidence scores (high/medium/low freq)"""
    counter = Counter()
    for sid in training_ids:
        for event in all_data[str(sid)]:
            for num in event:
                counter[num] += 1

    sorted_nums = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    high = [num for num, _ in sorted_nums[:8]]
    medium = [num for num, _ in sorted_nums[8:17]]
    low = [num for num, _ in sorted_nums[17:]]

    return {'high': high, 'medium': medium, 'low': low}

# MODEL 1: Pure Random (Baseline)
def pure_random_search(series_id, all_data, exclusion_set):
    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    while unique_tries < MAX_TRIES_PER_MODEL:
        combo = tuple(sorted(random.sample(range(1, 26), 14)))
        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)
        unique_tries += 1

        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {
                'model': 'Pure Random',
                'tries': unique_tries,
                'time_seconds': elapsed,
                'found': True
            }

    return {'model': 'Pure Random', 'tries': MAX_TRIES_PER_MODEL, 'found': False}

# MODEL 2: Weighted Mandel (2x/1x/0.5x)
def weighted_mandel_search(series_id, all_data, ml_confidence, exclusion_set):
    numbers = list(range(1, 26))
    weights = []
    for num in numbers:
        if num in ml_confidence['high']:
            weights.append(2.0)
        elif num in ml_confidence['medium']:
            weights.append(1.0)
        else:
            weights.append(0.5)

    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    while unique_tries < MAX_TRIES_PER_MODEL:
        selected = set()
        while len(selected) < 14:
            num = random.choices(numbers, weights=weights, k=1)[0]
            selected.add(num)
        combo = tuple(sorted(selected))

        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)
        unique_tries += 1

        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {
                'model': 'Weighted Mandel (2x/1x/0.5x)',
                'tries': unique_tries,
                'time_seconds': elapsed,
                'found': True
            }

    return {'model': 'Weighted Mandel (2x/1x/0.5x)', 'tries': MAX_TRIES_PER_MODEL, 'found': False}

# MODEL 3: Top-8 + Frequent Gaps Exhaustive
def top8_gaps_exhaustive(series_id, all_data):
    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    events = all_data[str(series_id)]

    # Get top 8 numbers
    counter = Counter()
    for event in events:
        for num in event:
            counter[num] += 1
    top_8 = [num for num, _ in counter.most_common(8)]

    # Get frequent gaps (3+ events)
    gap_counter = Counter()
    for event in events:
        gaps = set(event) - set(top_8)
        for num in gaps:
            gap_counter[num] += 1

    frequent_gaps = [num for num, count in gap_counter.items() if count >= 3]
    pool = sorted(set(top_8 + frequent_gaps))

    start_time = datetime.now()
    tries = 0

    for combo in combinations(pool, 14):
        tries += 1
        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {
                'model': 'Top-8 + Gaps Exhaustive',
                'tries': tries,
                'time_seconds': elapsed,
                'pool_size': len(pool),
                'found': True
            }

    elapsed = (datetime.now() - start_time).total_seconds()
    return {
        'model': 'Top-8 + Gaps Exhaustive',
        'tries': tries,
        'pool_size': len(pool),
        'found': False
    }

# MODEL 4: Inverse Weighting (0.5x/1x/2x)
def inverse_weighting_search(series_id, all_data, ml_confidence, exclusion_set):
    numbers = list(range(1, 26))
    weights = []
    for num in numbers:
        if num in ml_confidence['high']:
            weights.append(0.5)
        elif num in ml_confidence['medium']:
            weights.append(1.0)
        else:
            weights.append(2.0)

    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    while unique_tries < MAX_TRIES_PER_MODEL:
        selected = set()
        while len(selected) < 14:
            num = random.choices(numbers, weights=weights, k=1)[0]
            selected.add(num)
        combo = tuple(sorted(selected))

        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)
        unique_tries += 1

        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {
                'model': 'Inverse Weighting (0.5x/1x/2x)',
                'tries': unique_tries,
                'time_seconds': elapsed,
                'found': True
            }

    return {'model': 'Inverse Weighting (0.5x/1x/2x)', 'tries': MAX_TRIES_PER_MODEL, 'found': False}

# MODEL 5: Balanced Weighting (1.5x/1x/0.7x)
def balanced_weighting_search(series_id, all_data, ml_confidence, exclusion_set):
    numbers = list(range(1, 26))
    weights = []
    for num in numbers:
        if num in ml_confidence['high']:
            weights.append(1.5)
        elif num in ml_confidence['medium']:
            weights.append(1.0)
        else:
            weights.append(0.7)

    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    while unique_tries < MAX_TRIES_PER_MODEL:
        selected = set()
        while len(selected) < 14:
            num = random.choices(numbers, weights=weights, k=1)[0]
            selected.add(num)
        combo = tuple(sorted(selected))

        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)
        unique_tries += 1

        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {
                'model': 'Balanced Weighting (1.5x/1x/0.7x)',
                'tries': unique_tries,
                'time_seconds': elapsed,
                'found': True
            }

    return {'model': 'Balanced Weighting (1.5x/1x/0.7x)', 'tries': MAX_TRIES_PER_MODEL, 'found': False}

# MODEL 6: Hybrid Exhaustive + Random Fallback
def hybrid_exhaustive_random(series_id, all_data, exclusion_set):
    # First try exhaustive
    exhaustive_result = top8_gaps_exhaustive(series_id, all_data)

    if exhaustive_result['found']:
        exhaustive_result['model'] = 'Hybrid Exhaustive+Random'
        return exhaustive_result

    # Fallback to random
    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])

    # Build exclusion from exhaustive phase
    events = all_data[str(series_id)]
    counter = Counter()
    for event in events:
        for num in event:
            counter[num] += 1
    top_8 = [num for num, _ in counter.most_common(8)]
    gap_counter = Counter()
    for event in events:
        gaps = set(event) - set(top_8)
        for num in gaps:
            gap_counter[num] += 1
    frequent_gaps = [num for num, count in gap_counter.items() if count >= 3]
    pool = sorted(set(top_8 + frequent_gaps))

    exhaustive_combos = set(combinations(pool, 14))
    all_exclusions = exclusion_set.copy() | exhaustive_combos

    exhaustive_tries = exhaustive_result['tries']
    random_tries = 0
    start_time = datetime.now()

    while random_tries < (MAX_TRIES_PER_MODEL - exhaustive_tries):
        combo = tuple(sorted(random.sample(range(1, 26), 14)))
        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)
        random_tries += 1

        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {
                'model': 'Hybrid Exhaustive+Random (fallback)',
                'tries': exhaustive_tries + random_tries,
                'time_seconds': elapsed,
                'found': True
            }

    return {
        'model': 'Hybrid Exhaustive+Random',
        'tries': exhaustive_tries + random_tries,
        'found': False
    }

def run_comprehensive_simulation_from(start_series=3128):
    """Run comprehensive simulation from specified series"""
    print(f"COMPREHENSIVE JACKPOT SIMULATION - Series {start_series}-3151")
    print(f"Max tries per model: {MAX_TRIES_PER_MODEL:,}")
    print("="*80)

    all_data = load_all_series_data()
    test_series = list(range(start_series, 3152))

    results = []

    for series_id in test_series:
        print(f"\n{'='*80}")
        print(f"SERIES {series_id}")
        print(f"{'='*80}")

        training_ids = [sid for sid in map(int, all_data.keys()) if sid < series_id]
        exclusion_set = build_exclusion_set(all_data, series_id)
        ml_confidence = calculate_ml_confidence(all_data, training_ids)

        series_results = {
            'series_id': series_id,
            'models': []
        }

        # Model 1: Pure Random
        print(f"\n[1/6] Running Pure Random...")
        result = pure_random_search(series_id, all_data, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  Pure Random: {result['tries']:,} tries - {status}")

        # Model 2: Weighted Mandel
        print(f"\n[2/6] Running Weighted Mandel...")
        result = weighted_mandel_search(series_id, all_data, ml_confidence, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  Weighted Mandel: {result['tries']:,} tries - {status}")

        # Model 3: Top-8 + Gaps Exhaustive
        print(f"\n[3/6] Running Top-8 + Gaps Exhaustive...")
        result = top8_gaps_exhaustive(series_id, all_data)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  Top-8 + Gaps: {result['tries']:,} tries - {status}")

        # Model 4: Inverse Weighting
        print(f"\n[4/6] Running Inverse Weighting...")
        result = inverse_weighting_search(series_id, all_data, ml_confidence, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  Inverse Weighting: {result['tries']:,} tries - {status}")

        # Model 5: Balanced Weighting
        print(f"\n[5/6] Running Balanced Weighting...")
        result = balanced_weighting_search(series_id, all_data, ml_confidence, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  Balanced Weighting: {result['tries']:,} tries - {status}")

        # Model 6: Hybrid
        print(f"\n[6/6] Running Hybrid Exhaustive+Random...")
        result = hybrid_exhaustive_random(series_id, all_data, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  Hybrid: {result['tries']:,} tries - {status}")

        results.append(series_results)

        # Save incrementally
        with open(f'simulation_results_{start_series}_3151.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nSeries {series_id} complete. Progress: {len(results)}/{len(test_series)}")

    print(f"\n{'='*80}")
    print("SIMULATION COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults saved to: simulation_results_{start_series}_3151.json")

    return results

if __name__ == '__main__':
    # Run from Series 3140 to complete the missing 12 series
    run_comprehensive_simulation_from(3140)
