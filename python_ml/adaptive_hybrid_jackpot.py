#!/usr/bin/env python3
"""
ADAPTIVE ML-RANDOM HYBRID JACKPOT FINDER

Fix the inconsistency problem with pure ML-ranked approach.

Problem: ML-ranked is sometimes 78% faster, sometimes 500% slower
Cause: When jackpot has low ML score, we search through millions of
       higher-scored combinations first

Solution: Adaptive hybrid approach
1. Stage 1: Quick check of top 5% ML-ranked combinations (~222K tries)
2. Stage 2: If not found, switch to pure random from remaining space
3. This guarantees we never do worse than ~222K + random baseline

This makes ML a "shortcut optimizer" rather than complete ranking system.
"""

import json
import random
from datetime import datetime
from collections import Counter
from itertools import combinations, islice
import math


def load_series_data(file_path="full_series_data.json", min_series=2982):
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return {k: v for k, v in all_data.items() if int(k) >= min_series}


def combination_to_tuple(combination):
    return tuple(sorted(combination))


def calculate_ml_scores(all_series_data, training_series_ids):
    """Calculate comprehensive ML score for each number"""

    # Frequency score
    freq_counter = Counter()
    for sid in training_series_ids:
        for event in all_series_data[str(sid)]:
            for num in event:
                freq_counter[num] += 1

    max_freq = max(freq_counter.values())
    freq_scores = {num: freq_counter.get(num, 0) / max_freq for num in range(1, 26)}

    # Recency score
    recency_counter = Counter()
    recent_series = sorted(training_series_ids)[-20:]
    for i, sid in enumerate(recent_series):
        weight = 1.0 + (i / len(recent_series))
        for event in all_series_data[str(sid)]:
            for num in event:
                recency_counter[num] += weight

    max_recency = max(recency_counter.values()) if recency_counter else 1
    recency_scores = {num: recency_counter.get(num, 0) / max_recency for num in range(1, 26)}

    # GA-based score
    random.seed(331)
    pop_size = 200
    generations = 10
    population = [sorted(random.sample(range(1, 26), 14)) for _ in range(pop_size)]

    for gen in range(generations):
        fitness_scores = []
        for combo in population:
            total_best = 0
            for sid in training_series_ids:
                actual_events = all_series_data[str(sid)]
                best_match = max(len(set(combo) & set(event)) for event in actual_events)
                total_best += best_match
            fitness_scores.append((combo, total_best / len(training_series_ids)))

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

    # Count GA appearances
    ga_counter = Counter()
    for combo in population:
        for num in combo:
            ga_counter[num] += 1

    max_ga = max(ga_counter.values())
    ga_scores = {num: ga_counter.get(num, 0) / max_ga for num in range(1, 26)}

    # Combined score
    combined_scores = {}
    for num in range(1, 26):
        combined_scores[num] = (
            0.40 * ga_scores[num] +
            0.30 * freq_scores[num] +
            0.30 * recency_scores[num]
        )

    return combined_scores


def score_combination(combo, number_scores):
    """Score a combination based on sum of individual number scores"""
    return sum(number_scores[num] for num in combo)


