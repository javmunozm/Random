#!/usr/bin/env python3
"""
Test Approach 2: Hybrid Adaptive Learning

Rationale:
- Adaptive LR achieved 78.6% on Series 3145 (best of all models!)
- But only 65.9% overall (inconsistent)
- Hybrid approach: Use Phase 1 Pure normally, adapt only when needed

Strategy:
- Base learning rate: 0.10 (Phase 1 Pure default)
- Track performance over last 3 series
- If average drops below 65%, increase LR to 0.15 (moderate boost)
- If drops below 60%, increase LR to 0.20 (high boost for recovery)
- If stable above 70%, decrease LR to 0.08 (fine-tuning)

Expected: Better recovery from difficult series, maintain consistency on normal series
"""

import json
import random
from pathlib import Path
from collections import deque
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
print("IMPROVEMENT TEST 2: HYBRID ADAPTIVE LEARNING")
print("=" * 80)
print()
print("Approach: Adaptive learning rate based on recent performance")
print("Rationale: Adaptive LR achieved 78.6% on Series 3145 (hardest series!)")
print("Strategy: Adjust LR dynamically:")
print("  - Normal (>70%): LR = 0.08 (fine-tuning)")
print("  - Medium (65-70%): LR = 0.10 (standard)")
print("  - Low (60-65%): LR = 0.15 (moderate boost)")
print("  - Critical (<60%): LR = 0.20 (high boost for recovery)")
print()

# Prepare training/validation split
validation_start = 3137
training_data = [s for s in all_series_data if s['series_id'] < validation_start]
validation_data = [s for s in all_series_data if 3137 <= s['series_id'] <= 3145]

# Test baseline (from Approach 1 results)
baseline_avg_best = 0.722
baseline_3145 = 0.643

print("=" * 80)
print("BASELINE: Phase 1 Pure (from previous test)")
print("=" * 80)
print()
print(f"📊 Baseline Overall Best Average: {baseline_avg_best:.1%}")
print(f"📊 Baseline Series 3145: {baseline_3145:.1%}")
print()

# Test hybrid adaptive
print("=" * 80)
print("HYBRID ADAPTIVE: Phase 1 Pure + Adaptive Learning Rate")
print("=" * 80)
print()

random.seed(999)
hybrid_model = TrueLearningModel()

# Train
for series in training_data:
    hybrid_model.learn_from_series(series['series_id'], series['events'])

hybrid_results = []
recent_performance = deque(maxlen=3)  # Track last 3 series

for series_data in validation_data:
    series_id = series_data['series_id']
    actual_events = series_data['events']

    # Predict
    prediction = hybrid_model.predict_best_combination(series_id)

    # Calculate accuracy
    accuracies = []
    for event in actual_events:
        matches = len(set(prediction) & set(event))
        accuracy = matches / 14.0
        accuracies.append(accuracy)

    best_accuracy = max(accuracies)
    avg_accuracy = sum(accuracies) / len(accuracies)

    hybrid_results.append({
        'series_id': series_id,
        'best_accuracy': best_accuracy,
        'avg_accuracy': avg_accuracy,
    })

    # Track performance
    recent_performance.append(best_accuracy)

    # Calculate average of recent performance
    if len(recent_performance) >= 2:
        recent_avg = sum(recent_performance) / len(recent_performance)
    else:
        recent_avg = best_accuracy

    # Determine adaptive learning rate
    if recent_avg > 0.70:
        adaptive_lr = 0.08  # Fine-tuning
        status = "HIGH"
    elif recent_avg > 0.65:
        adaptive_lr = 0.10  # Standard
        status = "NORMAL"
    elif recent_avg > 0.60:
        adaptive_lr = 0.15  # Moderate boost
        status = "LOW"
    else:
        adaptive_lr = 0.20  # High boost
        status = "CRITICAL"

    # Apply adaptive learning rate
    original_lr = hybrid_model.learning_rate
    hybrid_model.learning_rate = adaptive_lr

    print(f"  Series {series_id}: Best={best_accuracy:.1%}, Avg={avg_accuracy:.1%} | Recent avg={recent_avg:.1%} → LR={adaptive_lr:.2f} ({status})")

    # Learn with adaptive rate
    hybrid_model.validate_and_learn(series_id, prediction, actual_events)

    # Restore original LR (model may have changed it)
    hybrid_model.learning_rate = adaptive_lr

print()

hybrid_avg_best = sum(r['best_accuracy'] for r in hybrid_results) / len(hybrid_results)
hybrid_avg_avg = sum(r['avg_accuracy'] for r in hybrid_results) / len(hybrid_results)
hybrid_3145 = [r for r in hybrid_results if r['series_id'] == 3145][0]

print(f"📊 Hybrid Overall Best Average: {hybrid_avg_best:.1%}")
print(f"📊 Hybrid Overall Average: {hybrid_avg_avg:.1%}")
print(f"📊 Hybrid Series 3145: {hybrid_3145['best_accuracy']:.1%}")
print()

# Comparison
print("=" * 80)
print("COMPARISON: BASELINE vs HYBRID ADAPTIVE")
print("=" * 80)
print()

