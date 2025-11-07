#!/usr/bin/env python3
"""
Test Approach 1: Enhanced Candidate Pool (10,000 → 50,000)

Rationale:
- Previous test showed 2,000→5,000 gave +4.7% improvement
- Current production uses 10,000 candidates
- Increasing to 50,000 may capture better combinations
- Low risk - no architectural changes, just more exploration
- Simple to test and rollback

Expected: +2-3% improvement (if pattern continues)
"""

import json
import random
from pathlib import Path
from true_learning_model import TrueLearningModel

# Load historical data
json_path = Path(__file__).parent.parent / "Results" / "database_export_2898_3143_20251105_135513.json"

with open(json_path, 'r') as f:
    json_data = json.load(f)

all_series_data = []
for series in json_data.get('data', []):
    series_id = series['series_id']
    events = [event['numbers'] for event in series['events']]
    all_series_data.append({'series_id': series_id, 'events': events})

# Add Series 3144 and 3145
SERIES_3144 = [
    [1, 2, 3, 9, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25],
    [1, 4, 6, 8, 11, 14, 16, 17, 18, 21, 22, 23, 24, 25],
    [2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 19, 21, 24],
    [4, 7, 12, 13, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25],
    [1, 2, 4, 5, 6, 8, 10, 11, 12, 20, 21, 22, 23, 25],
    [1, 4, 5, 6, 7, 8, 12, 14, 16, 17, 19, 20, 21, 24],
    [1, 2, 4, 6, 10, 11, 15, 16, 17, 21, 22, 23, 24, 25],
]

SERIES_3145 = [
    [1, 7, 8, 9, 12, 13, 15, 16, 17, 19, 21, 22, 23, 25],
    [1, 5, 7, 8, 9, 10, 11, 12, 14, 17, 18, 19, 20, 24],
    [3, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 22],
    [1, 3, 6, 7, 10, 11, 13, 14, 16, 20, 21, 22, 23, 25],
    [1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 17, 18, 21, 23],
    [1, 2, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 24, 25],
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 16, 18, 20, 21],
]

all_series_data.append({'series_id': 3144, 'events': SERIES_3144})
all_series_data.append({'series_id': 3145, 'events': SERIES_3145})

print("=" * 80)
print("IMPROVEMENT TEST 1: ENHANCED CANDIDATE POOL")
print("=" * 80)
print()
print("Approach: Increase candidate pool from 10,000 → 50,000")
print("Rationale: More exploration may find better combinations")
print("Evidence: Previous 2,000→5,000 showed +4.7% improvement")
print("Expected: +2-3% improvement if pattern continues")
print()

# Prepare training/validation split
validation_start = 3137
training_data = [s for s in all_series_data if s['series_id'] < validation_start]
validation_data = [s for s in all_series_data if 3137 <= s['series_id'] <= 3145]

# Test baseline (10,000 candidates - current production)
print("=" * 80)
print("BASELINE: Phase 1 Pure with 10,000 candidates")
print("=" * 80)
print()

random.seed(999)
baseline_model = TrueLearningModel()

# Train baseline
for series in training_data:
    baseline_model.learn_from_series(series['series_id'], series['events'])

baseline_results = []

for series_data in validation_data:
    series_id = series_data['series_id']
    actual_events = series_data['events']

    # Override candidate pool size (baseline uses 10,000 by default)
    original_pool_size = baseline_model.CANDIDATE_POOL_SIZE
    baseline_model.CANDIDATE_POOL_SIZE = 10000

    prediction = baseline_model.predict_best_combination(series_id)

    # Restore
    baseline_model.CANDIDATE_POOL_SIZE = original_pool_size

    # Calculate accuracy
    accuracies = []
    for event in actual_events:
        matches = len(set(prediction) & set(event))
        accuracy = matches / 14.0
        accuracies.append(accuracy)

    best_accuracy = max(accuracies)
    avg_accuracy = sum(accuracies) / len(accuracies)

    baseline_results.append({
        'series_id': series_id,
        'best_accuracy': best_accuracy,
        'avg_accuracy': avg_accuracy,
    })

    print(f"  Series {series_id}: Best={best_accuracy:.1%}, Avg={avg_accuracy:.1%}")

    # Learn
    baseline_model.validate_and_learn(series_id, prediction, actual_events)

