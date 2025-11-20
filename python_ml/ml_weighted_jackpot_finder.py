#!/usr/bin/env python3
"""
Find jackpot for Series 3151 using ML-GUIDED weighted generation
Keep trying ML-weighted combinations until jackpot found

This tests if ML guidance helps find jackpots faster than pure random
"""

import json
import random
from datetime import datetime
from collections import Counter


def load_series_data(file_path="full_series_data.json", min_series=2982):
    """Load and filter series data"""
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return {k: v for k, v in all_data.items() if int(k) >= min_series}


def combination_to_tuple(combination):
    """Convert combination to sorted tuple"""
    return tuple(sorted(combination))


def build_exclusion_set(all_data, exclude_series=None):
    """Build set of all historical combinations to exclude"""
    exclusion_set = set()
    for series_id, events in all_data.items():
        if exclude_series and str(series_id) == str(exclude_series):
            continue
        for event in events:
            exclusion_set.add(combination_to_tuple(event))
    return exclusion_set


def genetic_algorithm_for_weights(all_series_data, training_series_ids, seed=331):
    """Run GA to get ML weights for numbers"""
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

    # Calculate weights from final population
    number_freq = Counter()
    for combo in population:
        for num in combo:
            number_freq[num] += 1

    # Get best combination
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

    # Combine frequency with best combo bonus
    ml_weights = {}
    for num in range(1, 26):
        freq_weight = number_freq.get(num, 0) / pop_size
        best_bonus = 2.0 if num in best_combo else 1.0
        ml_weights[num] = freq_weight * best_bonus

    # Normalize
    total_weight = sum(ml_weights.values())
    ml_probabilities = {num: (weight / total_weight) for num, weight in ml_weights.items()}

    return best_combo, best_score, ml_probabilities


def generate_ml_weighted_combination(ml_probabilities, exclusion_set):
    """Generate combination weighted by ML predictions"""
    max_attempts = 1000
    for _ in range(max_attempts):
        numbers = list(range(1, 26))
        weights = [ml_probabilities[num] for num in numbers]

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

    # Fallback to pure random if weighted fails
    while True:
        combo = combination_to_tuple(random.sample(range(1, 26), 14))
        if combo not in exclusion_set:
            return combo


def find_jackpot_ml_guided(series_id, all_data, ml_probabilities, exclusion_set):
    """Find jackpot using ML-weighted generation"""
    print(f"\n{'='*80}")
    print(f"FINDING JACKPOT FOR SERIES {series_id} - ML-WEIGHTED APPROACH")
    print(f"{'='*80}")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    print(f"Target series has {len(target_events)} events")
    print(f"Exclusion set: {len(exclusion_set):,} historical combinations")
    print(f"Strategy: ML-WEIGHTED random (biased toward ML predictions)")
    print()

    # Show top ML weights
    sorted_weights = sorted(ml_probabilities.items(), key=lambda x: x[1], reverse=True)
    print("Top 10 ML-predicted numbers:")
    for i, (num, prob) in enumerate(sorted_weights[:10], 1):
        bar = '█' * int(prob * 100)
        print(f"  {i:2d}. Number {num:2d}: {bar} {prob*100:5.2f}%")
    print()

    tries = 0
    best_match = 0
    start_time = datetime.now()

    print("Searching for jackpot using ML-weighted generation...\n")

    while True:
        tries += 1

        # Generate ML-weighted combination
        combo = generate_ml_weighted_combination(ml_probabilities, exclusion_set)

        # Check against all events
        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if combo == event_tuple:
                # JACKPOT FOUND!
                elapsed = (datetime.now() - start_time).total_seconds()
                combo_str = ' '.join(f"{n:02d}" for n in combo)

                print(f"\n🎉 JACKPOT FOUND WITH ML-WEIGHTED APPROACH!")
                print(f"   Tries: {tries:,}")
                print(f"   Time: {elapsed:.1f} seconds")
                print(f"   Rate: {tries/elapsed:.0f} tries/sec")
                print(f"   Combination: {combo_str}")

                return {
                    'series_id': series_id,
                    'tries': tries,
                    'time_seconds': elapsed,
                    'rate': tries/elapsed,
                    'combination': list(combo),
                    'method': 'ML-Weighted',
                    'found': True
                }

            # Track best match
            matches = len(set(combo) & set(event))
            match_pct = (matches / 14) * 100
            if match_pct > best_match:
                best_match = match_pct

        # Progress every 100K tries
        if tries % 100000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = tries / elapsed if elapsed > 0 else 0
            print(f"  {tries:>10,} tries | Best: {best_match:5.2f}% | "
                  f"Time: {elapsed:>6.1f}s | Rate: {rate:>7.0f} tries/sec")


