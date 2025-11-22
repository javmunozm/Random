#!/usr/bin/env python3
"""
Predict expected tries to find jackpot for Series 3152
Based on historical performance and theoretical calculations
"""

import json
from math import comb

def predict_tries_for_3152():
    """Calculate expected tries for Series 3152"""

    print("="*80)
    print("THEORETICAL TRIES TO JACKPOT - SERIES 3152")
    print("="*80)

    # Series 3152 prediction parameters
    reduced_pool = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25]
    pool_size = len(reduced_pool)
    excluded = [5, 12, 17, 18]

    print(f"\nReduced pool: {pool_size} numbers")
    print(f"Excluded: {excluded}")

    # Total combinations
    total_combos = comb(pool_size, 14)
    print(f"Total combinations: {total_combos:,}")

    # Theoretical expectations
    print(f"\n{'='*80}")
    print("THEORETICAL CALCULATIONS")
    print(f"{'='*80}\n")

    # If jackpot is IN the reduced pool:
    # - There are 7 jackpot combinations total
    # - We need to find 1 of them
    # - Average tries = total_combos / 7 (if evenly distributed)
    theoretical_avg_if_in_pool = total_combos / 7
    theoretical_median = total_combos / 2  # Statistical median for random search

    print(f"If jackpot IS in reduced pool:")
    print(f"  Best case: 1 try (extremely lucky)")
    print(f"  Average case: {theoretical_avg_if_in_pool:,.0f} tries (1 of 7 events)")
    print(f"  Median case: {theoretical_median:,.0f} tries (50% probability)")
    print(f"  Worst case: {total_combos:,} tries (last combination)")

    # Historical performance
    print(f"\n{'='*80}")
    print("HISTORICAL PERFORMANCE (Series 3128-3151)")
    print(f"{'='*80}\n")

    # From the comprehensive results
    historical_tries = [
        21582, 26991, 2251, 27590, 42003, 51675, 79558, 67001,
        25141, 378918, 37936, 94933, 1065, 5890, 788, 396,
        2259, 3976, 14441, 43761, 76199, 5931
    ]  # Successful Top-8 + Gaps results (22 out of 24)

    avg_historical = sum(historical_tries) / len(historical_tries)
    median_historical = sorted(historical_tries)[len(historical_tries) // 2]
    min_historical = min(historical_tries)
    max_historical = max(historical_tries)

    print(f"Average tries (22 successful series): {avg_historical:,.0f}")
    print(f"Median tries: {median_historical:,.0f}")
    print(f"Best performance: {min_historical:,} tries (Series 3145)")
    print(f"Worst performance: {max_historical:,} tries (Series 3138)")

    # Distribution analysis
    under_10k = sum(1 for t in historical_tries if t < 10000)
    under_50k = sum(1 for t in historical_tries if t < 50000)
    under_100k = sum(1 for t in historical_tries if t < 100000)
    over_100k = sum(1 for t in historical_tries if t >= 100000)

    print(f"\nDistribution:")
    print(f"  < 10,000 tries: {under_10k}/22 ({under_10k/22*100:.1f}%)")
    print(f"  < 50,000 tries: {under_50k}/22 ({under_50k/22*100:.1f}%)")
    print(f"  < 100,000 tries: {under_100k}/22 ({under_100k/22*100:.1f}%)")
    print(f"  ≥ 100,000 tries: {over_100k}/22 ({over_100k/22*100:.1f}%)")

    # Prediction for 3152
    print(f"\n{'='*80}")
    print("PREDICTION FOR SERIES 3152")
    print(f"{'='*80}\n")

    # Statistical prediction based on historical performance
    # Most likely scenario: within 1 standard deviation of mean
    import statistics
    std_dev = statistics.stdev(historical_tries)

    print(f"Based on historical data (Top-8 + Gaps Exhaustive):")
    print(f"  Expected average: {avg_historical:,.0f} tries")
    print(f"  Standard deviation: {std_dev:,.0f}")
    print(f"  68% confidence range: {avg_historical - std_dev:,.0f} - {avg_historical + std_dev:,.0f} tries")
    print(f"  Most likely (median): {median_historical:,.0f} tries")

    # Probability ranges
    print(f"\nProbability estimates:")
    print(f"  10% chance: < {sorted(historical_tries)[2]:,} tries (very lucky)")
    print(f"  50% chance: < {median_historical:,} tries (median)")
    print(f"  90% chance: < {sorted(historical_tries)[-3]:,} tries (unlucky)")

    # Success rate consideration
    print(f"\n{'='*80}")
    print("SUCCESS PROBABILITY")
    print(f"{'='*80}\n")

    success_rate = 22 / 24  # Historical success rate
    print(f"Historical success rate: {success_rate*100:.1f}%")
    print(f"Failure rate: {(1-success_rate)*100:.1f}%")
    print(f"\nFor Series 3152:")
    print(f"  {success_rate*100:.1f}% chance: Jackpot found in reduced pool")
    print(f"  {(1-success_rate)*100:.1f}% chance: Need fallback to full space (1M+ tries)")

    # Final recommendation
    print(f"\n{'='*80}")
    print("FINAL PREDICTION")
    print(f"{'='*80}\n")

    print(f"🎯 EXPECTED TRIES FOR SERIES 3152:")
    print(f"\n   Best case (10%):     {sorted(historical_tries)[2]:,} tries")
    print(f"   Most likely (50%):   {median_historical:,} tries")
    print(f"   Expected average:    {avg_historical:,.0f} tries")
    print(f"   Pessimistic (90%):   {sorted(historical_tries)[-3]:,} tries")
    print(f"\n   Time estimate: < 1 second (for average case)")
    print(f"   Success probability: 91.7%")

    # Save results
    output = {
        'series_id': 3152,
        'reduced_pool_size': pool_size,
        'total_combinations': total_combos,
        'theoretical': {
            'best': 1,
            'average_if_in_pool': int(theoretical_avg_if_in_pool),
            'median': int(theoretical_median),
            'worst': total_combos
        },
        'historical_performance': {
            'average': int(avg_historical),
            'median': int(median_historical),
            'min': min_historical,
            'max': max_historical,
            'std_dev': int(std_dev)
        },
        'prediction_3152': {
            'expected_tries': int(avg_historical),
            'median_tries': int(median_historical),
            'confidence_range_68pct': [int(avg_historical - std_dev), int(avg_historical + std_dev)],
            'probability_10pct': sorted(historical_tries)[2],
            'probability_50pct': median_historical,
            'probability_90pct': sorted(historical_tries)[-3],
            'success_probability': success_rate
        }
    }

    with open('prediction_3152_tries.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📁 Saved to: prediction_3152_tries.json")
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    predict_tries_for_3152()
