#!/usr/bin/env python3
"""
INVERSE ML WEIGHTING EXPERIMENT

Hypothesis: If ML is biased toward pattern numbers and jackpots need gap numbers,
            maybe INVERTING the weighting (favor LOW-ML numbers) will work better?

Strategy:
- Bottom 7 numbers: 2.0x weight boost (INVERSE of normal)
- Next 10 numbers: 1.0x weight
- Top 8 numbers: 0.5x weight (REDUCE pattern bias)

This tests if gap numbers are more important than pattern numbers for jackpots.
"""

import json
import random
from collections import Counter
from datetime import datetime
from itertools import combinations

def load_all_series_data():
    """Load all series data"""
    with open('/home/user/Random/python_ml/all_series_data.json', 'r') as f:
        return json.load(f)

def calculate_ml_confidence_scores(all_series_data, training_series_ids):
    """Calculate ML confidence scores using GA + Frequency"""
    # Frequency analysis
    freq_counter = Counter()
    total_events = 0
    for sid in training_series_ids:
        for event in all_series_data[str(sid)]:
            for num in event:
                freq_counter[num] += 1
            total_events += 1

    max_freq = max(freq_counter.values()) if freq_counter else 1
    freq_scores = {num: freq_counter.get(num, 0) / max_freq for num in range(1, 26)}

    # Simple GA simulation
    population_size = 200
    generations = 10

    ga_scores = {}
    for num in range(1, 26):
        # Count how often this number appears in top performers
        appearance_count = 0
        for _ in range(population_size):
            sample_combos = random.sample(training_series_ids, min(10, len(training_series_ids)))
            for sid in sample_combos:
                for event in all_series_data[str(sid)]:
                    if num in event:
                        appearance_count += 1
        ga_scores[num] = appearance_count / (population_size * 10 * 7)

    # Combine: 60% GA + 40% Frequency
    confidence_scores = {}
    for num in range(1, 26):
        confidence_scores[num] = 0.60 * ga_scores[num] + 0.40 * freq_scores[num]

    return confidence_scores

def apply_inverse_tiered_weights(confidence_scores):
    """
    INVERSE weighting: Favor LOW-ML numbers instead of high-ML

    Bottom 7: 2.0x boost (these are gap numbers!)
    Next 10: 1.0x unchanged
    Top 8: 0.5x reduce (these are pattern numbers)
    """
    sorted_nums = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)

    weighted_scores = {}
    for rank, (num, score) in enumerate(sorted_nums, 1):
        if rank <= 8:
            # Top 8 ML numbers: REDUCE to 0.5x
            weighted_scores[num] = score * 0.5
        elif rank <= 18:
            # Next 10: unchanged
            weighted_scores[num] = score * 1.0
        else:
            # Bottom 7: BOOST to 2.0x (INVERSE!)
            weighted_scores[num] = score * 2.0

    # Normalize to probabilities
    total = sum(weighted_scores.values())
    probabilities = {num: score / total for num, score in weighted_scores.items()}

    return probabilities, weighted_scores

def generate_inverse_weighted_combination(probabilities):
    """Generate combination with inverse weighted sampling"""
    numbers = list(range(1, 26))
    probs = [probabilities[num] for num in numbers]

    selected = set()
    while len(selected) < 14:
        num = random.choices(numbers, weights=probs, k=1)[0]
        selected.add(num)

    return tuple(sorted(selected))

def inverse_weighted_search(series_id, all_data, probabilities, exclusion_set):
    """Search using INVERSE weighted sampling"""
    target_tuples = set()
    for event in all_data[str(series_id)]:
        target_tuples.add(tuple(sorted(event)))

    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    last_print = 0
    while True:
        combo = generate_inverse_weighted_combination(probabilities)

        if combo in all_exclusions:
            continue

        all_exclusions.add(combo)
        unique_tries += 1

        # Progress updates
        if unique_tries - last_print >= 50000:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = unique_tries / elapsed if elapsed > 0 else 0
            print(f"     {unique_tries:,} unique tries | Rate: {rate:8.0f}/sec | Time: {elapsed:.1f}s")
            last_print = unique_tries

        # Check if jackpot
        for event_num, target in enumerate(target_tuples, 1):
            if combo == target:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = unique_tries / elapsed if elapsed > 0 else 0
                return {
                    'series_id': series_id,
                    'method': 'Inverse ML Weighting',
                    'tries': unique_tries,
                    'time_seconds': elapsed,
                    'rate': rate,
                    'combination': list(combo),
                    'event_number': event_num,
                    'found': True
                }

def build_exclusion_set(all_series_data, before_series_id):
    """Build Mandel exclusion set from historical combinations"""
    exclusion_set = set()
    for sid_str, events in all_series_data.items():
        sid = int(sid_str)
        if sid < before_series_id:
            for event in events:
                exclusion_set.add(tuple(sorted(event)))
    return exclusion_set

