#!/usr/bin/env python3
"""
IMPROVED JACKPOT FINDER FOR SERIES 3152
Challenge: Create a better version that will actually GET a jackpot

Improvements:
1. Multi-signal scoring (frequency + patterns + recency + distribution)
2. Generate top 100 candidates (not just 7)
3. Rank by composite confidence score
4. Learn from ALL historical patterns, not just recent
"""

import json
from collections import Counter
from itertools import combinations

def load_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def calculate_multi_signal_score(combo, data, recent_series):
    """
    Calculate composite score for a combination using multiple signals

    Signals:
    1. Global frequency score
    2. Recent frequency score (last 5 series)
    3. Pattern match score (similarity to recent events)
    4. Distribution score (column balance)
    5. Pair affinity score (numbers that appear together)
    """

    # Signal 1: Global frequency (all history)
    global_counter = Counter()
    for sid, events in data.items():
        for event in events:
            for num in event:
                global_counter[num] += 1

    global_score = sum(global_counter[num] for num in combo) / len(combo)

    # Signal 2: Recent frequency (last 5 series)
    recent_counter = Counter()
    for sid in recent_series:
        for event in data[str(sid)]:
            for num in event:
                recent_counter[num] += 1

    recent_score = sum(recent_counter[num] for num in combo) / len(combo)

    # Signal 3: Pattern match (similarity to recent events)
    pattern_scores = []
    for sid in recent_series[-2:]:  # Last 2 series
        for event in data[str(sid)]:
            overlap = len(set(combo) & set(event))
            pattern_scores.append(overlap / 14)

    pattern_score = max(pattern_scores) if pattern_scores else 0

    # Signal 4: Distribution score (column balance)
    col0 = len([n for n in combo if 1 <= n <= 9])
    col1 = len([n for n in combo if 10 <= n <= 19])
    col2 = len([n for n in combo if 20 <= n <= 25])

    # Ideal: 5-6-3 or 4-7-3 or similar
    ideal_dist = [5, 6, 3]
    actual_dist = [col0, col1, col2]
    dist_diff = sum(abs(ideal_dist[i] - actual_dist[i]) for i in range(3))
    distribution_score = max(0, 1 - (dist_diff / 10))

    # Signal 5: Pair affinity (how often pairs appear together)
    pair_counter = Counter()
    for sid, events in data.items():
        for event in events:
            for i, n1 in enumerate(event):
                for n2 in event[i+1:]:
                    pair_counter[(min(n1, n2), max(n1, n2))] += 1

    pair_score = 0
    pair_count = 0
    for i, n1 in enumerate(combo):
        for n2 in combo[i+1:]:
            pair_count += 1
            pair_score += pair_counter[(min(n1, n2), max(n1, n2))]

    pair_score = pair_score / pair_count if pair_count > 0 else 0

    # Composite score (weighted average)
    composite = (
        global_score * 0.25 +
        recent_score * 0.35 +
        pattern_score * 0.20 +
        distribution_score * 0.10 +
        pair_score * 0.10
    )

    return {
        'composite': composite,
        'global': global_score,
        'recent': recent_score,
        'pattern': pattern_score,
        'distribution': distribution_score,
        'pair_affinity': pair_score
    }

def generate_smart_candidates(data, reduced_pool, recent_series, top_n=100):
    """
    Generate smart candidates using multiple strategies, then rank by score
    """

    candidates = set()

    # Strategy 1: All combinations of top-16 by recent frequency
    recent_counter = Counter()
    for sid in recent_series:
        for event in data[str(sid)]:
            for num in event:
                if num in reduced_pool:
                    recent_counter[num] += 1

    top_16 = [num for num, _ in recent_counter.most_common(16)]
    for combo in combinations(top_16, 14):
        candidates.add(combo)
        if len(candidates) >= top_n * 2:
            break

    # Strategy 2: Variations of recent winning patterns
    for sid in recent_series[-2:]:
        for event in data[str(sid)]:
            # Original
            if all(n in reduced_pool for n in event):
                candidates.add(tuple(sorted(event)))

            # Replace 1 number
            for i, num in enumerate(event):
                if num not in reduced_pool:
                    # Replace with top from pool
                    for replacement in top_16[:5]:
                        if replacement not in event:
                            modified = event.copy()
                            modified[i] = replacement
                            candidates.add(tuple(sorted(modified)))
                            break

    # Strategy 3: High-frequency pairs extended to full combinations
    pair_counter = Counter()
    for sid in recent_series:
        for event in data[str(sid)]:
            for i, n1 in enumerate(event):
                for n2 in event[i+1:]:
                    if n1 in reduced_pool and n2 in reduced_pool:
                        pair_counter[(min(n1, n2), max(n1, n2))] += 1

    # Get top pairs and extend to 14 numbers
    top_pairs = [pair for pair, _ in pair_counter.most_common(10)]
    for pair in top_pairs[:5]:
        # Start with pair, add top frequency numbers
        base = list(pair)
        remaining = [n for n in top_16 if n not in base][:12]
        candidates.add(tuple(sorted(base + remaining)))

    # Convert to list and score each
    print(f"Generated {len(candidates)} candidate combinations")
    print("Scoring candidates with multi-signal analysis...\n")

    scored_candidates = []
    for combo in candidates:
        scores = calculate_multi_signal_score(combo, data, recent_series)
        scored_candidates.append({
            'numbers': list(combo),
            'scores': scores
        })

    # Sort by composite score
    scored_candidates.sort(key=lambda x: x['scores']['composite'], reverse=True)

    return scored_candidates[:top_n]

