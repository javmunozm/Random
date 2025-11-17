#!/usr/bin/env python3
"""
Python-based ML Model Tester for Lottery Prediction System
Analyzes data from data_toadd.txt and validates model performance
"""

import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set
import statistics

class LotteryDataParser:
    """Parse lottery data from data_toadd.txt"""

    @staticmethod
    def parse_file(filepath: str) -> Dict[int, List[List[int]]]:
        """
        Parse data_toadd.txt format:
        3140:
        01 02 03 06 07 08 11 12 13 16 18 21 22 25
        ... (7 events total)

        Returns: {series_id: [[event1], [event2], ...]}
        """
        data = {}
        current_series = None
        current_events = []

        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()

                # Check for series ID line (e.g., "3140:")
                series_match = re.match(r'^(\d{4}):$', line)
                if series_match:
                    # Save previous series if exists
                    if current_series and current_events:
                        data[current_series] = current_events

                    # Start new series
                    current_series = int(series_match.group(1))
                    current_events = []
                    continue

                # Check for event line (14 numbers)
                if line and current_series:
                    numbers = [int(n) for n in line.split()]
                    if len(numbers) == 14:
                        current_events.append(numbers)

        # Save last series
        if current_series and current_events:
            data[current_series] = current_events

        return data

class SimpleLearningModel:
    """Simplified Python version of TrueLearningModel for testing"""

    def __init__(self):
        self.number_weights = {i: 1.0 for i in range(1, 26)}
        self.pair_affinities = defaultdict(float)
        self.critical_numbers = set()

    def learn_from_series(self, events: List[List[int]]):
        """Learn from all 7 events in a series (Phase 1 multi-event learning)"""

        # Count frequency across ALL events
        number_frequency = Counter()
        for event in events:
            number_frequency.update(event)

        # Identify critical numbers (appear in 5+ events)
        self.critical_numbers = {num for num, count in number_frequency.items() if count >= 5}

        # Update weights based on frequency
        for num, count in number_frequency.items():
            freq_ratio = count / len(events)
            if freq_ratio >= 0.7:  # 70%+ of events
                self.number_weights[num] *= 1.2  # Strong boost
            elif freq_ratio >= 0.5:  # 50%+ of events
                self.number_weights[num] *= 1.15  # Medium boost
            else:
                self.number_weights[num] *= 1.05  # Weak boost

        # Learn pair affinities
        for event in events:
            for i in range(len(event)):
                for j in range(i + 1, len(event)):
                    pair = tuple(sorted([event[i], event[j]]))
                    self.pair_affinities[pair] += 0.1

    def predict(self, cold_count: int = 7, hot_count: int = 7) -> List[int]:
        """
        Generate prediction using hybrid cold+hot strategy
        Returns 14 numbers
        """
        # Get top weighted (hot) and bottom weighted (cold) numbers
        sorted_weights = sorted(self.number_weights.items(), key=lambda x: x[1])

        cold_numbers = [num for num, _ in sorted_weights[:cold_count]]
        hot_numbers = [num for num, _ in sorted_weights[-hot_count:]]

        # Combine and ensure no duplicates
        prediction = list(set(cold_numbers + hot_numbers))

        # If we don't have 14, fill with critical numbers
        if len(prediction) < 14:
            remaining = 14 - len(prediction)
            available_critical = [n for n in self.critical_numbers if n not in prediction]
            prediction.extend(available_critical[:remaining])

        # If still not 14, fill randomly from remaining
        if len(prediction) < 14:
            remaining = 14 - len(prediction)
            all_numbers = set(range(1, 26))
            available = list(all_numbers - set(prediction))
            prediction.extend(available[:remaining])

        return sorted(prediction[:14])

class ModelValidator:
    """Validate model performance on historical data"""

    @staticmethod
    def calculate_accuracy(prediction: List[int], events: List[List[int]]) -> Tuple[float, float, int]:
        """
        Calculate best match and average match across 7 events
        Returns: (best_accuracy, avg_accuracy, best_match_count)
        """
        matches = []
        for event in events:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count)

        best_match = max(matches)
        avg_match = statistics.mean(matches)

        best_accuracy = best_match / 14.0
        avg_accuracy = avg_match / 14.0

        return best_accuracy, avg_accuracy, best_match

    @staticmethod
    def analyze_critical_numbers(prediction: List[int], events: List[List[int]]) -> Dict:
        """Analyze how well critical numbers were predicted"""
        # Find critical numbers (5+ events)
        number_frequency = Counter()
        for event in events:
            number_frequency.update(event)

        critical_numbers = {num for num, count in number_frequency.items() if count >= 5}

        critical_hit = set(prediction) & critical_numbers
        critical_missed = critical_numbers - set(prediction)

        return {
            'critical_numbers': sorted(critical_numbers),
            'critical_hit': sorted(critical_hit),
            'critical_missed': sorted(critical_missed),
            'hit_rate': len(critical_hit) / len(critical_numbers) if critical_numbers else 0
        }

