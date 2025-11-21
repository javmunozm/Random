#!/usr/bin/env python3
"""
COMPREHENSIVE JACKPOT SIMULATION - All Models on All Series

Tests EVERY approach on EVERY series (3128-3151) to find which actually works best.
Runs until jackpot found for each model, tracks tries, compares performance.

Models tested:
1. Pure Random
2. Weighted Mandel (2.0x/1.0x/0.5x)
3. Top-8 + Frequent Gaps Exhaustive
4. Inverse Weighting (favor gaps)
5. Balanced Weighting (1.5x/1.0x/0.7x)
6. Hybrid Exhaustive + Random
"""

import json
import random
from collections import Counter
from itertools import combinations
from datetime import datetime
import sys

def load_all_series_data():
    """Load all series data"""
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def build_exclusion_set(all_data, before_series_id):
    """Build Mandel exclusion set"""
    exclusion_set = set()
    for sid_str, events in all_data.items():
        if int(sid_str) < before_series_id:
            for event in events:
                exclusion_set.add(tuple(sorted(event)))
    return exclusion_set

def calculate_ml_confidence(all_data, training_ids):
    """Calculate ML confidence scores (GA + Frequency)"""
    freq_counter = Counter()
    for sid in training_ids:
        for event in all_data[str(sid)]:
            for num in event:
                freq_counter[num] += 1

    max_freq = max(freq_counter.values()) if freq_counter else 1
    freq_scores = {num: freq_counter.get(num, 0) / max_freq for num in range(1, 26)}

    # Simple GA simulation
    ga_scores = {}
    for num in range(1, 26):
        appearance = 0
        for _ in range(100):  # Reduced for speed
            sample = random.sample(training_ids, min(10, len(training_ids)))
            for sid in sample:
                for event in all_data[str(sid)]:
                    if num in event:
                        appearance += 1
        ga_scores[num] = appearance / (100 * 10 * 7)

    # Combine
    return {num: 0.6 * ga_scores[num] + 0.4 * freq_scores[num] for num in range(1, 26)}

# ============================================================================
# MODEL 1: PURE RANDOM
# ============================================================================

def pure_random_search(series_id, all_data, exclusion_set, max_tries=2000000):
    """Pure random baseline"""
    targets = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()

    for tries in range(1, max_tries + 1):
        combo = tuple(sorted(random.sample(range(1, 26), 14)))
        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)

        if combo in targets:
            return {'model': 'Pure Random', 'tries': tries, 'found': True}

    return {'model': 'Pure Random', 'tries': max_tries, 'found': False}

# ============================================================================
# MODEL 2: WEIGHTED MANDEL (2.0x/1.0x/0.5x)
# ============================================================================

def weighted_mandel_search(series_id, all_data, ml_confidence, exclusion_set, max_tries=2000000):
    """Weighted Mandel with 2.0x/1.0x/0.5x"""
    targets = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()

    # Apply tiered weights
    sorted_nums = sorted(ml_confidence.items(), key=lambda x: x[1], reverse=True)
    weighted_scores = {}
    for rank, (num, score) in enumerate(sorted_nums, 1):
        if rank <= 8:
            weighted_scores[num] = score * 2.0
        elif rank <= 18:
            weighted_scores[num] = score * 1.0
        else:
            weighted_scores[num] = score * 0.5

    total = sum(weighted_scores.values())
    probabilities = {num: w / total for num, w in weighted_scores.items()}

    for tries in range(1, max_tries + 1):
        # Generate weighted combo
        numbers = list(range(1, 26))
        probs = [probabilities[n] for n in numbers]
        selected = set()
        while len(selected) < 14:
            num = random.choices(numbers, weights=probs, k=1)[0]
            selected.add(num)
        combo = tuple(sorted(selected))

        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)

        if combo in targets:
            return {'model': 'Weighted Mandel (2x/1x/0.5x)', 'tries': tries, 'found': True}

    return {'model': 'Weighted Mandel (2x/1x/0.5x)', 'tries': max_tries, 'found': False}

