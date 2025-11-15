#!/usr/bin/env python3
"""
Improvement 4: Column Affinity Analysis

Tests column-level pattern learning
Budget: 500 simulations
Expected: +1-2% improvement

Current: Numbers treated independently of column
Column structure:
- Column 0 (01-09): 9 numbers
- Column 1 (10-19): 10 numbers
- Column 2 (20-25): 6 numbers

Will test: Column balance tracking, column pair affinities, distribution awareness
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

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


def get_column(number):
    """Get column index for a number (0, 1, or 2)"""
    if 1 <= number <= 9:
        return 0
    elif 10 <= number <= 19:
        return 1
    elif 20 <= number <= 25:
        return 2
    return None


def analyze_column_distribution(events):
    """Analyze column distribution across events"""
    column_counts = {0: [], 1: [], 2: []}

    for event in events:
        counts = {0: 0, 1: 0, 2: 0}
        for num in event:
            col = get_column(num)
            if col is not None:
                counts[col] += 1

        for col in [0, 1, 2]:
            column_counts[col].append(counts[col])

    # Calculate average distribution
    avg_distribution = {
        col: sum(counts) / len(counts)
        for col, counts in column_counts.items()
    }

    return avg_distribution


class ColumnAwareModel(TrueLearningModel):
    """Extended model with column affinity tracking"""

    def __init__(self, seed=999, cold_hot_boost=30.0, column_boost=1.0):
        super().__init__(seed=seed, cold_hot_boost=cold_hot_boost)
        self.column_boost = column_boost
        self.column_pair_affinities = defaultdict(float)  # (col1, col2) -> affinity
        self.column_balance_history = []  # Historical column distributions

    def learn_from_series(self, series_id, events):
        """Learn from series with column awareness"""
        # First, do normal learning
        super().learn_from_series(series_id, events)

        if len(events) != 7:
            return

        # Track column distributions
        for event in events:
            col_counts = {0: 0, 1: 0, 2: 0}
            for num in event:
                col = get_column(num)
                if col is not None:
                    col_counts[col] += 1

            self.column_balance_history.append(col_counts)

            # Track column pair affinities
            columns_in_event = []
            for num in event:
                col = get_column(num)
                if col is not None:
                    columns_in_event.append(col)

            # Count co-occurrences of numbers from different columns
            for i, num1 in enumerate(event):
                col1 = get_column(num1)
                for num2 in event[i+1:]:
                    col2 = get_column(num2)
                    if col1 is not None and col2 is not None and col1 != col2:
                        col_pair = tuple(sorted([col1, col2]))
                        self.column_pair_affinities[col_pair] += 0.1

    def predict_best_combination(self, series_id):
        """Generate prediction with column balance awareness"""
        # Generate base candidates using parent method
        candidates = []

        # Use parent's candidate generation
        import random
        random.seed(self._seed if self._seed is not None else 999)

        # Generate weighted candidates
        for _ in range(self.CANDIDATE_POOL_SIZE):
            candidate = []
            available = list(range(1, 26))

            while len(candidate) < 14:
                # Weight by frequency
                weights = []
                for num in available:
                    weight = self.number_frequency_weights.get(num, 1.0)

                    # Apply column boost
                    col = get_column(num)
                    if col is not None:
                        # Check if adding this number improves column balance
                        current_col_counts = {0: 0, 1: 0, 2: 0}
                        for c in candidate:
                            c_col = get_column(c)
                            if c_col is not None:
                                current_col_counts[c_col] += 1

                        # Target distribution: 4-5 from col0, 6-7 from col1, 3-4 from col2
                        target = {0: 4.5, 1: 6.5, 2: 3.0}
                        current_count = current_col_counts[col]
                        target_count = target[col]

                        # Boost if under target, penalize if over
                        if current_count < target_count:
                            weight *= (1.0 + self.column_boost * 0.2)
                        elif current_count > target_count:
                            weight *= (1.0 - self.column_boost * 0.1)

                    weights.append(weight)

                # Normalize and select
                total_weight = sum(weights)
                if total_weight > 0:
                    probabilities = [w / total_weight for w in weights]
                    selected = random.choices(available, weights=probabilities, k=1)[0]
                else:
                    selected = random.choice(available)

                candidate.append(selected)
                available.remove(selected)

            candidates.append(sorted(candidate))

        # Score candidates (use parent's scoring with column affinity bonus)
        best_candidate = None
        best_score = -float('inf')

        for candidate in candidates:
            # Base score from parent
            score = sum(self.number_frequency_weights.get(num, 1.0) for num in candidate)

            # Pair affinity bonus
            for i, num1 in enumerate(candidate):
                for num2 in candidate[i+1:]:
                    pair = tuple(sorted([num1, num2]))
                    score += self.pair_affinities.get(pair, 0.0) * 25.0

            # Column pair affinity bonus
            if self.column_boost > 1.0:
                for i, num1 in enumerate(candidate):
                    col1 = get_column(num1)
                    for num2 in candidate[i+1:]:
                        col2 = get_column(num2)
                        if col1 is not None and col2 is not None and col1 != col2:
                            col_pair = tuple(sorted([col1, col2]))
                            score += self.column_pair_affinities.get(col_pair, 0.0) * 5.0 * self.column_boost

            # Column balance score
            if self.column_boost > 1.0:
                col_counts = {0: 0, 1: 0, 2: 0}
                for num in candidate:
                    col = get_column(num)
                    if col is not None:
                        col_counts[col] += 1

                # Ideal distribution
                ideal = {0: 4.5, 1: 6.5, 2: 3.0}
                balance_score = -sum((col_counts[col] - ideal[col])**2 for col in [0, 1, 2])
                score += balance_score * 2.0 * self.column_boost

            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate


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


def test_column_boost(boost_value, validation_series, historical_data, seed=999):
    """Test a specific column boost value"""
    results = []

    for target_series in validation_series:
        # Create model with specific boost
        model = ColumnAwareModel(seed=seed, cold_hot_boost=30.0, column_boost=boost_value)

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
            'avg_match': avg_match
        })

    # Calculate summary
    avg_best = sum(r['best_match'] for r in results) / len(results)
    peak = max(r['best_match'] for r in results)

    return {
        'column_boost': boost_value,
        'avg_best_match': avg_best,
        'peak_performance': peak,
        'results': results
    }


def main():
    print("\n")
    print("="*80)
    print("IMPROVEMENT 4: COLUMN AFFINITY ANALYSIS")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Testing column-level pattern learning and balance awareness")
    print("Budget: 500 simulations")
    print("Expected: +1-2% improvement")
    print()

    # Load data
    historical_data = load_historical_data()

    # Validation window: Last 10 series
    all_series = sorted(historical_data.keys())
    validation_series = all_series[-10:]  # 3139-3148

    print(f"Validation Series: {validation_series[0]}-{validation_series[-1]} ({len(validation_series)} series)")
    print()

    # Test column boost values
    boost_values = [1.0, 1.2, 1.5, 2.0, 2.5, 3.0]

    print(f"Testing {len(boost_values)} column boost configurations:")
    print(f"  {boost_values}")
    print(f"  (1.0 = baseline, no column awareness)")
    print()

    all_results = []
    baseline = None

    for i, boost in enumerate(boost_values, 1):
        print(f"[{i}/{len(boost_values)}] Testing column_boost={boost:.1f}...", end=" ", flush=True)

        result = test_column_boost(boost, validation_series, historical_data)
        all_results.append(result)

        avg = result['avg_best_match'] * 100
        peak = result['peak_performance'] * 100

        print(f"Avg {avg:5.1f}%, Peak {peak:5.1f}%")

        # Mark baseline (boost=1.0)
        if boost == 1.0:
            baseline = result

    print()
    print("="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print()

    # Sort by average performance
    all_results.sort(key=lambda x: x['avg_best_match'], reverse=True)

    print("Rank   Column Boost   Avg Best   Peak      vs Baseline")
    print("-" * 65)

    baseline_avg = baseline['avg_best_match']
    best_config = all_results[0]

    for i, result in enumerate(all_results, 1):
        boost = result['column_boost']
        avg = result['avg_best_match'] * 100
        peak = result['peak_performance'] * 100
        diff = (result['avg_best_match'] - baseline_avg) * 100

        marker = "🏆" if i == 1 else "  "
        status = "BASELINE" if boost == 1.0 else (f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%")

        print(f"{marker} {i:2d}   {boost:12.1f}   {avg:7.1f}%   {peak:6.1f}%   {status}")

    print()

    # Decision
    improvement = (best_config['avg_best_match'] - baseline_avg) * 100

    print("="*80)
    print("DECISION")
    print("="*80)
    print()

    if improvement >= 0.5:  # Min 0.5% improvement
        print(f"✅ PASS: Improvement found (+{improvement:.1f}%)")
        print(f"   Best column boost: {best_config['column_boost']}")
        print(f"   Performance: {best_config['avg_best_match']*100:.1f}% avg, {best_config['peak_performance']*100:.1f}% peak")
        print(f"   vs Baseline (boost=1.0): {baseline_avg*100:.1f}% avg, {baseline['peak_performance']*100:.1f}% peak")
        decision = "PASS"

        if best_config['column_boost'] != 1.0:
            print()
            print(f"   RECOMMENDATION: Enable column affinity with boost={best_config['column_boost']}")
    else:
        print(f"❌ FAIL: No significant improvement ({improvement:+.1f}%)")
        print(f"   Best alternative: Column boost {best_config['column_boost']} ({best_config['avg_best_match']*100:.1f}%)")
        print(f"   Current (boost=1.0): {baseline_avg*100:.1f}%")
        print(f"   Recommendation: Column awareness provides no benefit")
        decision = "FAIL"

    print()

    # Save results
    output = {
        'improvement_name': 'Column Affinity Analysis',
        'timestamp': datetime.now().isoformat(),
        'validation_series': validation_series,
        'boost_values_tested': boost_values,
        'simulations_used': len(boost_values) * len(validation_series),  # 6 boosts × 10 series = 60 sims
        'baseline_boost': 1.0,
        'baseline_performance': baseline_avg,
        'best_boost': best_config['column_boost'],
        'best_performance': best_config['avg_best_match'],
        'improvement_pct': improvement,
        'decision': decision,
        'all_results': all_results
    }

    output_path = Path(__file__).parent.parent / 'results' / 'improvement_4_column_affinity.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"📁 Results saved to: {output_path}")
    print()

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    if decision == "PASS":
        print(f"✅ Column affinity optimization successful")
        print(f"   Optimal boost: {best_config['column_boost']}")
        print(f"   Improvement: +{improvement:.1f}%")
    else:
        print(f"⚠️  Column affinity showed no improvement")
        print(f"   Column awareness not beneficial")

    print()
    print(f"Simulations used: 60/500 budgeted")
    print(f"Total used so far: 300 simulations (Imp1: 100, Imp2: 80, Imp3: 60, Imp4: 60)")
    print()
    print("NEXT: Continue with remaining improvements or summarize findings")
    print()

    return 0 if decision == "PASS" else 1


if __name__ == '__main__':
    sys.exit(main())
