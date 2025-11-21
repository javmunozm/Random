#!/usr/bin/env python3
"""
HYBRID ML + RANDOM EXPERIMENT

Hypothesis: Since ML predicts 10/14 numbers well (71% accuracy) but fails on gap numbers,
            use ML ONLY for the 10 pattern numbers, then PURE RANDOM for the 4 gap numbers.

Strategy:
1. Use ML to select top 10 numbers (pattern numbers ML is good at)
2. Use PURE RANDOM to select 4 more from remaining 15 numbers (gap)
3. This respects ML's strength (pattern) while admitting its weakness (gap)

This is philosophically different: we're NOT biasing all 14 selections,
we're using ML for what it's good at, random for what it can't predict.
"""

import json
import random
from collections import Counter
from datetime import datetime

def load_all_series_data():
    """Load all series data"""
    with open('/home/user/Random/python_ml/all_series_data.json', 'r') as f:
        return json.load(f)

def calculate_ml_confidence_scores(all_series_data, training_series_ids):
    """Calculate ML confidence scores using GA + Frequency"""
    freq_counter = Counter()
    for sid in training_series_ids:
        for event in all_series_data[str(sid)]:
            for num in event:
                freq_counter[num] += 1

    max_freq = max(freq_counter.values()) if freq_counter else 1
    freq_scores = {num: freq_counter.get(num, 0) / max_freq for num in range(1, 26)}

    # GA simulation
    ga_scores = {}
    for num in range(1, 26):
        appearance_count = 0
        for _ in range(200):
            sample_combos = random.sample(training_series_ids, min(10, len(training_series_ids)))
            for sid in sample_combos:
                for event in all_series_data[str(sid)]:
                    if num in event:
                        appearance_count += 1
        ga_scores[num] = appearance_count / (200 * 10 * 7)

    # Combine
    confidence_scores = {}
    for num in range(1, 26):
        confidence_scores[num] = 0.60 * ga_scores[num] + 0.40 * freq_scores[num]

    return confidence_scores

def get_top_n_ml_numbers(confidence_scores, n):
    """Get top N numbers by ML confidence"""
    sorted_nums = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)
    return [num for num, _ in sorted_nums[:n]]

def generate_hybrid_combination(top_10_ml, all_numbers=list(range(1, 26))):
    """
    Generate combination: 10 from ML top picks + 4 random from remaining

    Note: We select from top 10 ML numbers WITH replacement for each slot (10 slots),
          then add 4 random from remaining 15 numbers.
    """
    # Select 10 numbers from top ML picks (with some randomness)
    ml_selected = set()
    while len(ml_selected) < 10:
        # Pick from top 10 with small randomness
        num = random.choice(top_10_ml)
        ml_selected.add(num)

    # Remaining numbers for random selection
    remaining = [n for n in all_numbers if n not in ml_selected]

    # Select 4 random from remaining
    random_selected = random.sample(remaining, 4)

    # Combine
    combo = sorted(list(ml_selected) + random_selected)
    return tuple(combo)

def hybrid_ml_random_search(series_id, all_data, top_10_ml, exclusion_set):
    """Search using HYBRID: ML for 10, random for 4"""
    target_tuples = set()
    for event in all_data[str(series_id)]:
        target_tuples.add(tuple(sorted(event)))

    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    last_print = 0
    while True:
        combo = generate_hybrid_combination(top_10_ml)

        if combo in all_exclusions:
            continue

        all_exclusions.add(combo)
        unique_tries += 1

        if unique_tries - last_print >= 50000:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = unique_tries / elapsed if elapsed > 0 else 0
            print(f"     {unique_tries:,} unique tries | Rate: {rate:8.0f}/sec | Time: {elapsed:.1f}s")
            last_print = unique_tries

        for event_num, target in enumerate(target_tuples, 1):
            if combo == target:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = unique_tries / elapsed if elapsed > 0 else 0
                return {
                    'series_id': series_id,
                    'method': 'Hybrid ML + Random',
                    'tries': unique_tries,
                    'time_seconds': elapsed,
                    'rate': rate,
                    'combination': list(combo),
                    'event_number': event_num,
                    'found': True
                }

