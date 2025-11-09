"""
Test Mandel Pool vs Random Pool on Series 3146

We have actual results for Series 3146, so we can test:
1. Random pool (current method) - we know this got 48.0%
2. Mandel pool (new method) - will it do better?

This is the REAL test of whether Mandel optimization works.
"""

import sys
import json
import random
from typing import List, Dict

sys.path.append('/home/user/Random/python_ml')
from true_learning_model import TrueLearningModel
from mandel_pool_generator import MandelPoolGenerator

# Actual results for Series 3146
ACTUAL_3146 = [
    [3, 4, 5, 6, 7, 9, 11, 13, 14, 17, 18, 20, 23, 25],
    [1, 2, 3, 4, 7, 8, 9, 11, 12, 13, 17, 18, 21, 24],
    [3, 4, 7, 8, 10, 11, 12, 13, 16, 17, 18, 19, 20, 22],
    [1, 2, 5, 6, 7, 9, 10, 12, 15, 17, 21, 23, 24, 25],
    [1, 3, 4, 6, 7, 8, 10, 12, 13, 16, 17, 19, 21, 22],
    [3, 4, 6, 7, 8, 12, 14, 15, 16, 17, 18, 19, 21, 22],
    [1, 6, 7, 9, 10, 12, 13, 14, 16, 17, 18, 22, 24, 25]
]

