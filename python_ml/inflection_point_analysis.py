#!/usr/bin/env python3
"""
Inflection Point Analysis - Predict Series 3153
Analyzes jackpot trends across series to find patterns and predict next series
"""

import json
import math
from collections import defaultdict

def analyze_inflection_point():
    """Analyze jackpot data to find trends and predict Series 3153"""

    # Load existing jackpot results
    with open('jackpot_finder_results.json', 'r') as f:
        data = json.load(f)

    # Extract found jackpots and group by series
    series_stats = defaultdict(lambda: {'found': 0, 'tries_list': [], 'events': []})

    for jackpot in data['jackpots']:
        series = jackpot['series']
        tries = jackpot['tries']
        event = jackpot['event']

        if tries is not None:
            series_stats[series]['found'] += 1
            series_stats[series]['tries_list'].append(tries)
            series_stats[series]['events'].append(event)

    # Add Series 3152 (0 found)
    series_stats[3152] = {'found': 0, 'tries_list': [], 'events': []}

    # Calculate statistics per series
    series_analysis = []
    for series in sorted(series_stats.keys()):
        stats = series_stats[series]

        if stats['tries_list']:
            avg_tries = sum(stats['tries_list']) / len(stats['tries_list'])
            min_tries = min(stats['tries_list'])
            max_tries = max(stats['tries_list'])
            median_tries = sorted(stats['tries_list'])[len(stats['tries_list'])//2]
        else:
            avg_tries = None
            min_tries = None
            max_tries = None
            median_tries = None

        series_analysis.append({
            'series': series,
            'found': stats['found'],
            'total_events': 7,
            'success_rate': stats['found'] / 7 * 100,
            'avg_tries': avg_tries,
            'min_tries': min_tries,
            'max_tries': max_tries,
            'median_tries': median_tries,
            'events_found': stats['events']
        })

    print("=" * 80)
    print("INFLECTION POINT ANALYSIS")
    print("Analyzing jackpot trends across Series 3135-3152")
    print("=" * 80)
    print()

    # Print series-by-series analysis
    print("SERIES-BY-SERIES ANALYSIS:")
    print()
    print(f"{'Series':<8} {'Found':<8} {'Success%':<10} {'Avg Tries':<15} {'Min':<12} {'Max':<12}")
    print("-" * 80)

    for sa in series_analysis:
        if sa['avg_tries']:
            print(f"{sa['series']:<8} {sa['found']}/7    {sa['success_rate']:>6.1f}%    "
                  f"{sa['avg_tries']:>13,.0f}  {sa['min_tries']:>10,}  {sa['max_tries']:>10,}")
        else:
            print(f"{sa['series']:<8} {sa['found']}/7    {sa['success_rate']:>6.1f}%    "
                  f"{'N/A':>13}  {'N/A':>10}  {'N/A':>10}")

    print()
    print("=" * 80)

    # Trend analysis
    print("TREND ANALYSIS:")
    print()

    # Calculate moving averages
    valid_series = [sa for sa in series_analysis if sa['avg_tries'] is not None]

    if len(valid_series) >= 3:
        # Early period (first third)
        early_count = len(valid_series) // 3
        early_series = valid_series[:early_count]
        early_avg = sum(sa['avg_tries'] for sa in early_series) / len(early_series)

        # Middle period
        mid_series = valid_series[early_count:2*early_count]
        mid_avg = sum(sa['avg_tries'] for sa in mid_series) / len(mid_series) if mid_series else early_avg

        # Late period (last third)
        late_series = valid_series[2*early_count:]
        late_avg = sum(sa['avg_tries'] for sa in late_series) / len(late_series)

        print(f"Early period (Series {early_series[0]['series']}-{early_series[-1]['series']}): {early_avg:,.0f} avg tries")
        print(f"Middle period: {mid_avg:,.0f} avg tries")
        print(f"Late period (Series {late_series[0]['series']}-{late_series[-1]['series']}): {late_avg:,.0f} avg tries")
        print()

        # Trend direction
        if late_avg > early_avg * 1.1:
            trend = "INCREASING (getting harder)"
            trend_pct = ((late_avg - early_avg) / early_avg) * 100
        elif late_avg < early_avg * 0.9:
            trend = "DECREASING (getting easier)"
            trend_pct = ((early_avg - late_avg) / early_avg) * 100
        else:
            trend = "STABLE (no significant change)"
            trend_pct = abs((late_avg - early_avg) / early_avg) * 100

        print(f"Overall Trend: {trend}")
        print(f"Change: {trend_pct:.1f}%")
        print()

    # Calculate overall statistics
    all_tries = [sa['avg_tries'] for sa in series_analysis if sa['avg_tries'] is not None]
    if all_tries:
        overall_avg = sum(all_tries) / len(all_tries)
        overall_median = sorted(all_tries)[len(all_tries)//2]
        overall_min = min(all_tries)
        overall_max = max(all_tries)

        print("OVERALL STATISTICS (All Series):")
        print(f"  Average of averages: {overall_avg:,.0f} tries")
        print(f"  Median of averages: {overall_median:,.0f} tries")
        print(f"  Best series avg: {overall_min:,.0f} tries (Series {[sa['series'] for sa in series_analysis if sa['avg_tries'] == overall_min][0]})")
        print(f"  Worst series avg: {overall_max:,.0f} tries (Series {[sa['series'] for sa in series_analysis if sa['avg_tries'] == overall_max][0]})")
        print()

    # Prediction for Series 3153
    print("=" * 80)
    print("PREDICTION FOR SERIES 3153:")
    print("=" * 80)
    print()

    if valid_series:
        # Use exponential smoothing with recent data weighted more
        recent_series = valid_series[-5:]  # Last 5 series with data
        weights = [1, 1.2, 1.4, 1.6, 2.0][:len(recent_series)]

        weighted_sum = sum(sa['avg_tries'] * w for sa, w in zip(recent_series, weights))
        weight_total = sum(weights)
        predicted_avg = weighted_sum / weight_total

        print(f"Based on weighted recent trend (last {len(recent_series)} series):")
        print(f"  Predicted average tries: {predicted_avg:,.0f}")
        print()

        # Confidence intervals (using standard deviation)
        recent_tries = [sa['avg_tries'] for sa in recent_series]
        std_dev = (sum((x - predicted_avg)**2 for x in recent_tries) / len(recent_tries)) ** 0.5

        print(f"Confidence intervals:")
        print(f"  68% confidence: {predicted_avg - std_dev:,.0f} - {predicted_avg + std_dev:,.0f} tries")
        print(f"  95% confidence: {predicted_avg - 2*std_dev:,.0f} - {predicted_avg + 2*std_dev:,.0f} tries")
        print()

        # Probability predictions using exponential model
        lambda_param = 1 / predicted_avg

        print(f"Probability of finding jackpot in Series 3153:")
        print(f"  Within 100K tries: {(1 - math.exp(-lambda_param * 100000)) * 100:.1f}%")
        print(f"  Within 300K tries: {(1 - math.exp(-lambda_param * 300000)) * 100:.1f}%")
        print(f"  Within 500K tries: {(1 - math.exp(-lambda_param * 500000)) * 100:.1f}%")
        print(f"  Within 1M tries: {(1 - math.exp(-lambda_param * 1000000)) * 100:.1f}%")
        print()

        # Recommended tries for different success rates
        print(f"Recommended tries for Series 3153:")
        for prob in [50, 75, 90, 95]:
            tries_needed = -math.log(1 - prob/100) / lambda_param
            print(f"  {prob}% success rate: {tries_needed:,.0f} tries")

    print()
    print("=" * 80)

    # Save detailed analysis
    results = {
        'series_analysis': series_analysis,
        'overall_stats': {
            'avg_of_avgs': overall_avg if all_tries else None,
            'median_of_avgs': overall_median if all_tries else None,
            'min_avg': overall_min if all_tries else None,
            'max_avg': overall_max if all_tries else None
        },
        'prediction_3153': {
            'predicted_avg_tries': predicted_avg if valid_series else None,
            'confidence_68': [predicted_avg - std_dev, predicted_avg + std_dev] if valid_series else None,
            'confidence_95': [predicted_avg - 2*std_dev, predicted_avg + 2*std_dev] if valid_series else None
        }
    }

    with open('inflection_point_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("📁 Detailed analysis saved to: inflection_point_analysis_results.json")
    print()

if __name__ == '__main__':
    analyze_inflection_point()
