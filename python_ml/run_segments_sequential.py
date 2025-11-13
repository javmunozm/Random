#!/usr/bin/env python3
"""
Run segments 2, 3, 4, and 5 sequentially for the exhaustive search
"""

import json
import sys
from pathlib import Path
from test_mandel_exhaustive_segmented import (
    load_all_series_data,
    run_segment
)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from true_learning_model import TrueLearningModel


def run_segments_sequential(series_id: int = 3147, segments_to_run: list = [2, 3, 4, 5]):
    """
    Run specific segments sequentially for the exhaustive search
    """
    print("=" * 80)
    print(f"SEQUENTIAL EXHAUSTIVE SEARCH - SEGMENTS {segments_to_run}")
    print("=" * 80)
    print()
    print(f"Target Series: {series_id}")
    print(f"Running segments: {segments_to_run}")
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

    # Define all segments
    total_combos = 4457400
    segment_size = total_combos // 5

    all_segments_def = [
        (1, 0, segment_size),                        # 0 - 891,480
        (2, segment_size, segment_size * 2),         # 891,480 - 1,782,960
        (3, segment_size * 2, segment_size * 3),     # 1,782,960 - 2,674,440
        (4, segment_size * 3, segment_size * 4),     # 2,674,440 - 3,565,920
        (5, segment_size * 4, total_combos),         # 3,565,920 - 4,457,400
    ]

    # Filter to only requested segments
    segments = [(seg_num, start, end) for seg_num, start, end in all_segments_def if seg_num in segments_to_run]

    # Load segment 1 if it exists and we need it for comparison
    all_results = []
    if 1 not in segments_to_run:
        seg1_file = Path(__file__).parent / 'exhaustive_segment_1_results.json'
        if seg1_file.exists():
            with open(seg1_file, 'r') as f:
                seg1_data = json.load(f)
                all_results.append(seg1_data['segment'])
                print("📂 Loaded Segment 1 results from file")
                print()

    # Run each requested segment
    overall_best_score = -float('inf')
    overall_best_combination = None
    overall_best_segment = None

    # Initialize with segment 1 if we have it
    if all_results:
        overall_best_score = all_results[0]['best_score']
        overall_best_combination = all_results[0]['best_combination']
        overall_best_segment = all_results[0]['segment']

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
    print(f"SEGMENTS {segments_to_run} COMPLETE")
    print("=" * 80)
    print()

    total_time = sum(r['time_seconds'] for r in all_results)
    total_scored = sum(r['combinations_scored'] for r in all_results)
    avg_rate = total_scored / total_time if total_time > 0 else 0

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
        'method': 'exhaustive_mandel_segmented_sequential',
        'segments_run': segments_to_run,
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
    # Default: run segments 2, 3, 4, 5
    segments = [2, 3, 4, 5]

    # Allow command line override
    if len(sys.argv) > 1:
        segments = [int(x) for x in sys.argv[1:]]

    results = run_segments_sequential(series_id=3147, segments_to_run=segments)
