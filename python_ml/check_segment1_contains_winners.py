#!/usr/bin/env python3
"""
Check if previous winning combinations are found in Segment 1

This validates whether Segment 1 (first 20% of all combinations) historically
contains the best ML-scored predictions.
"""

import json
from pathlib import Path
from itertools import combinations, islice


def combination_to_index(combo):
    """
    Convert a combination to its index in the sorted list of all combinations

    Args:
        combo: List of 14 numbers from 1-25

    Returns:
        Index (0-based) in the sequence of all C(25,14) combinations
    """
    # Generate all combinations and find the index
    all_combos = combinations(range(1, 26), 14)

    combo_tuple = tuple(sorted(combo))

    for idx, c in enumerate(all_combos):
        if c == combo_tuple:
            return idx

    return -1  # Not found (shouldn't happen for valid combinations)


def check_segment1_contains_winners():
    """
    Check if previous predictions are in Segment 1
    """
    print("=" * 80)
    print("CHECKING IF PREVIOUS WINNERS ARE IN SEGMENT 1")
    print("=" * 80)
    print()
    print("Segment 1 range: Combinations 0 to 891,479 (first 20%)")
    print()

    # Load previous predictions
    predictions_dir = Path(__file__).parent

    # Find all prediction files
    prediction_files = [
        'prediction_3145.json',
        'prediction_3146.json',
        'prediction_3147.json',
        'prediction_3148.json',
    ]

    results = []

    for pred_file in prediction_files:
        pred_path = predictions_dir / pred_file

        if not pred_path.exists():
            print(f"⏭️  {pred_file}: Not found (skipping)")
            continue

        with open(pred_path, 'r') as f:
            pred_data = json.load(f)

        series_id = pred_data.get('series_id')
        prediction = pred_data.get('prediction')

        if not prediction:
            print(f"⏭️  {pred_file}: No prediction field (skipping)")
            continue

        # Find the index of this combination
        print(f"🔍 Checking Series {series_id}...")
        print(f"   Prediction: {prediction}")

        idx = combination_to_index(prediction)

        in_segment1 = (0 <= idx < 891480)

        if idx >= 0:
            percentage = (idx / 4457400) * 100
            print(f"   Index: {idx:,} ({percentage:.2f}% through all combinations)")

            if in_segment1:
                print(f"   ✅ FOUND IN SEGMENT 1")
            else:
                segment = (idx // 891480) + 1
                print(f"   ❌ NOT in Segment 1 (found in Segment {segment})")
        else:
            print(f"   ⚠️  Invalid combination (not found)")

        print()

        results.append({
            'series_id': series_id,
            'prediction': prediction,
            'combination_index': idx,
            'in_segment1': in_segment1,
            'percentage': (idx / 4457400) * 100 if idx >= 0 else None,
            'segment': (idx // 891480) + 1 if idx >= 0 else None
        })

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    in_seg1 = sum(1 for r in results if r['in_segment1'])

    print(f"Total predictions checked: {total}")
    print(f"Found in Segment 1: {in_seg1}/{total} ({in_seg1/total*100:.1f}%)")
    print(f"Found in other segments: {total - in_seg1}/{total}")
    print()

    if in_seg1 == total:
        print("🎯 ALL predictions are in Segment 1!")
        print("   → Segment 1 pool is sufficient for generating predictions")
    elif in_seg1 > 0:
        print(f"⚠️  Only {in_seg1}/{total} predictions in Segment 1")
        print("   → May need to expand pool beyond Segment 1")
    else:
        print("❌ NO predictions found in Segment 1")
        print("   → Segment 1 pool is NOT sufficient")

    print("=" * 80)

    # Save results
    output_file = predictions_dir / 'segment1_winner_check.json'
    with open(output_file, 'w') as f:
        json.dump({
            'segment1_range': {
                'start': 0,
                'end': 891479,
                'size': 891480,
                'percentage': 20.0
            },
            'predictions_checked': results,
            'summary': {
                'total': total,
                'in_segment1': in_seg1,
                'in_other_segments': total - in_seg1,
                'percentage_in_segment1': (in_seg1 / total * 100) if total > 0 else 0
            }
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    return results


if __name__ == '__main__':
    results = check_segment1_contains_winners()
