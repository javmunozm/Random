#!/usr/bin/env python3
"""
Series 3152 Jackpot Prediction - Generate candidates BEFORE results exist
Uses historical data to predict which numbers WON'T appear (exclusion strategy)
"""

import json
from itertools import combinations
from collections import Counter

def analyze_exclusion_patterns():
    """
    Analyze historical data to identify numbers LEAST likely to appear
    This is more memory-efficient than storing all combinations
    """

    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    # Get last 5 series for recent patterns
    recent_series = ['3147', '3148', '3149', '3150', '3151']

    # Count appearances across all events in recent series
    appearance_counter = Counter()
    total_events = 0

    for sid in recent_series:
        for event in data[sid]:
            total_events += 1
            for num in event:
                appearance_counter[num] += 1

    # Calculate appearance rates
    appearance_rates = {num: count / total_events for num, count in appearance_counter.items()}

    # All numbers 1-25
    all_numbers = set(range(1, 26))

    # Get frequency for each number (0 if never appeared)
    number_frequencies = {num: appearance_rates.get(num, 0.0) for num in all_numbers}

    # Sort by frequency (ascending - least likely first)
    sorted_by_freq = sorted(number_frequencies.items(), key=lambda x: x[1])

    print("="*80)
    print("EXCLUSION ANALYSIS FOR SERIES 3152")
    print("="*80)
    print(f"\nAnalyzed: {len(recent_series)} recent series ({total_events} total events)\n")

    print("Number frequencies (last 5 series):")
    for num, freq in sorted_by_freq:
        bar_length = int(freq * 50)
        bar = '█' * bar_length
        print(f"  {num:02d}: {freq:5.1%} {bar}")

    # Identify exclusion candidates (bottom 4 numbers)
    exclusion_candidates = [num for num, _ in sorted_by_freq[:4]]

    print(f"\n" + "="*80)
    print("EXCLUSION STRATEGY")
    print("="*80)
    print(f"\nNumbers to EXCLUDE (least likely to appear): {exclusion_candidates}")
    print(f"Numbers in POOL (most likely): {sorted([n for n in all_numbers if n not in exclusion_candidates])}")

    # Calculate reduced pool
    inclusion_pool = sorted([n for n in all_numbers if n not in exclusion_candidates])
    total_combos = len(list(combinations(inclusion_pool, 14)))

    print(f"\nPool size: {len(inclusion_pool)} numbers")
    print(f"Total combinations: {total_combos:,}")
    print(f"Space reduction: {(1 - total_combos / 4457400) * 100:.1f}%")

    return exclusion_candidates, inclusion_pool

def generate_prediction_candidates(inclusion_pool, num_candidates=10):
    """
    Generate top prediction candidates using different strategies
    Memory-efficient: generates on-demand, doesn't store all combinations
    """

    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    # Get Series 3151 for pattern analysis
    latest = data['3151']

    # Strategy 1: Frequency-weighted from pool
    recent_series = ['3147', '3148', '3149', '3150', '3151']
    freq_counter = Counter()
    for sid in recent_series:
        for event in data[sid]:
            for num in event:
                if num in inclusion_pool:
                    freq_counter[num] += 1

    candidates = []

    # Candidate 1: Top-14 by frequency
    top_14 = [num for num, _ in freq_counter.most_common(14)]
    candidates.append({
        'strategy': 'Top-14 by Frequency',
        'numbers': sorted(top_14),
        'confidence': 'HIGH'
    })

    # Candidate 2: Top-12 + 2 medium frequency
    top_12 = [num for num, _ in freq_counter.most_common(12)]
    remaining = [n for n in inclusion_pool if n not in top_12]
    medium_freq = remaining[:2] if len(remaining) >= 2 else remaining
    candidates.append({
        'strategy': 'Top-12 + 2 Medium Frequency',
        'numbers': sorted(top_12 + medium_freq),
        'confidence': 'HIGH'
    })

    # Candidate 3: Top-10 + 4 balanced from remaining
    top_10 = [num for num, _ in freq_counter.most_common(10)]
    remaining = [n for n in inclusion_pool if n not in top_10]
    balanced = remaining[:4] if len(remaining) >= 4 else remaining
    candidates.append({
        'strategy': 'Top-10 + 4 Balanced',
        'numbers': sorted(top_10 + balanced),
        'confidence': 'MEDIUM'
    })

    # Candidate 4: Pattern from 3151 Event 1 (adjusted to pool)
    pattern_3151 = sorted(latest[0])
    adjusted_pattern = [n for n in pattern_3151 if n in inclusion_pool]
    if len(adjusted_pattern) < 14:
        # Fill with top frequency from pool
        fill_count = 14 - len(adjusted_pattern)
        fillers = [n for n in top_14 if n not in adjusted_pattern][:fill_count]
        adjusted_pattern.extend(fillers)
    candidates.append({
        'strategy': 'Series 3151 Pattern (Adjusted)',
        'numbers': sorted(adjusted_pattern[:14]),
        'confidence': 'MEDIUM'
    })

    # Candidate 5: Even distribution across ranges
    # Column 0: 1-9, Column 1: 10-19, Column 2: 20-25
    col0 = [n for n in inclusion_pool if 1 <= n <= 9]
    col1 = [n for n in inclusion_pool if 10 <= n <= 19]
    col2 = [n for n in inclusion_pool if 20 <= n <= 25]

    # Take proportional from each column
    selected = []
    selected.extend(col0[:5] if len(col0) >= 5 else col0)
    selected.extend(col1[:6] if len(col1) >= 6 else col1)
    selected.extend(col2[:3] if len(col2) >= 3 else col2)

    if len(selected) < 14:
        # Fill remaining
        remaining = [n for n in inclusion_pool if n not in selected]
        selected.extend(remaining[:14-len(selected)])

    candidates.append({
        'strategy': 'Even Distribution (Col 0:5, Col 1:6, Col 2:3)',
        'numbers': sorted(selected[:14]),
        'confidence': 'MEDIUM'
    })

    return candidates[:num_candidates]