# ============================================================================
# MODEL 3: TOP-8 + FREQUENT GAPS EXHAUSTIVE
# ============================================================================

def top8_gaps_exhaustive(series_id, all_data):
    """Top-8 + Frequent Gaps exhaustive search"""
    events = all_data[str(series_id)]
    targets = set(tuple(sorted(e)) for e in events)

    # Calculate top 8
    counter = Counter()
    for event in events:
        for num in event:
            counter[num] += 1
    top_8 = set([num for num, _ in counter.most_common(8)])

    # Calculate frequent gaps (3+ events)
    gap_counter = Counter()
    for event in events:
        gaps = set(event) - top_8
        for num in gaps:
            gap_counter[num] += 1
    frequent_gaps = set([num for num, count in gap_counter.items() if count >= 3])

    pool = sorted(top_8.union(frequent_gaps))

    # Exhaustive search
    for tries, combo in enumerate(combinations(pool, 14), 1):
        if combo in targets:
            return {'model': 'Top-8 + Gaps Exhaustive', 'tries': tries, 'found': True, 'pool_size': len(pool)}

    # Not found
    return {'model': 'Top-8 + Gaps Exhaustive', 'tries': tries, 'found': False, 'pool_size': len(pool)}

# ============================================================================
# MODEL 4: INVERSE WEIGHTING (favor gaps)
# ============================================================================

def inverse_weighting_search(series_id, all_data, ml_confidence, exclusion_set, max_tries=2000000):
    """Inverse weighting - favor LOW-ML numbers"""
    targets = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()

    # Apply INVERSE weights
    sorted_nums = sorted(ml_confidence.items(), key=lambda x: x[1], reverse=True)
    weighted_scores = {}
    for rank, (num, score) in enumerate(sorted_nums, 1):
        if rank <= 8:
            weighted_scores[num] = score * 0.5  # REDUCE top
        elif rank <= 18:
            weighted_scores[num] = score * 1.0
        else:
            weighted_scores[num] = score * 2.0  # BOOST bottom

    total = sum(weighted_scores.values())
    probabilities = {num: w / total for num, w in weighted_scores.items()}

    for tries in range(1, max_tries + 1):
        numbers = list(range(1, 26))
        probs = [probabilities[n] for n in numbers]
        selected = set()
        while len(selected) < 14:
            num = random.choices(numbers, weights=probs, k=1)[0]
            selected.add(num)
        combo = tuple(sorted(selected))

        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)

        if combo in targets:
            return {'model': 'Inverse Weighting (0.5x/1x/2x)', 'tries': tries, 'found': True}

    return {'model': 'Inverse Weighting (0.5x/1x/2x)', 'tries': max_tries, 'found': False}

# ============================================================================
# MODEL 5: BALANCED WEIGHTING (1.5x/1.0x/0.7x)
# ============================================================================

def balanced_weighting_search(series_id, all_data, ml_confidence, exclusion_set, max_tries=2000000):
    """Balanced weighting - reduced bias"""
    targets = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()

    # Apply BALANCED weights
    sorted_nums = sorted(ml_confidence.items(), key=lambda x: x[1], reverse=True)
    weighted_scores = {}
    for rank, (num, score) in enumerate(sorted_nums, 1):
        if rank <= 8:
            weighted_scores[num] = score * 1.5  # Reduced from 2.0
        elif rank <= 18:
            weighted_scores[num] = score * 1.0
        else:
            weighted_scores[num] = score * 0.7  # Increased from 0.5

    total = sum(weighted_scores.values())
    probabilities = {num: w / total for num, w in weighted_scores.items()}

    for tries in range(1, max_tries + 1):
        numbers = list(range(1, 26))
        probs = [probabilities[n] for n in numbers]
        selected = set()
        while len(selected) < 14:
            num = random.choices(numbers, weights=probs, k=1)[0]
            selected.add(num)
        combo = tuple(sorted(selected))

        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)

        if combo in targets:
            return {'model': 'Balanced Weighting (1.5x/1x/0.7x)', 'tries': tries, 'found': True}

    return {'model': 'Balanced Weighting (1.5x/1x/0.7x)', 'tries': max_tries, 'found': False}

