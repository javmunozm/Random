#!/usr/bin/env python3
"""
Test the FIXED Python TrueLearningModel that now matches C# implementation
Compare performance on Series 3146-3150 to validate parameter fixes
"""

import json
import sys
from true_learning_model import TrueLearningModel


def load_series_data(file_path="full_series_data.json"):
    """Load full series data from JSON"""
    with open(file_path, 'r') as f:
        return json.load(f)


def calculate_accuracy(prediction, actual):
    """Calculate match percentage"""
    matches = len(set(prediction) & set(actual))
    return (matches / 14.0) * 100.0


def test_fixed_model():
    """Test fixed model matching C# parameters"""
    print("=" * 80)
    print("PYTHON MODEL TEST - MATCHED TO C# IMPLEMENTATION")
    print("=" * 80)
    print()

    # Load data (JSON format: {"2980": [[event1], [event2], ...]} })
    all_series_data = load_series_data()

    # Test series: 3146-3150
    test_series = [3146, 3147, 3148, 3149, 3150]

    # Training: All series before 3146
    training_series_ids = sorted([int(sid) for sid in all_series_data.keys() if int(sid) < 3146])

    print(f"Training Data: Series {training_series_ids[0]}-{training_series_ids[-1]} ({len(training_series_ids)} series)")
    print(f"Test Data: Series {test_series[0]}-{test_series[-1]} ({len(test_series)} series)")
    print()

    # Initialize model (no seed - use default random)
    model = TrueLearningModel(seed=None)  # C# uses Random() without seed

    print("=" * 80)
    print("MODEL PARAMETERS (MATCHED TO C#)")
    print("=" * 80)
    print(f"RECENT_SERIES_LOOKBACK: {model.RECENT_SERIES_LOOKBACK}")
    print(f"Cold/Hot Boost: {model._cold_hot_boost}x")
    print(f"Pair Affinity Multiplier: {model.PAIR_AFFINITY_MULTIPLIER}x")
    print(f"Triplet Affinity Multiplier: {model.TRIPLET_AFFINITY_MULTIPLIER}x")
    print(f"Candidate Pool: {model.CANDIDATE_POOL_SIZE}")
    print(f"Candidates to Score: {model.CANDIDATES_TO_SCORE}")
    print(f"Critical Number Boost: {model.CRITICAL_NUMBER_GENERATION_BOOST}x")
    print(f"Weight Normalization: DISABLED (matching C#)")
    print(f"Weight Decay: DISABLED (matching C#)")
    print()

    # Phase 1: Bulk training
    print("=" * 80)
    print("PHASE 1: BULK TRAINING")
    print("=" * 80)
    print()
    for series_id in training_series_ids:
        events = all_series_data[str(series_id)]  # Direct list of 7 events
        model.learn_from_series(series_id, events)

    print(f"✅ Trained on {len(training_series_ids)} series")
    print()

    # Phase 2: Iterative validation
    print("=" * 80)
    print("PHASE 2: ITERATIVE VALIDATION ON SERIES 3146-3150")
    print("=" * 80)
    print()

    accuracies = []
    best_matches = []

    for series_id in test_series:
        print(f"\n--- Series {series_id} ---")

        # Get actual results
        actual_results = all_series_data[str(series_id)]  # Direct list of 7 events

        # Generate prediction
        prediction = model.predict_best_combination(series_id)
        print(f"🎯 Prediction: {' '.join(f'{n:02d}' for n in prediction)}")

        # Calculate best match across all 7 events
        best_match = 0
        best_event = None
        best_event_num = 0

        for i, actual in enumerate(actual_results, 1):
            matches = len(set(prediction) & set(actual))
            if matches > best_match:
                best_match = matches
                best_event = actual
                best_event_num = i
            print(f"   Event {i}: {matches}/14 match")

        accuracy = (best_match / 14.0) * 100.0
        accuracies.append(accuracy)
        best_matches.append(best_match)

        print(f"✅ Best Match: {best_match}/14 ({accuracy:.1f}%)")
        print(f"   Best Event {best_event_num}: {' '.join(f'{n:02d}' for n in best_event)}")

        # Learn from this series
        model.validate_and_learn(series_id, prediction, actual_results)

    # Summary
    print()
    print("=" * 80)
    print("PYTHON MODEL SUMMARY (MATCHED TO C#)")
    print("=" * 80)
    print()

    avg_accuracy = sum(accuracies) / len(accuracies)
    avg_best_match = sum(best_matches) / len(best_matches)
    peak_accuracy = max(accuracies)
    peak_match = max(best_matches)

    print(f"Test Series: 3146-3150 (5 series)")
    print(f"Training Data: {training_series_ids[0]}-{training_series_ids[-1]} ({len(training_series_ids)} series)")
    print()
    print(f"Average Accuracy: {avg_accuracy:.1f}% ({avg_best_match:.1f}/14 numbers)")
    print(f"Peak Accuracy: {peak_accuracy:.1f}% ({peak_match}/14 numbers)")
    print()
    print("Individual Results:")
    for i, series_id in enumerate(test_series):
        print(f"  Series {series_id}: {best_matches[i]}/14 ({accuracies[i]:.1f}%)")

    print()
    print("=" * 80)
    print("COMPARISON TO PREVIOUS PYTHON RESULTS")
    print("=" * 80)
    print()
    print("Previous Python (9-series, 30x boost):  67.1%")
    print("Previous Python (10-series, 30x boost): 64.3%")
    print(f"Fixed Python (16-series, 50x boost):    {avg_accuracy:.1f}%")
    print()
    print(f"Improvement: {avg_accuracy - 67.1:+.1f}% vs best previous")
    print()
    print("Expected C# Performance: 71.4% baseline, 78.6% peak")
    print()

    if avg_accuracy >= 70.0:
        print("✅ SUCCESS: Matches C# baseline range!")
    elif avg_accuracy >= 67.0:
        print("⚠️  PARTIAL: Better than unfixed Python, but below C# baseline")
    else:
        print("❌ FAILURE: Performance degraded - needs investigation")

    print()
    print("=" * 80)


if __name__ == "__main__":
    test_fixed_model()
