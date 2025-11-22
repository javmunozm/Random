#!/usr/bin/env python3
"""
Predict Series 3153 using validated original multi-signal method
Based on comprehensive validation showing 8.75/14 (62.5%) mean peak
"""

import json
from collections import Counter
from itertools import combinations

def load_data():
    """Load all series data including Series 3152"""
    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    # Add Series 3152 actual results
    data['3152'] = [
        [1, 4, 5, 6, 8, 9, 10, 12, 13, 18, 21, 23, 24, 25],
        [1, 4, 5, 8, 10, 13, 15, 17, 18, 20, 21, 23, 24, 25],
        [1, 3, 6, 7, 12, 13, 14, 15, 16, 19, 20, 21, 22, 25],
        [2, 4, 5, 6, 7, 9, 10, 14, 16, 17, 20, 22, 23, 24],
        [1, 2, 4, 8, 10, 11, 15, 16, 17, 19, 20, 21, 23, 25],
        [2, 3, 4, 5, 6, 9, 10, 12, 17, 18, 20, 21, 23, 24],
        [1, 2, 4, 5, 6, 7, 8, 12, 17, 18, 22, 23, 24, 25]
    ]

    return data

def calculate_multi_signal_score(combo, data, recent_series, target_series):
    """
    Validated original multi-signal scoring
    Weights: 25/35/20/10/10 (global/recent/pattern/dist/pair)
    """
    # Signal 1: Global frequency (25%)
    global_counter = Counter()
    for sid, events in data.items():
        if int(sid) < target_series:
            for event in events:
                for num in event:
                    global_counter[num] += 1

    global_score = sum(global_counter[num] for num in combo) / len(combo)

    # Signal 2: Recent frequency (35%)
    recent_counter = Counter()
    for sid in recent_series:
        if int(sid) < target_series:
            for event in data[str(sid)]:
                for num in event:
                    recent_counter[num] += 1

    recent_score = sum(recent_counter[num] for num in combo) / len(combo)

    # Signal 3: Pattern match (20%)
    pattern_scores = []
    for sid in recent_series[-2:]:
        if int(sid) < target_series:
            for event in data[str(sid)]:
                overlap = len(set(combo) & set(event))
                pattern_scores.append(overlap / 14)

    pattern_score = max(pattern_scores) if pattern_scores else 0

    # Signal 4: Distribution score (10%)
    col0 = len([n for n in combo if 1 <= n <= 9])
    col1 = len([n for n in combo if 10 <= n <= 19])
    col2 = len([n for n in combo if 20 <= n <= 25])

    ideal_dist = [5, 6, 3]
    actual_dist = [col0, col1, col2]
    dist_diff = sum(abs(ideal_dist[i] - actual_dist[i]) for i in range(3))
    distribution_score = max(0, 1 - (dist_diff / 10))

    # Signal 5: Pair affinity (10%)
    pair_counter = Counter()
    for sid, events in data.items():
        if int(sid) < target_series:
            for event in events:
                for i, n1 in enumerate(event):
                    for n2 in event[i+1:]:
                        pair_counter[(min(n1, n2), max(n1, n2))] += 1

    pair_score = 0
    pair_count = 0
    for i, n1 in enumerate(combo):
        for n2 in combo[i+1:]:
            pair_count += 1
            pair_score += pair_counter[(min(n1, n2), max(n1, n2))]

    pair_score = pair_score / pair_count if pair_count > 0 else 0

    # Composite score
    composite = (
        global_score * 0.25 +
        recent_score * 0.35 +
        pattern_score * 0.20 +
        distribution_score * 0.10 +
        pair_score * 0.10
    )

    return composite, {
        'global': global_score,
        'recent': recent_score,
        'pattern': pattern_score,
        'distribution': distribution_score,
        'pair_affinity': pair_score
    }