def load_full_data():
    """Load all 166 series"""
    with open('full_series_data.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def evaluate_prediction(prediction, actual_events):
    """Evaluate a prediction against actual events"""
    results = []
    for i, event in enumerate(actual_events, 1):
        matches = len(set(prediction) & set(event))
        accuracy = matches / 14.0
        results.append({
            "event": i,
            "matches": matches,
            "accuracy": accuracy
        })

    best_accuracy = max(r["accuracy"] for r in results)
    avg_accuracy = sum(r["accuracy"] for r in results) / len(results)

    return {
        "results": results,
        "best_accuracy": best_accuracy,
        "avg_accuracy": avg_accuracy
    }

class MandelTrueLearningModel(TrueLearningModel):
    """Enhanced model with Mandel pool generation"""

    def __init__(self, use_mandel_pool=True):
        super().__init__()
        self.use_mandel_pool = use_mandel_pool
        self.mandel_generator = None

    def _generate_candidates(self, target_series_id: int) -> List[List[int]]:
        """
        Override to use Mandel pool generation instead of random
        """
        if self.use_mandel_pool:
            # Initialize Mandel generator with learned weights
            self.mandel_generator = MandelPoolGenerator(
                frequency_weights=self.number_frequency_weights,
                pair_affinities=self.pair_affinities
            )

            # Generate Mandel pool
            candidate_pool = self.mandel_generator.generate_pool(
                size=self.CANDIDATES_TO_SCORE,
                seed=999  # Use consistent seed
            )
            return candidate_pool
        else:
            # Use parent's random generation
            return super()._generate_candidates(target_series_id)

def test_configuration(use_mandel, pool_size, learning_rate):
    """Test a configuration on Series 3146"""

    # Load data
    SERIES_DATA = load_full_data()

    # Use 70 most recent series for training (up to 3145)
    all_series = sorted(SERIES_DATA.keys())
    training_series = all_series[-71:-1]  # Up to 3145, exclude 3146

    # Train model
    random.seed(999)
    model = MandelTrueLearningModel(use_mandel_pool=use_mandel)
    model.learning_rate = learning_rate
    model.CANDIDATES_TO_SCORE = pool_size

    for series_id in training_series:
        if series_id in SERIES_DATA:
            model.learn_from_series(series_id, SERIES_DATA[series_id])

    # Predict Series 3146
    prediction = model.predict_best_combination(3146)

    # Evaluate
    eval_result = evaluate_prediction(prediction, ACTUAL_3146)

    return {
        "prediction": prediction,
        "best_accuracy": eval_result["best_accuracy"],
        "avg_accuracy": eval_result["avg_accuracy"],
        "event_results": eval_result["results"]
    }

def main():
    """Compare Mandel vs Random pools on Series 3146"""
    print("="*70)
    print("MANDEL POOL TEST ON SERIES 3146 (ACTUAL RESULTS)")
    print("="*70)
    print()

    configs_to_test = [
        # Original configurations
        {"name": "Random 2k, LR=0.10", "mandel": False, "pool": 2000, "lr": 0.10},
        {"name": "Random 2k, LR=0.05", "mandel": False, "pool": 2000, "lr": 0.05},
        {"name": "Random 10k, LR=0.10", "mandel": False, "pool": 10000, "lr": 0.10},

        # Mandel configurations
        {"name": "Mandel 2k, LR=0.10", "mandel": True, "pool": 2000, "lr": 0.10},
        {"name": "Mandel 2k, LR=0.05", "mandel": True, "pool": 2000, "lr": 0.05},
        {"name": "Mandel 5k, LR=0.10", "mandel": True, "pool": 5000, "lr": 0.10},
    ]

    results = []

    for config in configs_to_test:
        print(f"Testing: {config['name']}...")
        result = test_configuration(
            use_mandel=config['mandel'],
            pool_size=config['pool'],
            learning_rate=config['lr']
        )

        result['config'] = config
        results.append(result)

        print(f"  Prediction: {' '.join(f'{n:02d}' for n in result['prediction'])}")
        print(f"  Best match: {result['best_accuracy']:.1%}")
        print(f"  Average: {result['avg_accuracy']:.1%}")
        print()

    # Summary
    print("="*70)
    print("RESULTS SUMMARY:")
    print("="*70)
    print()

    # Sort by average accuracy
    results.sort(key=lambda x: x['avg_accuracy'], reverse=True)

    print(f"{'Configuration':<30} {'Best':<10} {'Average':<10}")
    print("-" * 70)
    for r in results:
        name = r['config']['name']
        print(f"{name:<30} {r['best_accuracy']:>8.1%}  {r['avg_accuracy']:>8.1%}")

    print()
    print("="*70)
    print("WINNER:")
    print("="*70)
    winner = results[0]
    print(f"Config: {winner['config']['name']}")
    print(f"Average: {winner['avg_accuracy']:.1%}")
    print(f"Prediction: {' '.join(f'{n:02d}' for n in winner['prediction'])}")
    print()

    # Compare to C# (62.2%)
    print("Comparison to C# (62.2% average):")
    if winner['avg_accuracy'] > 0.622:
        print(f"✅ BEATS C# by {(winner['avg_accuracy'] - 0.622)*100:+.1f}%!")
    elif winner['avg_accuracy'] > 0.60:
        print(f"⚠️  Close to C#: {(winner['avg_accuracy'] - 0.622)*100:+.1f}%")
    else:
        print(f"❌ Still below C#: {(winner['avg_accuracy'] - 0.622)*100:+.1f}%")

    print()

    # Mandel vs Random comparison
    print("="*70)
    print("MANDEL VS RANDOM:")
    print("="*70)

    mandel_results = [r for r in results if r['config']['mandel']]
    random_results = [r for r in results if not r['config']['mandel']]

    best_mandel = max(mandel_results, key=lambda x: x['avg_accuracy'])
    best_random = max(random_results, key=lambda x: x['avg_accuracy'])

    print(f"\nBest Mandel: {best_mandel['config']['name']}")
    print(f"  Performance: {best_mandel['avg_accuracy']:.1%}")
    print()
    print(f"Best Random: {best_random['config']['name']}")
    print(f"  Performance: {best_random['avg_accuracy']:.1%}")
    print()

    diff = best_mandel['avg_accuracy'] - best_random['avg_accuracy']
    if diff > 0.01:
        print(f"✅ Mandel WINS by {diff*100:+.1f}%!")
    elif diff > -0.01:
        print(f"🤝 Roughly EQUAL ({diff*100:+.1f}%)")
    else:
        print(f"❌ Random WINS by {-diff*100:+.1f}%")

    # Save results
    with open('mandel_test_3146_results.json', 'w') as f:
        json.dump([{
            'config': r['config'],
            'prediction': r['prediction'],
            'best_accuracy': r['best_accuracy'],
            'avg_accuracy': r['avg_accuracy']
        } for r in results], f, indent=2)

    print("\n💾 Results saved to: mandel_test_3146_results.json")
    print("="*70)

if __name__ == "__main__":
    main()
