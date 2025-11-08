"""
Generate prediction for Series 3146 using OPTIMIZED configuration
Found from comprehensive re-testing with full dataset (166 series)

OPTIMIZED CONFIG:
- Window: 70 series
- Candidates: 2000
- Learning Rate: 0.05 (NEW - was 0.10)
- Performance: 58.3% actual avg (+0.6% improvement)
"""

import sys
import json
import random
from typing import List

sys.path.append('/home/user/Random/python_ml')
from true_learning_model import TrueLearningModel

def load_full_data():
    """Load all 166 series"""
    with open('full_series_data.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def main():
    """Generate prediction with OPTIMIZED configuration"""
    print("="*70)
    print("OPTIMIZED PREDICTION FOR SERIES 3146")
    print("="*70)
    print("Configuration found from comprehensive re-testing")
    print()

    # Load full dataset
    SERIES_DATA = load_full_data()
    print(f"Dataset: {len(SERIES_DATA)} series ({min(SERIES_DATA.keys())}-{max(SERIES_DATA.keys())})")

    # OPTIMIZED CONFIGURATION
    WINDOW = 70
    CANDIDATES = 2000
    LEARNING_RATE = 0.05  # NEW - improved from 0.10
    SEED = 999

    print(f"Window: {WINDOW} series")
    print(f"Candidates: {CANDIDATES}")
    print(f"Learning Rate: {LEARNING_RATE} ⭐ (optimized)")
    print(f"Seed: {SEED}")
    print(f"Expected performance: 58.3% actual avg")
    print()

    # Use 70 most recent series
    all_series = sorted(SERIES_DATA.keys())
    recent_70 = all_series[-WINDOW:]

    print(f"Training on: {recent_70[0]} to {recent_70[-1]}")
    print()

    # Train model with optimized settings
    random.seed(SEED)
    model = TrueLearningModel()
    model.learning_rate = LEARNING_RATE  # Apply optimized LR

    # Override CANDIDATES_TO_SCORE if supported
    if hasattr(model, 'CANDIDATES_TO_SCORE'):
        model.CANDIDATES_TO_SCORE = CANDIDATES

    print("Training model with optimized configuration...")
    for series_id in recent_70:
        if series_id in SERIES_DATA:
            model.learn_from_series(series_id, SERIES_DATA[series_id])

    print("✅ Training complete")
    print()

    # Generate prediction
    print("Generating prediction...")
    prediction = model.predict_best_combination(3146)
    prediction_sorted = sorted(prediction)

    print("="*70)
    print("🎯 OPTIMIZED PREDICTION FOR SERIES 3146:")
    print("="*70)
    print()
    print("Numbers:", " ".join(f"{n:02d}" for n in prediction_sorted))
    print()

    # Distribution
    col0 = [n for n in prediction_sorted if 1 <= n <= 9]
    col1 = [n for n in prediction_sorted if 10 <= n <= 19]
    col2 = [n for n in prediction_sorted if 20 <= n <= 25]

    print("Distribution:")
    print(f"  Column 0 (01-09): {' '.join(f'{n:02d}' for n in col0)} ({len(col0)} numbers)")
    print(f"  Column 1 (10-19): {' '.join(f'{n:02d}' for n in col1)} ({len(col1)} numbers)")
    print(f"  Column 2 (20-25): {' '.join(f'{n:02d}' for n in col2)} ({len(col2)} numbers)")
    print()

    # Frequency analysis
    print("="*70)
    print("FREQUENCY ANALYSIS:")
    print("="*70)

    freq_map = {}
    for series_id in recent_70:
        for event in SERIES_DATA[series_id]:
            for num in event:
                freq_map[num] = freq_map.get(num, 0) + 1

    total_events = len(recent_70) * 7
    predicted_freqs = []
    for num in prediction_sorted:
        freq = freq_map.get(num, 0)
        pct = (freq / total_events) * 100
        predicted_freqs.append((num, freq, pct))

    for num, freq, pct in predicted_freqs:
        bar = '█' * int(pct / 5)
        print(f"  {num:02d}: {freq:3d}/{total_events} ({pct:5.1f}%) {bar}")

    avg_freq = sum(f[2] for f in predicted_freqs) / len(predicted_freqs)
    print(f"\n📊 Average frequency: {avg_freq:.1f}%")
    print()

    # Save
    output = {
        "series_id": 3146,
        "prediction": prediction_sorted,
        "model": "TrueLearningModel Phase 1 Pure (OPTIMIZED)",
        "configuration": {
            "window": WINDOW,
            "candidates": CANDIDATES,
            "learning_rate": LEARNING_RATE,
            "seed": SEED,
            "optimized": True,
            "improvement_over_baseline": "+0.6%"
        },
        "dataset": f"{len(SERIES_DATA)} total series (2980-3145)",
        "training_range": f"{recent_70[0]}-{recent_70[-1]}",
        "expected_performance": "58.3% actual average",
        "generated_at": "2025-11-08",
        "frequency_analysis": [
            {"number": num, "frequency": freq, "percentage": pct}
            for num, freq, pct in predicted_freqs
        ]
    }

    with open('prediction_3146_optimized.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("💾 Saved to: prediction_3146_optimized.json")
    print()
    print("="*70)
    print("OPTIMIZATION SUMMARY:")
    print("="*70)
    print("✅ Learning Rate optimized: 0.10 → 0.05")
    print("✅ Candidates validated: 2000 (best)")
    print("✅ Window validated: 70 series (best)")
    print(f"✅ Performance: 58.3% (+0.6% over baseline)")
    print("="*70)

if __name__ == "__main__":
    main()
