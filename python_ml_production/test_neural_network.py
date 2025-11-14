#!/usr/bin/env python3
"""
Test Modern Neural Network vs Traditional ML

Validates neural network approach on 10+ series
Compares to baseline: 73.5% avg, 78.6% peak
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'model'))
sys.path.insert(0, str(Path(__file__).parent / 'improvements'))

from true_learning_model import TrueLearningModel
from neural_network_hybrid import ModernLotteryNN, AdvancedFeatureExtractor


# Series 3144-3148 actual results
SERIES_DATA = {
    3144: [
        [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
        [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
        [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
        [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
        [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
        [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
        [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
    ],
    3145: [
        [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
        [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
        [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
        [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
        [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
        [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
        [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
    ],
    3147: [
        [1, 2, 4, 6, 7, 9, 11, 13, 16, 17, 18, 20, 21, 23],
        [1, 3, 5, 7, 8, 9, 11, 16, 18, 20, 21, 22, 23, 25],
        [1, 2, 3, 6, 7, 8, 10, 11, 14, 16, 18, 20, 21, 23],
        [2, 3, 4, 5, 7, 8, 10, 11, 14, 16, 18, 21, 23, 25],
        [1, 2, 5, 6, 7, 8, 10, 12, 14, 16, 17, 20, 22, 24],
        [2, 3, 4, 7, 9, 11, 14, 15, 16, 18, 19, 21, 22, 23],
        [2, 3, 4, 6, 7, 10, 11, 13, 16, 18, 21, 22, 23, 25],
    ],
    3148: [
        [1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 19, 22, 23, 25],
        [2, 3, 6, 7, 10, 12, 13, 14, 15, 16, 17, 19, 21, 23],
        [1, 2, 4, 5, 6, 8, 10, 12, 14, 15, 17, 18, 20, 22],
        [2, 3, 4, 5, 8, 10, 12, 13, 14, 15, 18, 20, 21, 25],
        [3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 19, 20, 21, 24],
        [2, 3, 4, 5, 9, 10, 12, 14, 15, 16, 17, 18, 22, 25],
        [1, 4, 6, 7, 9, 11, 12, 14, 16, 19, 20, 21, 23, 25],
    ],
}


def load_historical_data():
    """Load all historical data"""
    data_path = Path(__file__).parent / 'data' / 'full_series_data_expanded.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    series_data = {int(k): v for k, v in data.items()}

    # Add recent series
    for series_id, events in SERIES_DATA.items():
        if series_id not in series_data:
            series_data[series_id] = events

    return series_data


def test_traditional_ml(validation_series, historical_data, seed=999):
    """Test traditional ML model (baseline)"""
    print("="*80)
    print("TEST 1: Traditional ML (Baseline)")
    print("="*80)
    print()

    results = []

    for target_series in validation_series:
        # Create fresh model
        model = TrueLearningModel(seed=seed, cold_hot_boost=30.0)

        # Train on all data before target series
        for sid in sorted(historical_data.keys()):
            if sid < target_series:
                model.learn_from_series(sid, historical_data[sid])

        # Generate prediction
        prediction = model.predict_best_combination(target_series)

        # Evaluate
        actual = historical_data[target_series]
        matches = []
        for event in actual:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        results.append({
            'series_id': target_series,
            'best_match': best_match,
            'avg_match': avg_match,
            'prediction': prediction
        })

        print(f"Series {target_series}: Best {best_match*100:.1f}%, Avg {avg_match*100:.1f}%")

    avg_best = sum(r['best_match'] for r in results) / len(results)
    peak = max(r['best_match'] for r in results)

    print()
    print(f"📊 Traditional ML Results:")
    print(f"   Average Best Match: {avg_best*100:.1f}%")
    print(f"   Peak Performance: {peak*100:.1f}%")
    print()

    return {'method': 'Traditional ML', 'avg_best': avg_best, 'peak': peak, 'results': results}


def test_neural_network(validation_series, historical_data, seed=999, epochs=50):
    """Test modern neural network"""
    print("="*80)
    print("TEST 2: Modern Neural Network (Pattern Recognition)")
    print("="*80)
    print()

    feature_extractor = AdvancedFeatureExtractor()
    results = []

    for target_series in validation_series:
        # Extract features
        features = feature_extractor.extract_features(historical_data, target_series, lookback=10)

        # Create and train neural network
        nn = ModernLotteryNN(input_dim=100, hidden_dim=64, output_dim=25, seed=seed)

        # Training data: create binary labels from actual results
        actual = historical_data[target_series]

        # Train on similar historical patterns (simplified)
        # In full implementation, we'd train on many examples
        # For now, we'll use the NN in prediction mode only

        # Generate prediction
        prediction = nn.predict_numbers(features, n_numbers=14)

        # Evaluate
        matches = []
        for event in actual:
            match_count = len(set(prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        results.append({
            'series_id': target_series,
            'best_match': best_match,
            'avg_match': avg_match,
            'prediction': prediction
        })

        print(f"Series {target_series}: Best {best_match*100:.1f}%, Avg {avg_match*100:.1f}%")

    avg_best = sum(r['best_match'] for r in results) / len(results)
    peak = max(r['best_match'] for r in results)

    print()
    print(f"📊 Neural Network Results:")
    print(f"   Average Best Match: {avg_best*100:.1f}%")
    print(f"   Peak Performance: {peak*100:.1f}%")
    print()

    return {'method': 'Neural Network', 'avg_best': avg_best, 'peak': peak, 'results': results}


def test_hybrid_ensemble(validation_series, historical_data, seed=999):
    """Test hybrid ensemble (Traditional ML + Neural Network)"""
    print("="*80)
    print("TEST 3: Hybrid Ensemble (Traditional ML + Neural Network)")
    print("="*80)
    print()

    feature_extractor = AdvancedFeatureExtractor()
    results = []

    for target_series in validation_series:
        # Traditional ML prediction
        ml_model = TrueLearningModel(seed=seed, cold_hot_boost=30.0)
        for sid in sorted(historical_data.keys()):
            if sid < target_series:
                ml_model.learn_from_series(sid, historical_data[sid])
        ml_prediction = ml_model.predict_best_combination(target_series)

        # Neural Network prediction
        features = feature_extractor.extract_features(historical_data, target_series, lookback=10)
        nn = ModernLotteryNN(input_dim=100, hidden_dim=64, output_dim=25, seed=seed)
        nn_prediction = nn.predict_numbers(features, n_numbers=14)

        # Hybrid: Take numbers that appear in both predictions, then fill with ML
        common = set(ml_prediction) & set(nn_prediction)
        ml_only = [n for n in ml_prediction if n not in common]

        # Build hybrid prediction: common + top ML-only numbers
        hybrid_prediction = sorted(list(common) + ml_only[:14-len(common)])[:14]

        # Evaluate
        actual = historical_data[target_series]
        matches = []
        for event in actual:
            match_count = len(set(hybrid_prediction) & set(event))
            matches.append(match_count / 14)

        best_match = max(matches)
        avg_match = sum(matches) / len(matches)

        results.append({
            'series_id': target_series,
            'best_match': best_match,
            'avg_match': avg_match,
            'prediction': hybrid_prediction
        })

        print(f"Series {target_series}: Best {best_match*100:.1f}%, Avg {avg_match*100:.1f}%")
        print(f"  Common numbers: {len(common)}, ML-only: {len(ml_only)}")

    avg_best = sum(r['best_match'] for r in results) / len(results)
    peak = max(r['best_match'] for r in results)

    print()
    print(f"📊 Hybrid Ensemble Results:")
    print(f"   Average Best Match: {avg_best*100:.1f}%")
    print(f"   Peak Performance: {peak*100:.1f}%")
    print()

    return {'method': 'Hybrid Ensemble', 'avg_best': avg_best, 'peak': peak, 'results': results}


def main():
    print("\n")
    print("="*80)
    print("MODERN ML TECHNIQUES EVALUATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    historical_data = load_historical_data()

    # Validation window: Last 10 series
    all_series = sorted(historical_data.keys())
    validation_series = all_series[-10:]  # Last 10 series

    print(f"Validation Series: {validation_series[0]}-{validation_series[-1]} ({len(validation_series)} series)")
    print(f"Training Data: Series {all_series[0]}-{validation_series[0]-1}")
    print()

    # Run tests
    results = []

    # Test 1: Traditional ML (baseline)
    trad_results = test_traditional_ml(validation_series, historical_data)
    results.append(trad_results)

    # Test 2: Modern Neural Network
    nn_results = test_neural_network(validation_series, historical_data)
    results.append(nn_results)

    # Test 3: Hybrid Ensemble
    hybrid_results = test_hybrid_ensemble(validation_series, historical_data)
    results.append(hybrid_results)

    # Comparison
    print("="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print()

    print("Method                          | Avg Best | Peak    | vs Baseline")
    print("--------------------------------|----------|---------|------------")

    baseline_avg = trad_results['avg_best']

    for r in results:
        method = r['method']
        avg = r['avg_best'] * 100
        peak = r['peak'] * 100
        diff = (r['avg_best'] - baseline_avg) * 100

        status = "BASELINE" if method == "Traditional ML" else (f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%")

        print(f"{method:31s} | {avg:7.1f}% | {peak:6.1f}% | {status}")

    print()

    # Recommendations
    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print()

    best_method = max(results, key=lambda x: x['avg_best'])

    if best_method['avg_best'] > baseline_avg + 0.01:  # +1% improvement
        print(f"✅ RECOMMENDED: Use {best_method['method']}")
        print(f"   Performance: {best_method['avg_best']*100:.1f}% avg, {best_method['peak']*100:.1f}% peak")
        print(f"   Improvement: +{(best_method['avg_best'] - baseline_avg)*100:.1f}%")
    else:
        print(f"⚠️  RECOMMENDED: Keep Traditional ML (baseline)")
        print(f"   Neural network did not show significant improvement")
        print(f"   Best alternative: {best_method['method']} ({best_method['avg_best']*100:.1f}%)")

    print()

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'validation_series': validation_series,
        'baseline': baseline_avg,
        'results': results
    }

    output_path = Path(__file__).parent / 'results' / 'neural_network_evaluation.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"📁 Results saved to: {output_path}")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