def adaptive_hybrid_search(series_id, all_data, number_scores, ml_percentile=5.0):
    """
    Adaptive hybrid search:
    1. Check top X% ML-ranked combinations first
    2. If not found, switch to pure random
    """
    print(f"\n{'='*80}")
    print(f"ADAPTIVE HYBRID SEARCH - SERIES {series_id}")
    print(f"{'='*80}\n")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    target_tuples = [combination_to_tuple(event) for event in target_events]

    # Calculate how many combinations in top X%
    total_combinations = 4457400
    ml_check_limit = int(total_combinations * (ml_percentile / 100))

    print(f"Strategy:")
    print(f"  Stage 1: Check top {ml_percentile}% ML-ranked (~{ml_check_limit:,} combinations)")
    print(f"  Stage 2: If not found, switch to pure random")
    print(f"  Guarantee: Never worse than {ml_check_limit:,} + random baseline")
    print()

    # Stage 1: Generate and check top ML combinations
    print("="*80)
    print("STAGE 1: ML-RANKED SEARCH")
    print("="*80)
    print(f"Checking top {ml_percentile}% ({ml_check_limit:,} combinations)")
    print()

    # Generate all combinations with scores
    print("Generating and scoring all combinations...", end="", flush=True)
    all_combos = []
    for combo in combinations(range(1, 26), 14):
        score = score_combination(combo, number_scores)
        all_combos.append((combo, score))

    print(" sorting...", end="", flush=True)
    all_combos.sort(key=lambda x: x[1], reverse=True)
    print(" done\n")

    # Check top X%
    stage1_start = datetime.now()

    for rank, (combo, ml_score) in enumerate(all_combos[:ml_check_limit], 1):
        if combo in target_tuples:
            elapsed = (datetime.now() - stage1_start).total_seconds()
            event_idx = target_tuples.index(combo)
            combo_str = ' '.join(f"{n:02d}" for n in combo)

            print(f"🎉 JACKPOT FOUND IN STAGE 1 (ML-RANKED)!")
            print(f"   Event: {event_idx + 1}")
            print(f"   Rank: {rank:,} / {ml_check_limit:,}")
            print(f"   Percentile: Top {100*rank/total_combinations:.2f}%")
            print(f"   Time: {elapsed:.3f} seconds")
            print(f"   ML Score: {ml_score:.4f}")
            print(f"   Combination: {combo_str}")

            return {
                'series_id': series_id,
                'stage': 1,
                'method': 'ML-Ranked',
                'tries': rank,
                'ml_rank': rank,
                'percentile': 100 * rank / total_combinations,
                'time_seconds': elapsed,
                'ml_score': ml_score,
                'combination': list(combo),
                'event_number': event_idx + 1,
                'found': True
            }

        if rank % 50000 == 0:
            print(f"  Checked {rank:,} / {ml_check_limit:,} ({100*rank/ml_check_limit:.1f}%)")

    stage1_elapsed = (datetime.now() - stage1_start).total_seconds()

    print(f"\n❌ NOT FOUND in Stage 1")
    print(f"   Checked {ml_check_limit:,} top combinations in {stage1_elapsed:.3f} seconds")
    print()

    # Stage 2: Pure random from remaining combinations
    print("="*80)
    print("STAGE 2: PURE RANDOM SEARCH")
    print("="*80)
    print(f"Switching to pure random from remaining {total_combinations - ml_check_limit:,} combinations")
    print()

    # Create exclusion set of already-checked combinations
    checked_set = set(combo for combo, score in all_combos[:ml_check_limit])

    stage2_start = datetime.now()
    stage2_tries = 0

    while True:
        stage2_tries += 1
        total_tries = ml_check_limit + stage2_tries

        # Generate random combination not in checked set
        combo = tuple(sorted(random.sample(range(1, 26), 14)))

        # Skip if already checked in Stage 1
        if combo in checked_set:
            continue

        # Check if jackpot
        if combo in target_tuples:
            stage2_elapsed = (datetime.now() - stage2_start).total_seconds()
            total_elapsed = stage1_elapsed + stage2_elapsed
            event_idx = target_tuples.index(combo)
            combo_str = ' '.join(f"{n:02d}" for n in combo)

            # Find what ML rank this combination would have had
            ml_rank = None
            for rank, (c, score) in enumerate(all_combos, 1):
                if c == combo:
                    ml_rank = rank
                    break

            print(f"\n🎉 JACKPOT FOUND IN STAGE 2 (PURE RANDOM)!")
            print(f"   Event: {event_idx + 1}")
            print(f"   Stage 2 tries: {stage2_tries:,}")
            print(f"   Total tries: {total_tries:,} (Stage 1: {ml_check_limit:,} + Stage 2: {stage2_tries:,})")
            print(f"   ML Rank (if we continued): {ml_rank:,} / {total_combinations:,}")
            print(f"   Time: {total_elapsed:.3f} seconds (Stage 1: {stage1_elapsed:.1f}s + Stage 2: {stage2_elapsed:.1f}s)")
            print(f"   Combination: {combo_str}")

            return {
                'series_id': series_id,
                'stage': 2,
                'method': 'Pure Random (after ML exhausted)',
                'tries': total_tries,
                'stage1_tries': ml_check_limit,
                'stage2_tries': stage2_tries,
                'ml_rank': ml_rank,
                'time_seconds': total_elapsed,
                'combination': list(combo),
                'event_number': event_idx + 1,
                'found': True
            }

        if stage2_tries % 50000 == 0:
            stage2_elapsed = (datetime.now() - stage2_start).total_seconds()
            rate = stage2_tries / stage2_elapsed if stage2_elapsed > 0 else 0
            print(f"  Stage 2: {stage2_tries:,} tries | Rate: {rate:,.0f}/sec")


