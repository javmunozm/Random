#!/usr/bin/env python3
"""
Generate prediction using Segment 1 combinations as the candidate pool

Instead of generating 10,000 random weighted candidates, we use the 891,480
combinations from Segment 1 (0-20% of all combinations) as our pool and
select the best one based on the ML model's scoring.
"""

import json
import sys
import time
from pathlib import Path
from itertools import combinations, islice
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

    return series_dict


def generate_prediction_from_segment1_pool(series_id: int = 3148):
    """
    Generate prediction using Segment 1 combinations as candidate pool

    Args:
        series_id: The series to predict

    Returns:
        dict with prediction and metadata
    """
    print("=" * 80)
    print("PREDICTION FROM SEGMENT 1 POOL")
    print("=" * 80)
    print()
    print(f"Target Series: {series_id}")
    print(f"Candidate Pool: Segment 1 (891,480 combinations)")
    print(f"Method: Exhaustive scoring of all Segment 1 candidates")
    print()

    # Load data
    series_data = load_all_series_data()
    print(f"Loaded {len(series_data)} series for training")
    print()

    # Train model
    print("=" * 80)
    print("TRAINING MODEL")
    print("=" * 80)
    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = 8

    train_count = 0
    for sid in sorted(series_data.keys()):
        if sid < series_id:
            model.learn_from_series(sid, series_data[sid])
            train_count += 1

    print(f"✅ Trained on {train_count} series (up to {series_id-1})")
    print()

    # Generate Segment 1 combinations (0 to 891,479)
    print("=" * 80)
    print("SCORING SEGMENT 1 COMBINATIONS")
    print("=" * 80)
    print()

    segment_size = 891480
    print(f"Generating and scoring {segment_size:,} combinations...")
    print()

    start_time = time.time()

    all_combos = combinations(range(1, 26), 14)
    segment_combos = islice(all_combos, 0, segment_size)

    best_combination = None
    best_score = -float('inf')
    count = 0
    progress_interval = 100000
    next_report = progress_interval

    scoring_start = time.time()

    for combination in segment_combos:
        combo_list = list(combination)
        score = model._calculate_score(combo_list)

        if score > best_score:
            best_score = score
            best_combination = combo_list
            elapsed = time.time() - start_time
            print(f"  🎯 New best: score={score:.2f}, combo={combo_list}, time={elapsed:.1f}s")

        count += 1

        # Progress report
        if count >= next_report:
            elapsed = time.time() - start_time
            rate = count / (time.time() - scoring_start)
            progress_pct = (count / segment_size) * 100
            remaining = (segment_size - count) / rate

            print(f"  Progress: {count:,}/{segment_size:,} ({progress_pct:.1f}%) - "
                  f"{rate:.0f} combos/sec - ETA: {remaining:.1f}s")

            next_report += progress_interval

    end_time = time.time()
    total_time = end_time - start_time

    print()
    print("=" * 80)
    print("SCORING COMPLETE")
    print("=" * 80)
    print(f"Scored: {count:,} combinations")
    print(f"Time: {total_time:.1f} seconds ({total_time/60:.2f} minutes)")
    print(f"Rate: {count/total_time:.0f} combinations/second")
    print()
    print("=" * 80)
    print(f"PREDICTION FOR SERIES {series_id}")
    print("=" * 80)
    print(f"Best combination: {best_combination}")
    print(f"ML Score: {best_score:.4f}")
    print("=" * 80)
    print()

    # Format prediction
    prediction_str = ' '.join([f"{num:02d}" for num in best_combination])
    print(f"📊 PREDICTION: {prediction_str}")
    print()

    # Identify hot/cold numbers (optional - only if methods exist)
    hot_numbers = set()
    cold_numbers = set()

    try:
        if hasattr(model, '_identify_hot_numbers'):
            hot_numbers = model._identify_hot_numbers()
        if hasattr(model, '_identify_cold_numbers'):
            cold_numbers = model._identify_cold_numbers()

        if hot_numbers or cold_numbers:
            print("🔥 Hot numbers identified (last 8 series):")
            print(f"   {sorted(hot_numbers)}")
            print()
            print("❄️  Cold numbers identified (last 8 series):")
            print(f"   {sorted(cold_numbers)}")
            print()

            hot_in_prediction = [n for n in best_combination if n in hot_numbers]
            cold_in_prediction = [n for n in best_combination if n in cold_numbers]

            print(f"✅ Hot numbers in prediction: {hot_in_prediction} ({len(hot_in_prediction)}/14)")
            print(f"✅ Cold numbers in prediction: {cold_in_prediction} ({len(cold_in_prediction)}/14)")
            print()
    except Exception as e:
        print(f"ℹ️  Hot/cold identification skipped: {e}")
        print()

    # Save results
    results = {
        'series_id': series_id,
        'method': 'segment1_pool_exhaustive',
        'model': 'TrueLearningModel-Phase1-Optimized',
        'candidate_pool_size': segment_size,
        'pool_source': 'segment_1_combinations',
        'seed': 999,
        'cold_hot_boost': 30.0,
        'lookback_window': 8,
        'training_series_count': train_count,
        'prediction': best_combination,
        'prediction_formatted': prediction_str,
        'ml_score': best_score,
        'hot_numbers': sorted(hot_numbers) if hot_numbers else [],
        'cold_numbers': sorted(cold_numbers) if cold_numbers else [],
        'scoring_time_seconds': total_time,
        'scoring_rate': count / total_time
    }

    output_file = Path(__file__).parent / f'prediction_segment1_pool_{series_id}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"💾 Prediction saved to: {output_file}")
    print("=" * 80)

    return results


if __name__ == '__main__':
    # Allow series_id to be passed as argument
    series_id = 3148
    if len(sys.argv) > 1:
        series_id = int(sys.argv[1])

    results = generate_prediction_from_segment1_pool(series_id)
