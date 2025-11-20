#!/usr/bin/env python3
"""
SMART SAMPLING JACKPOT FINDER - Final Fix

Problem: Previous approaches either:
- Exhaust large top % (expensive penalty if not found)
- Use pure ML ranking (slow for low-scored jackpots)
- Use weighted random (too biased, slow)

Solution: Smart probabilistic sampling
- Generate combinations by sampling numbers with probability = ML score
- But use sqrt() transform to reduce bias (make it less extreme)
- Check each combination as generated
- Continue until found

This balances exploration (try high ML scores) with exploitation (still tries low scores).
"""

import json
import random
from datetime import datetime
from collections import Counter


def load_series_data(file_path="full_series_data.json", min_series=2982):
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return {k: v for k, v in all_data.items() if int(k) >= min_series}


def combination_to_tuple(combination):
    return tuple(sorted(combination))


def calculate_ml_scores(all_series_data, training_series_ids):
    """Calculate comprehensive ML score for each number"""

    # Frequency
    freq_counter = Counter()
    for sid in training_series_ids:
        for event in all_series_data[str(sid)]:
            for num in event:
                freq_counter[num] += 1

    max_freq = max(freq_counter.values())
    freq_scores = {num: freq_counter.get(num, 0) / max_freq for num in range(1, 26)}

    # Recency
    recency_counter = Counter()
    recent_series = sorted(training_series_ids)[-20:]
    for i, sid in enumerate(recent_series):
        weight = 1.0 + (i / len(recent_series))
        for event in all_series_data[str(sid)]:
            for num in event:
                recency_counter[num] += weight

    max_recency = max(recency_counter.values()) if recency_counter else 1
    recency_scores = {num: recency_counter.get(num, 0) / max_recency for num in range(1, 26)}

    # GA
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

    ga_counter = Counter()
    for combo in population:
        for num in combo:
            ga_counter[num] += 1

    max_ga = max(ga_counter.values())
    ga_scores = {num: ga_counter.get(num, 0) / max_ga for num in range(1, 26)}

    # Combined with sqrt transform to reduce bias
    combined_scores = {}
    for num in range(1, 26):
        raw_score = (
            0.40 * ga_scores[num] +
            0.30 * freq_scores[num] +
            0.30 * recency_scores[num]
        )
        # Apply sqrt to reduce extreme bias
        combined_scores[num] = raw_score ** 0.5

    # Normalize to probabilities
    total = sum(combined_scores.values())
    probabilities = {num: score / total for num, score in combined_scores.items()}

    return probabilities


def generate_smart_combination(probabilities, exclusion_set, max_attempts=1000):
    """Generate combination using smart probabilistic sampling"""
    for _ in range(max_attempts):
        numbers = list(range(1, 26))
        weights = [probabilities[num] for num in numbers]

        selected = []
        available_nums = numbers[:]
        available_weights = weights[:]

        for _ in range(14):
            choice_idx = random.choices(range(len(available_nums)), weights=available_weights)[0]
            selected.append(available_nums[choice_idx])
            available_nums.pop(choice_idx)
            available_weights.pop(choice_idx)

        combo_tuple = combination_to_tuple(selected)
        if combo_tuple not in exclusion_set:
            return combo_tuple

    return None


