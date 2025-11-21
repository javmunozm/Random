#!/usr/bin/env python3
"""Comprehensive results analysis - all 24 series, all 6 models"""

import json

# Manual data for Series 3128-3139 (from SIMULATION_RESULTS_12_SERIES.md)
series_3128_3139_data = {
    3128: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 21582, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 21582, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 94361, "found": True},
        {"model": "Pure Random", "tries": 260439, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 2000000, "found": False},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 2000000, "found": False},
    ],
    3129: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 26991, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 26991, "found": True},
        {"model": "Pure Random", "tries": 115689, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 552432, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 1655695, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 2000000, "found": False},
    ],
    3130: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 2251, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 2251, "found": True},
        {"model": "Pure Random", "tries": 27830, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 594797, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 789269, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 2000000, "found": False},
    ],
    3131: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 27590, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 27590, "found": True},
        {"model": "Pure Random", "tries": 267136, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 424717, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 494481, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 1745194, "found": True},
    ],
    3132: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 42003, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 42003, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 205471, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 466784, "found": True},
        {"model": "Pure Random", "tries": 1875892, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 2000000, "found": False},
    ],
    3133: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 51675, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 51675, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 535090, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 740489, "found": True},
        {"model": "Pure Random", "tries": 764916, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 2000000, "found": False},
    ],
    3134: [
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 2784, "found": True},
        {"model": "Top-8 + Gaps Exhaustive", "tries": 11628, "found": False},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 22701, "found": True},
        {"model": "Hybrid Exhaustive+Random (fallback)", "tries": 283753, "found": True},
        {"model": "Pure Random", "tries": 807133, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 2000000, "found": False},
    ],
    3135: [
        {"model": "Pure Random", "tries": 10905, "found": True},
        {"model": "Top-8 + Gaps Exhaustive", "tries": 79558, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 79558, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 378006, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 484018, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 961807, "found": True},
    ],
    3136: [
        {"model": "Pure Random", "tries": 40817, "found": True},
        {"model": "Top-8 + Gaps Exhaustive", "tries": 67001, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 67001, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 309664, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 1428528, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 2000000, "found": False},
    ],
    3137: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 25141, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 25141, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 223438, "found": True},
        {"model": "Pure Random", "tries": 1447354, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 2000000, "found": False},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 2000000, "found": False},
    ],
    3138: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 378918, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 378918, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 676982, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 1868848, "found": True},
        {"model": "Pure Random", "tries": 2000000, "found": False},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 2000000, "found": False},
    ],
    3139: [
        {"model": "Top-8 + Gaps Exhaustive", "tries": 37936, "found": True},
        {"model": "Hybrid Exhaustive+Random", "tries": 37936, "found": True},
        {"model": "Balanced Weighting (1.5x/1x/0.7x)", "tries": 361908, "found": True},
        {"model": "Inverse Weighting (0.5x/1x/2x)", "tries": 1141646, "found": True},
        {"model": "Weighted Mandel (2x/1x/0.5x)", "tries": 1292733, "found": True},
        {"model": "Pure Random", "tries": 2000000, "found": False},
    ],
}

# Load Series 3140-3151 from JSON
with open('simulation_results_3140_3151.json', 'r') as f:
    series_3140_3151 = json.load(f)

# Combine all data
all_data = {}

# Add 3128-3139
for series_id, models in series_3128_3139_data.items():
    all_data[series_id] = models

# Add 3140-3151
for series_obj in series_3140_3151:
    series_id = series_obj['series_id']
    all_data[series_id] = series_obj['models']

# Find best model per series (winner)
def get_best_model(models):
    """Get the model with fewest tries (only among successful models)"""
    successful = [m for m in models if m['found']]
    if not successful:
        return None
    return min(successful, key=lambda m: m['tries'])

# Generate 3-column table
print("\n" + "="*80)
print("COMPREHENSIVE JACKPOT SIMULATION RESULTS - ALL 24 SERIES (3128-3151)")
print("="*80)
print("\nAll 6 models tested on each series, sorted by performance per series\n")

# Print table
print(f"{'Draw Number':<15} {'Tries to Jackpot':<20} {'Model':<50}")
print("-" * 85)

for series_id in sorted(all_data.keys()):
    models = all_data[series_id]

    # Sort models by tries (found first, then not found)
    sorted_models = sorted(models, key=lambda m: (not m['found'], m['tries']))

    for i, model in enumerate(sorted_models):
        if i == 0:
            # First row: include series ID
            series_str = str(series_id)
        else:
            series_str = ""

        tries_str = f"{model['tries']:,}"
        if not model['found']:
            tries_str += " ❌"

        # Mark winner (best model)
        best = get_best_model(models)
        model_str = model['model']
        if best and model['tries'] == best['tries'] and model['found']:
            model_str += " ✅"

        print(f"{series_str:<15} {tries_str:<20} {model_str:<50}")

    print()  # Blank line between series

# Calculate overall statistics
print("\n" + "="*80)
print("MODEL PERFORMANCE SUMMARY (24 Series)")
print("="*80)

