#!/usr/bin/env python3
"""
Test exhaustive Mandel using 4 separate pool generator instances

Can run all 4 instances sequentially or individually.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from true_learning_model import TrueLearningModel
from mandel_pool_4_instances import MandelPoolGeneratorInstance


def load_all_series_data():
    """Load all series data"""
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
    series_dict[3144] = [[1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25], [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25], [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24], [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25], [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25], [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24], [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25]]
    series_dict[3145] = [[1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25], [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24], [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22], [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25], [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23], [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25], [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21]]
    series_dict[3147] = [[1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23], [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25], [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23], [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25], [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24], [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23], [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25]]

    return series_dict


def run_instance(model: TrueLearningModel, instance_num: int) -> Dict[str, Any]:
    """
    Run one pool generator instance

    Args:
        model: Trained ML model
        instance_num: Instance number (1-4)

    Returns:
        dict with best combination and score for this instance
    """
    print("=" * 80)
    print(f"INSTANCE {instance_num}/4")
    print("=" * 80)

    instance = MandelPoolGeneratorInstance(instance_num)
    instance.info()
    print()

    print(f"🔍 Scoring {instance.total_combinations:,} combinations...")
    print(f"⏱️  Estimated time: ~{instance.total_combinations/7000:.1f} minutes")
    print()

    start_time = time.time()

    best_combination = None
    best_score = -float('inf')
    count = 0
    progress_interval = 100000
    next_report = progress_interval

    for combination in instance.generate_pool():
        score = model._calculate_score(combination)

        if score > best_score:
            best_score = score
            best_combination = combination
            elapsed = time.time() - start_time
            print(f"  🎯 New best: score={score:.2f}, combo={combination[:3]}...{combination[-3:]}")

        count += 1

        # Progress report
        if count >= next_report:
            elapsed = time.time() - start_time
            rate = count / elapsed
            progress_pct = (count / instance.total_combinations) * 100
            remaining = (instance.total_combinations - count) / rate

            print(f"  ⏳ Progress: {count:,}/{instance.total_combinations:,} ({progress_pct:.1f}%) - "
                  f"{rate:.0f} combos/sec - ETA: {remaining:.0f}s")

            next_report += progress_interval

    end_time = time.time()
    total_time = end_time - start_time

    print()
    print("=" * 80)
    print(f"✅ INSTANCE {instance_num} COMPLETE")
    print("=" * 80)
    print(f"Scored: {count:,} combinations")
    print(f"Time: {total_time:.1f}s ({total_time/60:.2f} min)")
    print(f"Rate: {count/total_time:.0f} combos/sec")
    print()
    print(f"Best: {best_combination}")
    print(f"Score: {best_score:.4f}")
    print("=" * 80)
    print()

    return {
        'instance': instance_num,
        'start_idx': instance.start_idx,
        'end_idx': instance.end_idx,
        'combinations_scored': count,
        'best_combination': best_combination,
        'best_score': best_score,
        'time_seconds': total_time,
        'rate': count / total_time
    }


def run_all_instances(series_id: int = 3147, instances_to_run: list = None):
    """
    Run exhaustive search using 4 pool generator instances

    Args:
        series_id: Series to predict
        instances_to_run: List of instance numbers to run (default: [1,2,3,4])
    """
    if instances_to_run is None:
        instances_to_run = [1, 2, 3, 4]

    print("=" * 80)
    print("EXHAUSTIVE MANDEL - 4 POOL GENERATOR INSTANCES")
    print("=" * 80)
    print()
    print(f"Target Series: {series_id}")
    print(f"Instances to run: {instances_to_run}")
    print(f"Total combinations: 4,457,400")
    print()

    # Load data and train model
    print("📚 Loading data...")
    series_data = load_all_series_data()
    print(f"✅ Loaded {len(series_data)} series")
    print()

    print("🧠 Training model...")
    model = TrueLearningModel(seed=999, cold_hot_boost=30.0)
    model.RECENT_SERIES_LOOKBACK = 8

    train_count = 0
    for sid in sorted(series_data.keys()):
        if sid < series_id:
            model.learn_from_series(sid, series_data[sid])
            train_count += 1

    print(f"✅ Trained on {train_count} series")
    print()

    # Run each instance
    all_results = []
    overall_best_score = -float('inf')
    overall_best_combination = None
    overall_best_instance = None

    for instance_num in instances_to_run:
        result = run_instance(model, instance_num)
        all_results.append(result)

        # Track overall best
        if result['best_score'] > overall_best_score:
            overall_best_score = result['best_score']
            overall_best_combination = result['best_combination']
            overall_best_instance = instance_num

        # Save intermediate results
        output_file = Path(__file__).parent / f'exhaustive_instance_{instance_num}_results.json'
        with open(output_file, 'w') as f:
            json.dump({
                'instance_result': result,
                'overall_best_so_far': {
                    'combination': overall_best_combination,
                    'score': overall_best_score,
                    'found_in_instance': overall_best_instance
                }
            }, f, indent=2)

        print(f"💾 Instance {instance_num} saved to: {output_file}")
        print()

    # Final summary
    print()
    print("=" * 80)
    print("🎉 ALL INSTANCES COMPLETE")
    print("=" * 80)
    print()

    total_time = sum(r['time_seconds'] for r in all_results)
    total_scored = sum(r['combinations_scored'] for r in all_results)

    print(f"Total scored: {total_scored:,} combinations")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.2f} min)")
    print(f"Average rate: {total_scored/total_time:.0f} combos/sec")
    print()
    print("=" * 80)
    print("🏆 BEST COMBINATION (ACROSS ALL INSTANCES)")
    print("=" * 80)
    print(f"Combination: {overall_best_combination}")
    print(f"ML Score: {overall_best_score:.4f}")
    print(f"Found in: Instance {overall_best_instance}")
    print("=" * 80)

    # Calculate accuracy
    actual_events = series_data[series_id]
    prediction_set = set(overall_best_combination)

    matches_per_event = []
    for event in actual_events:
        matches = len(prediction_set & set(event))
        matches_per_event.append(matches)

    best_match = max(matches_per_event)

    print()
    print(f"📊 Best match: {best_match}/14 ({best_match/14*100:.1f}%)")
    print(f"   Matches per event: {matches_per_event}")
    print()

    # Save final results
    final_file = Path(__file__).parent / 'exhaustive_4_instances_final.json'
    with open(final_file, 'w') as f:
        json.dump({
            'series_id': series_id,
            'best_combination': overall_best_combination,
            'best_score': overall_best_score,
            'found_in_instance': overall_best_instance,
            'best_match_pct': (best_match / 14) * 100,
            'all_instances': all_results
        }, f, indent=2)

    print(f"💾 Final results: {final_file}")
    print("=" * 80)


if __name__ == '__main__':
    import sys

    # Check if specific instances requested
    if len(sys.argv) > 1:
        instances = [int(arg) for arg in sys.argv[1:]]
        print(f"Running specific instances: {instances}")
        run_all_instances(series_id=3147, instances_to_run=instances)
    else:
        print("Running all 4 instances")
        run_all_instances(series_id=3147)
