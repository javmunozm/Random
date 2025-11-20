#!/usr/bin/env python3
"""
ML POOL REDUCTION JACKPOT FINDER

Novel approach that combines ML strengths with exhaustive search:
1. Use ML (GA) to identify top N most likely numbers (e.g., 18-20)
2. Generate ALL C(N, 14) combinations from that pool
3. Exhaustively check all combinations against actual results
4. If jackpot is in the pool, we find it with 100% certainty

This works because:
- ML identifies the likely number pool (reduces from 25 to 18-20)
- Exhaustive search within reduced pool guarantees finding jackpot
- Much faster than searching all 4.4M combinations
"""

import json
import random
from datetime import datetime
from collections import Counter
from itertools import combinations
import math


def load_series_data(file_path="full_series_data.json", min_series=2982):
    """Load and filter series data"""
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return {k: v for k, v in all_data.items() if int(k) >= min_series}


def combination_to_tuple(combination):
    """Convert combination to sorted tuple"""
    return tuple(sorted(combination))


def genetic_algorithm_for_pool(all_series_data, training_series_ids, seed=331):
    """
    Run GA to identify most likely numbers
    Returns top N numbers based on frequency in best-performing population
    """
    if seed is not None:
        random.seed(seed)

    pop_size = 200
    generations = 10
    population = [sorted(random.sample(range(1, 26), 14)) for _ in range(pop_size)]

    for gen in range(generations):
        fitness_scores = []
        for combo in population:
            total_best = 0
            for series_id in training_series_ids:
                actual_events = all_series_data[str(series_id)]
                best_match = max(len(set(combo) & set(event)) for event in actual_events)
                total_best += best_match
            avg_best = total_best / len(training_series_ids)
            fitness_scores.append((combo, avg_best))

        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        survivors = [combo for combo, score in fitness_scores[:pop_size//2]]

        new_population = survivors[:]
        while len(new_population) < pop_size:
            parent1, parent2 = random.sample(survivors, 2)
            child = list(set(parent1[:7] + parent2[:7]))
            available = [n for n in range(1, 26) if n not in child]
            if available:
                needed = 14 - len(child)
                child.extend(random.sample(available, min(needed, len(available))))
            if random.random() < 0.1 and len(child) == 14:
                idx = random.randint(0, 13)
                new_num = random.randint(1, 25)
                if new_num not in child:
                    child[idx] = new_num
            if len(child) == 14:
                new_population.append(sorted(child))

        population = new_population[:pop_size]

    # Calculate number frequencies across entire final population
    number_freq = Counter()
    for combo in population:
        for num in combo:
            number_freq[num] += 1

    # Also get best combination
    final_fitness = []
    for combo in population:
        total_best = 0
        for series_id in training_series_ids:
            actual_events = all_series_data[str(series_id)]
            best_match = max(len(set(combo) & set(event)) for event in actual_events)
            total_best += best_match
        avg_best = total_best / len(training_series_ids)
        final_fitness.append((combo, avg_best))

    best_combo, best_score = max(final_fitness, key=lambda x: x[1])

    return number_freq, best_combo, best_score


def select_top_numbers(number_freq, best_combo, pool_size=18):
    """
    Select top N numbers based on GA analysis
    Combines frequency in population with best combo bonus
    """
    # Score each number
    scores = {}
    max_freq = max(number_freq.values())

    for num in range(1, 26):
        freq_score = number_freq.get(num, 0) / max_freq
        best_bonus = 0.5 if num in best_combo else 0.0
        scores[num] = freq_score + best_bonus

    # Sort and select top N
    sorted_numbers = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_numbers = [num for num, score in sorted_numbers[:pool_size]]

    return sorted(top_numbers), scores


def find_jackpot_with_pool(series_id, all_data, number_pool):
    """
    Find jackpot by exhaustively checking all combinations from number pool
    """
    print(f"\n{'='*80}")
    print(f"EXHAUSTIVE SEARCH IN ML-SELECTED POOL - SERIES {series_id}")
    print(f"{'='*80}")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    pool_size = len(number_pool)

    # Calculate total combinations to check
    def ncr(n, r):
        return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

    total_combinations = ncr(pool_size, 14)

    print(f"\nTarget series: {series_id}")
    print(f"Number pool: {pool_size} numbers")
    pool_str = ' '.join(f"{n:02d}" for n in number_pool)
    print(f"Pool: {pool_str}")
    print(f"Total combinations to check: {total_combinations:,}")
    print(f"Reduction from full space: {100 * (1 - total_combinations/4457400):.2f}%")
    print()

    tries = 0
    best_match = 0
    best_match_combo = None
    start_time = datetime.now()

    print("Exhaustively checking all combinations in pool...\n")

    # Generate all combinations from pool
    for combo in combinations(number_pool, 14):
        tries += 1
        combo_tuple = tuple(sorted(combo))

        # Check against all events
        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if combo_tuple == event_tuple:
                # JACKPOT FOUND!
                elapsed = (datetime.now() - start_time).total_seconds()
                combo_str = ' '.join(f"{n:02d}" for n in combo_tuple)

                print(f"\n🎉 JACKPOT FOUND IN ML-SELECTED POOL!")
                print(f"   Tries: {tries:,} / {total_combinations:,}")
                print(f"   Progress: {100*tries/total_combinations:.2f}%")
                print(f"   Time: {elapsed:.1f} seconds")
                print(f"   Rate: {tries/elapsed:.0f} combinations/sec")
                print(f"   Combination: {combo_str}")

                return {
                    'series_id': series_id,
                    'tries': tries,
                    'total_combinations': total_combinations,
                    'time_seconds': elapsed,
                    'rate': tries/elapsed,
                    'combination': list(combo_tuple),
                    'pool_size': pool_size,
                    'found': True
                }

            # Track best match
            matches = len(set(combo_tuple) & set(event))
            if matches > best_match:
                best_match = matches
                best_match_combo = combo_tuple

        # Progress every 10K tries
        if tries % 10000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = tries / elapsed if elapsed > 0 else 0
            progress = 100 * tries / total_combinations
            print(f"  {tries:>10,} / {total_combinations:,} ({progress:>5.1f}%) | "
                  f"Best: {best_match}/14 | Rate: {rate:>7.0f}/sec")

    # Not found in pool
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n❌ JACKPOT NOT FOUND IN POOL")
    print(f"   Checked all {total_combinations:,} combinations")
    print(f"   Time: {elapsed:.1f} seconds")
    print(f"   Best match: {best_match}/14")

    if best_match_combo:
        combo_str = ' '.join(f"{n:02d}" for n in best_match_combo)
        print(f"   Best combo: {combo_str}")

    return {
        'series_id': series_id,
        'tries': total_combinations,
        'total_combinations': total_combinations,
        'time_seconds': elapsed,
        'rate': total_combinations/elapsed,
        'pool_size': pool_size,
        'found': False,
        'best_match': best_match,
        'best_combination': list(best_match_combo) if best_match_combo else None
    }


def adaptive_pool_search(series_id, all_data, all_series_data, training_series_ids):
    """
    Adaptive approach: start with smaller pool, expand if needed
    """
    print("=" * 80)
    print("ADAPTIVE ML POOL REDUCTION JACKPOT FINDER")
    print("=" * 80)
    print()
    print("Strategy:")
    print("  1. Use GA to identify most likely numbers")
    print("  2. Start with pool of top 16 numbers")
    print("  3. Exhaustively check all C(16,14) = 120 combinations")
    print("  4. If not found, expand to 18, then 20, then 22...")
    print("=" * 80)
    print()

    # Run GA to get number frequencies
    print("Running Genetic Algorithm to analyze number patterns...")
    number_freq, best_combo, best_score = genetic_algorithm_for_pool(
        all_series_data,
        training_series_ids,
        seed=331
    )

    best_combo_str = ' '.join(f"{n:02d}" for n in best_combo)
    print(f"✅ GA Complete")
    print(f"   Best combo: {best_combo_str}")
    print(f"   Training score: {(best_score/14)*100:.2f}%")
    print()

    # Try progressively larger pools
    pool_sizes = [16, 18, 20, 22, 24]

    for pool_size in pool_sizes:
        print(f"\n{'='*80}")
        print(f"ATTEMPT: Pool size = {pool_size} numbers")
        print(f"{'='*80}")

        # Select top numbers
        number_pool, scores = select_top_numbers(number_freq, best_combo, pool_size)

        # Calculate combinations
        def ncr(n, r):
            return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

        total_combos = ncr(pool_size, 14)
        print(f"Pool size: {pool_size} → {total_combos:,} combinations to check")

        # Try to find jackpot in this pool
        result = find_jackpot_with_pool(series_id, all_data, number_pool)

        if result['found']:
            return result
        else:
            print(f"\n⚠️  Jackpot not in pool of {pool_size} numbers, expanding...")

    print(f"\n❌ Jackpot not found even with pool of {pool_sizes[-1]} numbers")
    return result


def main():
    print("=" * 80)
    print("ML POOL REDUCTION JACKPOT FINDER - SERIES 3151")
    print("=" * 80)
    print()
    print("Novel Approach:")
    print("  - Use ML to reduce search space (25 → 16-20 numbers)")
    print("  - Exhaustively check all combinations in reduced pool")
    print("  - Guarantees finding jackpot IF numbers are in ML-selected pool")
    print("  - Much faster than brute force (check tens of thousands, not millions)")
    print("=" * 80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    print(f"✅ Loaded {len(all_series_data)} series ({min(all_series_ids)}-{max(all_series_ids)})")

    # Training data
    training_series_ids = [sid for sid in all_series_ids if sid <= 3150]
    print(f"✅ Training on {len(training_series_ids)} series")
    print()

    # Run adaptive pool search
    result = adaptive_pool_search(3151, all_series_data, all_series_data, training_series_ids)

    # Final summary
    print()
    print("=" * 80)
    print("FINAL RESULT - ML POOL REDUCTION APPROACH")
    print("=" * 80)
    print()

    if result['found']:
        combo_str = ' '.join(f"{n:02d}" for n in result['combination'])
        print(f"✅ JACKPOT FOUND!")
        print(f"   Pool size: {result['pool_size']} numbers")
        print(f"   Tries: {result['tries']:,} / {result['total_combinations']:,}")
        print(f"   Time: {result['time_seconds']:.1f} seconds")
        print(f"   Combination: {combo_str}")
        print()

        # Compare to other methods
        print("COMPARISON TO OTHER METHODS:")
        print(f"  Pure Random:       285,368 tries")
        print(f"  ML-Weighted:     1,933,375 tries")
        print(f"  ML Pool Reduction: {result['tries']:,} tries")
        print()

        if result['tries'] < 285368:
            improvement = ((285368 - result['tries']) / 285368) * 100
            print(f"✅ ML Pool is {improvement:.1f}% FASTER than pure random!")

    else:
        print(f"❌ JACKPOT NOT FOUND")
        print(f"   Best match: {result['best_match']}/14")
        print()
        print("This means jackpot numbers were NOT in ML-predicted pool")
        print("This proves ML cannot reliably identify all jackpot numbers")

    # Save results
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'series_id': 3151,
        'method': 'ML Pool Reduction + Exhaustive Search',
        'result': result
    }

    with open('ml_pool_reduction_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("📁 Results saved to: ml_pool_reduction_3151.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