def run_validation_test(data: Dict[int, List[List[int]]], validation_start: int, validation_end: int):
    """
    Run iterative validation test similar to real-train command
    """
    print("="*80)
    print("PYTHON ML MODEL VALIDATION TEST")
    print("="*80)
    print()

    # Get all series IDs
    all_series = sorted(data.keys())

    # Find training cutoff
    training_series = [s for s in all_series if s < validation_start]
    validation_series = [s for s in all_series if validation_start <= s <= validation_end]

    print(f"Training series: {len(training_series)} series ({min(training_series)}-{max(training_series)})")
    print(f"Validation series: {len(validation_series)} series ({min(validation_series)}-{max(validation_series)})")
    print()

    # Initialize model
    model = SimpleLearningModel()

    # Bulk training on historical data
    print("Phase 1: Bulk training...")
    for series_id in training_series:
        if series_id in data:
            model.learn_from_series(data[series_id])
    print(f"✓ Trained on {len(training_series)} series")
    print()

    # Iterative validation
    print("Phase 2: Iterative validation...")
    print("-"*80)

    results = []
    validator = ModelValidator()

    for series_id in validation_series:
        if series_id not in data:
            continue

        # Generate prediction
        prediction = model.predict()

        # Validate against actual results
        actual_events = data[series_id]
        best_acc, avg_acc, best_match = validator.calculate_accuracy(prediction, actual_events)
        critical_analysis = validator.analyze_critical_numbers(prediction, actual_events)

        # Print results
        print(f"Series {series_id}:")
        print(f"  Prediction: {' '.join(f'{n:02d}' for n in prediction)}")
        print(f"  Best Match: {best_match}/14 ({best_acc*100:.1f}%)")
        print(f"  Avg Match:  {avg_acc*14:.1f}/14 ({avg_acc*100:.1f}%)")
        print(f"  Critical Numbers: {' '.join(f'{n:02d}' for n in critical_analysis['critical_numbers'])}")
        print(f"  Critical Hit: {len(critical_analysis['critical_hit'])}/{len(critical_analysis['critical_numbers'])} - {' '.join(f'{n:02d}' for n in critical_analysis['critical_hit'])}")
        print(f"  Critical Missed: {' '.join(f'{n:02d}' for n in critical_analysis['critical_missed'])}")
        print()

        results.append({
            'series_id': series_id,
            'best_accuracy': best_acc,
            'avg_accuracy': avg_acc,
            'best_match': best_match,
            'critical_hit_rate': critical_analysis['hit_rate']
        })

        # Learn from this series for next iteration
        model.learn_from_series(actual_events)

    # Summary
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    overall_best_avg = statistics.mean([r['best_accuracy'] for r in results])
    overall_avg = statistics.mean([r['avg_accuracy'] for r in results])
    overall_critical_hit = statistics.mean([r['critical_hit_rate'] for r in results])

    print(f"Overall Best Average: {overall_best_avg*100:.2f}%")
    print(f"Overall Avg: {overall_avg*100:.2f}%")
    print(f"Critical Hit Rate: {overall_critical_hit*100:.1f}%")
    print()

    # Learning trend
    if len(results) >= 6:
        first_three = statistics.mean([r['best_accuracy'] for r in results[:3]])
        last_three = statistics.mean([r['best_accuracy'] for r in results[-3:]])
        improvement = (last_three - first_three) * 100

        print(f"Learning Trend:")
        print(f"  First 3 avg: {first_three*100:.2f}%")
        print(f"  Last 3 avg: {last_three*100:.2f}%")
        print(f"  Improvement: {improvement:+.2f}%")
        print()

    # Individual results table
    print("Individual Results:")
    print(f"{'Series':<10} {'Best':<10} {'Avg':<10} {'Critical Hit':<15}")
    print("-"*50)
    for r in results:
        print(f"{r['series_id']:<10} {r['best_accuracy']*100:>6.1f}%   {r['avg_accuracy']*100:>6.1f}%   {r['critical_hit_rate']*100:>6.1f}%")

    return results

if __name__ == "__main__":
    # Parse data
    print("Loading data from data_toadd.txt...")
    data = LotteryDataParser.parse_file("/home/user/Random/data_toadd.txt")
    print(f"✓ Loaded {len(data)} series (Series {min(data.keys())}-{max(data.keys())})")
    print()

    # Run validation test on recent series (similar to C# model)
    # Validate on last 8 series (matching the JSON results)
    all_series = sorted(data.keys())
    validation_start = all_series[-8] if len(all_series) >= 8 else all_series[0]
    validation_end = all_series[-1]

    results = run_validation_test(data, validation_start, validation_end)
