#!/usr/bin/env python3
"""
Test genetic algorithm approach for generating predictions.

Instead of weighted candidates, evolve a population of predictions over
multiple generations using:
- Fitness: Historical performance on recent series
- Selection: Keep top performers
- Crossover: Combine two parents
- Mutation: Random changes

This is a completely different approach from the ML weight-based system.
"""

import json
import sys
import random
from pathlib import Path

# Series data
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]

SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
]


def load_database_export():
    """Load data from JSON export"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found: {json_path}")
        return []

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    series_list = []
    for series in json_data.get('data', []):
        series_id = series['series_id']
        events = []
        for event in series['events']:
            numbers = event['numbers']
            events.append(numbers)

        series_list.append({
            'series_id': series_id,
            'events': events
        })

    return series_list


def calculate_fitness(candidate, historical_series, fitness_window=10):
    """
    Calculate fitness of a candidate based on how well it would have
    performed on recent historical series
    """
    fitness_series = historical_series[-fitness_window:]

    total_accuracy = 0
    count = 0

    for series in fitness_series:
        for event in series['events']:
            matches = len(set(candidate) & set(event))
            accuracy = matches / 14
            total_accuracy += accuracy
            count += 1

    return total_accuracy / count if count > 0 else 0


def create_random_candidate():
    """Create a random candidate (14 numbers from 1-25)"""
    return sorted(random.sample(range(1, 26), 14))


def crossover(parent1, parent2):
    """Combine two parents to create offspring"""
    # Take numbers from parent1 that are in parent2
    common = list(set(parent1) & set(parent2))

    # Fill remaining slots with numbers from either parent
    remaining_slots = 14 - len(common)
    if remaining_slots > 0:
        available = list((set(parent1) | set(parent2)) - set(common))
        if len(available) >= remaining_slots:
            additional = random.sample(available, remaining_slots)
        else:
            # Not enough, add random numbers
            all_numbers = set(range(1, 26))
            used = set(common) | set(available)
            missing = list(all_numbers - used)
            additional = available + random.sample(missing, remaining_slots - len(available))

        child = sorted(common + additional)
    else:
        # Too many common numbers, randomly select 14
        child = sorted(random.sample(common, 14))

    return child


def mutate(candidate, mutation_rate=0.2):
    """Randomly mutate some numbers in candidate"""
    mutated = candidate.copy()

    for i in range(len(mutated)):
        if random.random() < mutation_rate:
            # Replace this number with a random unused number
            all_numbers = set(range(1, 26))
            used = set(mutated)
            available = list(all_numbers - used)

            if available:
                mutated[i] = random.choice(available)

    return sorted(mutated)


def genetic_algorithm(historical_series, population_size=1000, generations=50,
                     elite_size=100, mutation_rate=0.1):
    """
    Run genetic algorithm to evolve best prediction

    Args:
        historical_series: Historical data to train on
        population_size: Size of population per generation
        generations: Number of generations to evolve
        elite_size: Number of top performers to keep each generation
        mutation_rate: Probability of mutation per number
    """
    print(f"  Population: {population_size}, Generations: {generations}")
    print(f"  Elite: {elite_size}, Mutation rate: {mutation_rate}")

    # Initialize population
    population = [create_random_candidate() for _ in range(population_size)]

    best_fitness = 0
    best_candidate = None

    for gen in range(generations):
        # Calculate fitness for all candidates
        fitness_scores = [(candidate, calculate_fitness(candidate, historical_series))
                         for candidate in population]

        # Sort by fitness (descending)
        fitness_scores.sort(key=lambda x: x[1], reverse=True)

        # Track best
        if fitness_scores[0][1] > best_fitness:
            best_fitness = fitness_scores[0][1]
            best_candidate = fitness_scores[0][0]

        if gen % 10 == 0 or gen == generations - 1:
            print(f"  Gen {gen:3d}: Best fitness = {best_fitness:.4f}")

        # Select elite
        elite = [candidate for candidate, _ in fitness_scores[:elite_size]]

        # Create new generation
        new_population = elite.copy()

        # Fill rest with offspring
        while len(new_population) < population_size:
            # Select two parents from elite
            parent1 = random.choice(elite)
            parent2 = random.choice(elite)

            # Crossover
            child = crossover(parent1, parent2)

            # Mutate
            child = mutate(child, mutation_rate)

            new_population.append(child)

        population = new_population

    return best_candidate, best_fitness


def test_genetic_algorithm(seed=999):
    """Test genetic algorithm on validation series"""
    print(f"\n{'='*80}")
    print(f"Testing Genetic Algorithm")
    print(f"{'='*80}\n")

    random.seed(seed)

    # Load data
    all_series_data = load_database_export()
    all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
    all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

    # Use 50 recent series for training (best config from previous tests)
    validation_window = 8
    latest_series = 3145
    validation_start = latest_series - validation_window + 1  # 3138
    training_start = validation_start - 50  # Use 50 recent

    print(f"Training: Series {training_start}-{validation_start-1} (50 series)")
    print(f"Validation: Series {validation_start}-{latest_series} ({validation_window} series)")
    print()

    training_data = [s for s in all_series_data
                     if training_start <= s['series_id'] < validation_start]

    validation_series = [s for s in all_series_data
                        if validation_start <= s['series_id'] <= latest_series]

    results = []

    for series in validation_series:
        series_id = series['series_id']
        actual_events = series['events']

        print(f"Series {series_id}: Evolving prediction...")

        # Run genetic algorithm
        prediction, fitness = genetic_algorithm(
            training_data,
            population_size=1000,
            generations=50,
            elite_size=100,
            mutation_rate=0.1
        )

        print(f"  Best fitness on training: {fitness:.4f}")

        # Calculate accuracy on actual results
        event_accuracies = []
        for actual in actual_events:
            matches = len(set(prediction) & set(actual))
            accuracy = matches / 14
            event_accuracies.append(accuracy)

        best_accuracy = max(event_accuracies)
        avg_accuracy = sum(event_accuracies) / len(event_accuracies)

        print(f"  Validation: Best={best_accuracy*100:.1f}%, Avg={avg_accuracy*100:.1f}%")
        print()

        results.append({
            'series_id': series_id,
            'best_accuracy': best_accuracy,
            'avg_accuracy': avg_accuracy,
            'training_fitness': fitness,
            'prediction': prediction
        })

        # Add this series to training data for next iteration
        training_data.append(series)

    # Calculate overall metrics
    overall_best_avg = sum(r['best_accuracy'] for r in results) / len(results)
    overall_actual_avg = sum(r['avg_accuracy'] for r in results) / len(results)

    print(f"\n{'='*80}")
    print(f"GENETIC ALGORITHM RESULTS")
    print(f"{'='*80}\n")
    print(f"Best Match Average: {overall_best_avg*100:.1f}% (misleading)")
    print(f"ACTUAL Average: {overall_actual_avg*100:.1f}% ← REAL METRIC")
    print()

    return {
        'actual_avg': overall_actual_avg,
        'best_match_avg': overall_best_avg,
        'results': results
    }


def main():
    """Test genetic algorithm approach"""
    print("="*80)
    print("GENETIC ALGORITHM TEST")
    print("="*80)
    print()
    print("Completely different approach: Evolve predictions using GA")
    print("Baseline: 57.1% actual average (50 recent series)")
    print()
    print("CRITICAL: Using ACTUAL average (all 7 events), not 'best match'")
    print("="*80)

    result = test_genetic_algorithm()

    print("="*80)
    print("CONCLUSION:")
    print("="*80)

    baseline_actual = 0.571
    vs_baseline = result['actual_avg'] - baseline_actual

    print(f"Genetic Algorithm: {result['actual_avg']*100:.1f}%")
    print(f"Baseline (50 recent): {baseline_actual*100:.1f}%")
    print(f"Difference: {vs_baseline*100:+.1f}%")
    print()

    if vs_baseline > 0.01:
        print("✅ IMPROVEMENT: Genetic algorithm beats baseline!")
        print(f"   Improvement: +{vs_baseline*100:.1f}%")
    elif vs_baseline > -0.01:
        print("➖ NO DIFFERENCE: Same as baseline")
    else:
        print("❌ WORSE: Genetic algorithm underperforms baseline")
        print(f"   Decline: {vs_baseline*100:.1f}%")

    # Save results
    output_file = "test_genetic_algorithm_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'baseline': baseline_actual,
            'genetic_algorithm': result,
            'vs_baseline': vs_baseline
        }, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
