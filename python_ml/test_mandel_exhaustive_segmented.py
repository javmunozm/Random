#!/usr/bin/env python3
"""
SEGMENTED EXHAUSTIVE MANDEL TEST
=================================

Run exhaustive search in 5 segments of 20% each to avoid long-running process issues.

Total: 4,457,400 combinations
Each segment: ~891,480 combinations (~2 minutes each)

Segments:
1. 0% - 20%: Combinations 0 to 891,479
2. 20% - 40%: Combinations 891,480 to 1,782,959
3. 40% - 60%: Combinations 1,782,960 to 2,674,439
4. 60% - 80%: Combinations 2,674,440 to 3,565,919
5. 80% - 100%: Combinations 3,565,920 to 4,457,399
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


def run_segment(model: TrueLearningModel, segment_num: int, start_idx: int, end_idx: int) -> dict:
    """
    Run one segment of the exhaustive search

    Args:
        model: Trained ML model
        segment_num: Segment number (1-5)
        start_idx: Starting combination index (inclusive)
        end_idx: Ending combination index (exclusive)

    Returns:
        dict with best combination and score for this segment
    """
    print("=" * 80)
    print(f"SEGMENT {segment_num}/5: Combinations {start_idx:,} to {end_idx-1:,}")
    print("=" * 80)

    segment_size = end_idx - start_idx
    print(f"Processing {segment_size:,} combinations (~{segment_size/7000:.1f} minutes)")
    print()

    start_time = time.time()

    # Generate all combinations
    all_combos = combinations(range(1, 26), 14)

    # Skip to start_idx
    if start_idx > 0:
        print(f"⏩ Skipping to combination {start_idx:,}...")
        skip_start = time.time()
        all_combos = islice(all_combos, start_idx, None)
        skip_time = time.time() - skip_start
        print(f"   Skipped in {skip_time:.2f} seconds")

    # Process this segment
    best_combination = None
    best_score = -float('inf')
    count = 0
    progress_interval = 100000
    next_report = progress_interval

    print(f"\n🔍 Scoring combinations...")
    scoring_start = time.time()

    for combination in islice(all_combos, segment_size):
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
    print(f"SEGMENT {segment_num} COMPLETE")
    print("=" * 80)
    print(f"Scored: {count:,} combinations")
    print(f"Time: {total_time:.1f} seconds ({total_time/60:.2f} minutes)")
    print(f"Rate: {count/total_time:.0f} combinations/second")
    print()
    print(f"Best in segment: {best_combination}")
    print(f"Score: {best_score:.4f}")
    print("=" * 80)
    print()

    return {
        'segment': segment_num,
        'start_idx': start_idx,
        'end_idx': end_idx,
        'combinations_scored': count,
        'best_combination': best_combination,
        'best_score': best_score,
        'time_seconds': total_time,
        'rate': count / total_time
    }


def run_segmented_exhaustive_test(series_id: int = 3147):
    """
    Run complete exhaustive test in 5 segments
    """
    print("=" * 80)
    print("SEGMENTED EXHAUSTIVE MANDEL TEST")
    print("=" * 80)
    print()
    print(f"Target Series: {series_id}")
    print(f"Total Combinations: 4,457,400")
    print(f"Segments: 5 (20% each = ~891,480 per segment)")
    print(f"Estimated Time: ~10 minutes total (~2 min per segment)")
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

    # Define segments
    total_combos = 4457400
    segment_size = total_combos // 5

    segments = [
        (1, 0, segment_size),                        # 0 - 891,480
        (2, segment_size, segment_size * 2),         # 891,480 - 1,782,960
        (3, segment_size * 2, segment_size * 3),     # 1,782,960 - 2,674,440
        (4, segment_size * 3, segment_size * 4),     # 2,674,440 - 3,565,920
        (5, segment_size * 4, total_combos),         # 3,565,920 - 4,457,400
    ]

    # Run each segment
    all_results = []
    overall_best_score = -float('inf')
    overall_best_combination = None
    overall_best_segment = None

    for seg_num, start_idx, end_idx in segments:
        result = run_segment(model, seg_num, start_idx, end_idx)
        all_results.append(result)

        # Track overall best
        if result['best_score'] > overall_best_score:
            overall_best_score = result['best_score']
            overall_best_combination = result['best_combination']
            overall_best_segment = seg_num

        # Save intermediate results after each segment
        intermediate_file = Path(__file__).parent / f'exhaustive_segment_{seg_num}_results.json'
        with open(intermediate_file, 'w') as f:
            json.dump({
                'segment': result,
                'overall_best_so_far': {
                    'combination': overall_best_combination,
                    'score': overall_best_score,
                    'found_in_segment': overall_best_segment
                }
            }, f, indent=2)

        print(f"💾 Segment {seg_num} results saved to: {intermediate_file}")
        print()

    # Final summary
    print()
    print("=" * 80)
    print("EXHAUSTIVE SEARCH COMPLETE - ALL 5 SEGMENTS FINISHED")
    print("=" * 80)
    print()

    total_time = sum(r['time_seconds'] for r in all_results)
    total_scored = sum(r['combinations_scored'] for r in all_results)
    avg_rate = total_scored / total_time

    print(f"Total combinations scored: {total_scored:,}")
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.2f} minutes)")
    print(f"Average rate: {avg_rate:.0f} combinations/second")
    print()
    print("=" * 80)
    print("BEST COMBINATION FOUND (ACROSS ALL SEGMENTS)")
    print("=" * 80)
    print(f"Combination: {overall_best_combination}")
    print(f"ML Score: {overall_best_score:.4f}")
    print(f"Found in: Segment {overall_best_segment}")
    print("=" * 80)
    print()

    # Calculate actual match
    actual_events = series_data[series_id]
    prediction_set = set(overall_best_combination)

    matches_per_event = []
    for event in actual_events:
        event_set = set(event)
        matches = len(prediction_set & event_set)
        matches_per_event.append(matches)

    best_match = max(matches_per_event)
    avg_match = sum(matches_per_event) / len(matches_per_event)

    print("PREDICTION ACCURACY:")
    print(f"Best match: {best_match}/14 ({best_match/14*100:.1f}%)")
    print(f"Average match: {avg_match:.2f}/14 ({avg_match/14*100:.1f}%)")
    print(f"Matches per event: {matches_per_event}")
    print()

    # Save final results
    final_results = {
        'series_id': series_id,
        'method': 'exhaustive_mandel_segmented',
        'total_combinations': total_scored,
        'total_time_seconds': total_time,
        'average_rate': avg_rate,
        'best_combination': overall_best_combination,
        'best_score': overall_best_score,
        'found_in_segment': overall_best_segment,
        'accuracy': {
            'best_match': best_match,
            'best_match_pct': (best_match / 14) * 100,
            'avg_match': avg_match,
            'avg_match_pct': (avg_match / 14) * 100,
            'matches_per_event': matches_per_event
        },
        'segments': all_results
    }

    output_file = Path(__file__).parent / 'exhaustive_segmented_final_results.json'
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"💾 Final results saved to: {output_file}")
    print("=" * 80)

    return final_results


if __name__ == '__main__':
    results = run_segmented_exhaustive_test(series_id=3147)
