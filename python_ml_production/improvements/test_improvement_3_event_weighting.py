#!/usr/bin/env python3
"""
Improvement 3: Event-Level Importance Weighting

Tests different weighting strategies for the 7 events within each series
Budget: 600 simulations
Expected: +2-3% improvement

Current baseline: All events weighted equally (1.0x each)
Will test: Weighted by critical number count, position-based, frequency-based
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'model'))
from true_learning_model import TrueLearningModel


# Series 3144-3148 actual results
SERIES_DATA = {
    3144: [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
    ],
    3145: [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
    ],
    3147: [
        [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
        [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
        [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
        [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
        [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
        [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
        [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
    ],
    3148: [
        [1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 19, 22, 23, 25],
        [2, 3, 6, 7, 10, 12, 13, 14, 15, 16, 17, 19, 21, 23],
        [1, 2, 4, 5, 6, 8, 10, 12, 14, 15, 17, 18, 20, 22],
        [2, 3, 4, 5, 8, 10, 12, 13, 14, 15, 18, 20, 21, 25],
        [3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 19, 20, 21, 24],
        [2, 3, 4, 5, 9, 10, 12, 14, 15, 16, 17, 18, 22, 25],
        [1, 4, 6, 7, 9, 11, 12, 14, 16, 19, 20, 21, 23, 25],
    ],
}


def load_historical_data():
    """Load all historical data"""
    data_path = Path(__file__).parent.parent / 'data' / 'full_series_data_expanded.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    series_data = {int(k): v for k, v in data.items()}

    # Add recent series
    for series_id, events in SERIES_DATA.items():
        if series_id not in series_data:
            series_data[series_id] = events

    return series_data


def count_critical_numbers(events):
    """Count how many critical numbers (5+ appearances) in each event"""
    # Count number frequencies across all 7 events
    number_counts = {}
    for event in events:
        for num in event:
            number_counts[num] = number_counts.get(num, 0) + 1

    # Critical numbers: appear in 5+ events
    critical_numbers = {num for num, count in number_counts.items() if count >= 5}

    # Count critical numbers in each event
    critical_counts = []
    for event in events:
        count = sum(1 for num in event if num in critical_numbers)
        critical_counts.append(count)

    return critical_counts


class WeightedLearningModel(TrueLearningModel):
    """Extended model with event-level weighting"""

    def __init__(self, seed=999, cold_hot_boost=30.0, event_weights=None):
        super().__init__(seed=seed, cold_hot_boost=cold_hot_boost)
        self.event_weights = event_weights or [1.0] * 7  # Default: equal weights

    def learn_from_series(self, series_id, events):
        """Learn from series with event-level weighting"""
        # First, do normal learning (parent class)
        super().learn_from_series(series_id, events)

        if len(events) != 7:
            return

        # Then apply additional event-level weighting
        for event_idx, event in enumerate(events):
            weight = self.event_weights[event_idx]

            # Skip if weight is 1.0 (no additional weighting needed)
            if weight == 1.0:
                continue

            # Additional weight adjustment factor (weight - 1.0)
            weight_adjustment = (weight - 1.0) * 0.15  # Scale down to avoid over-weighting

            # Apply additional weighting to frequency
            for num in event:
                self.number_frequency_weights[num] = self.number_frequency_weights[num] * (1.0 + weight_adjustment)

            # Apply additional weighting to pair affinities
            for i, num1 in enumerate(event):
                for num2 in event[i+1:]:
                    pair = tuple(sorted([num1, num2]))
                    if pair in self.pair_affinities:
                        self.pair_affinities[pair] = self.pair_affinities[pair] * (1.0 + weight_adjustment)


def test_weighting_strategy(strategy_name, weight_generator, validation_series, historical_data, seed=999):
    """
    Test a specific event weighting strategy

    Args:
        strategy_name: Name of the strategy
        weight_generator: Function that takes events and returns [7] weights
        validation_series: Series to validate on
        historical_data: All historical data
        seed: Random seed

    Returns:
        dict with results
    """
    results = []

    for target_series in validation_series:
        # Generate weights for this target series (based on training data patterns)
        # We'll use the last series before target as a proxy for expected patterns
        proxy_series = target_series - 1
        if proxy_series in historical_data:
            event_weights = weight_generator(historical_data[proxy_series])
        else:
            event_weights = [1.0] * 7

        # Create model with specific weights
        model = WeightedLearningModel(seed=seed, cold_hot_boost=30.0, event_weights=event_weights)

        # Train on all data before target series
        for sid in sorted(historical_data.keys()):
            if sid < target_series:
                model.learn_from_series(sid, historical_data[sid])

        # Generate prediction
        prediction = model.predict_best_combination(target_series)

        # Evaluate
        actual = historical_data[target_series]
        matches = []
        for event in actual:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        results.append({
            'series_id': target_series,
            'best_match': best_match,
            'avg_match': avg_match,
            'event_weights': event_weights
        })

    # Calculate summary
    avg_best = sum(r['best_match'] for r in results) / len(results)
    peak = max(r['best_match'] for r in results)

    return {
        'strategy_name': strategy_name,
        'avg_best_match': avg_best,
        'peak_performance': peak,
        'results': results
    }


def main():
    print("\n")
    print("="*80)
    print("IMPROVEMENT 3: EVENT-LEVEL IMPORTANCE WEIGHTING")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Testing different weighting strategies for 7 events within each series")
    print("Budget: 600 simulations")
    print("Expected: +2-3% improvement")
    print()

    # Load data
    historical_data = load_historical_data()

    # Validation window: Last 10 series
    all_series = sorted(historical_data.keys())
    validation_series = all_series[-10:]  # 3139-3148

    print(f"Validation Series: {validation_series[0]}-{validation_series[-1]} ({len(validation_series)} series)")
    print()

    # Define weighting strategies
    strategies = [
        {
            'name': 'Baseline (Equal Weights)',
            'generator': lambda events: [1.0] * 7
        },
        {
            'name': 'Critical Number Count',
            'generator': lambda events: [
                1.0 + (count * 0.15) for count in count_critical_numbers(events)
            ]
        },
        {
            'name': 'Position-Based (Early events more important)',
            'generator': lambda events: [1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9]
        },
        {
            'name': 'Position-Based (Late events more important)',
            'generator': lambda events: [0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        },
        {
            'name': 'Position-Based (Middle events more important)',
            'generator': lambda events: [1.0, 1.2, 1.4, 1.5, 1.4, 1.2, 1.0]
        },
        {
            'name': 'Adaptive (High critical = high weight)',
            'generator': lambda events: [
                0.8 + (count * 0.20) for count in count_critical_numbers(events)
            ]
        },
    ]

    print(f"Testing {len(strategies)} weighting strategies:")
    for i, strategy in enumerate(strategies, 1):
        print(f"  {i}. {strategy['name']}")
    print()

    all_results = []
    baseline = None

    for i, strategy in enumerate(strategies, 1):
        print(f"[{i}/{len(strategies)}] Testing {strategy['name']}...", end=" ", flush=True)

        result = test_weighting_strategy(
            strategy['name'],
            strategy['generator'],
            validation_series,
            historical_data
        )
        all_results.append(result)

        avg = result['avg_best_match'] * 100
        peak = result['peak_performance'] * 100

        print(f"Avg {avg:5.1f}%, Peak {peak:5.1f}%")

        # Mark baseline
        if strategy['name'] == 'Baseline (Equal Weights)':
            baseline = result

    print()
    print("="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print()

    # Sort by average performance
    all_results.sort(key=lambda x: x['avg_best_match'], reverse=True)

    print("Rank   Strategy                                      Avg Best   Peak      vs Baseline")
    print("-" * 95)

    baseline_avg = baseline['avg_best_match']
    best_strategy = all_results[0]

    for i, result in enumerate(all_results, 1):
        name = result['strategy_name']
        avg = result['avg_best_match'] * 100
        peak = result['peak_performance'] * 100
        diff = (result['avg_best_match'] - baseline_avg) * 100

        marker = "🏆" if i == 1 else "  "
        status = "BASELINE" if name == 'Baseline (Equal Weights)' else (f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%")

        print(f"{marker} {i:2d}   {name:42s}   {avg:7.1f}%   {peak:6.1f}%   {status}")

    print()

    # Decision
    improvement = (best_strategy['avg_best_match'] - baseline_avg) * 100

    print("="*80)
    print("DECISION")
    print("="*80)
    print()

    if improvement >= 0.5:  # Min 0.5% improvement
        print(f"✅ PASS: Improvement found (+{improvement:.1f}%)")
        print(f"   Best strategy: {best_strategy['strategy_name']}")
        print(f"   Performance: {best_strategy['avg_best_match']*100:.1f}% avg, {best_strategy['peak_performance']*100:.1f}% peak")
        print(f"   vs Baseline: {baseline_avg*100:.1f}% avg, {baseline['peak_performance']*100:.1f}% peak")
        decision = "PASS"

        # Show example weights
        example_weights = all_results[0]['results'][0]['event_weights']
        print()
        print(f"   Example weights: {[f'{w:.2f}' for w in example_weights]}")
        print(f"   Interpretation: Events with these weights during learning")
    else:
        print(f"❌ FAIL: No significant improvement ({improvement:+.1f}%)")
        print(f"   Best alternative: {best_strategy['strategy_name']} ({best_strategy['avg_best_match']*100:.1f}%)")
        print(f"   Baseline: {baseline_avg*100:.1f}%")
        print(f"   Recommendation: Keep equal weighting (1.0x for all events)")
        decision = "FAIL"

    print()

    # Save results
    output = {
        'improvement_name': 'Event-Level Importance Weighting',
        'timestamp': datetime.now().isoformat(),
        'validation_series': validation_series,
        'strategies_tested': len(strategies),
        'simulations_used': len(strategies) * len(validation_series),  # 6 strategies × 10 series = 60 sims
        'baseline_performance': baseline_avg,
        'best_strategy': best_strategy['strategy_name'],
        'best_performance': best_strategy['avg_best_match'],
        'improvement_pct': improvement,
        'decision': decision,
        'all_results': all_results
    }

    output_path = Path(__file__).parent.parent / 'results' / 'improvement_3_event_weighting.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"📁 Results saved to: {output_path}")
    print()

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    if decision == "PASS":
        print(f"✅ Event weighting optimization successful")
        print(f"   Best strategy: {best_strategy['strategy_name']}")
        print(f"   Improvement: +{improvement:.1f}%")
    else:
        print(f"⚠️  Event weighting showed no improvement")
        print(f"   Equal weighting (1.0x) already optimal")

    print()
    print(f"Simulations used: 60/600 budgeted")
    print(f"Remaining budget: 540 simulations")
    print()
    print("NEXT: Test Improvement 4 (Column Affinity Analysis)")
    print()

    return 0 if decision == "PASS" else 1


if __name__ == '__main__':
    sys.exit(main())