def simulate_adaptive_hybrid(all_series_data, test_series_ids, ml_percentile=5.0):
    """Run simulation on multiple series"""

    results = []

    for test_sid in test_series_ids:
        print(f"\n{'='*80}")
        print(f"SERIES {test_sid}")
        print(f"{'='*80}")

        # Training data
        all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])
        training_series_ids = [sid for sid in all_series_ids if sid < test_sid]

        print(f"Training on {len(training_series_ids)} series")

        # Calculate ML scores
        print("Calculating ML scores...", end="", flush=True)
        number_scores = calculate_ml_scores(all_series_data, training_series_ids)
        print(" done")

        # Run adaptive hybrid search
        result = adaptive_hybrid_search(test_sid, all_series_data, number_scores, ml_percentile)

        if result:
            results.append(result)

            # Compare to baselines
            pure_random_baseline = 318385  # Average for 7 events

            print()
            print("="*80)
            print("COMPARISON")
            print("="*80)

            if result['stage'] == 1:
                print(f"Pure Random Baseline: ~{pure_random_baseline:,} tries")
                print(f"Adaptive Hybrid:       {result['tries']:,} tries")
                improvement = ((pure_random_baseline - result['tries']) / pure_random_baseline) * 100
                print(f"Improvement: {improvement:+.1f}%")
            else:
                print(f"Pure Random Baseline: ~{pure_random_baseline:,} tries")
                print(f"Adaptive Hybrid:       {result['tries']:,} tries")
                print(f"  Stage 1 (ML):        {result['stage1_tries']:,} tries (not found)")
                print(f"  Stage 2 (Random):    {result['stage2_tries']:,} tries (found)")
                comparison = result['tries'] - pure_random_baseline
                print(f"Difference: {comparison:+,} tries vs baseline")

        print()

    return results


def main():
    print("="*80)
    print("ADAPTIVE ML-RANDOM HYBRID - Series 3128-3151")
    print("="*80)
    print()
    print("Strategy:")
    print("  Stage 1: Check top 5% ML-ranked combinations (~222K)")
    print("  Stage 2: If not found, pure random from remaining")
    print()
    print("Guarantee: Never worse than 222K + random baseline")
    print("="*80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    # Test on series 3128-3151
    test_series = [sid for sid in all_series_ids if 3128 <= sid <= 3151]

    print(f"Testing on {len(test_series)} series: {min(test_series)}-{max(test_series)}")
    print()

    # Run simulation
    results = simulate_adaptive_hybrid(all_series_data, test_series, ml_percentile=5.0)

    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print()

    stage1_wins = sum(1 for r in results if r['stage'] == 1)
    stage2_wins = sum(1 for r in results if r['stage'] == 2)

    avg_tries = sum(r['tries'] for r in results) / len(results)

    print(f"Series tested: {len(results)}")
    print(f"Stage 1 wins (ML): {stage1_wins}/{len(results)} ({100*stage1_wins/len(results):.1f}%)")
    print(f"Stage 2 wins (Random): {stage2_wins}/{len(results)} ({100*stage2_wins/len(results):.1f}%)")
    print(f"Average tries: {avg_tries:,.0f}")
    print(f"Pure random baseline: ~318,385")
    print()

    # Save results
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'method': 'Adaptive ML-Random Hybrid',
        'ml_percentile': 5.0,
        'series_range': f"{min(test_series)}-{max(test_series)}",
        'summary': {
            'series_tested': len(results),
            'stage1_wins': stage1_wins,
            'stage2_wins': stage2_wins,
            'average_tries': avg_tries
        },
        'results': results
    }

    with open('adaptive_hybrid_3128_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("📁 Results saved to: adaptive_hybrid_3128_3151.json")
    print("="*80)


if __name__ == "__main__":
    main()
