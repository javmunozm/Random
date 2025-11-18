#!/usr/bin/env python3
"""
Mandel-Style Systematic Testing with ML Optimization
Generate 20,000 candidates and test against historical data to find best performers
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
    """Generate a random 14-number combination from 25 numbers"""
    return sorted(random.sample(range(1, 26), 14))


def calculate_match_score(combination, actual_events):
    """Calculate how well a combination matches actual events"""
    best_match = max(len(set(combination) & set(event)) for event in actual_events)
    avg_match = sum(len(set(combination) & set(event)) for event in actual_events) / len(actual_events)
    return best_match, avg_match


def test_combination_on_history(combination, all_series_data, test_series_ids):
    """Test a single combination against all historical series"""
    total_best = 0
    total_avg = 0
    perfect_matches = 0
    excellent_matches = 0  # 11+ matches
    good_matches = 0  # 10 matches

    for series_id in test_series_ids:
        actual_events = all_series_data[str(series_id)]
        best_match, avg_match = calculate_match_score(combination, actual_events)

        total_best += best_match
        total_avg += avg_match

        if best_match == 14:
            perfect_matches += 1
        elif best_match >= 11:
            excellent_matches += 1
        elif best_match >= 10:
            good_matches += 1

    num_series = len(test_series_ids)
    return {
        'combination': combination,
        'avg_best_match': total_best / num_series,
        'avg_avg_match': total_avg / num_series,
        'total_best': total_best,
        'perfect_14': perfect_matches,
        'excellent_11plus': excellent_matches,
        'good_10plus': good_matches,
        'score': (total_best / num_series) * 100  # Percentage score
    }


def generate_ml_guided_combinations(model, series_id, count):
    """Generate combinations using ML model guidance"""
    combinations = set()

    # Generate candidates with different random states
    for i in range(count):
        # Use model to predict
        prediction = model.predict_best_combination(series_id)
        combinations.add(tuple(prediction))

        # Add slight variations
        if len(combinations) < count:
            # Random swap variations
            for _ in range(3):
                variant = list(prediction)
                if random.random() > 0.5:
                    # Replace random number
                    idx = random.randint(0, 13)
                    new_num = random.randint(1, 25)
                    if new_num not in variant:
                        variant[idx] = new_num
                        combinations.add(tuple(sorted(variant)))

    return [list(c) for c in combinations]


print("=" * 80)
print("MANDEL-STYLE SYSTEMATIC LOTTERY PREDICTION")
print("Testing 20,000 Candidates Against Historical Data")
print("=" * 80)
print()

# Load data
print("Loading historical data...")
all_series_data = load_series_data()
all_series_ids = sorted([int(sid) for sid in all_series_data.keys()])

# Use recent history for testing
test_series_ids = [sid for sid in all_series_ids if sid >= 3130 and sid <= 3150]  # Last 21 series
training_series_ids = [sid for sid in all_series_ids if sid < 3130]

print(f"Training data: Series {min(training_series_ids)} - {max(training_series_ids)} ({len(training_series_ids)} series)")
print(f"Test data: Series {min(test_series_ids)} - {max(test_series_ids)} ({len(test_series_ids)} series)")
print()

# Initialize ML model for guided generation
print("Initializing ML model (seed=650 - best performer)...")
model = TrueLearningModel(seed=650)

# Train model
print("Training model on historical data...")
for series_id in training_series_ids:
    events = all_series_data[str(series_id)]
    model.learn_from_series(series_id, events)
print()

# Generate candidates
print("Generating 20,000 candidate combinations...")
print("-" * 80)
candidates = []

# Strategy 1: Pure random (10,000 candidates)
print("Strategy 1: Generating 10,000 pure random combinations...")
for i in range(10000):
    candidates.append(generate_random_combination())
    if (i + 1) % 2000 == 0:
        print(f"  Generated {i + 1}/10,000 random combinations...")

# Strategy 2: ML-guided (10,000 candidates)
print("\nStrategy 2: Generating 10,000 ML-guided combinations...")
ml_candidates = generate_ml_guided_combinations(model, 3151, 10000)
candidates.extend(ml_candidates[:10000])
print(f"  Generated {len(ml_candidates[:10000])} ML-guided combinations...")

# Remove duplicates
print(f"\nRemoving duplicates...")
unique_candidates = []
seen = set()
for combo in candidates:
    key = tuple(combo)
    if key not in seen:
        seen.add(key)
        unique_candidates.append(combo)

print(f"Unique candidates: {len(unique_candidates)}")
print()

# Test all candidates
print("=" * 80)
print("TESTING CANDIDATES AGAINST HISTORICAL DATA")
print("=" * 80)
print()

results = []
total_candidates = len(unique_candidates)

print(f"Testing {total_candidates} combinations against {len(test_series_ids)} series...")
print("This may take a few minutes...")
print()

for idx, combination in enumerate(unique_candidates, 1):
    result = test_combination_on_history(combination, all_series_data, test_series_ids)
    results.append(result)

    if idx % 2000 == 0:
        print(f"Progress: {idx}/{total_candidates} ({100*idx/total_candidates:.1f}%) - Best so far: {max(r['score'] for r in results):.2f}%")

print()
print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print()

# Sort by score
results.sort(key=lambda x: x['score'], reverse=True)

# Statistics
avg_score = sum(r['score'] for r in results) / len(results)
median_score = results[len(results)//2]['score']
best_score = results[0]['score']
worst_score = results[-1]['score']

print(f"Total candidates tested: {len(results)}")
print(f"Best score: {best_score:.2f}%")
print(f"Average score: {avg_score:.2f}%")
print(f"Median score: {median_score:.2f}%")
print(f"Worst score: {worst_score:.2f}%")
print(f"Score range: {best_score - worst_score:.2f}%")
print()

# Count excellent performers
excellent = [r for r in results if r['excellent_11plus'] > 0]
very_good = [r for r in results if r['good_10plus'] >= 10]

print(f"Combinations with at least one 11+ match: {len(excellent)} ({100*len(excellent)/len(results):.2f}%)")
print(f"Combinations with 10+ matches on 10+ series: {len(very_good)} ({100*len(very_good)/len(results):.2f}%)")
print()

# Top 10 performers
print("=" * 80)
print("TOP 10 BEST PERFORMING COMBINATIONS")
print("=" * 80)
print()

for rank, result in enumerate(results[:10], 1):
    combo = result['combination']
    score = result['score']
    avg_best = result['avg_best_match']
    excellent = result['excellent_11plus']
    good = result['good_10plus']

    marker = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank:2d}."
    combo_str = ' '.join(f"{n:02d}" for n in combo)

    print(f"{marker} Score: {score:.2f}% | Avg: {avg_best:.2f}/14 | 11+: {excellent} | 10+: {good}")
    print(f"    Numbers: {combo_str}")
    print()

# Get ML model prediction for comparison
print("=" * 80)
print("PREDICTION FOR SERIES 3151")
print("=" * 80)
print()

# Use top 3 combinations for ensemble
print("Using TOP 3 combinations from historical testing:")
print()

for i, result in enumerate(results[:3], 1):
    combo = result['combination']
    combo_str = ' '.join(f"{n:02d}" for n in combo)
    print(f"{i}. {combo_str} (Score: {result['score']:.2f}%)")

print()

# Create ensemble prediction
top_combos = [r['combination'] for r in results[:3]]

# Count frequency of each number in top 3
number_freq = defaultdict(int)
for combo in top_combos:
    for num in combo:
        number_freq[num] += 1

# Sort by frequency
sorted_nums = sorted(number_freq.items(), key=lambda x: (-x[1], x[0]))

# Take top 14 numbers
ensemble_prediction = sorted([num for num, freq in sorted_nums[:14]])

print("ENSEMBLE PREDICTION (Top 3 combinations):")
ensemble_str = ' '.join(f"{n:02d}" for n in ensemble_prediction)
print(f"  {ensemble_str}")
print()

# ML Model prediction
ml_prediction = model.predict_best_combination(3151)
ml_str = ' '.join(f"{n:02d}" for n in ml_prediction)
print("ML MODEL PREDICTION (seed=650):")
print(f"  {ml_str}")
print()

# Hybrid: Combine ensemble + ML
hybrid_nums = set(ensemble_prediction + ml_prediction)
hybrid_freq = defaultdict(int)
for num in ensemble_prediction:
    hybrid_freq[num] += 2  # Weight ensemble higher
for num in ml_prediction:
    hybrid_freq[num] += 1

sorted_hybrid = sorted(hybrid_freq.items(), key=lambda x: (-x[1], x[0]))
hybrid_prediction = sorted([num for num, freq in sorted_hybrid[:14]])

hybrid_str = ' '.join(f"{n:02d}" for n in hybrid_prediction)
print("HYBRID PREDICTION (Ensemble + ML):")
print(f"  {hybrid_str}")
print()

# Save results
output = {
    "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "method": "mandel_style_systematic_testing",
    "total_candidates_tested": len(results),
    "test_series": list(test_series_ids),
    "statistics": {
        "best_score": round(best_score, 2),
        "average_score": round(avg_score, 2),
        "median_score": round(median_score, 2),
        "worst_score": round(worst_score, 2),
        "score_range": round(best_score - worst_score, 2)
    },
    "top_10_combinations": [
        {
            "rank": i,
            "combination": r['combination'],
            "score": round(r['score'], 2),
            "avg_best_match": round(r['avg_best_match'], 2),
            "excellent_11plus": r['excellent_11plus'],
            "good_10plus": r['good_10plus']
        }
        for i, r in enumerate(results[:10], 1)
    ],
    "predictions": {
        "ensemble_top3": ensemble_prediction,
        "ml_model_seed650": ml_prediction,
        "hybrid_ensemble_ml": hybrid_prediction
    }
}

with open('mandel_style_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("=" * 80)
print("COMPARISON TO C# BASELINE")
print("=" * 80)
print()

# Test top combination against C# baseline
top_combo_score = results[0]['score']
csharp_baseline_score = 71.4  # C# baseline on similar test

print(f"Top combination score: {top_combo_score:.2f}%")
print(f"C# ML baseline: {csharp_baseline_score:.2f}%")
print(f"Difference: {top_combo_score - csharp_baseline_score:+.2f}%")
print()

if top_combo_score >= csharp_baseline_score:
    print("🎯 SUCCESS: Systematic testing found combinations matching/exceeding ML performance!")
else:
    print("📊 Result: ML model still outperforms pure systematic testing")
    print(f"   This validates the ML approach over brute-force methods")
print()

print("=" * 80)
print("FILES SAVED")
print("=" * 80)
print()
print("📁 mandel_style_results.json - Complete results and predictions")
print()
print("✅ ANALYSIS COMPLETE!")