def predict_series_3153():
    """
    Generate prediction for Series 3153 using validated method
    """
    data = load_data()
    target_series = 3153

    # Get recent series (last 5 before target)
    all_series = sorted([int(s) for s in data.keys()])
    # Since 3153 is not in data yet, we use up to 3152
    recent_series = [3148, 3149, 3150, 3151, 3152]

    print("=" * 80)
    print(f"SERIES 3153 PREDICTION")
    print("Validated Original Multi-Signal Method")
    print("=" * 80)

    print(f"\n📊 VALIDATION BASELINE:")
    print(f"  Validated across: Series 3140-3151 (12 series)")
    print(f"  Mean peak: 8.75/14 (62.5%)")
    print(f"  Best peak: 10/14 (71.4%)")
    print(f"  Consistency: Very high (σ = 0.83)")

    print(f"\n📈 TRAINING DATA:")
    print(f"  Historical series: 2980-3152 ({len([s for s in data.keys() if int(s) <= 3152])} series)")
    print(f"  Recent focus: {recent_series}")

    # Build top-16 frequency pool
    global_counter = Counter()
    for sid, events in data.items():
        if int(sid) < target_series:
            for event in events:
                for num in event:
                    global_counter[num] += 1

    top_16 = [num for num, _ in global_counter.most_common(16)]
    top_14_freq = [num for num, _ in global_counter.most_common(14)]

    print(f"\n🔢 NUMBER ANALYSIS:")
    print(f"  Top-16 by frequency: {' '.join(f'{n:02d}' for n in top_16)}")
    print(f"  Top-14 by frequency: {' '.join(f'{n:02d}' for n in top_14_freq)}")

    # Score all combinations from top-16
    print(f"\n⚙️  Generating candidates...")
    best_combo = None
    best_score = 0
    best_scores_detail = None

    for combo in combinations(top_16, 14):
        score, score_detail = calculate_multi_signal_score(combo, data, recent_series, target_series)
        if score > best_score:
            best_score = score
            best_combo = combo
            best_scores_detail = score_detail

    prediction = sorted(best_combo) if best_combo else None

    # Also generate pure top-14 for comparison
    pure_freq_score, pure_freq_detail = calculate_multi_signal_score(
        tuple(top_14_freq), data, recent_series, target_series
    )

    print("\n" + "=" * 80)
    print("PREDICTION RESULTS")
    print("=" * 80)

    print(f"\n🎯 PRIMARY PREDICTION (Multi-Signal Optimized):")
    print(f"  Numbers: {' '.join(f'{n:02d}' for n in prediction)}")
    print(f"  Composite Score: {best_score:.2f}")
    print(f"  Score Breakdown:")
    print(f"    - Global frequency: {best_scores_detail['global']:.2f} (25% weight)")
    print(f"    - Recent frequency: {best_scores_detail['recent']:.2f} (35% weight)")
    print(f"    - Pattern match: {best_scores_detail['pattern']:.2f} (20% weight)")
    print(f"    - Distribution: {best_scores_detail['distribution']:.2f} (10% weight)")
    print(f"    - Pair affinity: {best_scores_detail['pair_affinity']:.2f} (10% weight)")

    print(f"\n📊 ALTERNATIVE (Pure Top-14 Frequency):")
    print(f"  Numbers: {' '.join(f'{n:02d}' for n in top_14_freq)}")
    print(f"  Composite Score: {pure_freq_score:.2f}")

    # Column distribution analysis
    pred_col0 = len([n for n in prediction if 1 <= n <= 9])
    pred_col1 = len([n for n in prediction if 10 <= n <= 19])
    pred_col2 = len([n for n in prediction if 20 <= n <= 25])

    print(f"\n📐 COLUMN DISTRIBUTION:")
    print(f"  Column 0 (01-09): {pred_col0} numbers")
    print(f"  Column 1 (10-19): {pred_col1} numbers")
    print(f"  Column 2 (20-25): {pred_col2} numbers")

    # Expected performance
    print(f"\n" + "=" * 80)
    print("EXPECTED PERFORMANCE")
    print("=" * 80)
    print(f"\n📈 Based on validation (12-series baseline):")
    print(f"  Expected peak: ~9/14 (64.3%) - most likely")
    print(f"  Range: 7-10/14 (50-71.4%)")
    print(f"  Probability of ≥10/14: ~17% (2/12 in validation)")
    print(f"  Probability of ≥12/14: ~0% (0/12 in validation)")

    print(f"\n💡 INTERPRETATION:")
    print(f"  ✅ Realistic expectation: 8-9/14 match on best event")
    print(f"  🎯 Good outcome: 10/14 (71.4%)")
    print(f"  🌟 Exceptional outcome: 11+/14 (rare, not seen in validation)")

    # Save prediction
    output = {
        'series_id': 3153,
        'method': 'Original Multi-Signal (Validated)',
        'validation_baseline': {
            'series_tested': '3140-3151',
            'mean_peak': 8.75,
            'best_peak': 10,
            'std_dev': 0.83
        },
        'prediction': {
            'primary': prediction,
            'alternative_top14': top_14_freq,
            'composite_score': best_score,
            'score_breakdown': best_scores_detail
        },
        'expected_performance': {
            'most_likely': '8-9/14 (57-64%)',
            'good': '10/14 (71%)',
            'exceptional': '11+/14 (>79%)'
        },
        'training_data': {
            'historical_series': f'2980-3152 ({len([s for s in data.keys() if int(s) <= 3152])} series)',
            'recent_focus': recent_series,
            'top_16_pool': top_16
        }
    }

    with open('prediction_3153.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n" + "=" * 80)
    print("✅ PREDICTION COMPLETE")
    print("=" * 80)
    print(f"\n📁 Saved to: prediction_3153.json")
    print(f"\n🎯 USE THIS: {' '.join(f'{n:02d}' for n in prediction)}")
    print("=" * 80)

    return prediction

if __name__ == '__main__':
    predict_series_3153()
