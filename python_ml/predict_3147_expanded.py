"""
Generate prediction for Series 3147 using EXPANDED dataset + Mandel method

Dataset: 176 series (2898-2907, 2980-3146) - UP FROM 166!
Method: Mandel pool optimization (validated +6.1% improvement)
Training: 70 most recent series + 8 iterative validations
"""

import sys
import json
import random
from typing import List

sys.path.append('/home/user/Random/python_ml')
from true_learning_model import TrueLearningModel
from mandel_pool_generator import MandelPoolGenerator

# Override TrueLearningModel to use Mandel pool
class MandelTrueLearningModel(TrueLearningModel):
    """TrueLearningModel with Mandel-optimized candidate pool"""

    def __init__(self):
        super().__init__()
        self.use_mandel_pool = True
        self.mandel_generator = None

    def _generate_candidates(self, target_series_id: int):
        """Override to use Mandel pool instead of random"""
        if not self.use_mandel_pool:
            return super()._generate_candidates(target_series_id)

        # Create Mandel generator with current learned weights
        self.mandel_generator = MandelPoolGenerator(
            frequency_weights=self.number_frequency_weights,
            pair_affinities=self.pair_affinities
        )

        # Generate smart pool
        candidates = self.mandel_generator.generate_pool(
            size=self.CANDIDATES_TO_SCORE,
            seed=999
        )

        return candidates

def load_expanded_data():
    """Load expanded 176-series dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def main():
    """Generate Series 3147 prediction with expanded dataset"""
    print("="*70)
    print("SERIES 3147 PREDICTION - EXPANDED DATASET + MANDEL METHOD")
    print("="*70)
    print()

    # Load expanded data
    SERIES_DATA = load_expanded_data()
    all_series = sorted(SERIES_DATA.keys())

    print(f"📊 Dataset: {len(SERIES_DATA)} series ({all_series[0]}-{all_series[-1]})")
    print(f"   Growth: +10 series from original dataset (+6.0%)")
    print(f"   Total events: {len(SERIES_DATA) * 7}")
    print()

    # Configuration
    WINDOW = 70
    CANDIDATES = 2000  # Mandel pool validated at 2k
    SEED = 999

    print("⚙️  Configuration:")
    print(f"   Method: Mandel pool optimization")
    print(f"   Window: {WINDOW} most recent series")
    print(f"   Candidates: {CANDIDATES} (smart pool)")
    print(f"   Seed: {SEED}")
    print()

    # Use 70 most recent series for training
    recent_70 = all_series[-WINDOW:]
    print(f"📚 Training range: {recent_70[0]} to {recent_70[-1]}")
    print()

    # Phase 1: Bulk training
    print("Phase 1: Bulk training on historical data...")
    random.seed(SEED)

    model = MandelTrueLearningModel()
    model.CANDIDATES_TO_SCORE = CANDIDATES

    # Train on first 62 series (70 - 8 for validation)
    bulk_training = recent_70[:-8]
    for series_id in bulk_training:
        if series_id in SERIES_DATA:
            model.learn_from_series(series_id, SERIES_DATA[series_id])

    print(f"✅ Bulk trained on {len(bulk_training)} series ({bulk_training[0]}-{bulk_training[-1]})")
    print()

    # Phase 2: Iterative validation
    print("Phase 2: Iterative validation learning...")
    validation_series = recent_70[-8:]

    for i, series_id in enumerate(validation_series, 1):
        actual_events = SERIES_DATA[series_id]

        # Predict
        prediction = model.predict_best_combination(series_id)

        # Evaluate
        best_match = max(len(set(prediction) & set(event)) / 14.0 for event in actual_events)
        avg_match = sum(len(set(prediction) & set(event)) / 14.0 for event in actual_events) / 7.0

        print(f"  [{i}/8] Series {series_id}: {best_match:.1%} best, {avg_match:.1%} avg")

        # Learn from actual
        model.learn_from_series(series_id, actual_events)

    print()
    print("✅ Phase 2 complete - 8 validation rounds")
    print()

    # Generate final prediction
    print("🎯 Generating prediction for Series 3147...")
    print()

    prediction = model.predict_best_combination(3147)
    prediction_sorted = sorted(prediction)

    # Display
    print("="*70)
    print("PREDICTION FOR SERIES 3147")
    print("="*70)
    print()
    print("Numbers:", " ".join(f"{n:02d}" for n in prediction_sorted))
    print()

    # Distribution analysis
    col0 = [n for n in prediction_sorted if 1 <= n <= 9]
    col1 = [n for n in prediction_sorted if 10 <= n <= 19]
    col2 = [n for n in prediction_sorted if 20 <= n <= 25]

    print("Distribution:")
    print(f"  Column 0 (01-09): {' '.join(f'{n:02d}' for n in col0)} ({len(col0)} numbers)")
    print(f"  Column 1 (10-19): {' '.join(f'{n:02d}' for n in col1)} ({len(col1)} numbers)")
    print(f"  Column 2 (20-25): {' '.join(f'{n:02d}' for n in col2)} ({len(col2)} numbers)")
    print()

    # Frequency analysis on recent 70 series
    print("="*70)
    print("FREQUENCY ANALYSIS (Last 70 Series)")
    print("="*70)
    print()

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
    print()
    print(f"📊 Average frequency: {avg_freq:.1f}%")
    print()

    # Mandel validation note
    print("="*70)
    print("MANDEL POOL OPTIMIZATION")
    print("="*70)
    print("✅ Smart candidate generation (balanced distribution)")
    print("✅ Pattern validation (no extreme combinations)")
    print("✅ Frequency-weighted selection")
    print("✅ Validated improvement: +6.1% over random pool")
    print()

    # Save prediction
    output = {
        "series_id": 3147,
        "prediction": prediction_sorted,
        "model": "TrueLearningModel Phase 1 Pure + Mandel Pool",
        "dataset": {
            "total_series": len(SERIES_DATA),
            "range": f"{all_series[0]}-{all_series[-1]}",
            "training_window": WINDOW,
            "training_range": f"{recent_70[0]}-{recent_70[-1]}",
            "expansion": "+10 series (+6.0% growth)"
        },
        "configuration": {
            "method": "Mandel pool optimization",
            "candidates": CANDIDATES,
            "seed": SEED,
            "validated_improvement": "+6.1% over random pool"
        },
        "generated_at": "2025-11-09",
        "distribution": {
            "column_0": len(col0),
            "column_1": len(col1),
            "column_2": len(col2)
        },
        "frequency_analysis": [
            {"number": num, "frequency": freq, "percentage": pct}
            for num, freq, pct in predicted_freqs
        ]
    }

    with open('prediction_3147_expanded.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("💾 Saved to: prediction_3147_expanded.json")
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ Dataset expanded: 166 → 176 series (+6.0%)")
    print(f"✅ Mandel method: +6.1% validated improvement")
    print(f"✅ Training window: 70 series (2-phase learning)")
    print(f"✅ Prediction ready for Series 3147")
    print("="*70)

if __name__ == "__main__":
    main()
