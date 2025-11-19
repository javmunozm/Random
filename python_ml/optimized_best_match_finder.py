#!/usr/bin/env python3
"""
OPTIMIZED BEST MATCH FINDER
Iteratively search for the absolute best match possible using multiple strategies

Unlike single-shot prediction, this system:
1. Tries multiple seeds and approaches
2. Measures tries needed to reach match thresholds
3. Finds the BEST possible combination
4. Reports statistics on optimization process
"""

import json
import random
from datetime import datetime
from collections import Counter
import statistics


def load_series_data(file_path="full_series_data.json", min_series=2982):
    """Load and filter series data"""
    with open(file_path, 'r') as f:
        all_data = json.load(f)
    return {k: v for k, v in all_data.items() if int(k) >= min_series}


def test_combination_detailed(combination, all_series_data, test_series_ids):
    """
    Test combination and return detailed match statistics

    Returns:
        {
            'average_best': Average best match across all series,
            'total_best': Sum of all best matches,
            'individual_scores': List of best matches per series,
            'percentage': Match percentage (0-100)
        }
    """
    individual_scores = []

    for series_id in test_series_ids:
        actual_events = all_series_data[str(series_id)]
        best_match = max(len(set(combination) & set(event)) for event in actual_events)
        individual_scores.append(best_match)

    total_best = sum(individual_scores)
    average_best = total_best / len(test_series_ids)
    percentage = (average_best / 14) * 100

    return {
        'average_best': average_best,
        'total_best': total_best,
        'individual_scores': individual_scores,
        'percentage': percentage
    }


