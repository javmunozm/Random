#!/usr/bin/env python3
"""
ML ENSEMBLE CONSENSUS JACKPOT FINDER

Most sophisticated approach combining multiple ML strategies:
1. Train MULTIPLE different ML models (GA, PSO, Frequency, etc.)
2. Each model predicts 14 numbers
3. Find CONSENSUS numbers (appear in 80%+ of models)
4. These consensus numbers are "highly confident" ML predictions
5. Brute force the GAP (remaining numbers needed to reach 14)
6. This dramatically reduces search space

Example:
- 5 models predict different 14-number combinations
- 11 numbers appear in 80%+ of predictions (consensus)
- Need 3 more numbers from remaining 14 (gap)
- C(14, 3) = 364 combinations (tiny!)
- Exhaustively check all 364 combinations

This leverages ML for what it's good at (finding likely numbers)
while using brute force only for the uncertain gap.
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


def test_combination(combination, all_series_data, test_series_ids):
    """Test combination and return average best match"""
    total_best = 0
    for series_id in test_series_ids:
        actual_events = all_series_data[str(series_id)]
        best_match = max(len(set(combination) & set(event)) for event in actual_events)
        total_best += best_match
    return total_best / len(test_series_ids)


def genetic_algorithm_model(all_series_data, training_series_ids, seed=None):
    """Genetic Algorithm model"""
    if seed is not None:
        random.seed(seed)

    pop_size = 200
    generations = 10
    population = [sorted(random.sample(range(1, 26), 14)) for _ in range(pop_size)]

    for gen in range(generations):
        fitness_scores = []
        for combo in population:
            score = test_combination(combo, all_series_data, training_series_ids)
            fitness_scores.append((combo, score))

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

    # Return best combination
    final_fitness = [(combo, test_combination(combo, all_series_data, training_series_ids))
                     for combo in population]
    best_combo, best_score = max(final_fitness, key=lambda x: x[1])

    return best_combo, best_score


def frequency_based_model(all_series_data, training_series_ids):
    """Frequency-based model - selects most common numbers"""
    number_freq = Counter()

    for series_id in training_series_ids:
        events = all_series_data[str(series_id)]
        for event in events:
            for num in event:
                number_freq[num] += 1

    # Select top 14 most frequent
    sorted_numbers = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
    prediction = sorted([num for num, freq in sorted_numbers[:14]])
    score = test_combination(prediction, all_series_data, training_series_ids)

    return prediction, score


def recent_pattern_model(all_series_data, training_series_ids):
    """Recent pattern model - emphasizes recent series"""
    number_freq = Counter()

    # Weight recent series more heavily
    sorted_series = sorted(training_series_ids, reverse=True)
    for i, series_id in enumerate(sorted_series):
        weight = 1.0 / (1 + i * 0.01)  # Decay weight for older series
        events = all_series_data[str(series_id)]
        for event in events:
            for num in event:
                number_freq[num] += weight

    sorted_numbers = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
    prediction = sorted([num for num, freq in sorted_numbers[:14]])
    score = test_combination(prediction, all_series_data, training_series_ids)

    return prediction, score


def hot_numbers_model(all_series_data, training_series_ids, window=10):
    """Hot numbers model - most frequent in recent window"""
    number_freq = Counter()

    # Only look at last N series
    recent_series = sorted(training_series_ids)[-window:]
    for series_id in recent_series:
        events = all_series_data[str(series_id)]
        for event in events:
            for num in event:
                number_freq[num] += 1

    sorted_numbers = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
    prediction = sorted([num for num, freq in sorted_numbers[:14]])
    score = test_combination(prediction, all_series_data, training_series_ids)

    return prediction, score


def train_ensemble_models(all_series_data, training_series_ids):
    """Train multiple different ML models"""
    print("Training ensemble of ML models...\n")

    models = []

    # Model 1-3: Genetic Algorithm with different seeds
    for i, seed in enumerate([331, 1660, 1995], 1):
        print(f"Training GA Model {i} (seed {seed})...")
        combo, score = genetic_algorithm_model(all_series_data, training_series_ids, seed=seed)
        combo_str = ' '.join(f"{n:02d}" for n in combo)
        print(f"  Prediction: {combo_str}")
        print(f"  Score: {score*100/14:.2f}%")
        models.append(('GA-' + str(seed), combo, score))
        print()

    # Model 4: Frequency-based
    print("Training Frequency Model...")
    combo, score = frequency_based_model(all_series_data, training_series_ids)
    combo_str = ' '.join(f"{n:02d}" for n in combo)
    print(f"  Prediction: {combo_str}")
    print(f"  Score: {score*100/14:.2f}%")
    models.append(('Frequency', combo, score))
    print()

    # Model 5: Recent pattern
    print("Training Recent Pattern Model...")
    combo, score = recent_pattern_model(all_series_data, training_series_ids)
    combo_str = ' '.join(f"{n:02d}" for n in combo)
    print(f"  Prediction: {combo_str}")
    print(f"  Score: {score*100/14:.2f}%")
    models.append(('Recent', combo, score))
    print()

    # Model 6: Hot numbers (last 20 series)
    print("Training Hot Numbers Model (window=20)...")
    combo, score = hot_numbers_model(all_series_data, training_series_ids, window=20)
    combo_str = ' '.join(f"{n:02d}" for n in combo)
    print(f"  Prediction: {combo_str}")
    print(f"  Score: {score*100/14:.2f}%")
    models.append(('Hot-20', combo, score))
    print()

    return models


def find_consensus_numbers(models, consensus_threshold=0.6):
    """Find numbers that appear in at least X% of models"""
    number_appearances = Counter()

    for model_name, prediction, score in models:
        for num in prediction:
            number_appearances[num] += 1

    total_models = len(models)
    min_appearances = int(total_models * consensus_threshold)

    consensus = []
    for num in range(1, 26):
        appearances = number_appearances.get(num, 0)
        if appearances >= min_appearances:
            consensus.append(num)

    return sorted(consensus), number_appearances


def find_jackpot_with_consensus(series_id, all_data, consensus_numbers, gap_numbers):
    """Find jackpot using consensus + gap brute force"""
    print(f"\n{'='*80}")
    print(f"CONSENSUS-BASED JACKPOT SEARCH - SERIES {series_id}")
    print(f"{'='*80}")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]

    consensus_count = len(consensus_numbers)
    gap_size = 14 - consensus_count

    print(f"\nConsensus numbers ({consensus_count}): {' '.join(f'{n:02d}' for n in consensus_numbers)}")
    print(f"Gap size: {gap_size} numbers needed")
    print(f"Gap pool: {len(gap_numbers)} numbers")
    print(f"Gap numbers: {' '.join(f'{n:02d}' for n in gap_numbers)}")

    if gap_size <= 0:
        print(f"\nERROR: Consensus already has {consensus_count} numbers (need exactly 14)")
        return None

    if gap_size > len(gap_numbers):
        print(f"\nERROR: Need {gap_size} more numbers but only {len(gap_numbers)} available")
        return None

    # Calculate total combinations
    def ncr(n, r):
        if r > n or r < 0:
            return 0
        return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

    total_combinations = ncr(len(gap_numbers), gap_size)

    print(f"\nTotal combinations to check: C({len(gap_numbers)}, {gap_size}) = {total_combinations:,}")
    print(f"Reduction from pure random: {100 * (1 - total_combinations/285368):.2f}%")
    print()

    tries = 0
    best_match = 0
    start_time = datetime.now()

    print("Searching for jackpot...\n")

    # Try all combinations of gap numbers
    for gap_combo in combinations(gap_numbers, gap_size):
        tries += 1

        # Combine consensus + gap
        full_combo = tuple(sorted(consensus_numbers + list(gap_combo)))

        # Check against all events
        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if full_combo == event_tuple:
                # JACKPOT FOUND!
                elapsed = (datetime.now() - start_time).total_seconds()
                combo_str = ' '.join(f"{n:02d}" for n in full_combo)

                print(f"\n🎉 JACKPOT FOUND WITH CONSENSUS APPROACH!")
                print(f"   Tries: {tries:,} / {total_combinations:,}")
                print(f"   Progress: {100*tries/total_combinations:.2f}%")
                print(f"   Time: {elapsed:.3f} seconds")
                print(f"   Rate: {tries/elapsed:.0f} combinations/sec")
                print(f"   Combination: {combo_str}")
                print(f"   Consensus: {' '.join(f'{n:02d}' for n in consensus_numbers)}")
                print(f"   Gap filled: {' '.join(f'{n:02d}' for n in sorted(gap_combo))}")

                return {
                    'series_id': series_id,
                    'tries': tries,
                    'total_combinations': total_combinations,
                    'time_seconds': elapsed,
                    'rate': tries/elapsed,
                    'combination': list(full_combo),
                    'consensus_numbers': consensus_numbers,
                    'gap_numbers': list(gap_combo),
                    'consensus_size': consensus_count,
                    'gap_size': gap_size,
                    'found': True
                }

            # Track best match
            matches = len(set(full_combo) & set(event))
            if matches > best_match:
                best_match = matches

        # Progress updates
        if tries % 10000 == 0 and tries > 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = tries / elapsed if elapsed > 0 else 0
            progress = 100 * tries / total_combinations
            print(f"  {tries:>10,} / {total_combinations:,} ({progress:>5.1f}%) | "
                  f"Best: {best_match}/14 | Rate: {rate:>7.0f}/sec")

    # Not found
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n❌ JACKPOT NOT FOUND")
    print(f"   Checked all {total_combinations:,} combinations")
    print(f"   Time: {elapsed:.3f} seconds")
    print(f"   Best match: {best_match}/14")

    return {
        'series_id': series_id,
        'tries': total_combinations,
        'total_combinations': total_combinations,
        'time_seconds': elapsed,
        'consensus_size': consensus_count,
        'gap_size': gap_size,
        'found': False,
        'best_match': best_match
    }


def main():
    print("=" * 80)
    print("ML ENSEMBLE CONSENSUS JACKPOT FINDER - SERIES 3151")
    print("=" * 80)
    print()
    print("Revolutionary Approach:")
    print("  1. Train MULTIPLE different ML models (GA, Frequency, Recent, Hot)")
    print("  2. Each model predicts 14 numbers independently")
    print("  3. Find CONSENSUS numbers (appear in 60%+ of models)")
    print("  4. Brute force the GAP (remaining numbers to reach 14)")
    print("  5. This minimizes search space while leveraging ML strengths")
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
    print("=" * 80)

    # Train ensemble models
    models = train_ensemble_models(all_series_data, training_series_ids)

    print("=" * 80)
    print("ENSEMBLE SUMMARY")
    print("=" * 80)
    print(f"\nTrained {len(models)} models:")
    for model_name, prediction, score in models:
        pred_str = ' '.join(f"{n:02d}" for n in prediction)
        print(f"  {model_name:12s}: {pred_str} ({score*100/14:.2f}%)")
    print()

    # Try different consensus thresholds
    thresholds = [0.8, 0.6, 0.5]

    for threshold in thresholds:
        print("=" * 80)
        print(f"ATTEMPTING WITH {threshold*100:.0f}% CONSENSUS THRESHOLD")
        print("=" * 80)
        print()

        consensus_numbers, number_appearances = find_consensus_numbers(models, threshold)

        print(f"Number appearances across {len(models)} models:")
        for num in range(1, 26):
            count = number_appearances.get(num, 0)
            pct = 100 * count / len(models)
            bar = '█' * count
            in_consensus = "✅" if num in consensus_numbers else "  "
            print(f"  {num:2d}: {bar:6s} ({count}/{len(models)}) {pct:>5.1f}% {in_consensus}")
        print()

        print(f"Consensus numbers ({len(consensus_numbers)}): ", end="")
        if consensus_numbers:
            print(' '.join(f"{n:02d}" for n in consensus_numbers))
        else:
            print("None")
        print()

        # Calculate gap
        gap_size = 14 - len(consensus_numbers)
        gap_pool = sorted([n for n in range(1, 26) if n not in consensus_numbers])

        print(f"Gap size: {gap_size} numbers")
        print(f"Gap pool: {gap_pool}")
        print()

        if gap_size < 0 or gap_size > 14:
            print(f"⚠️  Invalid gap size, trying next threshold...")
            continue

        # Try to find jackpot
        result = find_jackpot_with_consensus(3151, all_series_data, consensus_numbers, gap_pool)

        if result['found']:
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print()

            combo_str = ' '.join(f"{n:02d}" for n in result['combination'])
            print(f"✅ JACKPOT FOUND with {threshold*100:.0f}% consensus!")
            print(f"   Consensus size: {result['consensus_size']} numbers")
            print(f"   Gap size: {result['gap_size']} numbers")
            print(f"   Total tries: {result['tries']:,}")
            print(f"   Time: {result['time_seconds']:.3f} seconds")
            print(f"   Combination: {combo_str}")
            print()

            # Compare to other methods
            print("COMPARISON TO OTHER METHODS:")
            print(f"  Pure Random:          285,368 tries")
            print(f"  ML-Weighted:        1,933,375 tries")
            print(f"  ML Pool Reduction:    359,112 tries")
            print(f"  ML Ensemble Consensus: {result['tries']:,} tries")
            print()

            if result['tries'] < 285368:
                improvement = ((285368 - result['tries']) / 285368) * 100
                print(f"✅ ML Ensemble is {improvement:.1f}% FASTER than pure random!")
                print(f"   Saved {285368 - result['tries']:,} tries!")
            else:
                slower = ((result['tries'] - 285368) / 285368) * 100
                print(f"⚠️  ML Ensemble is {slower:.1f}% slower than pure random")

            # Save results
            output = {
                'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'series_id': 3151,
                'method': 'ML Ensemble Consensus + Gap Brute Force',
                'consensus_threshold': threshold,
                'models_used': len(models),
                'result': result
            }

            with open('ml_ensemble_consensus_3151.json', 'w') as f:
                json.dump(output, f, indent=2)

            print()
            print("📁 Results saved to: ml_ensemble_consensus_3151.json")
            print("=" * 80)

            return
        else:
            print(f"❌ Not found with {threshold*100:.0f}% threshold, trying lower threshold...\n")

    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("Jackpot not found with any consensus threshold.")
    print("This indicates jackpot numbers don't have strong ML consensus.")
    print("=" * 80)


if __name__ == "__main__":
    main()