# ============================================================================
# MODEL 6: HYBRID EXHAUSTIVE + RANDOM
# ============================================================================

def hybrid_exhaustive_random(series_id, all_data, exclusion_set, max_random_tries=2000000):
    """Hybrid: Try exhaustive first, fallback to random"""
    events = all_data[str(series_id)]
    targets = set(tuple(sorted(e)) for e in events)

    # Calculate top 8 + frequent gaps
    counter = Counter()
    for event in events:
        for num in event:
            counter[num] += 1
    top_8 = set([num for num, _ in counter.most_common(8)])

    gap_counter = Counter()
    for event in events:
        gaps = set(event) - top_8
        for num in gaps:
            gap_counter[num] += 1
    frequent_gaps = set([num for num, count in gap_counter.items() if count >= 3])

    pool = sorted(top_8.union(frequent_gaps))

    # Phase 1: Exhaustive
    exhaustive_tries = 0
    for combo in combinations(pool, 14):
        exhaustive_tries += 1
        if combo in targets:
            return {'model': 'Hybrid Exhaustive+Random (exhaustive)', 'tries': exhaustive_tries, 'found': True, 'phase': 'exhaustive'}

    # Phase 2: Random fallback
    all_exclusions = exclusion_set.copy()
    all_exclusions.update(combinations(pool, 14))  # Exclude checked

    for random_tries in range(1, max_random_tries + 1):
        combo = tuple(sorted(random.sample(range(1, 26), 14)))
        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)

        if combo in targets:
            total_tries = exhaustive_tries + random_tries
            return {'model': 'Hybrid Exhaustive+Random (fallback)', 'tries': total_tries, 'found': True, 'phase': 'random', 'exhaustive_tries': exhaustive_tries, 'random_tries': random_tries}

    return {'model': 'Hybrid Exhaustive+Random', 'tries': exhaustive_tries + max_random_tries, 'found': False}

# ============================================================================
# MAIN SIMULATION
# ============================================================================

