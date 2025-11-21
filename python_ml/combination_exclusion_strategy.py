#!/usr/bin/env python3
"""
Combination Exclusion Strategy for Series 3152 Prediction

CORRECT APPROACH: Exclude COMBINATIONS that won't appear, not individual numbers

Exclusion criteria:
1. Historical combinations (Mandel exclusion - already appeared, won't repeat)
2. Pattern-violating combinations (too many gaps, missing critical patterns)
3. Invalid distributions (all numbers from one column, etc.)
"""

import json
from itertools import combinations
from collections import Counter

def load_historical_combinations():
    """Load all historical combinations to exclude (Mandel strategy)"""
    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    historical_combos = set()
    for series_id, events in data.items():
        for event in events:
            combo = tuple(sorted(event))
            historical_combos.add(combo)

    return historical_combos

def analyze_ml_patterns(recent_series_ids):
    """Analyze ML patterns from recent series to identify critical constraints"""

    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    # Pattern 1: Count critical numbers (appear in most events)
    counter = Counter()
    total_events = 0

    for sid in recent_series_ids:
        for event in data[str(sid)]:
            total_events += 1
            for num in event:
                counter[num] += 1

    # Identify critical numbers (appear in >50% of events)
    critical_threshold = total_events * 0.5
    critical_numbers = {num for num, count in counter.items() if count > critical_threshold}

    # Pattern 2: Identify rare numbers (appear in <30% of events)
    rare_threshold = total_events * 0.3
    rare_numbers = {num for num in range(1, 26) if counter.get(num, 0) < rare_threshold}

    # Pattern 3: Column distribution analysis
    # Column 0: 1-9, Column 1: 10-19, Column 2: 20-25
    col_distributions = []
    for sid in recent_series_ids:
        for event in data[str(sid)]:
            col0 = len([n for n in event if 1 <= n <= 9])
            col1 = len([n for n in event if 10 <= n <= 19])
            col2 = len([n for n in event if 20 <= n <= 25])
            col_distributions.append((col0, col1, col2))

    # Get typical ranges for each column
    col0_values = [d[0] for d in col_distributions]
    col1_values = [d[1] for d in col_distributions]
    col2_values = [d[2] for d in col_distributions]

    col0_range = (min(col0_values), max(col0_values))
    col1_range = (min(col1_values), max(col1_values))
    col2_range = (min(col2_values), max(col2_values))

    return {
        'critical_numbers': critical_numbers,
        'rare_numbers': rare_numbers,
        'col0_range': col0_range,
        'col1_range': col1_range,
        'col2_range': col2_range,
        'total_events': total_events
    }

def should_exclude_combination(combo, patterns, historical_combos):
    """
    Determine if a combination should be EXCLUDED based on learned patterns

    Args:
        combo: Tuple of 14 sorted numbers
        patterns: Dict of ML-learned patterns
        historical_combos: Set of historical combinations to exclude

    Returns:
        (bool, str): (should_exclude, reason)
    """

    # Rule 1: Exclude historical combinations (Mandel exclusion)
    if combo in historical_combos:
        return (True, "Historical (already appeared)")

    # Rule 2: Must contain at least 50% of critical numbers
    critical_overlap = len(set(combo) & patterns['critical_numbers'])
    if critical_overlap < len(patterns['critical_numbers']) * 0.5:
        return (True, f"Insufficient critical numbers ({critical_overlap}/{len(patterns['critical_numbers'])})")

    # Rule 3: Cannot have more than 8 rare numbers
    rare_count = len(set(combo) & patterns['rare_numbers'])
    if rare_count > 8:
        return (True, f"Too many rare numbers ({rare_count}/14)")

    # Rule 4: Column distribution must be within observed ranges
    col0 = len([n for n in combo if 1 <= n <= 9])
    col1 = len([n for n in combo if 10 <= n <= 19])
    col2 = len([n for n in combo if 20 <= n <= 25])

    col0_min, col0_max = patterns['col0_range']
    col1_min, col1_max = patterns['col1_range']
    col2_min, col2_max = patterns['col2_range']

    # Allow some flexibility (±1)
    if not (col0_min - 1 <= col0 <= col0_max + 1):
        return (True, f"Column 0 out of range ({col0} not in [{col0_min-1}, {col0_max+1}])")
    if not (col1_min - 1 <= col1 <= col1_max + 1):
        return (True, f"Column 1 out of range ({col1} not in [{col1_min-1}, {col1_max+1}])")
    if not (col2_min - 1 <= col2 <= col2_max + 1):
        return (True, f"Column 2 out of range ({col2} not in [{col2_min-1}, {col2_max+1}])")

    # Passed all exclusion rules
    return (False, "Valid candidate")

def generate_valid_combinations_iterator(patterns, historical_combos, max_candidates=None):
    """
    Memory-efficient generator for valid combinations (excludes invalid ones)

    Yields combinations that pass all exclusion filters
    """

    count = 0
    excluded_count = 0
    exclusion_reasons = Counter()

    for combo in combinations(range(1, 26), 14):
        should_exclude, reason = should_exclude_combination(combo, patterns, historical_combos)

        if should_exclude:
            excluded_count += 1
            exclusion_reasons[reason] += 1
            continue

        # Valid candidate
        count += 1
        yield combo

        if max_candidates and count >= max_candidates:
            break

    return count, excluded_count, exclusion_reasons

