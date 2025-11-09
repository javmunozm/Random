"""
Evaluate Series 3146 predictions against actual results
"""

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

# Our predictions
CSHARP_PRED = [1, 3, 4, 6, 7, 9, 10, 11, 12, 13, 15, 16, 21, 24]
PYTHON_OPTIMIZED = [1, 2, 3, 5, 9, 10, 14, 16, 19, 21, 22, 23, 24, 25]

def evaluate_prediction(prediction, actual_events):
    """Evaluate a prediction against actual events"""
    results = []
    for i, event in enumerate(actual_events, 1):
        matches = len(set(prediction) & set(event))
        accuracy = matches / 14.0
        results.append({
            "event": i,
            "matches": matches,
            "accuracy": accuracy,
            "matched_numbers": sorted(set(prediction) & set(event))
        })

    best_accuracy = max(r["accuracy"] for r in results)
    avg_accuracy = sum(r["accuracy"] for r in results) / len(results)

    return {
        "results": results,
        "best_accuracy": best_accuracy,
        "avg_accuracy": avg_accuracy,
        "best_event": [r for r in results if r["accuracy"] == best_accuracy][0]
    }

print("="*70)
print("SERIES 3146 ACTUAL RESULTS EVALUATION")
print("="*70)
print()

# Evaluate C# prediction
print("C# PREDICTION:")
print(f"  {' '.join(f'{n:02d}' for n in CSHARP_PRED)}")
print()

csharp_eval = evaluate_prediction(CSHARP_PRED, ACTUAL_3146)

print("Performance by event:")
for r in csharp_eval["results"]:
    bar = '█' * r["matches"]
    print(f"  Event {r['event']}: {r['matches']:2d}/14 ({r['accuracy']:5.1%}) {bar}")

print()
print(f"📊 Best match: {csharp_eval['best_accuracy']:.1%} (Event {csharp_eval['best_event']['event']})")
print(f"📊 Average: {csharp_eval['avg_accuracy']:.1%}")
print()

# Evaluate Python Optimized
print("="*70)
print("PYTHON OPTIMIZED PREDICTION:")
print(f"  {' '.join(f'{n:02d}' for n in PYTHON_OPTIMIZED)}")
print()

python_eval = evaluate_prediction(PYTHON_OPTIMIZED, ACTUAL_3146)

print("Performance by event:")
for r in python_eval["results"]:
    bar = '█' * r["matches"]
    print(f"  Event {r['event']}: {r['matches']:2d}/14 ({r['accuracy']:5.1%}) {bar}")

print()
print(f"📊 Best match: {python_eval['best_accuracy']:.1%} (Event {python_eval['best_event']['event']})")
print(f"📊 Average: {python_eval['avg_accuracy']:.1%}")
print()

# Comparison
print("="*70)
print("COMPARISON:")
print("="*70)
print()
print(f"C# Prediction:")
print(f"  Best match: {csharp_eval['best_accuracy']:.1%}")
print(f"  Average: {csharp_eval['avg_accuracy']:.1%}")
print()
print(f"Python Optimized (LR=0.05, 2k candidates):")
print(f"  Best match: {python_eval['best_accuracy']:.1%}")
print(f"  Average: {python_eval['avg_accuracy']:.1%}")
print()

if python_eval['avg_accuracy'] > csharp_eval['avg_accuracy']:
    diff = python_eval['avg_accuracy'] - csharp_eval['avg_accuracy']
    print(f"✅ Python Optimized WINS by {diff:.1%}!")
elif csharp_eval['avg_accuracy'] > python_eval['avg_accuracy']:
    diff = csharp_eval['avg_accuracy'] - python_eval['avg_accuracy']
    print(f"✅ C# WINS by {diff:.1%}!")
else:
    print(f"🤝 TIE!")

print()

# Number frequency in actual results
print("="*70)
print("MOST COMMON NUMBERS IN ACTUAL RESULTS:")
print("="*70)

freq = {}
for event in ACTUAL_3146:
    for num in event:
        freq[num] = freq.get(num, 0) + 1

sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)

print()
for num, count in sorted_freq[:14]:
    pct = (count / 7) * 100
    bar = '█' * count
    in_csharp = '✓' if num in CSHARP_PRED else '✗'
    in_python = '✓' if num in PYTHON_OPTIMIZED else '✗'
    print(f"  {num:02d}: {count}/7 events ({pct:5.1f}%) {bar} | C#:{in_csharp} Py:{in_python}")

print()

# Which prediction captured more high-frequency numbers?
top_14_numbers = [n for n, _ in sorted_freq[:14]]
csharp_top_captured = len(set(CSHARP_PRED) & set(top_14_numbers))
python_top_captured = len(set(PYTHON_OPTIMIZED) & set(top_14_numbers))

print(f"Top 14 most frequent numbers captured:")
print(f"  C#: {csharp_top_captured}/14")
print(f"  Python Optimized: {python_top_captured}/14")
print()

# Save results
import json

results = {
    "series_id": 3146,
    "actual_results": ACTUAL_3146,
    "predictions": {
        "csharp": {
            "prediction": CSHARP_PRED,
            "best_match": csharp_eval['best_accuracy'],
            "avg_accuracy": csharp_eval['avg_accuracy'],
            "event_results": csharp_eval['results']
        },
        "python_optimized": {
            "prediction": PYTHON_OPTIMIZED,
            "best_match": python_eval['best_accuracy'],
            "avg_accuracy": python_eval['avg_accuracy'],
            "event_results": python_eval['results']
        }
    },
    "frequency_analysis": {
        "top_14": sorted_freq[:14],
        "csharp_captured": csharp_top_captured,
        "python_captured": python_top_captured
    }
}

with open('series_3146_evaluation.json', 'w') as f:
    json.dump(results, f, indent=2)

print("💾 Results saved to: series_3146_evaluation.json")