improvement_best = hybrid_avg_best - baseline_avg_best
improvement_3145 = hybrid_3145['best_accuracy'] - baseline_3145

print("Metric                  | Baseline | Hybrid   | Improvement")
print("------------------------|----------|----------|------------")
print(f"Overall Best Average    | {baseline_avg_best:7.1%} | {hybrid_avg_best:7.1%} | {improvement_best:+6.1%}")
print(f"Series 3145 Performance | {baseline_3145:7.1%} | {hybrid_3145['best_accuracy']:7.1%} | {improvement_3145:+6.1%}")
print()

# Decision
print("=" * 80)
print("DECISION")
print("=" * 80)
print()

if improvement_best > 0.02:
    print("✅ SIGNIFICANT IMPROVEMENT DETECTED")
    print(f"   Hybrid adaptive approach improved performance by {improvement_best:+.1%}")
    print(f"   This is a meaningful gain worth keeping.")
    print()
    print("🎯 RECOMMENDATION: DEPLOY HYBRID VERSION")
    print("   - Implement adaptive learning rate mechanism")
    print("   - Expected performance: {:.1%} average best match".format(hybrid_avg_best))
    print("   - Adaptive LR adjusts based on recent performance")
    decision = "KEEP_HYBRID"
elif improvement_best > 0:
    print("⚠️  MARGINAL IMPROVEMENT DETECTED")
    print(f"   Hybrid approach improved performance by {improvement_best:+.1%}")
    print(f"   This is a small gain - may or may not justify complexity.")
    print()
    print("🤔 RECOMMENDATION: CONSIDER TRADE-OFF")
    print("   - Gain: {:.1%}".format(improvement_best))
    print("   - Cost: Additional complexity (adaptive LR tracking)")
    print("   - Decision: Deploy if adaptive behavior desired")
    decision = "MARGINAL_KEEP"
else:
    print("❌ NO IMPROVEMENT DETECTED")
    print(f"   Hybrid approach changed performance by {improvement_best:+.1%}")
    print(f"   Adaptive learning rate did not help overall performance.")
    print()
    print("🔄 RECOMMENDATION: ROLLBACK TO BASELINE")
    print("   - Keep current Phase 1 Pure without adaptive LR")
    print("   - Try different improvement approach")
    decision = "ROLLBACK"

print()

# Check Series 3145 specifically
if hybrid_3145['best_accuracy'] > baseline_3145:
    print(f"📈 NOTE: Hybrid performed BETTER on Series 3145 ({hybrid_3145['best_accuracy']:.1%} vs {baseline_3145:.1%})")
    print(f"   Improvement of {improvement_3145:+.1%} on the hardest series")
    print(f"   This suggests adaptive LR helps with difficult series")
else:
    print(f"📉 NOTE: Hybrid did NOT improve on Series 3145")

print()

# Save results
results = {
    'approach': 'Hybrid Adaptive Learning',
    'baseline': {
        'learning_rate': 'fixed 0.10',
        'overall_best_avg': baseline_avg_best,
        'series_3145_best': baseline_3145,
    },
    'hybrid': {
        'learning_rate': 'adaptive 0.08-0.20',
        'overall_best_avg': hybrid_avg_best,
        'series_3145_best': hybrid_3145['best_accuracy'],
        'series_results': hybrid_results,
    },
    'improvement': {
        'overall_best_avg': improvement_best,
        'series_3145_best': improvement_3145,
    },
    'decision': decision,
}

output_path = Path(__file__).parent / "test_hybrid_adaptive_results.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"📁 Results saved to: {output_path}")
print()

# Final summary
if decision == "ROLLBACK":
    print("=" * 80)
    print("FINAL SUMMARY: BOTH APPROACHES FAILED")
    print("=" * 80)
    print()
    print("Approach 1 (Enhanced Candidate Pool): +0.0% improvement")
    print(f"Approach 2 (Hybrid Adaptive Learning): {improvement_best:+.1%} improvement")
    print()
    print("CONCLUSION:")
    print("  After testing 2 approaches, neither improved performance beyond baseline.")
    print("  This confirms our comprehensive simulation study findings:")
    print("  - Phase 1 Pure is already optimal (72.2%)")
    print("  - 72% ceiling is due to data limitations, not architecture")
    print("  - 39+ improvement attempts, 0 succeeded")
    print()
    print("🎯 FINAL RECOMMENDATION: ACCEPT PHASE 1 PURE AS OPTIMAL")
    print("   - Deploy current system (72.2% average best match)")
    print("   - Accept 68-72% performance range")
    print("   - OR: Pivot to more predictable problem domains")
    print()
elif decision == "KEEP_HYBRID":
    print("=" * 80)
    print("SUCCESS: HYBRID ADAPTIVE FOUND IMPROVEMENT!")
    print("=" * 80)
    print()
    print(f"Improvement: {improvement_best:+.1%}")
    print(f"New Performance: {hybrid_avg_best:.1%}")
    print()
    print("Next steps:")
    print("  1. Implement adaptive LR in production code")
    print("  2. Test on new data (Series 3146+)")
    print("  3. Monitor performance over time")
    print()
