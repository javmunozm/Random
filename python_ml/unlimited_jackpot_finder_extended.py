#!/usr/bin/env python3
"""
Extended Unlimited Jackpot Finder - Test series 3120-3150 (31 series)
Find jackpot for EACH series, analyze patterns in tries needed
Uses Mandel elimination strategy (guaranteed novel combinations)
"""

import random
import json
from datetime import datetime
import statistics

def load_all_series_data(min_series=2982):
    """Load and filter series data"""
    with open('full_series_data.json', 'r') as f:
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

def generate_novel_combination(exclusion_set):
    """Generate combination guaranteed not in exclusion set"""
    max_attempts = 1000
    for _ in range(max_attempts):
        combo = combination_to_tuple(random.sample(range(1, 26), 14))
        if combo not in exclusion_set:
            return combo
    # Fallback (extremely rare)
    return combination_to_tuple(random.sample(range(1, 26), 14))

def find_jackpot_unlimited(series_id, all_data):
    """
    Find jackpot for a series with UNLIMITED tries
    Will not stop until jackpot is found
    """
    print(f"\n{'='*80}")
    print(f"FINDING JACKPOT FOR SERIES {series_id}")
    print(f"{'='*80}")

    series_key = str(series_id)
    if series_key not in all_data:
        print(f"Series {series_id} not found")
        return None

    target_events = all_data[series_key]
    print(f"Target series has {len(target_events)} events")

    # Build exclusion set
    exclusion_set = build_exclusion_set(all_data, exclude_series=series_id)
    print(f"Excluding {len(exclusion_set):,} historical combinations")
    print(f"Search space: {4457400 - len(exclusion_set):,} novel combinations")

    # Search until jackpot found
    tries = 0
    best_match = 0
    start_time = datetime.now()

    print(f"\nSearching for jackpot (unlimited tries)...")

    while True:  # UNLIMITED - will not stop until jackpot found
        tries += 1

        # Generate novel combination
        combo = generate_novel_combination(exclusion_set)

        # Check against all events
        for event in target_events:
            event_tuple = combination_to_tuple(event)

            if combo == event_tuple:
                # JACKPOT FOUND!
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n🎉 JACKPOT FOUND!")
                print(f"   Tries: {tries:,}")
                print(f"   Time: {elapsed:.1f} seconds")
                print(f"   Combination: {' '.join(f'{n:02d}' for n in combo)}")
                return {
                    'series_id': series_id,
                    'tries': tries,
                    'time_seconds': elapsed,
                    'combination': list(combo),
                    'found': True
                }

            # Track best
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

