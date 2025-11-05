#!/usr/bin/env python3
"""
Phase 2 Test 3: Confidence-Based Selection

Hypothesis: Select combinations with HIGH CONFIDENCE, not just high score
- Generate top 100 candidates as usual
- For each number, calculate "confidence" = how many top candidates include it
- Select the final combination based on high-confidence numbers
- Example: If 80/100 top candidates include #07, that's high confidence

Expected: High potential - may reduce prediction variance
Baseline: 73.214% (seed 999, perfectly stable)
Target: >73.214% to show improvement
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
from true_learning_model import TrueLearningModel

# Series 3144 actual results
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]


class ConfidenceBasedSelectionModel(TrueLearningModel):
    """
    Modified TrueLearningModel with confidence-based selection

    Instead of selecting the highest-scoring candidate directly,
    analyze the top N candidates to find which numbers appear most
    consistently (high confidence), then construct combination from
    high-confidence numbers.
    """

    def __init__(self):
        super().__init__()
        self.confidence_sample_size = 100  # Analyze top 100 candidates
        self.confidence_history = []

    def predict_best_combination(self, series_id: int) -> List[int]:
        """
        Predict best combination using confidence-based selection.

        Instead of picking top-scored candidate directly:
        1. Generate and score candidate pool (10k candidates)
        2. Select top 100 candidates
        3. Calculate confidence for each number (how many times it appears)
        4. Select top 14 numbers by confidence
        """
        # Generate and score candidate pool (use parent's logic)
        candidates = self._generate_candidates(series_id)
        scored_candidates = [(cand, self._calculate_score(cand)) for cand in candidates]
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Take top N candidates for confidence analysis
        top_candidates = [cand for cand, score in scored_candidates[:self.confidence_sample_size]]

        # Calculate confidence for each number
        number_confidence = Counter()
        for candidate in top_candidates:
            for number in candidate:
                number_confidence[number] += 1

        # Select top 14 numbers by confidence
        most_confident_numbers = [num for num, count in number_confidence.most_common(14)]

        # Store confidence data for analysis
        self.confidence_history.append({
            'series_id': series_id,
            'top_confidence': [
                {'number': num, 'confidence': count, 'percentage': (count / self.confidence_sample_size) * 100}
                for num, count in number_confidence.most_common(20)
            ]
        })

        return sorted(most_confident_numbers)


def load_all_data():
    """Load all series data"""
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    if not json_path.exists():
        print(f"❌ JSON export not found")
        return []

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    all_series = []
    for series in json_data.get('data', []):
        all_series.append({
            'series_id': series['series_id'],
            'events': [event['numbers'] for event in series['events']]
        })

    # Add Series 3144
    all_series.append({'series_id': 3144, 'events': SERIES_3144})

    return all_series


def run_confidence_based_test(all_series_data, verbose=True):
    """Run single test with confidence-based selection"""
    random.seed(999)  # Same seed as baseline

    validation_window = 8
    latest_series = 3144
    validation_start = latest_series - validation_window + 1  # 3137

    # Initialize confidence-based model
    model = ConfidenceBasedSelectionModel()

    # Bulk training
    for series in all_series_data:
        if series['series_id'] < validation_start:
            model.learn_from_series(series['series_id'], series['events'])

    print(f"\n🎯 Confidence-based selection active")
    print(f"   Sample size: Top {model.confidence_sample_size} candidates")
    print(f"   Strategy: Select 14 numbers with highest appearance frequency")
    print()

    # Iterative validation
    accuracies = []
    series_details = []

    for series_data in all_series_data:
        if validation_start <= series_data['series_id'] <= latest_series:
            series_id = series_data['series_id']
            actual_results = series_data['events']

            # Predict
            prediction = model.predict_best_combination(series_id)

            # Calculate best match
            best_match = max(len(set(prediction) & set(actual)) for actual in actual_results)
            best_accuracy = best_match / 14.0
            accuracies.append(best_accuracy)

            series_details.append({
                'series_id': series_id,
                'best_match': best_match,
                'accuracy': best_accuracy,
                'prediction': prediction
            })

            if verbose:
                print(f"  Series {series_id}: {best_accuracy:.1%} ({best_match}/14)")
                # Show top confidence numbers
                conf_data = model.confidence_history[-1]['top_confidence'][:5]
                conf_str = ', '.join(f"#{d['number']:02d} ({d['percentage']:.0f}%)" for d in conf_data)
                print(f"    Top 5 confidence: {conf_str}")

            # Learn
            model.validate_and_learn(series_id, prediction, actual_results)

    avg_accuracy = sum(accuracies) / len(accuracies)
    peak_accuracy = max(accuracies)
    min_accuracy = min(accuracies)

    return {
        'average': avg_accuracy,
        'peak': peak_accuracy,
        'min': min_accuracy,
        'series_details': series_details,
        'confidence_history': model.confidence_history
    }


def main():
    print("=" * 80)
    print("PHASE 2 TEST 3: CONFIDENCE-BASED SELECTION")
    print("=" * 80)
    print()
    print("Hypothesis: Select combinations with HIGH CONFIDENCE, not just high score")
    print("  - Analyze top 100 candidates")
    print("  - Calculate confidence for each number (appearance frequency)")
    print("  - Select 14 numbers with highest confidence")
    print()
    print("Baseline: 73.214% (seed 999)")
    print("Target: >73.214% to demonstrate improvement")
    print()

    # Load data
    print("Loading data...")
    all_series_data = load_all_data()
    if not all_series_data:
        print("❌ Failed to load data")
        return
    print(f"✅ Loaded {len(all_series_data)} series")

    # Run test
    print("\nRunning confidence-based selection test with seed 999...")
    result = run_confidence_based_test(all_series_data, verbose=True)

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    # Performance metrics
    print(f"Average Performance: {result['average']:.3%}")
    print(f"Peak Performance:    {result['peak']:.3%}")
    print(f"Min Performance:     {result['min']:.3%}")
    print()

    # Comparison to baseline
    baseline = 0.73214
    improvement = result['average'] - baseline
    improvement_pct = (improvement / baseline) * 100

    print(f"Baseline:           {baseline:.3%}")
    print(f"Confidence-Based:   {result['average']:.3%}")
    print(f"Difference:         {improvement:+.3%} ({improvement_pct:+.2f}%)")
    print()

    if result['average'] > baseline:
        print(f"✅ IMPROVEMENT: +{improvement:.3%} over baseline!")
        print("   Confidence-based selection shows positive impact")
    elif abs(improvement) < 0.001:
        print(f"➖ NEUTRAL: No significant change")
        print("   Confidence-based selection has no impact on this dataset")
    else:
        print(f"❌ REGRESSION: {improvement:.3%} worse than baseline")
        print("   Confidence-based selection negatively impacts performance")
    print()

    # Confidence analysis
    print("=" * 80)
    print("CONFIDENCE ANALYSIS (Sample)")
    print("=" * 80)
    print()

    # Show Series 3142 (best performer in baseline)
    series_3142_data = next((entry for entry in result['confidence_history'] if entry['series_id'] == 3142), None)
    if series_3142_data:
        print("Series 3142 (Peak Performance):")
        print("  Top 10 confidence numbers:")
        for i, conf in enumerate(series_3142_data['top_confidence'][:10], 1):
            print(f"    {i:2d}. #{conf['number']:02d}: {conf['confidence']:3d}/100 ({conf['percentage']:5.1f}%)")
        print()

    # Save results
    output = {
        'test_name': 'confidence_based_selection',
        'hypothesis': 'Select high-confidence numbers from top candidates',
        'baseline': baseline,
        'result': result,
        'improvement': improvement,
        'improvement_pct': improvement_pct,
        'verdict': 'improvement' if result['average'] > baseline else ('neutral' if abs(improvement) < 0.001 else 'regression')
    }

    output_file = Path(__file__).parent / 'test_confidence_based_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"📊 Results saved to: {output_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