def main():
    print("=" * 80)
    print("INVERSE ML WEIGHTING - Series 3128-3151")
    print("=" * 80)
    print()
    print("Strategy: INVERSE weighting - favor LOW-ML numbers")
    print("  - Top 8 numbers (pattern): 0.5x weight REDUCE")
    print("  - Next 10 numbers: 1.0x weight")
    print("  - Bottom 7 numbers (gap): 2.0x weight BOOST")
    print("  - Mandel exclusion: Remove historical combinations")
    print("=" * 80)
    print()

    all_series_data = load_all_series_data()
    test_series = list(range(3128, 3152))

    print(f"Testing on {len(test_series)} series: {test_series[0]}-{test_series[-1]}")
    print()

    results = []
    baseline_avg = 318385

    for series_id in test_series:
        print("=" * 80)
        print(f"SERIES {series_id}")
        print("=" * 80)

        # Training data: all series before target
        training_series_ids = [sid for sid in map(int, all_series_data.keys()) if sid < series_id]
        print(f"Training on {len(training_series_ids)} series")

        # Calculate ML scores
        print("Calculating ML confidence scores...")
        confidence_scores = calculate_ml_confidence_scores(all_series_data, training_series_ids)

        # Apply INVERSE tiered weights
        probabilities, weighted_scores = apply_inverse_tiered_weights(confidence_scores)

        # Show top 10 weighted numbers
        sorted_weighted = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
        sorted_confidence = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)

        print("\nTop 10 INVERSE weighted numbers:")
        for rank, (num, weight) in enumerate(sorted_weighted[:10], 1):
            # Determine tier
            conf_rank = [n for n, _ in sorted_confidence].index(num) + 1
            if conf_rank <= 8:
                tier = "Top8   "
            elif conf_rank <= 18:
                tier = "Next10 "
            else:
                tier = "Bottom7"

            bar_length = int(weight / max(w for _, w in sorted_weighted[:10]) * 16)
            bar = "█" * bar_length
            print(f"  {rank:2d}. Number {num:2d} [{tier}]: {bar} {probabilities[num]:.4f}")

        print()

        # Build exclusion set
        exclusion_set = build_exclusion_set(all_series_data, series_id)

        # Run INVERSE weighted search
        print("=" * 80)
        print(f"INVERSE ML WEIGHTING - SERIES {series_id}")
        print("=" * 80)
        print()
        print(f"Target: 7 events")
        print(f"Exclusion set: {len(exclusion_set):,} historical combinations")
        print(f"Strategy: INVERSE (favor gap, reduce pattern)")
        print()

        result = inverse_weighted_search(series_id, all_series_data, probabilities, exclusion_set)
        results.append(result)

        print()
        print(f"🎉 JACKPOT FOUND!")
        print(f"   Event: {result['event_number']}")
        print(f"   Unique tries: {result['tries']:,}")
        print(f"   Time: {result['time_seconds']:.3f} seconds")
        print(f"   Rate: {result['rate']:.0f} unique/sec")
        print(f"   Combination: {' '.join(f'{n:02d}' for n in result['combination'])}")
        print()

        improvement = (baseline_avg - result['tries']) / baseline_avg * 100
        print("=" * 80)
        print("COMPARISON")
        print("=" * 80)
        print(f"Pure Random Baseline: ~{baseline_avg:,} tries")
        print(f"Inverse ML:            {result['tries']:,} tries")
        print(f"Improvement: {improvement:+.1f}%")
        print()

    # Summary statistics
    total_tries = sum(r['tries'] for r in results)
    avg_tries = total_tries / len(results)
    avg_improvement = (baseline_avg - avg_tries) / baseline_avg * 100

    wins = sum(1 for r in results if r['tries'] < baseline_avg)
    losses = len(results) - wins
    win_rate = wins / len(results) * 100

    print()
    print("=" * 80)
    print("FINAL SUMMARY - INVERSE ML WEIGHTING")
    print("=" * 80)
    print(f"Series tested: {len(results)}")
    print(f"Average tries: {avg_tries:,.0f}")
    print(f"Baseline: {baseline_avg:,}")
    print(f"Average improvement: {avg_improvement:+.1f}%")
    print(f"Win rate: {win_rate:.1f}% ({wins} wins, {losses} losses)")
    print(f"Best: {min(r['tries'] for r in results):,} tries")
    print(f"Worst: {max(r['tries'] for r in results):,} tries")
    print()

    # Save results
    output = {
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'method': 'Inverse ML Weighting',
        'series_range': f"{test_series[0]}-{test_series[-1]}",
        'strategy': {
            'top_8_weight': 0.5,
            'middle_10_weight': 1.0,
            'bottom_7_weight': 2.0,
            'mandel_exclusion': True,
            'description': 'INVERSE - favor gap numbers, reduce pattern bias'
        },
        'summary': {
            'series_tested': len(results),
            'average_tries': avg_tries,
            'baseline': baseline_avg,
            'average_improvement_pct': avg_improvement,
            'win_rate': win_rate,
            'wins': wins,
            'losses': losses,
            'best_series': min(results, key=lambda r: r['tries'])['series_id'],
            'best_tries': min(r['tries'] for r in results),
            'worst_series': max(results, key=lambda r: r['tries'])['series_id'],
            'worst_tries': max(r['tries'] for r in results)
        },
        'results': results
    }

    output_file = '/home/user/Random/python_ml/inverse_ml_weighting_3128_3151.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()

    if avg_improvement > 0:
        print("✅ SUCCESS! Inverse ML weighting BEATS random baseline!")
        print(f"   Average improvement: {avg_improvement:+.1f}%")
    else:
        print("❌ FAILED: Inverse ML weighting is WORSE than random baseline")
        print(f"   Average deterioration: {avg_improvement:.1f}%")

if __name__ == '__main__':
    main()
