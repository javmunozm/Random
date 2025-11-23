#!/usr/bin/env python3
"""
Jackpot Prediction Analysis
1. Plot draw number vs tries (2D graph)
2. Fit curve to predict tries for Series 3153
3. Predict the actual combination for Series 3153
"""

import json
import math
from collections import defaultdict

def predict_series_3153():
    """Predict both tries and combination for Series 3153"""

    # Load jackpot data
    with open('jackpot_finder_results.json', 'r') as f:
        data = json.load(f)

    # Load all series data for pattern analysis
    with open('all_series_data.json', 'r') as f:
        all_data = json.load(f)

    # Extract 2D graph points: (draw_number, tries)
    graph_points = []
    draw_number = 0

    for jackpot in data['jackpots']:
        if jackpot['tries'] is not None:
            series = jackpot['series']
            event = jackpot['event']
            tries = jackpot['tries']
            combination = jackpot['combination']

            # Draw number = continuous numbering of all events
            # Calculate draw number from series
            draw_num = (series - 3135) * 7 + event

            graph_points.append({
                'draw_number': draw_num,
                'series': series,
                'event': event,
                'tries': tries,
                'combination': combination
            })

    # Sort by draw number
    graph_points.sort(key=lambda x: x['draw_number'])

    print("=" * 80)
    print("JACKPOT PREDICTION - SERIES 3153")
    print("2D Graph Analysis: Draw Number vs Tries")
    print("=" * 80)
    print()

    # Print the 2D graph data
    print("2D GRAPH POINTS (X=Draw Number, Y=Tries):")
    print()
    print(f"{'Draw #':<8} {'Series-Event':<15} {'Tries (Y)':<15} {'Combination':<50}")
    print("-" * 80)

    for point in graph_points:
        combo_str = ' '.join(f'{n:02d}' for n in point['combination'])
        print(f"{point['draw_number']:<8} {point['series']}-E{point['event']:<13} "
              f"{point['tries']:<15,} {combo_str}")

    print()
    print("=" * 80)

    # Fit polynomial curve to predict tries for Series 3153
    # Series 3153 draw numbers would be: (3153-3135)*7 + 1 through 7 = 126-132

    n = len(graph_points)
    sum_x = sum(p['draw_number'] for p in graph_points)
    sum_y = sum(p['tries'] for p in graph_points)
    sum_xy = sum(p['draw_number'] * p['tries'] for p in graph_points)
    sum_x2 = sum(p['draw_number'] ** 2 for p in graph_points)

    # Linear regression: y = mx + b
    m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    b = (sum_y - m * sum_x) / n

    print("CURVE FITTING - LINEAR REGRESSION:")
    print()
    print(f"Equation: Y = {m:.2f}X + {b:.2f}")
    print(f"Where X = draw number, Y = tries")
    print()

    # Predict tries for Series 3153
    # Series 3153 starts at draw number 126
    series_3153_draws = []
    for event in range(1, 8):
        draw_num = (3153 - 3135) * 7 + event  # = 126 + event - 1
        predicted_tries = m * draw_num + b
        series_3153_draws.append({
            'event': event,
            'draw_number': draw_num,
            'predicted_tries': max(0, int(predicted_tries))  # Can't be negative
        })

    print("PREDICTED TRIES FOR SERIES 3153:")
    print()
    print(f"{'Event':<8} {'Draw #':<10} {'Predicted Tries':<20}")
    print("-" * 50)
    for pred in series_3153_draws:
        print(f"{pred['event']:<8} {pred['draw_number']:<10} {pred['predicted_tries']:<20,}")

    avg_predicted_tries = sum(p['predicted_tries'] for p in series_3153_draws) / 7
    print()
    print(f"Average predicted tries for Series 3153: {int(avg_predicted_tries):,}")
    print()

    # Now predict the actual COMBINATION using pattern analysis
    print("=" * 80)
    print("PREDICTING COMBINATION FOR SERIES 3153")
    print("=" * 80)
    print()

    # Analyze frequency of numbers in recent jackpots
    recent_jackpots = [p for p in graph_points[-10:]]  # Last 10 jackpots
    number_freq = defaultdict(int)

    for jp in recent_jackpots:
        for num in jp['combination']:
            number_freq[num] += 1

    print("NUMBER FREQUENCY IN RECENT 10 JACKPOTS:")
    print()
    sorted_freq = sorted(number_freq.items(), key=lambda x: x[1], reverse=True)
    for i in range(0, len(sorted_freq), 5):
        row = sorted_freq[i:i+5]
        print("  " + "  ".join(f"{num:02d}:{freq:2d}" for num, freq in row))

    print()

    # Analyze pair affinities in jackpots
    pair_freq = defaultdict(int)
    for jp in recent_jackpots:
        combo = jp['combination']
        for i in range(len(combo)):
            for j in range(i+1, len(combo)):
                pair = tuple(sorted([combo[i], combo[j]]))
                pair_freq[pair] += 1

    top_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    print("TOP 10 NUMBER PAIRS IN RECENT JACKPOTS:")
    print()
    for pair, freq in top_pairs:
        print(f"  {pair[0]:02d}-{pair[1]:02d}: {freq} times")

    print()
    print("=" * 80)

    # Generate prediction based on:
    # 1. High frequency numbers
    # 2. Strong pair affinities
    # 3. Historical patterns

    # Select top 14 most frequent numbers
    top_numbers = [num for num, freq in sorted_freq[:14]]
    predicted_combination = sorted(top_numbers)

    print("PREDICTED COMBINATION FOR SERIES 3153:")
    print()
    print("Based on frequency analysis of recent jackpots:")
    print()
    print("  " + " ".join(f"{num:02d}" for num in predicted_combination))
    print()

    # Calculate confidence based on how recent jackpots match this pattern
    match_scores = []
    for jp in recent_jackpots:
        matches = len(set(jp['combination']) & set(predicted_combination))
        match_scores.append(matches)

    avg_match = sum(match_scores) / len(match_scores)
    confidence = (avg_match / 14) * 100

    print(f"Confidence: {confidence:.1f}%")
    print(f"(Based on average {avg_match:.1f}/14 match with recent jackpots)")
    print()

    # Alternative: Use TrueLearningModel to generate prediction
    print("=" * 80)
    print("ALTERNATIVE: USING ML MODEL (TrueLearningModel)")
    print("=" * 80)
    print()

    try:
        # Try to use TrueLearningModel
        import sys
        sys.path.insert(0, '/home/user/Random/python_ml')
        from true_learning_model import TrueLearningModel

        model = TrueLearningModel(data_file='all_series_data.json')
        ml_prediction = model.predict_best_combination(3153)

        print("ML Model Prediction:")
        print()
        print("  " + " ".join(f"{num:02d}" for num in ml_prediction))
        print()

    except Exception as e:
        print(f"ML model not available: {e}")
        print("Using frequency-based prediction above.")
        ml_prediction = None

    # Final summary
    print("=" * 80)
    print("FINAL PREDICTION SUMMARY FOR SERIES 3153")
    print("=" * 80)
    print()
    print(f"Predicted Average Tries: {int(avg_predicted_tries):,}")
    print()
    print("Predicted Combination (Frequency-based):")
    print("  " + " ".join(f"{num:02d}" for num in predicted_combination))
    print()

    if ml_prediction:
        print("Predicted Combination (ML Model):")
        print("  " + " ".join(f"{num:02d}" for num in ml_prediction))
        print()

    # Save results
    results = {
        'series': 3153,
        'graph_points': graph_points,
        'regression': {
            'slope': m,
            'intercept': b,
            'equation': f'Y = {m:.2f}X + {b:.2f}'
        },
        'predicted_tries': series_3153_draws,
        'avg_predicted_tries': int(avg_predicted_tries),
        'predicted_combination_frequency': predicted_combination,
        'predicted_combination_ml': ml_prediction,
        'confidence': confidence
    }

    with open('series_3153_prediction.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("📁 Results saved to: series_3153_prediction.json")
    print()

    return results

if __name__ == '__main__':
    predict_series_3153()