def build_exclusion_set(all_series_data, before_series_id):
    """Build Mandel exclusion set"""
    exclusion_set = set()
    for sid_str, events in all_series_data.items():
        sid = int(sid_str)
        if sid < before_series_id:
            for event in events:
                exclusion_set.add(tuple(sorted(event)))
    return exclusion_set

def main():
    print("=" * 80)
    print("HYBRID ML + RANDOM - Series 3128-3151")
    print("=" * 80)
    print()
    print("Strategy: Use ML where it works, random where it doesn't")
    print("  - Step 1: ML selects 10 numbers (pattern numbers)")
    print("  - Step 2: Random selects 4 numbers from remaining 15 (gap)")
    print("  - Philosophy: Respect ML's strength (pattern) and weakness (gap)")
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

        training_series_ids = [sid for sid in map(int, all_series_data.keys()) if sid < series_id]
        print(f"Training on {len(training_series_ids)} series")

        print("Calculating ML confidence scores...")
        confidence_scores = calculate_ml_confidence_scores(all_series_data, training_series_ids)

        # Get top 10 ML numbers
        top_10_ml = get_top_n_ml_numbers(confidence_scores, 10)

        print(f"\nTop 10 ML numbers (for pattern): {' '.join(f'{n:02d}' for n in top_10_ml)}")
        print(f"Remaining 15 numbers (for random gap): {' '.join(f'{n:02d}' for n in range(1, 26) if n not in top_10_ml)}")
        print()

        exclusion_set = build_exclusion_set(all_series_data, series_id)

        print("=" * 80)
        print(f"HYBRID ML + RANDOM - SERIES {series_id}")
        print("=" * 80)
        print()
        print(f"Target: 7 events")
        print(f"Exclusion set: {len(exclusion_set):,} historical combinations")
        print(f"Strategy: 10 from ML top + 4 random from remaining")
        print()

        result = hybrid_ml_random_search(series_id, all_series_data, top_10_ml, exclusion_set)
        results.append(result)

        print()
        print(f"🎉 JACKPOT FOUND!")
        print(f"   Event: {result['event_number']}")
        print(f"   Unique tries: {result['tries']:,}")
        print(f"   Time: {result['time_seconds']:.3f} seconds")
        print(f"   Rate: {result['rate']:.0f} unique/sec")
        print(f"   Combination: {' '.join(f'{n:02d}' for n in result['combination'])}")

        # Check overlap with ML top 10
        combo_set = set(result['combination'])
        ml_overlap = len(combo_set.intersection(set(top_10_ml)))
        print(f"   ML overlap: {ml_overlap}/10 from ML top picks, {14-ml_overlap}/4 from random")
        print()

        improvement = (baseline_avg - result['tries']) / baseline_avg * 100
        print("=" * 80)
        print("COMPARISON")
        print("=" * 80)
        print(f"Pure Random Baseline: ~{baseline_avg:,} tries")
        print(f"Hybrid ML+Random:      {result['tries']:,} tries")
        print(f"Improvement: {improvement:+.1f}%")
        print()

    # Summary
    total_tries = sum(r['tries'] for r in results)
    avg_tries = total_tries / len(results)
    avg_improvement = (baseline_avg - avg_tries) / baseline_avg * 100

    wins = sum(1 for r in results if r['tries'] < baseline_avg)
    losses = len(results) - wins
    win_rate = wins / len(results) * 100

    print()
    print("=" * 80)
    print("FINAL SUMMARY - HYBRID ML + RANDOM")
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
        'method': 'Hybrid ML + Random',
        'series_range': f"{test_series[0]}-{test_series[-1]}",
        'strategy': {
            'ml_selection': 10,
            'random_selection': 4,
            'mandel_exclusion': True,
            'description': 'ML for pattern numbers (10), pure random for gap (4)'
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

    output_file = '/home/user/Random/python_ml/hybrid_ml_random_3128_3151.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()

    if avg_improvement > 0:
        print("✅ SUCCESS! Hybrid ML+Random BEATS random baseline!")
        print(f"   Average improvement: {avg_improvement:+.1f}%")
    else:
        print("❌ FAILED: Hybrid ML+Random is WORSE than random baseline")
        print(f"   Average deterioration: {avg_improvement:.1f}%")

if __name__ == '__main__':
    main()