baseline_avg_best = sum(r['best_accuracy'] for r in baseline_results) / len(baseline_results)
baseline_avg_avg = sum(r['avg_accuracy'] for r in baseline_results) / len(baseline_results)
baseline_3145 = [r for r in baseline_results if r['series_id'] == 3145][0]

print()
print(f"📊 Baseline Overall Best Average: {baseline_avg_best:.1%}")
print(f"📊 Baseline Overall Average: {baseline_avg_avg:.1%}")
print(f"📊 Baseline Series 3145: {baseline_3145['best_accuracy']:.1%}")
print()

# Test enhanced (50,000 candidates)
print("=" * 80)
print("ENHANCED: Phase 1 Pure with 50,000 candidates")
print("=" * 80)
print()

random.seed(999)
enhanced_model = TrueLearningModel()

# Train enhanced
for series in training_data:
    enhanced_model.learn_from_series(series['series_id'], series['events'])

enhanced_results = []

for series_data in validation_data:
    series_id = series_data['series_id']
    actual_events = series_data['events']

    # Override candidate pool size to 50,000
    original_pool_size = enhanced_model.CANDIDATE_POOL_SIZE
    enhanced_model.CANDIDATE_POOL_SIZE = 50000

    prediction = enhanced_model.predict_best_combination(series_id)

    # Restore
    enhanced_model.CANDIDATE_POOL_SIZE = original_pool_size

    # Calculate accuracy
    accuracies = []
    for event in actual_events:
        matches = len(set(prediction) & set(event))
        accuracy = matches / 14.0
        accuracies.append(accuracy)

    best_accuracy = max(accuracies)
    avg_accuracy = sum(accuracies) / len(accuracies)

    enhanced_results.append({
        'series_id': series_id,
        'best_accuracy': best_accuracy,
        'avg_accuracy': avg_accuracy,
    })

    print(f"  Series {series_id}: Best={best_accuracy:.1%}, Avg={avg_accuracy:.1%}")

    # Learn
    enhanced_model.validate_and_learn(series_id, prediction, actual_events)

enhanced_avg_best = sum(r['best_accuracy'] for r in enhanced_results) / len(enhanced_results)
enhanced_avg_avg = sum(r['avg_accuracy'] for r in enhanced_results) / len(enhanced_results)
enhanced_3145 = [r for r in enhanced_results if r['series_id'] == 3145][0]

print()
print(f"📊 Enhanced Overall Best Average: {enhanced_avg_best:.1%}")
print(f"📊 Enhanced Overall Average: {enhanced_avg_avg:.1%}")
print(f"📊 Enhanced Series 3145: {enhanced_3145['best_accuracy']:.1%}")
print()

# Comparison
print("=" * 80)
print("COMPARISON: BASELINE vs ENHANCED")
print("=" * 80)
print()

improvement_best = enhanced_avg_best - baseline_avg_best
improvement_avg = enhanced_avg_avg - baseline_avg_avg
improvement_3145 = enhanced_3145['best_accuracy'] - baseline_3145['best_accuracy']

print("Metric                  | Baseline | Enhanced | Improvement")
print("------------------------|----------|----------|------------")
print(f"Overall Best Average    | {baseline_avg_best:7.1%} | {enhanced_avg_best:7.1%} | {improvement_best:+6.1%}")
print(f"Overall Average         | {baseline_avg_avg:7.1%} | {enhanced_avg_avg:7.1%} | {improvement_avg:+6.1%}")
print(f"Series 3145 Performance | {baseline_3145['best_accuracy']:7.1%} | {enhanced_3145['best_accuracy']:7.1%} | {improvement_3145:+6.1%}")
print()