def predict_series_3152_improved():
    """
    Generate improved predictions for Series 3152 with multi-signal ranking
    """

    print("="*80)
    print("IMPROVED JACKPOT FINDER - SERIES 3152")
    print("="*80)
    print("\nMulti-Signal Scoring System:")
    print("  • Global frequency (25%)")
    print("  • Recent frequency (35%)")
    print("  • Pattern match (20%)")
    print("  • Distribution balance (10%)")
    print("  • Pair affinity (10%)")
    print("="*80)

    data = load_data()
    recent_series = [3147, 3148, 3149, 3150, 3151]
    reduced_pool = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25]

    # Generate top 100 candidates
    top_candidates = generate_smart_candidates(data, reduced_pool, recent_series, top_n=100)

    print(f"\n{'='*80}")
    print("TOP 20 JACKPOT CANDIDATES (Ranked by Composite Score)")
    print(f"{'='*80}\n")

    for i, cand in enumerate(top_candidates[:20], 1):
        nums = cand['numbers']
        scores = cand['scores']

        print(f"[{i:2d}] {' '.join(f'{n:02d}' for n in nums)}")
        print(f"     Composite: {scores['composite']:.3f} | "
              f"Recent: {scores['recent']:.1f} | "
              f"Pattern: {scores['pattern']:.2f} | "
              f"Dist: {scores['distribution']:.2f}")

        if i == 5 or i == 10 or i == 15:
            print()

    # Show confidence tiers
    print(f"\n{'='*80}")
    print("CONFIDENCE TIERS")
    print(f"{'='*80}\n")

    tier_1 = [c for c in top_candidates if c['scores']['composite'] >= top_candidates[0]['scores']['composite'] * 0.95]
    tier_2 = [c for c in top_candidates if top_candidates[0]['scores']['composite'] * 0.90 <= c['scores']['composite'] < top_candidates[0]['scores']['composite'] * 0.95]
    tier_3 = [c for c in top_candidates[:20] if c['scores']['composite'] < top_candidates[0]['scores']['composite'] * 0.90]

    print(f"TIER 1 (Highest): {len(tier_1)} candidates")
    for c in tier_1[:3]:
        print(f"  {' '.join(f'{n:02d}' for n in c['numbers'])}")

    print(f"\nTIER 2 (High): {len(tier_2)} candidates")
    for c in tier_2[:2]:
        print(f"  {' '.join(f'{n:02d}' for n in c['numbers'])}")

    print(f"\nTIER 3 (Medium): {len(tier_3)} candidates")

    # Save results
    output = {
        'series_id': 3152,
        'method': 'Multi-Signal Improved Jackpot Finder',
        'signals': {
            'global_frequency': 0.25,
            'recent_frequency': 0.35,
            'pattern_match': 0.20,
            'distribution_balance': 0.10,
            'pair_affinity': 0.10
        },
        'reduced_pool': reduced_pool,
        'top_100_candidates': top_candidates,
        'recommendation': {
            'tier_1_best': tier_1[0]['numbers'] if tier_1 else None,
            'tier_1_count': len(tier_1),
            'total_generated': len(top_candidates)
        }
    }

    with open('improved_predictions_3152.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}\n")
    print("🎯 ABSOLUTE BEST (Highest Composite Score):")
    print(f"   {' '.join(f'{n:02d}' for n in top_candidates[0]['numbers'])}")
    print(f"\n📊 Coverage: Top 100 candidates (0.086% of reduced space)")
    print(f"💾 Saved: improved_predictions_3152.json")
    print(f"\n{'='*80}")
    print("CHALLENGE STATUS")
    print(f"{'='*80}")
    print("✅ Multi-signal scoring implemented")
    print("✅ 100 top candidates generated and ranked")
    print("✅ Tier system for confidence levels")
    print("⏳ Waiting for Series 3152 results to validate...")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    predict_series_3152_improved()
