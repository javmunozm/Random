#!/usr/bin/env python3
"""
WEIGHTED MANDEL ENSEMBLE - Final Optimized Approach

Combines:
1. ML confidence scores (top 8 numbers get 2x boost)
2. Mandel exclusion (eliminate historical combinations)
3. Weighted probabilistic generation (balanced exploration)

This leverages what ML does well without over-relying on it.
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


def calculate_ml_confidence_scores(all_series_data, training_series_ids):
    """Calculate ML confidence scores with GA + frequency"""

    # Frequency
    freq_counter = Counter()
    for sid in training_series_ids:
        for event in all_series_data[str(sid)]:
            for num in event:
                freq_counter[num] += 1

    max_freq = max(freq_counter.values())
    freq_scores = {num: freq_counter.get(num, 0) / max_freq for num in range(1, 26)}

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

    # Combined (weight GA more)
    confidence_scores = {}
    for num in range(1, 26):
        confidence_scores[num] = (
            0.60 * ga_scores[num] +
            0.40 * freq_scores[num]
        )

    return confidence_scores


def build_mandel_exclusion_set(all_series_data, series_ids):
    """Build Mandel exclusion set"""
    exclusion_set = set()
    for sid in series_ids:
        for event in all_series_data[str(sid)]:
            exclusion_set.add(combination_to_tuple(event))
    return exclusion_set


def apply_tiered_weights(confidence_scores):
    """
    Apply tiered weight boost:
    - Top 8: 2.0x boost
    - Next 10: 1.0x (unchanged)
    - Bottom 7: 0.5x (reduced)
    """
    sorted_nums = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)

    weighted_scores = {}
    for rank, (num, score) in enumerate(sorted_nums, 1):
        if rank <= 8:
            weighted_scores[num] = score * 2.0  # Top 8: boost
        elif rank <= 18:
            weighted_scores[num] = score * 1.0  # Next 10: unchanged
        else:
            weighted_scores[num] = score * 0.5  # Bottom 7: reduce

    # Normalize to probabilities
    total = sum(weighted_scores.values())
    probabilities = {num: score / total for num, score in weighted_scores.items()}

    return probabilities, weighted_scores


def generate_weighted_mandel_combination(probabilities):
    """Generate combination using weighted sampling (exclusion checked externally)"""
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

    return combination_to_tuple(selected)


def weighted_mandel_search(series_id, all_data, probabilities, exclusion_set):
    """Search using weighted Mandel ensemble"""
    print(f"\n{'='*80}")
    print(f"WEIGHTED MANDEL ENSEMBLE - SERIES {series_id}")
    print(f"{'='*80}\n")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    target_tuples = [combination_to_tuple(event) for event in target_events]

    print(f"Target: {len(target_events)} events")
    print(f"Exclusion set: {len(exclusion_set):,} historical combinations")
    print(f"Strategy: Weighted (top 8: 2x, next 10: 1x, bottom 7: 0.5x) + Mandel")
    print()

    all_exclusions = exclusion_set.copy()  # Start with Mandel exclusions
    unique_tries = 0
    start_time = datetime.now()

    while True:
        # Generate weighted combination
        combo = generate_weighted_mandel_combination(probabilities)

        # Skip if already tried or in exclusion set
        if combo in all_exclusions:
            continue

        all_exclusions.add(combo)
        unique_tries += 1

        # Check if jackpot
        if combo in target_tuples:
            elapsed = (datetime.now() - start_time).total_seconds()
            event_idx = target_tuples.index(combo)
            combo_str = ' '.join(f"{n:02d}" for n in combo)

            print(f"\n🎉 JACKPOT FOUND!")
            print(f"   Event: {event_idx + 1}")
            print(f"   Unique tries: {unique_tries:,}")
            print(f"   Time: {elapsed:.3f} seconds")
            print(f"   Rate: {unique_tries/elapsed:.0f} unique/sec")
            print(f"   Combination: {combo_str}")

            return {
                'series_id': series_id,
                'method': 'Weighted Mandel Ensemble',
                'tries': unique_tries,
                'time_seconds': elapsed,
                'rate': unique_tries/elapsed,
                'combination': list(combo),
                'event_number': event_idx + 1,
                'found': True
            }

        # Progress
        if unique_tries % 50000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = unique_tries / elapsed if elapsed > 0 else 0
            print(f"  {unique_tries:>10,} unique tries | Rate: {rate:>7.0f}/sec | Time: {elapsed:.1f}s")


def simulate_weighted_mandel_ensemble(all_series_data, test_series_ids):
    """Run simulation on multiple series"""

    results = []
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    for test_sid in test_series_ids:
        print(f"\n{'='*80}")
        print(f"SERIES {test_sid}")
        print(f"{'='*80}")

        # Training data
        training_series_ids = [sid for sid in all_series_ids if sid < test_sid]

        print(f"Training on {len(training_series_ids)} series")

        # Calculate ML confidence
        print("Calculating ML confidence scores...")
        confidence_scores = calculate_ml_confidence_scores(all_series_data, training_series_ids)

        # Apply tiered weights
        probabilities, weighted_scores = apply_tiered_weights(confidence_scores)

        # Build Mandel exclusion
        exclusion_set = build_mandel_exclusion_set(all_series_data, training_series_ids)

        # Show top numbers
        sorted_weighted = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
        print(f"\nTop 10 weighted numbers:")
        for rank, (num, score) in enumerate(sorted_weighted[:10], 1):
            prob = probabilities[num]
            tier = "Top8" if rank <= 8 else "Next10" if rank <= 18 else "Bottom7"
            bar = '█' * int(prob * 200)
            print(f"  {rank:2d}. Number {num:2d} [{tier:7s}]: {bar} {prob:.4f}")

        # Run search
        result = weighted_mandel_search(test_sid, all_series_data, probabilities, exclusion_set)

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
            print(f"Weighted Mandel:       {result['tries']:,} tries")
            print(f"Improvement: {improvement:+.1f}%")

    return results


def main():
    print("="*80)
    print("WEIGHTED MANDEL ENSEMBLE - Series 3128-3151")
    print("="*80)
    print()
    print("Strategy: ML-weighted + Mandel exclusion")
    print("  - Top 8 numbers: 2.0x weight boost")
    print("  - Next 10 numbers: 1.0x weight")
    print("  - Bottom 7 numbers: 0.5x weight")
    print("  - Mandel exclusion: Remove historical combinations")
    print("="*80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    # Test series
    test_series = [sid for sid in all_series_ids if 3128 <= sid <= 3151]

    print(f"Testing on {len(test_series)} series: {min(test_series)}-{max(test_series)}")

    # Run simulation
    results = simulate_weighted_mandel_ensemble(all_series_data, test_series)

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

    best_result = min(results, key=lambda x: x['tries'])
    worst_result = max(results, key=lambda x: x['tries'])

    print(f"Series tested: {len(results)}")
    print(f"Average tries: {avg_tries:,.0f}")
    print(f"Pure random baseline: ~{baseline:,}")
    print(f"Average improvement: {avg_improvement:+.1f}%")
    print(f"Win rate: {wins}/{len(results)} ({100*wins/len(results):.1f}%)")
    print()
    print(f"Best: Series {best_result['series_id']} - {best_result['tries']:,} tries")
    print(f"Worst: Series {worst_result['series_id']} - {worst_result['tries']:,} tries")
    print()

    # Comparison to other methods
    print("="*80)
    print("COMPARISON TO OTHER ML APPROACHES")
    print("="*80)
    print()
    print(f"{'Method':<30s} {'Avg Tries':<15s} {'vs Baseline':<15s} {'Win Rate':<10s}")
    print("-"*70)
    print(f"{'Pure Random Baseline':<30s} {'~318,385':<15s} {'0%':<15s} {'N/A':<10s}")
    print(f"{'ML-Ranked (exhaustive)':<30s} {'538,173':<15s} {'-69.0%':<15s} {'41.7%':<10s}")
    print(f"{'Smart Sampling':<30s} {'493,378':<15s} {'-55.0%':<15s} {'33.3%':<10s}")
    print(f"{'Weighted Mandel Ensemble':<30s} {f'{avg_tries:,.0f}':<15s} {f'{avg_improvement:+.1f}%':<15s} {f'{100*wins/len(results):.1f}%':<10s}")
    print()

    # Save
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'method': 'Weighted Mandel Ensemble',
        'series_range': f"{min(test_series)}-{max(test_series)}",
        'strategy': {
            'top_8_weight': 2.0,
            'middle_10_weight': 1.0,
            'bottom_7_weight': 0.5,
            'mandel_exclusion': True
        },
        'summary': {
            'series_tested': len(results),
            'average_tries': avg_tries,
            'baseline': baseline,
            'average_improvement_pct': avg_improvement,
            'win_rate': 100 * wins / len(results),
            'wins': wins,
            'losses': losses,
            'best_series': best_result['series_id'],
            'best_tries': best_result['tries'],
            'worst_series': worst_result['series_id'],
            'worst_tries': worst_result['tries']
        },
        'results': results
    }

    with open('weighted_mandel_ensemble_3128_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("📁 Results saved to: weighted_mandel_ensemble_3128_3151.json")
    print("="*80)


if __name__ == "__main__":
    main()