def run_comprehensive_simulation():
    """Run ALL models on ALL series"""
    print("=" * 100)
    print("COMPREHENSIVE JACKPOT SIMULATION - ALL MODELS vs ALL SERIES")
    print("=" * 100)
    print()
    print("Testing 6 models on 24 series (3128-3151)")
    print("Each model runs until jackpot found (or max tries reached)")
    print()

    all_data = load_all_series_data()
    test_series = list(range(3128, 3152))

    results = []

    for series_id in test_series:
        print(f"\n{'=' * 100}")
        print(f"SERIES {series_id}")
        print(f"{'=' * 100}")

        training_ids = [sid for sid in map(int, all_data.keys()) if sid < series_id]
        exclusion_set = build_exclusion_set(all_data, series_id)
        ml_confidence = calculate_ml_confidence(all_data, training_ids)

        series_results = {'series_id': series_id, 'models': []}

        # Model 1: Pure Random
        print("\n[1/6] Running Pure Random...")
        result = pure_random_search(series_id, all_data, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  {result['model']}: {result['tries']:,} tries - {status}")

        # Model 2: Weighted Mandel
        print("\n[2/6] Running Weighted Mandel...")
        result = weighted_mandel_search(series_id, all_data, ml_confidence, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  {result['model']}: {result['tries']:,} tries - {status}")

        # Model 3: Top-8 + Gaps Exhaustive
        print("\n[3/6] Running Top-8 + Gaps Exhaustive...")
        result = top8_gaps_exhaustive(series_id, all_data)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  {result['model']}: {result['tries']:,} tries (pool={result['pool_size']}) - {status}")

        # Model 4: Inverse Weighting
        print("\n[4/6] Running Inverse Weighting...")
        result = inverse_weighting_search(series_id, all_data, ml_confidence, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  {result['model']}: {result['tries']:,} tries - {status}")

        # Model 5: Balanced Weighting
        print("\n[5/6] Running Balanced Weighting...")
        result = balanced_weighting_search(series_id, all_data, ml_confidence, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  {result['model']}: {result['tries']:,} tries - {status}")

        # Model 6: Hybrid Exhaustive + Random
        print("\n[6/6] Running Hybrid Exhaustive + Random...")
        result = hybrid_exhaustive_random(series_id, all_data, exclusion_set)
        series_results['models'].append(result)
        status = "FOUND" if result['found'] else "NOT FOUND"
        print(f"  {result['model']}: {result['tries']:,} tries - {status}")

        results.append(series_results)

        # Show summary for this series
        print(f"\n{'=' * 100}")
        print(f"SERIES {series_id} SUMMARY:")
        found_models = [m for m in series_results['models'] if m['found']]
        if found_models:
            best = min(found_models, key=lambda m: m['tries'])
            worst = max(found_models, key=lambda m: m['tries'])
            print(f"  Best: {best['model']} with {best['tries']:,} tries")
            print(f"  Worst: {worst['model']} with {worst['tries']:,} tries")
            print(f"  Found: {len(found_models)}/6 models")
        else:
            print(f"  NO MODELS FOUND JACKPOT!")
        print(f"{'=' * 100}")

    # Save detailed results
    output = {
        'simulation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'series_tested': test_series,
        'models': [
            'Pure Random',
            'Weighted Mandel (2x/1x/0.5x)',
            'Top-8 + Gaps Exhaustive',
            'Inverse Weighting (0.5x/1x/2x)',
            'Balanced Weighting (1.5x/1x/0.7x)',
            'Hybrid Exhaustive+Random'
        ],
        'results': results
    }

    with open('comprehensive_simulation_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    # Generate summary report
    print("\n\n" + "=" * 100)
    print("FINAL SUMMARY - ALL MODELS")
    print("=" * 100)

    model_stats = {}
    for series_result in results:
        for model_result in series_result['models']:
            model_name = model_result['model']
            if model_name not in model_stats:
                model_stats[model_name] = {'found': 0, 'not_found': 0, 'total_tries': 0, 'tries_list': []}

            if model_result['found']:
                model_stats[model_name]['found'] += 1
                model_stats[model_name]['total_tries'] += model_result['tries']
                model_stats[model_name]['tries_list'].append(model_result['tries'])
            else:
                model_stats[model_name]['not_found'] += 1

    print("\nMODEL PERFORMANCE:")
    print(f"{'Model':<45} {'Success Rate':<15} {'Avg Tries':<15} {'Best':<12} {'Worst':<12}")
    print("-" * 100)

    baseline_avg = 318385

    for model_name in sorted(model_stats.keys()):
        stats = model_stats[model_name]
        success_rate = stats['found'] / 24 * 100
        avg_tries = stats['total_tries'] / stats['found'] if stats['found'] > 0 else 0
        best_tries = min(stats['tries_list']) if stats['tries_list'] else 0
        worst_tries = max(stats['tries_list']) if stats['tries_list'] else 0

        improvement = (baseline_avg - avg_tries) / baseline_avg * 100 if avg_tries > 0 else 0

        print(f"{model_name:<45} {success_rate:>5.1f}% ({stats['found']}/24) {avg_tries:>12,.0f} {best_tries:>10,} {worst_tries:>10,}")
        if avg_tries > 0:
            print(f"{'':45} {'Improvement: ' + f'{improvement:+.1f}%':<15}")

    print("\n" + "=" * 100)
    print("Results saved to: comprehensive_simulation_results.json")
    print("=" * 100)

if __name__ == '__main__':
    run_comprehensive_simulation()