# Series-by-series comparison
print("Series-by-Series Comparison:")
print()
print("Series | Baseline | Enhanced | Change")
print("-------|----------|----------|--------")
for baseline_r, enhanced_r in zip(baseline_results, enhanced_results):
    series_id = baseline_r['series_id']
    baseline_acc = baseline_r['best_accuracy']
    enhanced_acc = enhanced_r['best_accuracy']
    change = enhanced_acc - baseline_acc
    symbol = "✅" if change > 0 else ("🔻" if change < 0 else "➖")
    print(f" {series_id} | {baseline_acc:7.1%} | {enhanced_acc:7.1%} | {change:+5.1%} {symbol}")

print()

# Decision
print("=" * 80)
print("DECISION")
print("=" * 80)
print()

if improvement_best > 0.02:  # More than 2% improvement
    print("✅ SIGNIFICANT IMPROVEMENT DETECTED")
    print(f"   Enhanced candidate pool improved performance by {improvement_best:+.1%}")
    print(f"   This is a meaningful gain worth keeping.")
    print()
    print("🎯 RECOMMENDATION: DEPLOY ENHANCED VERSION")
    print("   - Update CANDIDATE_POOL_SIZE from 10,000 to 50,000")
    print("   - Expected performance: {:.1%} average best match".format(enhanced_avg_best))
    print("   - Trade-off: ~5x more compute time for generation")
    decision = "KEEP_ENHANCED"
elif improvement_best > 0:
    print("⚠️  MARGINAL IMPROVEMENT DETECTED")
    print(f"   Enhanced candidate pool improved performance by {improvement_best:+.1%}")
    print(f"   This is a small gain - may not justify 5x compute cost.")
    print()
    print("🤔 RECOMMENDATION: CONSIDER TRADE-OFF")
    print("   - Gain: {:.1%}".format(improvement_best))
    print("   - Cost: ~5x longer prediction time")
    print("   - Decision: Deploy if compute cost acceptable")
    decision = "MARGINAL_KEEP"
else:
    print("❌ NO IMPROVEMENT DETECTED")
    print(f"   Enhanced candidate pool changed performance by {improvement_best:+.1%}")
    print(f"   This does not justify 5x compute cost.")
    print()
    print("🔄 RECOMMENDATION: ROLLBACK TO BASELINE")
    print("   - Keep current 10,000 candidate pool")
    print("   - Look for alternative improvement approaches")
    decision = "ROLLBACK"

print()

# Save results
results = {
    'approach': 'Enhanced Candidate Pool (10,000 → 50,000)',
    'baseline': {
        'candidate_pool': 10000,
        'overall_best_avg': baseline_avg_best,
        'overall_avg': baseline_avg_avg,
        'series_3145_best': baseline_3145['best_accuracy'],
        'series_results': baseline_results,
    },
    'enhanced': {
        'candidate_pool': 50000,
        'overall_best_avg': enhanced_avg_best,
        'overall_avg': enhanced_avg_avg,
        'series_3145_best': enhanced_3145['best_accuracy'],
        'series_results': enhanced_results,
    },
    'improvement': {
        'overall_best_avg': improvement_best,
        'overall_avg': improvement_avg,
        'series_3145_best': improvement_3145,
    },
    'decision': decision,
}

output_path = Path(__file__).parent / "test_enhanced_pool_results.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"📁 Results saved to: {output_path}")
print()

# Next steps
if decision == "ROLLBACK":
    print("=" * 80)
    print("NEXT STEPS: TRY ALTERNATIVE APPROACH")
    print("=" * 80)
    print()
    print("Since enhanced candidate pool didn't improve performance,")
    print("we should try the next most promising approach:")
    print()
    print("Option 2: Hybrid Adaptive Learning")
    print("  - Keep Phase 1 Pure base")
    print("  - Add adaptive component for difficult series detection")
    print("  - Use higher learning rate when performance drops")
    print()
    print("Rationale:")
    print("  - Adaptive LR achieved 78.6% on Series 3145")
    print("  - Could help recover from difficult series faster")
    print("  - Hybrid approach may balance consistency + adaptability")
    print()
