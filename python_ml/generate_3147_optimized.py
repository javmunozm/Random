#!/usr/bin/env python3
"""
Generate Series 3147 Prediction - OPTIMIZED Configuration

Uses newly optimized 25x cold/hot boost (was 50x)
Expected improvement: +1.19% over previous configuration
"""

import json
from datetime import datetime
from true_learning_model import TrueLearningModel


def load_data():
    """Load full historical dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def main():
    print("="*70)
    print("SERIES 3147 PREDICTION - OPTIMIZED CONFIGURATION")
    print("="*70)
    print()
    print("Configuration:")
    print("  - Cold/Hot Boost: 25x (OPTIMIZED, was 50x)")
    print("  - Pool Size: 10,000")
    print("  - Seed: 999")
    print("  - Expected Improvement: +1.19%")
    print()

    # Load all historical data
    SERIES_DATA = load_data()
    all_series = sorted(SERIES_DATA.keys())

    print(f"Training Data:")
    print(f"  - Total Series: {len(all_series)} ({min(all_series)}-{max(all_series)})")
    print(f"  - Training on: Series {min(all_series)}-3145")
    print()

    # Create model with OPTIMIZED configuration (25x boost is now default)
    model = TrueLearningModel(seed=999)

    print(f"Model Configuration:")
    print(f"  - Cold/Hot Boost: {model._cold_hot_boost}x (optimized)")
    print(f"  - Pool Size: {model.CANDIDATE_POOL_SIZE}")
    print(f"  - Seed: {model._seed}")
    print()

    # Train on ALL historical data
    print("Training model...")
    for series_id in all_series:
        model.learn_from_series(series_id, SERIES_DATA[series_id])

    print(f"✅ Training complete: {len(all_series)} series processed")
    print()

    # Check cold/hot activation
    print("Cold/Hot Strategy:")
    print(f"  - Cold Numbers: {sorted(model.hybrid_cold_numbers)}")
    print(f"  - Hot Numbers: {sorted(model.hybrid_hot_numbers)}")
    print(f"  - Total: {len(model.hybrid_cold_numbers) + len(model.hybrid_hot_numbers)}/25 numbers")
    print()

    # Generate prediction
    print("Generating prediction...")
    prediction = model.predict_best_combination(3147)

    print()
    print("="*70)
    print("SERIES 3147 PREDICTION")
    print("="*70)
    print()
    print("Prediction (14 numbers):")
    print(f"  {' '.join(f'{n:02d}' for n in prediction)}")
    print()

    # Count cold/hot in prediction
    cold_hot_in_pred = sum(1 for n in prediction
                           if n in model.hybrid_cold_numbers or n in model.hybrid_hot_numbers)
    print(f"Cold/Hot Usage: {cold_hot_in_pred}/14 numbers ({cold_hot_in_pred/14*100:.1f}%)")
    print()

    # Expected performance based on optimization study
    print("Expected Performance (based on validation):")
    print("  - Baseline (50x boost): 66.667% avg, 78.6% peak")
    print("  - Optimized (25x boost): 67.857% avg, 78.6% peak")
    print("  - Improvement: +1.19%")
    print()

    # Save prediction
    output = {
        "series_id": 3147,
        "prediction": prediction,
        "model_type": "TrueLearningModel Phase 1 Pure (OPTIMIZED)",
        "configuration": {
            "cold_hot_boost": model._cold_hot_boost,
            "pool_size": model.CANDIDATE_POOL_SIZE,
            "seed": model._seed,
            "optimization": "25x boost (was 50x)"
        },
        "cold_hot_strategy": {
            "cold_numbers": sorted(model.hybrid_cold_numbers),
            "hot_numbers": sorted(model.hybrid_hot_numbers),
            "usage_in_prediction": cold_hot_in_pred,
            "usage_percentage": f"{cold_hot_in_pred/14*100:.1f}%"
        },
        "training_data": {
            "total_series": len(all_series),
            "range": f"{min(all_series)}-{max(all_series)}",
            "total_events": len(all_series) * 7
        },
        "expected_performance": {
            "avg_best_match": "67.857%",
            "peak_performance": "78.6%",
            "improvement_vs_baseline": "+1.19%"
        },
        "generated_at": datetime.now().isoformat(),
        "optimization_study": "November 10, 2025 - Comprehensive Pool Optimization"
    }

    output_file = "prediction_3147_optimized.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Prediction saved to: {output_file}")
    print()
    print("="*70)
    print("READY FOR SERIES 3147")
    print("="*70)
    print()
    print("Next Steps:")
    print("  1. Wait for Series 3147 actual results")
    print("  2. Validate +1.19% improvement vs previous predictions")
    print("  3. Continue monitoring optimized performance")


if __name__ == "__main__":
    main()
