#!/usr/bin/env python3
"""
ML-RANKED SIMULATION: Series 3128-3151

Test ML-ranked approach on historical data to validate performance.
For each series:
1. Train on data before that series
2. Rank all combinations by ML score
3. Find jackpot in ranked order
4. Compare to pure random baseline
"""

import json
import random
from datetime import datetime
from collections import Counter
from itertools import combinations
import math


def load_series_data(file_path="full_series_data.json", min_series=2982):
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return {k: v for k, v in all_data.items() if int(k) >= min_series}


def combination_to_tuple(combination):
    return tuple(sorted(combination))


def calculate_ml_scores(all_series_data, training_series_ids):
    """Calculate comprehensive ML score for each number"""

    # 1. Frequency score
    freq_counter = Counter()
    for sid in training_series_ids:
        for event in all_series_data[str(sid)]:
            for num in event:
                freq_counter[num] += 1

    max_freq = max(freq_counter.values())
    freq_scores = {num: freq_counter.get(num, 0) / max_freq for num in range(1, 26)}

    # 2. Recency score (last 20 series weighted higher)
    recency_counter = Counter()
    recent_series = sorted(training_series_ids)[-20:]
    for i, sid in enumerate(recent_series):
        weight = 1.0 + (i / len(recent_series))
        for event in all_series_data[str(sid)]:
            for num in event:
                recency_counter[num] += weight

    max_recency = max(recency_counter.values()) if recency_counter else 1
    recency_scores = {num: recency_counter.get(num, 0) / max_recency for num in range(1, 26)}

    # 3. GA-based score
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

    # 4. Combined score
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


def find_jackpot_rank(target_events, number_scores):
    """
    Find rank of jackpot in ML-scored combinations.
    Returns rank of first jackpot found.
    """
    target_tuples = [combination_to_tuple(event) for event in target_events]

    # Generate all combinations with scores
    print("    Generating and scoring combinations...", end="", flush=True)
    all_combos = []
    for combo in combinations(range(1, 26), 14):
        score = score_combination(combo, number_scores)
        all_combos.append((combo, score))

    print(" sorting...", end="", flush=True)
    all_combos.sort(key=lambda x: x[1], reverse=True)
    print(" done")

    # Find rank
    for rank, (combo, score) in enumerate(all_combos, 1):
        if combo in target_tuples:
            event_idx = target_tuples.index(combo)
            return rank, combo, score, event_idx + 1

    return None, None, None, None


def simulate_pure_random_baseline(target_events, num_simulations=100):
    """Simulate pure random search to establish baseline"""
    target_tuples = [combination_to_tuple(event) for event in target_events]

    tries_list = []
    for _ in range(num_simulations):
        tries = 0
        while True:
            tries += 1
            combo = tuple(sorted(random.sample(range(1, 26), 14)))
            if combo in target_tuples:
                tries_list.append(tries)
                break

    avg_tries = sum(tries_list) / len(tries_list)
    return avg_tries, tries_list


