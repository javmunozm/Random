#!/usr/bin/env python3
"""Adaptive weighting - weights change based on jackpot characteristics"""
import json
import random
from collections import Counter
from datetime import datetime

def load_all_series_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def analyze_recent_jackpots(all_data, training_ids, recent_n=10):
    """Analyze last N jackpots to detect patterns"""
    recent_ids = sorted(training_ids)[-recent_n:]
    counter = Counter()

    for sid in recent_ids:
        for event in all_data[str(sid)]:
            for num in event:
                counter[num] += 1

    # Return frequency in recent jackpots
    total = sum(counter.values())
    return {num: counter.get(num, 0) / total for num in range(1, 26)}

def adaptive_weights(all_data, training_ids):
    """Calculate adaptive weights based on recent trends"""
    # Overall frequency
    overall = Counter()
    for sid in training_ids:
        for event in all_data[str(sid)]:
            for num in event:
                overall[num] += 1

    # Recent frequency (last 10 series)
    recent = analyze_recent_jackpots(all_data, training_ids, 10)

    # Combine: 30% overall + 70% recent (favor recent trends)
    max_overall = max(overall.values())
    weights = {}
    for num in range(1, 26):
        overall_score = overall.get(num, 0) / max_overall
        recent_score = recent.get(num, 0)
        weights[num] = 0.3 * overall_score + 0.7 * recent_score

    # Normalize
    total = sum(weights.values())
    return {num: w / total for num, w in weights.items()}

def generate_adaptive_combo(weights):
    numbers = list(range(1, 26))
    probs = [weights[num] for num in numbers]

    selected = set()
    while len(selected) < 14:
        num = random.choices(numbers, weights=probs, k=1)[0]
        selected.add(num)

    return tuple(sorted(selected))

def adaptive_search(series_id, all_data, weights, exclusion_set):
    target_tuples = set(tuple(sorted(e)) for e in all_data[str(series_id)])
    all_exclusions = exclusion_set.copy()
    unique_tries = 0
    start_time = datetime.now()

    while True:
        combo = generate_adaptive_combo(weights)
        if combo in all_exclusions:
            continue
        all_exclusions.add(combo)
        unique_tries += 1

        if unique_tries % 50000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  {unique_tries:,} tries | {elapsed:.1f}s")

        for event_num, target in enumerate(target_tuples, 1):
            if combo == target:
                elapsed = (datetime.now() - start_time).total_seconds()
                return {
                    'series_id': series_id,
                    'tries': unique_tries,
                    'time_seconds': elapsed,
                    'event_number': event_num
                }

def build_exclusion_set(all_data, before_series_id):
    exclusion_set = set()
    for sid_str, events in all_data.items():
        if int(sid_str) < before_series_id:
            for event in events:
                exclusion_set.add(tuple(sorted(event)))
    return exclusion_set

def main():
    print("ADAPTIVE WEIGHTS - Series 3128-3151")
    all_data = load_all_series_data()
    results = []

    for series_id in range(3128, 3152):
        print(f"\nSeries {series_id}:")
        training_ids = [sid for sid in map(int, all_data.keys()) if sid < series_id]
        weights = adaptive_weights(all_data, training_ids)
        exclusion_set = build_exclusion_set(all_data, series_id)

        result = adaptive_search(series_id, all_data, weights, exclusion_set)
        results.append(result)
        print(f"  FOUND in {result['tries']:,} tries ({result['time_seconds']:.1f}s)")

    avg_tries = sum(r['tries'] for r in results) / len(results)
    baseline = 318385
    improvement = (baseline - avg_tries) / baseline * 100

    output = {
        'method': 'Adaptive Weights (30% overall + 70% recent)',
        'average_tries': avg_tries,
        'baseline': baseline,
        'improvement_pct': improvement,
        'results': results
    }

    with open('adaptive_weights_3128_3151.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nAverage: {avg_tries:,.0f} tries ({improvement:+.1f}% vs baseline)")

if __name__ == '__main__':
    main()