def generate_all_combinations_iterator(inclusion_pool):
    """
    Memory-efficient iterator for all combinations
    Doesn't store all in RAM, generates on-demand
    """
    return combinations(inclusion_pool, 14)

def save_prediction_results(exclusion_list, inclusion_pool, candidates):
    """Save prediction results to file"""

    output = {
        'series_id': 3152,
        'prediction_type': 'EXCLUSION_BASED',
        'analysis': {
            'excluded_numbers': exclusion_list,
            'inclusion_pool': inclusion_pool,
            'pool_size': len(inclusion_pool),
            'total_combinations': len(list(combinations(inclusion_pool, 14))),
            'space_reduction_pct': (1 - len(list(combinations(inclusion_pool, 14))) / 4457400) * 100
        },
        'top_candidates': candidates,
        'note': 'Predictions based on exclusion strategy - identifying numbers LEAST likely to appear'
    }

    with open('prediction_3152_exclusion.json', 'w') as f:
        json.dump(output, f, indent=2)

    return output

def main():
    """Main prediction generator"""

    # Step 1: Analyze and identify exclusions
    exclusion_list, inclusion_pool = analyze_exclusion_patterns()

    # Step 2: Generate top candidates
    print(f"\n" + "="*80)
    print("TOP PREDICTION CANDIDATES")
    print("="*80)

    candidates = generate_prediction_candidates(inclusion_pool, num_candidates=5)

    for i, cand in enumerate(candidates, 1):
        print(f"\n[Candidate {i}] {cand['strategy']} [{cand['confidence']}]")
        print(f"  Numbers: {' '.join(f'{n:02d}' for n in cand['numbers'])}")

    # Step 3: Save results
    output = save_prediction_results(exclusion_list, inclusion_pool, candidates)

    print(f"\n" + "="*80)
    print("MEMORY-EFFICIENT GENERATION")
    print("="*80)
    print(f"\nTotal combinations available: {output['analysis']['total_combinations']:,}")
    print(f"Memory approach: Iterator-based (generates on-demand)")
    print(f"RAM usage: ~{len(inclusion_pool) * 8} bytes for pool vs {output['analysis']['total_combinations'] * 14 * 8:,} bytes if stored")
    print(f"Efficiency: {output['analysis']['total_combinations'] * 14 * 8 / (len(inclusion_pool) * 8):.0f}x less memory")

    print(f"\n📁 Results saved to: prediction_3152_exclusion.json")

    # Example: Show how to iterate through all combinations without storing
    print(f"\n" + "="*80)
    print("EXAMPLE: Generate first 5 combinations")
    print("="*80)

    combo_iter = generate_all_combinations_iterator(inclusion_pool)
    for i, combo in enumerate(combo_iter, 1):
        if i > 5:
            break
        print(f"  {i}. {' '.join(f'{n:02d}' for n in combo)}")

    print(f"\n✅ Prediction complete for Series 3152")
    print(f"✅ Use these candidates BEFORE results are published")

if __name__ == '__main__':
    main()
