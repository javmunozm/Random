#!/usr/bin/env python3
"""
FAST Mandel-Style Systematic Testing
Optimized version with 20,000 candidates
"""

import json
import random
from collections import defaultdict
from datetime import datetime
from true_learning_model import TrueLearningModel


def load_series_data(file_path="full_series_data.json"):
    """Load full series data from JSON"""
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_random_combination():
    """Generate a random 14-number combination"""
    return sorted(random.sample(range(1, 26), 14))


def test_combination_fast(combination, all_series_data, test_series_ids):
    """Fast testing - only track best matches"""
    total_best = 0
    for series_id in test_series_ids:
        actual_events = all_series_data[str(series_id)]
        best_match = max(len(set(combination) & set(event)) for event in actual_events)
        total_best += best_match

    return total_best / len(test_series_ids)


print("=" * 80)
print("FAST MANDEL-STYLE SYSTEMATIC TESTING")
print("20,000 Candidates | Optimized for Speed")
print("=" * 80)
print()

# Load data
all_series_data = load_series_data()
all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

# Test on last 21 series
test_series_ids = [sid for sid in all_series_ids if sid >= 3130 and sid <= 3150]
training_series_ids = [sid for sid in all_series_ids if sid < 3130]

print(f"Training: {len(training_series_ids)} series ({min(training_series_ids)}-{max(training_series_ids)})")
print(f"Testing: {len(test_series_ids)} series ({min(test_series_ids)}-{max(test_series_ids)})")
print()

# Initialize ML model
print("Training ML model (seed=650)...")
model = TrueLearningModel(seed=650)
for series_id in training_series_ids:
    events = all_series_data[str(series_id)]
    model.learn_from_series(series_id, events)
print("✅ Model trained")
print()

# Generate candidates
print("Generating 20,000 candidates...")
candidates = []

# 10k pure random
random.seed(650)  # For reproducibility
for _ in range(10000):
    candidates.append(generate_random_combination())

# 10k ML-guided variations
ml_base = model.predict_best_combination(3151)
for _ in range(10000):
    variant = list(ml_base)
    # Make 1-3 random swaps
    num_swaps = random.randint(1, 3)
    for _ in range(num_swaps):
        idx = random.randint(0, 13)
        new_num = random.randint(1, 25)
        if new_num not in variant:
            variant[idx] = new_num
    candidates.append(sorted(variant))

# Remove duplicates
unique_candidates = list({tuple(c): c for c in candidates}.values())
print(f"✅ Generated {len(unique_candidates)} unique combinations")
print()

# Test all candidates
print("Testing combinations against historical data...")
results = []

for idx, combo in enumerate(unique_candidates, 1):
    score = test_combination_fast(combo, all_series_data, test_series_ids)
    results.append({
        'combination': combo,
        'score': score * 100 / 14  # Convert to percentage
    })

    if idx % 5000 == 0:
        print(f"  {idx}/{len(unique_candidates)} tested...")

print(f"✅ All {len(results)} combinations tested")
print()

# Sort by score
results.sort(key=lambda x: x['score'], reverse=True)

# Statistics
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()

best = results[0]['score']
avg = sum(r['score'] for r in results) / len(results)
median = results[len(results)//2]['score']

print(f"Best score: {best:.2f}%")
print(f"Average: {avg:.2f}%")
print(f"Median: {median:.2f}%")
print()

# Top 10
print("TOP 10 COMBINATIONS:")
print()
for i, r in enumerate(results[:10], 1):
    combo_str = ' '.join(f"{n:02d}" for n in r['combination'])
    marker = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
    print(f"{marker} {combo_str} | Score: {r['score']:.2f}%")

print()

# Predictions
print("=" * 80)
print("PREDICTIONS FOR SERIES 3151")
print("=" * 80)
print()

# Top 3 ensemble
top3 = [r['combination'] for r in results[:3]]
num_freq = defaultdict(int)
for combo in top3:
    for num in combo:
        num_freq[num] += 1

ensemble = sorted([n for n, _ in sorted(num_freq.items(), key=lambda x: (-x[1], x[0]))[:14]])
ensemble_str = ' '.join(f"{n:02d}" for n in ensemble)

# ML model
ml_pred = model.predict_best_combination(3151)
ml_str = ' '.join(f"{n:02d}" for n in ml_pred)

# Hybrid
hybrid_freq = defaultdict(int)
for num in ensemble:
    hybrid_freq[num] += 2
for num in ml_pred:
    hybrid_freq[num] += 1
hybrid = sorted([n for n, _ in sorted(hybrid_freq.items(), key=lambda x: (-x[1], x[0]))[:14]])
hybrid_str = ' '.join(f"{n:02d}" for n in hybrid)

print(f"🏆 BEST HISTORICAL: {' '.join(f'{n:02d}' for n in results[0]['combination'])} ({results[0]['score']:.2f}%)")
print()
print(f"📊 ENSEMBLE (Top 3): {ensemble_str}")
print()
print(f"🤖 ML MODEL (650):   {ml_str}")
print()
print(f"🔀 HYBRID (Ens+ML):  {hybrid_str}")
print()

# Save
output = {
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "candidates_tested": len(results),
    "test_series": test_series_ids,
    "stats": {
        "best": round(best, 2),
        "average": round(avg, 2),
        "median": round(median, 2)
    },
    "top_10": [
        {"rank": i, "combination": r['combination'], "score": round(r['score'], 2)}
        for i, r in enumerate(results[:10], 1)
    ],
    "predictions_3151": {
        "best_historical": results[0]['combination'],
        "ensemble_top3": ensemble,
        "ml_model": ml_pred,
        "hybrid": hybrid
    }
}

with open('mandel_fast_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("=" * 80)
print(f"Best historical score: {best:.2f}%")
print(f"C# baseline: 71.4%")
print(f"Difference: {best - 71.4:+.2f}%")
print()
print("📁 Results saved to: mandel_fast_results.json")
print("✅ COMPLETE!")
