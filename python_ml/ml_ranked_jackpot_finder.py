#!/usr/bin/env python3
"""
ML-RANKED EXHAUSTIVE JACKPOT FINDER

Force ML to predict jackpots by:
1. Use ALL ML signals (GA, frequency, recency, pairs)
2. Score every single number 1-25 with combined ML weights
3. Generate combinations in order of ML-predicted likelihood
4. Try highest-ranked combinations first until jackpot found

This makes ML actively drive the search order.
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
        weight = 1.0 + (i / len(recent_series))  # More recent = higher weight
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

    # 4. Combined score (weighted average)
    combined_scores = {}
    for num in range(1, 26):
        combined_scores[num] = (
            0.40 * ga_scores[num] +        # GA is best model
            0.30 * freq_scores[num] +       # Overall frequency
            0.30 * recency_scores[num]      # Recent patterns
        )

    return combined_scores, ga_scores, freq_scores, recency_scores


def score_combination(combo, number_scores):
    """Score a combination based on sum of individual number scores"""
    return sum(number_scores[num] for num in combo)


def generate_all_combinations_ranked(number_scores):
    """Generate all C(25,14) combinations ranked by ML score"""
    print("Generating and ranking all 4,457,400 combinations...")
    print("(This will take a moment...)")

    all_combos = []
    count = 0

    for combo in combinations(range(1, 26), 14):
        score = score_combination(combo, number_scores)
        all_combos.append((combo, score))
        count += 1
        if count % 500000 == 0:
            print(f"  Generated {count:,} combinations...")

    print(f"Sorting {len(all_combos):,} combinations by ML score...")
    all_combos.sort(key=lambda x: x[1], reverse=True)  # Highest score first

    return all_combos


def find_jackpot_ml_ranked(series_id, all_data, ranked_combinations):
    """Search through combinations in ML-ranked order"""
    print(f"\n{'='*80}")
    print(f"ML-RANKED JACKPOT SEARCH - SERIES {series_id}")
    print(f"{'='*80}\n")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    target_tuples = [combination_to_tuple(event) for event in target_events]

    print(f"Searching through {len(ranked_combinations):,} combinations")
    print(f"Ordered by ML prediction score (highest first)")
    print(f"Target: {len(target_events)} jackpot events\n")

    print("Top 10 ML-predicted combinations:")
    for i in range(10):
        combo, score = ranked_combinations[i]
        combo_str = ' '.join(f"{n:02d}" for n in combo)
        print(f"  Rank {i+1:2d}: {combo_str} (ML score: {score:.4f})")
    print()

    tries = 0
    start_time = datetime.now()
    best_match = 0

    print("Searching for jackpot in ML-ranked order...\n")

    for combo, ml_score in ranked_combinations:
        tries += 1

        # Check if this is a jackpot
        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            combo_str = ' '.join(f"{n:02d}" for n in combo)

            # Find which event
            event_idx = target_tuples.index(combo)

            print(f"\n{'='*80}")
            print(f"🎉 JACKPOT FOUND WITH ML-RANKED SEARCH!")
            print(f"{'='*80}")
            print(f"Event: {event_idx + 1}")
            print(f"Tries: {tries:,}")
            print(f"Rank: {tries} / 4,457,400 (top {100*tries/4457400:.4f}%)")
            print(f"Time: {elapsed:.1f} seconds")
            print(f"Rate: {tries/elapsed:.0f} combinations/sec")
            print(f"ML Score: {ml_score:.4f}")
            print(f"Combination: {combo_str}")

            return {
                'series_id': series_id,
                'tries': tries,
                'rank': tries,
                'total_combinations': len(ranked_combinations),
                'percentile': 100 * tries / len(ranked_combinations),
                'time_seconds': elapsed,
                'rate': tries/elapsed,
                'ml_score': ml_score,
                'combination': list(combo),
                'event_number': event_idx + 1,
                'found': True
            }

        # Track best match
        for target in target_tuples:
            matches = len(set(combo) & set(target))
            if matches > best_match:
                best_match = matches

        # Progress every 100K
        if tries % 100000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = tries / elapsed if elapsed > 0 else 0
            percentile = 100 * tries / len(ranked_combinations)
            print(f"  {tries:>10,} / {len(ranked_combinations):,} ({percentile:>6.2f}%) | "
                  f"Best: {best_match}/14 | Rate: {rate:>7.0f}/sec | Score: {ml_score:.4f}")

    # Not found
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n❌ JACKPOT NOT FOUND")
    print(f"   Searched all {len(ranked_combinations):,} combinations")
    print(f"   Time: {elapsed:.1f} seconds")

    return {
        'series_id': series_id,
        'tries': len(ranked_combinations),
        'found': False
    }


def main():
    print("="*80)
    print("ML-RANKED EXHAUSTIVE JACKPOT FINDER - SERIES 3151")
    print("="*80)
    print()
    print("Strategy:")
    print("  1. Calculate ML score for each number (GA + frequency + recency)")
    print("  2. Score all 4,457,400 combinations by sum of number scores")
    print("  3. Sort combinations by ML score (highest first)")
    print("  4. Search in ML-ranked order until jackpot found")
    print()
    print("This forces ML to actively drive the search order.")
    print("="*80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])
    training_series_ids = [sid for sid in all_series_ids if sid <= 3150]

    print(f"✅ Loaded {len(all_series_data)} series")
    print(f"✅ Training on {len(training_series_ids)} series\n")

    # Calculate ML scores
    print("Calculating ML scores for each number...")
    number_scores, ga_scores, freq_scores, recency_scores = calculate_ml_scores(
        all_series_data, training_series_ids
    )

    print("\nML Number Rankings:")
    sorted_numbers = sorted(number_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (num, score) in enumerate(sorted_numbers, 1):
        bar = '█' * int(score * 40)
        print(f"  {rank:2d}. Number {num:2d}: {bar} {score:.4f} "
              f"(GA:{ga_scores[num]:.3f} Freq:{freq_scores[num]:.3f} Recent:{recency_scores[num]:.3f})")
    print()

    # Generate and rank all combinations
    ranked_combos = generate_all_combinations_ranked(number_scores)

    print(f"✅ Generated and ranked {len(ranked_combos):,} combinations\n")

    # Find jackpot
    result = find_jackpot_ml_ranked(3151, all_series_data, ranked_combos)

    if result['found']:
        print()
        print("="*80)
        print("RESULT: ML-RANKED SEARCH")
        print("="*80)
        print()

        combo_str = ' '.join(f"{n:02d}" for n in result['combination'])
        print(f"✅ ML-RANKED SEARCH FOUND JACKPOT")
        print(f"   Event: {result['event_number']}")
        print(f"   Tries: {result['tries']:,}")
        print(f"   ML Rank: {result['rank']:,} / 4,457,400")
        print(f"   Percentile: Top {result['percentile']:.4f}%")
        print(f"   Time: {result['time_seconds']:.1f} seconds")
        print(f"   Combination: {combo_str}")
        print()

        print("COMPARISON TO OTHER METHODS:")
        print(f"  Pure Random:          285,368 tries")
        print(f"  ML-Weighted:        1,933,375 tries")
        print(f"  ML Pool Reduction:    359,112 tries")
        print(f"  ML-Ranked:            {result['tries']:,} tries")
        print()

        if result['tries'] < 285368:
            improvement = ((285368 - result['tries']) / 285368) * 100
            print(f"✅ ML-Ranked is {improvement:.1f}% FASTER than pure random!")
        else:
            slower = ((result['tries'] - 285368) / 285368) * 100
            print(f"ML-Ranked is {slower:.1f}% slower than pure random")

        # Save
        output = {
            'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'series_id': 3151,
            'method': 'ML-Ranked Exhaustive Search',
            'result': result
        }

        with open('ml_ranked_jackpot_3151.json', 'w') as f:
            json.dump(output, f, indent=2)

        print()
        print("📁 Results saved to: ml_ranked_jackpot_3151.json")
        print("="*80)


if __name__ == "__main__":
    main()