def genetic_algorithm_optimized(all_series_data, training_series_ids, seed=None,
                                generations=10, pop_size=200):
    """Genetic algorithm with detailed tracking"""
    if seed is not None:
        random.seed(seed)

    # Initial population
    population = [sorted(random.sample(range(1, 26), 14)) for _ in range(pop_size)]

    best_ever = None
    best_score = 0

    for gen in range(generations):
        # Evaluate fitness
        fitness_scores = []
        for combo in population:
            result = test_combination_detailed(combo, all_series_data, training_series_ids)
            fitness_scores.append((combo, result['average_best']))

            # Track best
            if result['average_best'] > best_score:
                best_score = result['average_best']
                best_ever = combo

        fitness_scores.sort(key=lambda x: x[1], reverse=True)

        # Keep top 50%
        survivors = [combo for combo, score in fitness_scores[:pop_size//2]]

        # Breed new population
        new_population = survivors[:]
        while len(new_population) < pop_size:
            parent1, parent2 = random.sample(survivors, 2)

            # Crossover
            child = list(set(parent1[:7] + parent2[:7]))

            # Fill to 14
            available = [n for n in range(1, 26) if n not in child]
            if available:
                needed = 14 - len(child)
                child.extend(random.sample(available, min(needed, len(available))))

            # Mutation (10% chance)
            if random.random() < 0.1 and len(child) == 14:
                idx = random.randint(0, 13)
                new_num = random.randint(1, 25)
                if new_num not in child:
                    child[idx] = new_num

            if len(child) == 14:
                new_population.append(sorted(child))

        population = new_population[:pop_size]

    # Return best from entire evolution
    if best_ever:
        result = test_combination_detailed(best_ever, all_series_data, training_series_ids)
        return best_ever, result
    else:
        # Fallback: best from final population
        final_fitness = [(combo, test_combination_detailed(combo, all_series_data, training_series_ids))
                        for combo in population]
        best_combo, best_result = max(final_fitness, key=lambda x: x[1]['average_best'])
        return best_combo, best_result


def iterative_search_best_match(all_series_data, training_series_ids,
                                max_tries=1000, target_percentage=None):
    """
    Iteratively search for the best match using multiple GA runs with different seeds

    Args:
        all_series_data: All historical data
        training_series_ids: Series to train/test on
        max_tries: Maximum number of GA runs to attempt
        target_percentage: Stop if this percentage is reached (None = run all)

    Returns:
        dict with best combination, statistics, and tries needed
    """
    print(f"=" * 80)
    print(f"ITERATIVE BEST MATCH SEARCH")
    print(f"=" * 80)
    print(f"\nTarget: Find the BEST possible match")
    print(f"Method: Multiple GA runs with different seeds")
    print(f"Max tries: {max_tries}")
    if target_percentage:
        print(f"Target threshold: {target_percentage:.2f}%")
    print(f"Training series: {len(training_series_ids)} ({min(training_series_ids)}-{max(training_series_ids)})")
    print()

    best_combination = None
    best_result = None
    best_percentage = 0

    all_results = []
    percentages = []

    try_count = 0
    milestone_tries = {}  # Track tries needed to reach certain percentages

    print("Searching...\n")

    for seed in range(1, max_tries + 1):
        try_count += 1

        # Run GA with this seed
        combo, result = genetic_algorithm_optimized(
            all_series_data,
            training_series_ids,
            seed=seed,
            generations=10,
            pop_size=200
        )

        all_results.append({
            'seed': seed,
            'combination': combo,
            'percentage': result['percentage'],
            'average_best': result['average_best']
        })

        percentages.append(result['percentage'])

        # Check if new best
        if result['percentage'] > best_percentage:
            prev_best = best_percentage
            best_percentage = result['percentage']
            best_combination = combo
            best_result = result

            combo_str = ' '.join(f"{n:02d}" for n in combo)
            print(f"  🎯 Try {try_count:>4}: NEW BEST! {result['percentage']:>6.2f}% "
                  f"(+{result['percentage']-prev_best:.2f}%) | Seed {seed:>4} | {combo_str}")

            # Record milestone
            pct_int = int(result['percentage'])
            if pct_int not in milestone_tries:
                milestone_tries[pct_int] = try_count
        else:
            # Progress update every 100 tries
            if try_count % 100 == 0:
                print(f"  ... Try {try_count:>4}: {result['percentage']:>6.2f}% | "
                      f"Best so far: {best_percentage:.2f}%")

        # Check if target reached
        if target_percentage and best_percentage >= target_percentage:
            print(f"\n✅ Target {target_percentage:.2f}% reached in {try_count} tries!")
            break

    print()
    print(f"=" * 80)
    print(f"OPTIMIZATION COMPLETE")
    print(f"=" * 80)
    print()

    # Statistics
    mean_pct = statistics.mean(percentages)
    median_pct = statistics.median(percentages)
    std_pct = statistics.stdev(percentages) if len(percentages) > 1 else 0

    print(f"Total tries: {try_count}")
    print(f"Best percentage: {best_percentage:.2f}% ({best_result['average_best']:.2f}/14 numbers)")
    print(f"Mean percentage: {mean_pct:.2f}%")
    print(f"Median percentage: {median_pct:.2f}%")
    print(f"Std deviation: {std_pct:.2f}%")
    print(f"Improvement over mean: +{best_percentage - mean_pct:.2f}%")
    print()

    best_combo_str = ' '.join(f"{n:02d}" for n in best_combination)
    print(f"🏆 BEST COMBINATION FOUND:")
    print(f"   Seed: {all_results[try_count-1]['seed']}")
    print(f"   Score: {best_percentage:.2f}%")
    print(f"   Numbers: {best_combo_str}")
    print()

    # Milestone analysis
    if milestone_tries:
        print(f"Tries needed to reach milestones:")
        for pct in sorted(milestone_tries.keys()):
            tries = milestone_tries[pct]
            print(f"  {pct:>3}%: {tries:>4} tries")
        print()

    # Distribution
    excellent = len([p for p in percentages if p >= 72.0])
    very_good = len([p for p in percentages if 70.0 <= p < 72.0])
    good = len([p for p in percentages if 68.0 <= p < 70.0])
    average = len([p for p in percentages if p < 68.0])

    print(f"Performance distribution:")
    print(f"  Excellent (≥72%): {excellent:>4} ({100*excellent/try_count:>5.1f}%)")
    print(f"  Very Good (70-72%): {very_good:>4} ({100*very_good/try_count:>5.1f}%)")
    print(f"  Good (68-70%): {good:>4} ({100*good/try_count:>5.1f}%)")
    print(f"  Average (<68%): {average:>4} ({100*average/try_count:>5.1f}%)")
    print()

    return {
        'best_combination': best_combination,
        'best_result': best_result,
        'best_percentage': best_percentage,
        'total_tries': try_count,
        'mean_percentage': mean_pct,
        'median_percentage': median_pct,
        'std_deviation': std_pct,
        'milestone_tries': milestone_tries,
        'all_results': all_results,
        'distribution': {
            'excellent': excellent,
            'very_good': very_good,
            'good': good,
            'average': average
        }
    }


def main():
    print("=" * 80)
    print("OPTIMIZED BEST MATCH FINDER FOR SERIES 3151")
    print("=" * 80)
    print()
    print("This system iteratively searches for the BEST possible match")
    print("by trying multiple GA runs with different seeds.")
    print()
    print("Unlike single-shot prediction:")
    print("  - Tries multiple seeds until best match found")
    print("  - Measures tries needed to reach match thresholds")
    print("  - Reports comprehensive optimization statistics")
    print("=" * 80)
    print()

    # Load data
    all_series_data = load_series_data(min_series=2982)
    all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

    print(f"✅ Loaded {len(all_series_data)} series ({min(all_series_ids)}-{max(all_series_ids)})")

    # Use all available data for training
    training_series_ids = [sid for sid in all_series_ids if sid <= 3150]

    print(f"✅ Training on {len(training_series_ids)} series")
    print()

    # Run iterative search
    # Try up to 200 different seeds to find the best match
    result = iterative_search_best_match(
        all_series_data,
        training_series_ids,
        max_tries=200,
        target_percentage=None  # Find absolute best, no threshold
    )

    print("=" * 80)
    print("SERIES 3151 PREDICTION")
    print("=" * 80)
    print()

    combo_str = ' '.join(f"{n:02d}" for n in result['best_combination'])
    print(f"🎯 OPTIMIZED PREDICTION:")
    print(f"   {combo_str}")
    print()
    print(f"   Training score: {result['best_percentage']:.2f}%")
    print(f"   Found after: {result['total_tries']} tries")
    print(f"   Improvement over mean: +{result['best_percentage'] - result['mean_percentage']:.2f}%")
    print()

    # Save results
    output = {
        'prediction_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'target_series': 3151,
        'method': 'Iterative GA Optimization',
        'training_series_count': len(training_series_ids),
        'best_combination': result['best_combination'],
        'best_percentage': round(result['best_percentage'], 2),
        'tries_needed': result['total_tries'],
        'statistics': {
            'mean_percentage': round(result['mean_percentage'], 2),
            'median_percentage': round(result['median_percentage'], 2),
            'std_deviation': round(result['std_deviation'], 2),
            'improvement_over_mean': round(result['best_percentage'] - result['mean_percentage'], 2)
        },
        'milestone_tries': result['milestone_tries'],
        'distribution': result['distribution']
    }

    with open('optimized_best_match_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 80)
    print(f"📁 Results saved to: optimized_best_match_3151.json")
    print("✅ OPTIMIZATION COMPLETE!")
    print("=" * 80)
    print()

    print("Summary:")
    print(f"  Method: Iterative GA with {result['total_tries']} different seeds")
    print(f"  Best match: {result['best_percentage']:.2f}% ({result['best_result']['average_best']:.2f}/14 numbers)")
    print(f"  Predicted: {combo_str}")
    print()


if __name__ == "__main__":
    main()