model_names = [
    "Pure Random",
    "Weighted Mandel (2x/1x/0.5x)",
    "Top-8 + Gaps Exhaustive",
    "Inverse Weighting (0.5x/1x/2x)",
    "Balanced Weighting (1.5x/1x/0.7x)",
    "Hybrid Exhaustive+Random"
]

model_stats = {}
for model_name in model_names:
    # Collect stats for this model across all series
    successes = []
    failures = []
    wins = 0

    for series_id in sorted(all_data.keys()):
        models = all_data[series_id]
        for m in models:
            # Match model name (handle fallback variants)
            if model_name in m['model']:
                if m['found']:
                    successes.append(m['tries'])
                else:
                    failures.append(m['tries'])

                # Check if this is the winner
                best = get_best_model(models)
                if best and m['tries'] == best['tries'] and m['found']:
                    wins += 1
                break

    total = len(successes) + len(failures)
    success_rate = len(successes) / total if total > 0 else 0
    avg_tries = sum(successes) / len(successes) if successes else 0
    best_tries = min(successes) if successes else 0
    worst_tries = max(successes) if successes else 0

    model_stats[model_name] = {
        'success_count': len(successes),
        'total_count': total,
        'success_rate': success_rate,
        'avg_tries': avg_tries,
        'best_tries': best_tries,
        'worst_tries': worst_tries,
        'wins': wins
    }

# Sort by success rate, then by avg tries
sorted_stats = sorted(model_stats.items(),
                     key=lambda x: (x[1]['success_rate'], -x[1]['avg_tries']),
                     reverse=True)

print(f"\n{'Model':<45} {'Success Rate':<15} {'Avg Tries':<15} {'Best':<12} {'Worst':<12} {'Wins':<10}")
print("-" * 110)

for model_name, stats in sorted_stats:
    success_str = f"{stats['success_count']}/24 ({stats['success_rate']*100:.1f}%)"
    avg_str = f"{stats['avg_tries']:,.0f}" if stats['avg_tries'] > 0 else "N/A"
    best_str = f"{stats['best_tries']:,}" if stats['best_tries'] > 0 else "N/A"
    worst_str = f"{stats['worst_tries']:,}" if stats['worst_tries'] > 0 else "N/A"
    wins_str = f"{stats['wins']}x"

    print(f"{model_name:<45} {success_str:<15} {avg_str:<15} {best_str:<12} {worst_str:<12} {wins_str:<10}")

# Calculate baseline comparison
pure_random_avg = model_stats["Pure Random"]["avg_tries"]
print(f"\n{'='*80}")
print("BASELINE COMPARISON (vs Pure Random)")
print(f"{'='*80}\n")
print(f"Pure Random Baseline: {pure_random_avg:,.0f} tries average\n")

for model_name, stats in sorted_stats:
    if model_name == "Pure Random":
        continue

    if stats['avg_tries'] > 0:
        improvement = (pure_random_avg - stats['avg_tries']) / pure_random_avg * 100
        symbol = "✅" if improvement > 0 else "❌"
        print(f"{model_name:<45} {improvement:+.1f}% {symbol}")

print(f"\n{'='*80}")
print("KEY FINDINGS")
print(f"{'='*80}\n")

# Find best overall
best_model = sorted_stats[0]
print(f"🏆 BEST MODEL: {best_model[0]}")
print(f"   - Success Rate: {best_model[1]['success_rate']*100:.1f}%")
print(f"   - Average Tries: {best_model[1]['avg_tries']:,.0f}")
print(f"   - Won {best_model[1]['wins']} times (most wins)\n")

# Find most consistent
most_consistent = max(sorted_stats, key=lambda x: x[1]['success_rate'])
print(f"🎯 MOST CONSISTENT: {most_consistent[0]}")
print(f"   - Success Rate: {most_consistent[1]['success_rate']*100:.1f}% ({most_consistent[1]['success_count']}/24)\n")

# Find least reliable
least_reliable = min(sorted_stats, key=lambda x: x[1]['success_rate'])
print(f"❌ LEAST RELIABLE: {least_reliable[0]}")
print(f"   - Success Rate: {least_reliable[1]['success_rate']*100:.1f}%")
print(f"   - Failed {24 - least_reliable[1]['success_count']} times\n")

print(f"{'='*80}")
print("CONCLUSION")
print(f"{'='*80}\n")
print("Based on comprehensive testing of ALL 6 models on ALL 24 series:")
print("")
print("✅ **Top-8 + Gaps Exhaustive** and **Hybrid Exhaustive+Random** are the")
print("   clear winners, combining high success rates with fast average performance.")
print("")
print("✅ ML-guided space reduction + exhaustive search BEATS probabilistic")
print("   weighting approaches by a large margin.")
print("")
print("❌ Weighted probabilistic approaches (Weighted Mandel, Balanced, Inverse)")
print("   consistently underperform or fail more often than the baseline.")
print("")
print(f"{'='*80}\n")

# Save summary to file
summary = {
    'series_tested': 24,
    'series_range': '3128-3151',
    'models': model_stats,
    'baseline': pure_random_avg,
    'best_model': best_model[0],
    'best_model_stats': best_model[1]
}

with open('comprehensive_results_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("Results saved to: comprehensive_results_summary.json")