def main():
    print("=" * 80)
    print("ML-WEIGHTED JACKPOT FINDER - SERIES 3151")
    print("=" * 80)
    print()
    print("Using the ML-GUIDED MODEL to find jackpot")
    print("Generates combinations WEIGHTED by ML predictions")
    print("Tests if ML guidance helps find jackpots faster than pure random")
    print("=" * 80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    print(f"✅ Loaded {len(all_series_data)} series ({min(all_series_ids)}-{max(all_series_ids)})")

    # Build exclusion set
    exclusion_set = build_exclusion_set(all_series_data, exclude_series=3151)
    print(f"✅ Built exclusion set: {len(exclusion_set):,} combinations to avoid")

    # Train ML
    training_series_ids = [sid for sid in all_series_ids if sid <= 3150]
    print(f"✅ Training ML on {len(training_series_ids)} series")
    print()

    print("Running Genetic Algorithm for ML weights...")
    best_combo, best_score, ml_probabilities = genetic_algorithm_for_weights(
        all_series_data,
        training_series_ids,
        seed=331
    )

    best_combo_str = ' '.join(f"{n:02d}" for n in best_combo)
    print(f"✅ ML Training complete")
    print(f"   Best GA combination: {best_combo_str}")
    print(f"   Training score: {(best_score/14)*100:.2f}%")

    # Find jackpot using ML-weighted approach
    result = find_jackpot_ml_guided(3151, all_series_data, ml_probabilities, exclusion_set)

    if result:
        print()
        print("=" * 80)
        print("FINAL RESULT - ML-WEIGHTED APPROACH")
        print("=" * 80)
        print()
        print(f"Jackpot found after {result['tries']:,} ML-weighted tries")
        print(f"Time taken: {result['time_seconds']:.1f} seconds")
        print(f"Processing rate: {result['rate']:.0f} tries/second")
        print()

        combo_str = ' '.join(f"{n:02d}" for n in result['combination'])
        print(f"Jackpot combination: {combo_str}")
        print()

        # Compare to pure random
        print("=" * 80)
        print("COMPARISON: ML-WEIGHTED vs PURE RANDOM")
        print("=" * 80)
        print()
        print(f"Pure Random (previous test):    285,368 tries")
        print(f"ML-Weighted (this test):        {result['tries']:,} tries")
        print()

        if result['tries'] < 285368:
            improvement = ((285368 - result['tries']) / 285368) * 100
            print(f"✅ ML-Weighted is FASTER by {improvement:.1f}%")
            print(f"   Saved {285368 - result['tries']:,} tries!")
        elif result['tries'] > 285368:
            slower = ((result['tries'] - 285368) / 285368) * 100
            print(f"❌ ML-Weighted is SLOWER by {slower:.1f}%")
            print(f"   Needed {result['tries'] - 285368:,} more tries")
        else:
            print("➡️  Same performance")

        print()

        # Save result
        output = {
            'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'series_id': 3151,
            'method': 'ML-Weighted Generation',
            'tries_to_jackpot': result['tries'],
            'time_seconds': result['time_seconds'],
            'processing_rate': result['rate'],
            'jackpot_combination': result['combination'],
            'comparison': {
                'pure_random_tries': 285368,
                'ml_weighted_tries': result['tries'],
                'difference': result['tries'] - 285368,
                'improvement_pct': ((285368 - result['tries']) / 285368) * 100
            }
        }

        with open('ml_weighted_jackpot_3151.json', 'w') as f:
            json.dump(output, f, indent=2)

        print("📁 Results saved to: ml_weighted_jackpot_3151.json")
        print("=" * 80)


if __name__ == "__main__":
    main()
