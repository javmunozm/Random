#!/usr/bin/env python3
"""
Evaluate Series 3147 Optimized Prediction Performance
"""

import json

# Our optimized prediction
PREDICTION = [1, 2, 3, 5, 6, 9, 10, 13, 15, 19, 21, 22, 23, 25]

# Actual Series 3147 results
ACTUAL_3147 = [
    [1, 3, 5, 7, 10, 12, 14, 15, 17, 18, 20, 21, 22, 25],  # Event 1
    [2, 5, 7, 8, 9, 10, 11, 15, 16, 17, 18, 21, 22, 25],   # Event 2
    [1, 3, 4, 5, 7, 10, 12, 14, 16, 19, 21, 22, 23, 25],   # Event 3
    [1, 2, 3, 4, 7, 10, 11, 13, 14, 16, 18, 19, 23, 25],   # Event 4
    [1, 6, 7, 8, 11, 12, 14, 15, 16, 18, 21, 22, 23, 24],  # Event 5
    [1, 3, 4, 5, 8, 11, 12, 15, 18, 19, 20, 22, 23, 24],   # Event 6
    [6, 7, 10, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25] # Event 7
]


def evaluate_prediction():
    """Evaluate prediction against actual results"""
    print("="*70)
    print("SERIES 3147 - OPTIMIZED PREDICTION EVALUATION")
    print("="*70)
    print()

    print(f"Prediction: {' '.join(f'{n:02d}' for n in PREDICTION)}")
    print()

    # Evaluate each event
    matches = []
    match_counts = []

    print("Event-by-Event Results:")
    print(f"{'Event':<8} {'Matches':<10} {'Match %':<12} {'Matched Numbers'}")
    print("-"*70)

    for i, event in enumerate(ACTUAL_3147, 1):
        matched = set(PREDICTION) & set(event)
        match_count = len(matched)
        match_pct = match_count / 14

        matches.append(match_pct)
        match_counts.append(match_count)

        print(f"Event {i}  {match_count:>2}/14      {match_pct:>6.1%}       "
              f"{' '.join(f'{n:02d}' for n in sorted(matched))}")

    print()

    # Summary statistics
    best_match = max(matches)
    avg_match = sum(matches) / len(matches)
    best_count = max(match_counts)
    avg_count = sum(match_counts) / len(match_counts)

    print("="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    print()
    print(f"Best Match:    {best_count}/14 numbers ({best_match:.1%})")
    print(f"Average Match: {avg_count:.1f}/14 numbers ({avg_match:.1%})")
    print()

    # Compare to expected performance
    print("="*70)
    print("COMPARISON TO OPTIMIZATION STUDY")
    print("="*70)
    print()
    print("Expected (based on Series 3140-3145 validation):")
    print("  - Best Match: 67.857%")
    print("  - Optimized Config: 25x boost")
    print()
    print("Actual (Series 3147):")
    print(f"  - Best Match: {best_match:.3%}")
    print(f"  - Difference: {best_match - 0.67857:+.3%}")
    print()

    if best_match >= 0.67857:
        print("✅ MEETS OR EXCEEDS EXPECTED PERFORMANCE")
    elif best_match >= 0.64:
        print("⚠️  SLIGHTLY BELOW EXPECTED (within normal variance)")
    else:
        print("❌ BELOW EXPECTED PERFORMANCE")
    print()

    # Identify critical numbers
    print("="*70)
    print("CRITICAL NUMBER ANALYSIS")
    print("="*70)
    print()

    # Count frequency of each number across all events
    freq = {}
    for num in range(1, 26):
        count = sum(1 for event in ACTUAL_3147 if num in event)
        freq[num] = count

    # Identify critical numbers (5+ events)
    critical = {num: count for num, count in freq.items() if count >= 5}

    print(f"Critical Numbers (appeared in 5+ events):")
    critical_sorted = sorted(critical.items(), key=lambda x: x[1], reverse=True)
    for num, count in critical_sorted:
        in_pred = "✅" if num in PREDICTION else "❌"
        print(f"  {num:02d}: {count}/7 events {in_pred}")
    print()

    critical_in_pred = sum(1 for num in critical if num in PREDICTION)
    critical_total = len(critical)
    print(f"Critical Hit Rate: {critical_in_pred}/{critical_total} ({critical_in_pred/critical_total*100:.1f}%)")
    print()

    # Identify numbers we predicted that were NOT critical
    non_critical_pred = [num for num in PREDICTION if num not in critical]
    print(f"Non-Critical Numbers in Prediction:")
    for num in non_critical_pred:
        print(f"  {num:02d}: {freq[num]}/7 events")
    print()

    # Save evaluation
    output = {
        "series_id": 3147,
        "prediction": PREDICTION,
        "configuration": "OPTIMIZED (25x boost)",
        "actual_results": ACTUAL_3147,
        "performance": {
            "best_match": f"{best_match:.1%}",
            "best_match_count": f"{best_count}/14",
            "average_match": f"{avg_match:.1%}",
            "average_match_count": f"{avg_count:.1f}/14",
            "event_matches": [f"{m:.1%}" for m in matches]
        },
        "expected_performance": {
            "best_match": "67.857%",
            "difference": f"{best_match - 0.67857:+.3%}"
        },
        "critical_numbers": {
            "total": critical_total,
            "predicted": critical_in_pred,
            "hit_rate": f"{critical_in_pred/critical_total*100:.1f}%",
            "list": critical_sorted
        }
    }

    with open('evaluation_3147_optimized.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Evaluation saved to: evaluation_3147_optimized.json")
    print()


if __name__ == "__main__":
    evaluate_prediction()