def main():
    print("="*80)
    print("ML-RANKED SIMULATION: Series 3128-3151")
    print("="*80)
    print()
    print("Testing ML-ranked approach on 24 historical series")
    print("For each series:")
    print("  1. Train ML on data BEFORE that series")
    print("  2. Find jackpot rank in ML-sorted combinations")
    print("  3. Compare to pure random baseline")
    print()
    print("="*80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    # Test series: 3128 to 3151
    test_series = [sid for sid in all_series_ids if 3128 <= sid <= 3151]

    print(f"✅ Loaded {len(all_series_data)} series ({min(all_series_ids)}-{max(all_series_ids)})")
    print(f"✅ Testing on {len(test_series)} series ({min(test_series)}-{max(test_series)})")
    print()

    results = []

    for test_sid in test_series:
        print(f"{'='*80}")
        print(f"SERIES {test_sid}")
        print(f"{'='*80}")

        # Training data: all series before this one
        training_series_ids = [sid for sid in all_series_ids if sid < test_sid]
        target_events = all_series_data[str(test_sid)]

        print(f"  Training on {len(training_series_ids)} series ({min(training_series_ids)}-{max(training_series_ids)})")
        print(f"  Target: {len(target_events)} events")

        # Calculate ML scores
        print(f"  Calculating ML scores...")
        number_scores = calculate_ml_scores(all_series_data, training_series_ids)

        # Find jackpot rank
        rank, combo, ml_score, event_num = find_jackpot_rank(target_events, number_scores)

        if rank is None:
            print(f"  ❌ ERROR: Jackpot not found in combinations")
            continue

        percentile = 100 * rank / 4457400
        combo_str = ' '.join(f"{n:02d}" for n in combo)

        print(f"  ✅ ML-Ranked: {rank:,} tries (top {percentile:.2f}%)")
        print(f"     Event {event_num}: {combo_str} (score: {ml_score:.4f})")

        # Pure random baseline (quick estimate using expected value)
        # Average tries to find one of 7 jackpots = 4457400 / 7 ≈ 636,771
        # But we want single trial estimate, so use 636771 / 2 for median
        estimated_random = 4457400 // (len(target_events) * 2)

        print(f"  📊 Estimated Pure Random: ~{estimated_random:,} tries")

        if rank < estimated_random:
            improvement = ((estimated_random - rank) / estimated_random) * 100
            print(f"  ✅ ML-Ranked is ~{improvement:.1f}% faster")
        else:
            slower = ((rank - estimated_random) / estimated_random) * 100
            print(f"  ❌ ML-Ranked is ~{slower:.1f}% slower")

        print()

        results.append({
            'series_id': test_sid,
            'training_size': len(training_series_ids),
            'ml_rank': rank,
            'ml_percentile': percentile,
            'ml_score': ml_score,
            'combination': list(combo),
            'event_number': event_num,
            'estimated_random': estimated_random,
            'improvement_pct': ((estimated_random - rank) / estimated_random) * 100
        })

    # Summary statistics
    print("="*80)
    print("SIMULATION SUMMARY")
    print("="*80)
    print()

    ml_ranks = [r['ml_rank'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    percentiles = [r['ml_percentile'] for r in results]

    avg_rank = sum(ml_ranks) / len(ml_ranks)
    avg_improvement = sum(improvements) / len(improvements)
    avg_percentile = sum(percentiles) / len(percentiles)

    wins = sum(1 for imp in improvements if imp > 0)
    losses = sum(1 for imp in improvements if imp <= 0)

    print(f"Series tested: {len(results)}")
    print(f"ML-Ranked average rank: {avg_rank:,.0f} / 4,457,400")
    print(f"ML-Ranked average percentile: Top {avg_percentile:.2f}%")
    print(f"Average improvement: {avg_improvement:+.1f}%")
    print(f"Win rate: {wins}/{len(results)} ({100*wins/len(results):.1f}%)")
    print()

    print("Best performances:")
    sorted_results = sorted(results, key=lambda x: x['improvement_pct'], reverse=True)
    for i, r in enumerate(sorted_results[:5], 1):
        combo_str = ' '.join(f"{n:02d}" for n in r['combination'])
        print(f"  {i}. Series {r['series_id']}: {r['improvement_pct']:+.1f}% (rank {r['ml_rank']:,})")
        print(f"     {combo_str}")

    print()
    print("Worst performances:")
    for i, r in enumerate(sorted_results[-5:][::-1], 1):
        combo_str = ' '.join(f"{n:02d}" for n in r['combination'])
        print(f"  {i}. Series {r['series_id']}: {r['improvement_pct']:+.1f}% (rank {r['ml_rank']:,})")
        print(f"     {combo_str}")

    print()
    print("="*80)
    print("DETAILED RESULTS")
    print("="*80)
    print()

    print(f"{'Series':<8} {'Rank':>10} {'Percentile':>12} {'Est Random':>12} {'Improvement':>12}")
    print(f"{'-'*8} {'-'*10} {'-'*12} {'-'*12} {'-'*12}")

    for r in results:
        print(f"{r['series_id']:<8} {r['ml_rank']:>10,} {r['ml_percentile']:>11.2f}% "
              f"{r['estimated_random']:>12,} {r['improvement_pct']:>11.1f}%")

    print()
    print("="*80)

    # Save results
    output = {
        'simulation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'series_range': f"{min(test_series)}-{max(test_series)}",
        'series_count': len(results),
        'summary': {
            'average_rank': avg_rank,
            'average_percentile': avg_percentile,
            'average_improvement_pct': avg_improvement,
            'win_rate': 100 * wins / len(results),
            'wins': wins,
            'losses': losses
        },
        'results': results
    }

    with open('ml_ranked_simulation_3128_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("📁 Results saved to: ml_ranked_simulation_3128_3151.json")
    print("="*80)


if __name__ == "__main__":
    main()