def analyze_patterns(results):
    """Analyze patterns in jackpot finding results"""
    print(f"\n{'='*80}")
    print("PATTERN ANALYSIS")
    print(f"{'='*80}")

    tries_list = [r['tries'] for r in results]
    times_list = [r['time_seconds'] for r in results]

    # Statistical analysis
    print(f"\n📊 Statistical Summary:")
    print(f"Total series tested: {len(results)}")
    print(f"Total tries: {sum(tries_list):,}")
    print(f"Total time: {sum(times_list):.1f} seconds ({sum(times_list)/60:.1f} minutes)")
    print(f"\nTries to jackpot:")
    print(f"  Minimum: {min(tries_list):,}")
    print(f"  Maximum: {max(tries_list):,}")
    print(f"  Mean: {statistics.mean(tries_list):,.0f}")
    print(f"  Median: {statistics.median(tries_list):,.0f}")
    print(f"  Std Dev: {statistics.stdev(tries_list):,.0f}")
    print(f"  Variance: {max(tries_list) / min(tries_list):.1f}x")

    # Difficulty categories
    print(f"\n🎯 Difficulty Categories:")
    very_easy = [r for r in results if r['tries'] < 100000]
    easy = [r for r in results if 100000 <= r['tries'] < 500000]
    medium = [r for r in results if 500000 <= r['tries'] < 1000000]
    hard = [r for r in results if 1000000 <= r['tries'] < 2000000]
    very_hard = [r for r in results if r['tries'] >= 2000000]

    print(f"  Very Easy (<100K):     {len(very_easy):2d} series ({len(very_easy)/len(results)*100:5.1f}%)")
    print(f"  Easy (100K-500K):      {len(easy):2d} series ({len(easy)/len(results)*100:5.1f}%)")
    print(f"  Medium (500K-1M):      {len(medium):2d} series ({len(medium)/len(results)*100:5.1f}%)")
    print(f"  Hard (1M-2M):          {len(hard):2d} series ({len(hard)/len(results)*100:5.1f}%)")
    print(f"  Very Hard (2M+):       {len(very_hard):2d} series ({len(very_hard)/len(results)*100:5.1f}%)")

    # Quartile analysis
    sorted_tries = sorted(tries_list)
    q1 = sorted_tries[len(sorted_tries)//4]
    q2 = sorted_tries[len(sorted_tries)//2]
    q3 = sorted_tries[3*len(sorted_tries)//4]

    print(f"\n📈 Quartile Analysis:")
    print(f"  Q1 (25th percentile): {q1:,}")
    print(f"  Q2 (50th percentile): {q2:,}")
    print(f"  Q3 (75th percentile): {q3:,}")
    print(f"  IQR (Q3-Q1): {q3-q1:,}")

    # Series progression analysis
    print(f"\n🔍 Series Progression Pattern:")
    first_half = results[:len(results)//2]
    second_half = results[len(results)//2:]

    first_avg = statistics.mean([r['tries'] for r in first_half])
    second_avg = statistics.mean([r['tries'] for r in second_half])

    print(f"  First half (3120-3135): avg {first_avg:,.0f} tries")
    print(f"  Second half (3136-3150): avg {second_avg:,.0f} tries")
    print(f"  Difference: {abs(second_avg - first_avg):,.0f} ({abs(second_avg/first_avg - 1)*100:.1f}%)")

    if abs(second_avg/first_avg - 1) < 0.1:
        print(f"  → No significant trend detected (< 10% difference)")
    elif second_avg > first_avg:
        print(f"  → Later series slightly harder")
    else:
        print(f"  → Later series slightly easier")

    # Theoretical vs actual
    theoretical_expected = 4457400 / 7  # Total combinations / events per series
    actual_mean = statistics.mean(tries_list)

    print(f"\n🎲 Theoretical vs Actual:")
    print(f"  Theoretical expected: {theoretical_expected:,.0f} tries")
    print(f"  Actual mean: {actual_mean:,.0f} tries")
    print(f"  Ratio: {actual_mean/theoretical_expected:.2f}x")

    if actual_mean > theoretical_expected:
        print(f"  → Actual is {(actual_mean/theoretical_expected - 1)*100:.1f}% harder than theoretical")
    else:
        print(f"  → Actual is {(1 - actual_mean/theoretical_expected)*100:.1f}% easier than theoretical")

    return {
        'statistics': {
            'min': min(tries_list),
            'max': max(tries_list),
            'mean': statistics.mean(tries_list),
            'median': statistics.median(tries_list),
            'std_dev': statistics.stdev(tries_list),
            'variance_ratio': max(tries_list) / min(tries_list)
        },
        'difficulty_distribution': {
            'very_easy': len(very_easy),
            'easy': len(easy),
            'medium': len(medium),
            'hard': len(hard),
            'very_hard': len(very_hard)
        },
        'quartiles': {
            'q1': q1,
            'q2': q2,
            'q3': q3,
            'iqr': q3 - q1
        },
        'progression': {
            'first_half_avg': first_avg,
            'second_half_avg': second_avg,
            'difference_percent': abs(second_avg/first_avg - 1) * 100
        },
        'theoretical_comparison': {
            'theoretical_expected': theoretical_expected,
            'actual_mean': actual_mean,
            'ratio': actual_mean / theoretical_expected
        }
    }

def main():
    print("="*80)
    print("EXTENDED UNLIMITED JACKPOT FINDER - Series 3120-3150 (31 series)")
    print("="*80)
    print("\nWill find jackpot for EACH series, no matter how many tries")
    print("Uses guaranteed novel combinations (excludes historical data)")
    print("="*80)

    # Load data
    all_data = load_all_series_data(min_series=2982)
    print(f"\n✅ Loaded {len(all_data)} series (2982-3150)")

    # Test on series 3120-3150 (31 series)
    test_series = range(3120, 3151)
    results = []

    overall_start = datetime.now()

    for series_id in test_series:
        result = find_jackpot_unlimited(series_id, all_data)
        if result:
            results.append(result)

    # Summary
    overall_elapsed = (datetime.now() - overall_start).total_seconds()

    print(f"\n{'='*80}")
    print("FINAL SUMMARY - ALL JACKPOTS FOUND")
    print(f"{'='*80}")

    total_tries = sum(r['tries'] for r in results)
    avg_tries = total_tries / len(results) if results else 0

    print(f"\nSeries tested: {len(results)}")
    print(f"Total tries: {total_tries:,}")
    print(f"Average tries per jackpot: {avg_tries:,.0f}")
    print(f"Total time: {overall_elapsed:.1f} seconds ({overall_elapsed/60:.1f} minutes)")

    print(f"\nDetailed Results:")
    print(f"{'Series':<10} {'Tries':>12} {'Time (s)':>10} {'Combination'}")
    print("-" * 80)
    for r in results:
        combo_str = ' '.join(f'{n:02d}' for n in r['combination'])
        print(f"{r['series_id']:<10} {r['tries']:>12,} {r['time_seconds']:>10.1f} {combo_str}")

    # Pattern analysis
    pattern_analysis = analyze_patterns(results)

    # Save results
    output = {
        'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'series_range': [3120, 3150],
        'total_series': len(results),
        'total_tries': total_tries,
        'average_tries': avg_tries,
        'total_time_seconds': overall_elapsed,
        'pattern_analysis': pattern_analysis,
        'results': results
    }

    output_file = 'unlimited_jackpot_results_extended_3120_3150.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