def smart_sampling_search(series_id, all_data, probabilities):
    """Search using smart probabilistic sampling"""
    print(f"\n{'='*80}")
    print(f"SMART SAMPLING SEARCH - SERIES {series_id}")
    print(f"{'='*80}\n")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    target_tuples = [combination_to_tuple(event) for event in target_events]

    print(f"Target: {len(target_events)} events")
    print(f"Strategy: Smart probabilistic sampling (ML-guided with reduced bias)")
    print()

    print("ML Probabilities (sqrt-transformed for balanced exploration):")
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    for rank, (num, prob) in enumerate(sorted_probs[:10], 1):
        bar = '█' * int(prob * 200)
        print(f"  {rank:2d}. Number {num:2d}: {bar} {prob:.4f}")
    print()

    print("Searching with smart sampling...\n")

    tried = set()
    tries = 0
    start_time = datetime.now()

    while True:
        tries += 1

        # Generate smart combination
        combo = generate_smart_combination(probabilities, tried)

        if combo is None:
            # Exhausted attempts, generate pure random
            combo = combination_to_tuple(random.sample(range(1, 26), 14))
            while combo in tried:
                combo = combination_to_tuple(random.sample(range(1, 26), 14))

        tried.add(combo)

        # Check if jackpot
        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            event_idx = target_tuples.index(combo)
            combo_str = ' '.join(f"{n:02d}" for n in combo)

            print(f"\n🎉 JACKPOT FOUND WITH SMART SAMPLING!")
            print(f"   Event: {event_idx + 1}")
            print(f"   Tries: {tries:,}")
            print(f"   Time: {elapsed:.3f} seconds")
            print(f"   Rate: {tries/elapsed:.0f} tries/sec")
            print(f"   Combination: {combo_str}")

            return {
                'series_id': series_id,
                'method': 'Smart Sampling',
                'tries': tries,
                'time_seconds': elapsed,
                'rate': tries/elapsed,
                'combination': list(combo),
                'event_number': event_idx + 1,
                'found': True
            }

        # Progress
        if tries % 50000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = tries / elapsed if elapsed > 0 else 0
            print(f"  {tries:>10,} tries | Rate: {rate:>7.0f}/sec | Time: {elapsed:.1f}s")


def simulate_smart_sampling(all_series_data, test_series_ids):
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

        # Calculate ML probabilities
        print("Calculating ML probabilities...")
        probabilities = calculate_ml_scores(all_series_data, training_series_ids)

        # Run smart sampling
        result = smart_sampling_search(test_sid, all_series_data, probabilities)

        if result:
            results.append(result)

            # Compare
            baseline = 318385
            improvement = ((baseline - result['tries']) / baseline) * 100

            print()
            print("="*80)
            print("COMPARISON")
            print("="*80)
            print(f"Pure Random Baseline: ~{baseline:,} tries")
            print(f"Smart Sampling:        {result['tries']:,} tries")
            print(f"Improvement: {improvement:+.1f}%")

    return results


def main():
    print("="*80)
    print("SMART SAMPLING APPROACH - Series 3128-3151")
    print("="*80)
    print()
    print("Strategy: Probabilistic sampling with ML guidance")
    print("  - Sample numbers with probability ∝ sqrt(ML_score)")
    print("  - Sqrt transform reduces bias, balances exploration")
    print("  - No exhaustive stage - continuous smart generation")
    print("="*80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    # Test series
    test_series = [sid for sid in all_series_ids if 3128 <= sid <= 3151]

    print(f"Testing on {len(test_series)} series: {min(test_series)}-{max(test_series)}")

    # Run simulation
    results = simulate_smart_sampling(all_series_data, test_series)

    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print()

    tries_list = [r['tries'] for r in results]
    avg_tries = sum(tries_list) / len(tries_list)
    baseline = 318385

    wins = sum(1 for t in tries_list if t < baseline)
    losses = sum(1 for t in tries_list if t >= baseline)

    avg_improvement = ((baseline - avg_tries) / baseline) * 100

    print(f"Series tested: {len(results)}")
    print(f"Average tries: {avg_tries:,.0f}")
    print(f"Pure random baseline: ~{baseline:,}")
    print(f"Average improvement: {avg_improvement:+.1f}%")
    print(f"Win rate: {wins}/{len(results)} ({100*wins/len(results):.1f}%)")
    print()

    # Save
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'method': 'Smart Sampling (sqrt-transformed ML probabilities)',
        'series_range': f"{min(test_series)}-{max(test_series)}",
        'summary': {
            'series_tested': len(results),
            'average_tries': avg_tries,
            'baseline': baseline,
            'average_improvement_pct': avg_improvement,
            'win_rate': 100 * wins / len(results),
            'wins': wins,
            'losses': losses
        },
        'results': results
    }

    with open('smart_sampling_3128_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("📁 Results saved to: smart_sampling_3128_3151.json")
    print("="*80)


if __name__ == "__main__":
    main()
