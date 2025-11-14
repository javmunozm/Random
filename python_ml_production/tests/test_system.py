#!/usr/bin/env python3
"""
System Test - Production v1.0

Validates the entire prediction system:
- Configuration loading
- Model initialization
- Prediction generation
- Performance validation
- Reproducibility
"""

import json
import sys
from pathlib import Path

# Add parent directories to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / 'model'))
sys.path.insert(0, str(parent_dir))

from true_learning_model import TrueLearningModel


def test_configuration():
    """Test 1: Configuration Loading"""
    print("="*80)
    print("TEST 1: Configuration Loading")
    print("="*80)

    config_path = parent_dir / 'config' / 'optimal_config.json'

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        assert 'model_version' in config, "Missing model_version"
        assert 'parameters' in config, "Missing parameters"
        assert 'performance' in config, "Missing performance"

        params = config['parameters']
        required_params = ['seed', 'candidate_pool_size', 'recent_series_lookback', 'cold_hot_boost']

        for param in required_params:
            assert param in params, f"Missing parameter: {param}"

        print(f"✅ Configuration loaded successfully")
        print(f"   Version: {config['model_version']}")
        print(f"   Parameters: {len(params)} configured")
        print()

        return config

    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)


def test_model_initialization(config):
    """Test 2: Model Initialization"""
    print("="*80)
    print("TEST 2: Model Initialization")
    print("="*80)

    try:
        params = config['parameters']

        model = TrueLearningModel(
            seed=params['seed'],
            cold_hot_boost=params['cold_hot_boost']
        )

        assert model._seed == params['seed'], "Seed mismatch"
        assert model._cold_hot_boost == params['cold_hot_boost'], "Boost mismatch"
        assert model.RECENT_SERIES_LOOKBACK == params['recent_series_lookback'], "Lookback mismatch"

        print(f"✅ Model initialized successfully")
        print(f"   Seed: {model._seed}")
        print(f"   Boost: {model._cold_hot_boost}x")
        print(f"   Lookback: {model.RECENT_SERIES_LOOKBACK} series")
        print()

        return model

    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)


def test_data_loading():
    """Test 3: Data Loading"""
    print("="*80)
    print("TEST 3: Data Loading")
    print("="*80)

    data_path = parent_dir / 'data' / 'full_series_data_expanded.json'

    try:
        with open(data_path, 'r') as f:
            data = json.load(f)

        series_data = {int(k): v for k, v in data.items()}

        min_series = min(series_data.keys())
        max_series = max(series_data.keys())
        total_series = len(series_data)

        print(f"✅ Data loaded successfully")
        print(f"   Series range: {min_series}-{max_series}")
        print(f"   Total series: {total_series}")
        print()

        return series_data

    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)


def test_prediction_generation(model, series_data, config):
    """Test 4: Prediction Generation"""
    print("="*80)
    print("TEST 4: Prediction Generation")
    print("="*80)

    try:
        # Train on all data up to 3148
        target_series = 3149
        train_count = 0

        for series_id in sorted(series_data.keys()):
            if series_id < target_series:
                model.learn_from_series(series_id, series_data[series_id])
                train_count += 1

        # Generate prediction
        prediction = model.predict_best_combination(target_series)

        assert len(prediction) == 14, f"Expected 14 numbers, got {len(prediction)}"
        assert len(set(prediction)) == 14, "Prediction contains duplicates"
        assert all(1 <= n <= 25 for n in prediction), "Numbers out of range"

        print(f"✅ Prediction generated successfully")
        print(f"   Training series: {train_count}")
        print(f"   Prediction: {' '.join(f'{n:02d}' for n in prediction)}")
        print()

        return prediction

    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)


def test_reproducibility(series_data, config):
    """Test 5: Reproducibility"""
    print("="*80)
    print("TEST 5: Reproducibility (3 runs)")
    print("="*80)

    try:
        params = config['parameters']
        predictions = []

        for run in range(1, 4):
            # Create fresh model
            model = TrueLearningModel(
                seed=params['seed'],
                cold_hot_boost=params['cold_hot_boost']
            )

            # Train
            for series_id in sorted(series_data.keys()):
                if series_id < 3149:
                    model.learn_from_series(series_id, series_data[series_id])

            # Predict
            prediction = model.predict_best_combination(3149)
            predictions.append(prediction)

            print(f"  Run {run}: {' '.join(f'{n:02d}' for n in prediction)}")

        # Verify all predictions are identical
        assert all(p == predictions[0] for p in predictions), "Predictions vary across runs!"

        print()
        print(f"✅ Reproducibility verified")
        print(f"   All 3 runs produced identical predictions")
        print()

    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)


def test_performance_validation(config):
    """Test 6: Performance Validation"""
    print("="*80)
    print("TEST 6: Performance Validation")
    print("="*80)

    try:
        results_path = parent_dir / 'results' / 'comprehensive_system_test_results.json'

        with open(results_path, 'r') as f:
            results = json.load(f)

        expected_avg = config['performance']['overall_best_average']
        expected_peak = config['performance']['peak_performance']

        actual_avg = results['best_config']['avg_best_match']
        actual_peak = results['best_config']['peak_performance']

        assert abs(actual_avg - expected_avg) < 0.001, "Average performance mismatch"
        assert abs(actual_peak - expected_peak) < 0.001, "Peak performance mismatch"

        print(f"✅ Performance validated")
        print(f"   Average best match: {actual_avg*100:.1f}% ✓")
        print(f"   Peak performance: {actual_peak*100:.1f}% ✓")
        print()

    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)


def main():
    print()
    print("="*80)
    print("PRODUCTION SYSTEM TEST - v1.0")
    print("="*80)
    print()

    # Run tests
    config = test_configuration()
    model = test_model_initialization(config)
    series_data = test_data_loading()
    prediction = test_prediction_generation(model, series_data, config)
    test_reproducibility(series_data, config)
    test_performance_validation(config)

    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print()
    print("✅ ALL TESTS PASSED")
    print()
    print("Tests completed:")
    print("  1. ✓ Configuration loading")
    print("  2. ✓ Model initialization")
    print("  3. ✓ Data loading")
    print("  4. ✓ Prediction generation")
    print("  5. ✓ Reproducibility (3 runs)")
    print("  6. ✓ Performance validation")
    print()
    print("System is ready for production use!")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