def predict_series_3152():
    """Generate Series 3152 predictions using combination exclusion"""

    print("="*80)
    print("SERIES 3152 PREDICTION - COMBINATION EXCLUSION STRATEGY")
    print("="*80)

    # Step 1: Load historical combinations (Mandel exclusion)
    print("\n[Step 1] Loading historical combinations...")
    historical_combos = load_historical_combinations()
    print(f"  Historical combinations to exclude: {len(historical_combos):,}")

    # Step 2: Analyze ML patterns from recent series
    print("\n[Step 2] Analyzing ML patterns...")
    recent_series = [3147, 3148, 3149, 3150, 3151]
    patterns = analyze_ml_patterns(recent_series)

    print(f"  Critical numbers ({len(patterns['critical_numbers'])}): {sorted(patterns['critical_numbers'])}")
    print(f"  Rare numbers ({len(patterns['rare_numbers'])}): {sorted(patterns['rare_numbers'])}")
    print(f"  Column 0 range: {patterns['col0_range']}")
    print(f"  Column 1 range: {patterns['col1_range']}")
    print(f"  Column 2 range: {patterns['col2_range']}")

    # Step 3: Generate valid candidates (exclusion filtering)
    print("\n[Step 3] Generating valid candidates (excluding invalid combinations)...")
    print("  This may take a moment...\n")

    valid_combos = []
    excluded_count = 0
    exclusion_reasons = Counter()

    for combo in combinations(range(1, 26), 14):
        should_exclude, reason = should_exclude_combination(combo, patterns, historical_combos)

        if should_exclude:
            excluded_count += 1
            exclusion_reasons[reason] += 1
        else:
            valid_combos.append(combo)

            # Limit to first 10,000 valid candidates for memory
            if len(valid_combos) >= 10000:
                break

    print(f"  Total combinations checked: {len(valid_combos) + excluded_count:,}")
    print(f"  Valid candidates found: {len(valid_combos):,}")
    print(f"  Excluded combinations: {excluded_count:,}")
    print(f"  Exclusion rate: {excluded_count / (len(valid_combos) + excluded_count) * 100:.1f}%")

    print(f"\n  Exclusion breakdown:")
    for reason, count in exclusion_reasons.most_common():
        print(f"    {reason}: {count:,}")

    # Step 4: Show top candidates
    print(f"\n" + "="*80)
    print("TOP 10 VALID CANDIDATES")
    print("="*80)

    for i, combo in enumerate(valid_combos[:10], 1):
        print(f"\n[Candidate {i}]")
        print(f"  Numbers: {' '.join(f'{n:02d}' for n in combo)}")

        # Show why it's valid
        critical_overlap = len(set(combo) & patterns['critical_numbers'])
        rare_count = len(set(combo) & patterns['rare_numbers'])
        col0 = len([n for n in combo if 1 <= n <= 9])
        col1 = len([n for n in combo if 10 <= n <= 19])
        col2 = len([n for n in combo if 20 <= n <= 25])

        print(f"  Critical: {critical_overlap}/{len(patterns['critical_numbers'])} | "
              f"Rare: {rare_count}/14 | "
              f"Columns: [{col0}, {col1}, {col2}]")

    # Step 5: Calculate total valid space
    print(f"\n" + "="*80)
    print("PREDICTION SUMMARY")
    print("="*80)

    total_possible = 4457400
    estimated_valid = len(valid_combos) * (4457400 / (len(valid_combos) + excluded_count))

    print(f"\nTotal possible combinations: {total_possible:,}")
    print(f"Estimated valid combinations: {estimated_valid:,.0f}")
    print(f"Space reduction: {(1 - estimated_valid / total_possible) * 100:.1f}%")
    print(f"\nFirst {len(valid_combos):,} valid candidates generated")
    print(f"Memory usage: ~{len(valid_combos) * 14 * 8 / 1024 / 1024:.1f} MB")

    # Save results
    output = {
        'series_id': 3152,
        'strategy': 'Combination Exclusion',
        'exclusion_criteria': {
            'historical_combinations': len(historical_combos),
            'critical_numbers': sorted(patterns['critical_numbers']),
            'rare_numbers': sorted(patterns['rare_numbers']),
            'column_ranges': {
                'col0': patterns['col0_range'],
                'col1': patterns['col1_range'],
                'col2': patterns['col2_range']
            }
        },
        'results': {
            'valid_candidates_generated': len(valid_combos),
            'excluded_count': excluded_count,
            'exclusion_rate': excluded_count / (len(valid_combos) + excluded_count),
            'estimated_total_valid': int(estimated_valid)
        },
        'top_10_candidates': [list(c) for c in valid_combos[:10]],
        'exclusion_reasons': dict(exclusion_reasons)
    }

    with open('combination_exclusion_3152.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n📁 Results saved to: combination_exclusion_3152.json")

    return valid_combos

if __name__ == '__main__':
    valid_combos = predict_series_3152()
