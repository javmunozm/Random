#!/usr/bin/env python3
"""
MANDEL METHOD - ML-Guided Exhaustive Search (WITH VALIDATION LEARNING)

Stefan Mandel's principle: Reduce search space intelligently, then exhaustively search.

Instead of:
- Searching ALL 4,457,400 combinations (too slow)
- Random 10k weighted samples (not exhaustive)

Mandel approach:
1. Train ML model with ITERATIVE VALIDATION LEARNING:
   - Bulk train on historical data
   - Generate predictions for recent 8 series
   - Validate against actual results
   - Learn from errors (multiplicative updates for missed critical numbers)
2. ML identifies top N most likely numbers based on calibrated weights
3. Generate ALL C(N,14) combinations from those N numbers
4. Exhaustively score that focused pool
5. Pick the highest scoring combination

Key advantages:
- Each series gets its own ML-guided pool!
- Weights calibrated by actual prediction performance
- Stronger learning (multiplicative vs additive updates)
"""

import json
import sys
import time
from pathlib import Path
from itertools import combinations
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from true_learning_model import TrueLearningModel


def load_all_series_data():
    """Load all series data from JSON export + hardcoded recent series"""
    # Load from JSON export
    json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

    series_dict = {}

    if json_path.exists():
        with open(json_path, 'r') as f:
            json_data = json.load(f)

        for series in json_data.get('data', []):
            series_id = series['series_id']
            events = [event['numbers'] for event in series['events']]
            series_dict[series_id] = events

    # Add hardcoded recent series
    series_dict[3144] = [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
    ]

    series_dict[3145] = [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
    ]

    series_dict[3147] = [
        [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
        [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
        [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
        [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
        [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
        [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
        [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
    ]

    series_dict[3148] = [
        [1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 19, 22, 23, 25],
        [2, 3, 6, 7, 10, 12, 13, 14, 15, 16, 17, 19, 21, 23],
        [1, 2, 4, 5, 6, 8, 10, 12, 14, 15, 17, 18, 20, 22],
        [2, 3, 4, 5, 8, 10, 12, 13, 14, 15, 18, 20, 21, 25],
        [3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 19, 20, 21, 24],
        [2, 3, 4, 5, 9, 10, 12, 14, 15, 16, 17, 18, 22, 25],
        [1, 4, 6, 7, 9, 11, 12, 14, 16, 19, 20, 21, 23, 25],
    ]

    return series_dict


def generate_mandel_prediction(series_id: int = 3149, top_n: int = 18):
    """
    Generate prediction using Mandel method

    Args:
        series_id: The series to predict
        top_n: Number of top numbers to select (16-20 recommended)
               C(16,14) = 120, C(17,14) = 680, C(18,14) = 3060,
               C(19,14) = 11628, C(20,14) = 38760

    Returns:
        dict with prediction and metadata
    """
    print("=" * 80)
    print("MANDEL METHOD - ML-GUIDED EXHAUSTIVE SEARCH")
    print("=" * 80)
    print()
    print(f"Target Series: {series_id}")
    print(f"Top N numbers to select: {top_n}")

    # Calculate pool size
    from math import comb
    pool_size = comb(top_n, 14)
    print(f"Mandel pool size: {pool_size:,} combinations (vs 4,457,400 total)")
    print(f"Reduction: {(1 - pool_size/4457400)*100:.1f}% smaller search space")
    print()

    # Load data
    series_data = load_all_series_data()
    print(f"Loaded {len(series_data)} series for training")
    print()

    # Train model with iterative validation learning
    print("=" * 80)
    print("PHASE 1: TRAINING ML MODEL WITH VALIDATION LEARNING")
    print("=" * 80)
    print("Using validate_and_learn for better weight calibration")
    print()

    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = 8

    # Get all training series
    training_series = sorted([sid for sid in series_data.keys() if sid < series_id])

    # Split into bulk training and iterative validation
    if len(training_series) >= 8:
        # Bulk train on all but last 8
        bulk_series = training_series[:-8]
        validation_series = training_series[-8:]

        print(f"Bulk training on {len(bulk_series)} series (basic learning)")
        for sid in bulk_series:
            model.learn_from_series(sid, series_data[sid])

        print(f"✅ Bulk training complete")
        print()
        print(f"Iterative validation learning on last {len(validation_series)} series")
        print("(Generates predictions, validates, learns from errors)")
        print()

        # Iterative validation learning on recent series
        for i, sid in enumerate(validation_series, 1):
            print(f"  [{i}/{len(validation_series)}] Series {sid}:", end=" ")

            # Generate prediction
            prediction = model.predict_best_combination(sid)

            # Validate and learn (strong multiplicative updates)
            actual_results = series_data[sid]
            matches = [len(set(prediction) & set(event)) for event in actual_results]
            best_match = max(matches)
            avg_match = sum(matches) / len(matches)

            print(f"Best={best_match}/14 ({best_match/14*100:.1f}%), Avg={avg_match:.2f}/14", end="")

            # This uses the stronger validate_and_learn mechanism
            model.validate_and_learn(sid, prediction, actual_results)

            print(" ✅")

        train_count = len(training_series)
    else:
        # Not enough data for split, just bulk train
        print(f"Training on {len(training_series)} series (bulk only)")
        for sid in training_series:
            model.learn_from_series(sid, series_data[sid])
        train_count = len(training_series)

    print()
    print(f"✅ Training complete: {train_count} series")
    print(f"   - Bulk training: {len(bulk_series) if len(training_series) >= 8 else len(training_series)} series")
    print(f"   - Iterative validation: {len(validation_series) if len(training_series) >= 8 else 0} series")
    print()

    # Select top N numbers based on ML weights
    print("=" * 80)
    print(f"PHASE 2: SELECT TOP {top_n} NUMBERS (ML-GUIDED)")
    print("=" * 80)

    # Get all weights
    all_weights = sorted(model.number_frequency_weights.items(), key=lambda x: -x[1])

    print("All 25 numbers ranked by ML weight:")
    for i, (num, weight) in enumerate(all_weights, 1):
        marker = "✅" if i <= top_n else "❌"
        print(f"  {i:2d}. #{num:02d}: {weight:.2f} {marker}")
    print()

    # Select top N
    selected_numbers = [num for num, _ in all_weights[:top_n]]
    selected_numbers.sort()

    print(f"🎯 Selected {top_n} numbers for Mandel pool:")
    print(f"   {' '.join(f'{n:02d}' for n in selected_numbers)}")
    print()

    # Generate all combinations from selected numbers
    print("=" * 80)
    print(f"PHASE 3: GENERATE & SCORE MANDEL POOL ({pool_size:,} combinations)")
    print("=" * 80)
    print()

    start_time = time.time()

    best_combination = None
    best_score = -float('inf')
    count = 0
    progress_interval = max(pool_size // 10, 100)  # Report every 10%
    next_report = progress_interval

    print(f"🔍 Scoring {pool_size:,} combinations...")
    scoring_start = time.time()

    for combination in combinations(selected_numbers, 14):
        combo_list = list(combination)
        score = model._calculate_score(combo_list)

        if score > best_score:
            best_score = score
            best_combination = combo_list
            elapsed = time.time() - start_time
            print(f"  🎯 New best: score={score:.2f}, combo={combo_list[:3]}...{combo_list[-3:]}, time={elapsed:.1f}s")

        count += 1

        # Progress report
        if count >= next_report:
            elapsed = time.time() - start_time
            rate = count / (time.time() - scoring_start) if (time.time() - scoring_start) > 0 else 0
            progress_pct = (count / pool_size) * 100
            remaining = (pool_size - count) / rate if rate > 0 else 0

            print(f"  Progress: {count:,}/{pool_size:,} ({progress_pct:.1f}%) - "
                  f"{rate:.0f} combos/sec - ETA: {remaining:.1f}s")

            next_report += progress_interval

    end_time = time.time()
    total_time = end_time - start_time

    print()
    print("=" * 80)
    print("MANDEL POOL SCORING COMPLETE")
    print("=" * 80)
    print(f"Pool size: {pool_size:,} combinations")
    print(f"Time: {total_time:.1f} seconds ({total_time/60:.2f} minutes)")
    print(f"Rate: {count/total_time:.0f} combinations/second")
    print()
    print("=" * 80)
    print(f"BEST PREDICTION FOR SERIES {series_id}")
    print("=" * 80)
    print(f"Combination: {best_combination}")
    print(f"ML Score: {best_score:.4f}")
    print("=" * 80)
    print()

    # Format prediction
    prediction_str = ' '.join([f"{num:02d}" for num in best_combination])
    print(f"📊 PREDICTION: {prediction_str}")
    print()

    # Check which selected numbers made it into final prediction
    in_prediction = set(best_combination)
    selected_set = set(selected_numbers)
    not_selected = [n for n in range(1, 26) if n not in selected_set]

    print(f"✅ All 14 numbers from top-{top_n} pool: {sorted(in_prediction)}")
    print(f"❌ Excluded numbers (not in top-{top_n}): {not_selected}")
    print()

    # Save results
    results = {
        'series_id': series_id,
        'method': 'mandel_ml_guided_exhaustive_with_validation',
        'model': 'TrueLearningModel-Phase1-Optimized',
        'training_method': 'iterative_validation_learning',
        'top_n_selected': top_n,
        'selected_numbers': selected_numbers,
        'mandel_pool_size': pool_size,
        'reduction_vs_total': f"{(1 - pool_size/4457400)*100:.1f}%",
        'seed': 999,
        'cold_hot_boost': 30.0,
        'lookback_window': 8,
        'training_series_count': train_count,
        'bulk_training_series': len(bulk_series) if len(training_series) >= 8 else len(training_series),
        'validation_learning_series': len(validation_series) if len(training_series) >= 8 else 0,
        'prediction': best_combination,
        'prediction_formatted': prediction_str,
        'ml_score': best_score,
        'scoring_time_seconds': total_time,
        'scoring_rate': count / total_time,
        'comparison_to_full_exhaustive': {
            'mandel_pool': pool_size,
            'full_exhaustive': 4457400,
            'speedup': f"{4457400/pool_size:.1f}x faster"
        }
    }

    output_file = Path(__file__).parent / f'prediction_mandel_{series_id}_top{top_n}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"💾 Prediction saved to: {output_file}")
    print("=" * 80)

    return results


if __name__ == '__main__':
    # Allow series_id and top_n to be passed as arguments
    series_id = 3149
    top_n = 18  # Default: top 18 numbers

    if len(sys.argv) > 1:
        series_id = int(sys.argv[1])
    if len(sys.argv) > 2:
        top_n = int(sys.argv[2])

    results = generate_mandel_prediction(series_id, top_n)
