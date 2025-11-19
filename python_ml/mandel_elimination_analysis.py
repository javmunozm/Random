#!/usr/bin/env python3
"""
Mandel-Style Jackpot Finder: Systematic Elimination Approach
Step 1: Analyze if exact 14/14 combinations ever repeat
Step 2: Eliminate non-repeating combinations from search pool
Step 3: Test enhanced jackpot finding with reduced search space
"""

import json
from collections import Counter
from datetime import datetime

def load_all_series_data(min_series=2982):
    """
    Load full series data from JSON file

    Args:
        min_series: Minimum series ID to include (default: 2982)

    Returns:
        Dictionary of series data, filtered to only include series >= min_series
    """
    with open('full_series_data.json', 'r') as f:
        all_data = json.load(f)

    # Filter to only include series >= min_series
    filtered_data = {k: v for k, v in all_data.items() if int(k) >= min_series}

    return filtered_data

def combination_to_tuple(combination):
    """Convert combination list to sorted tuple for hashing"""
    return tuple(sorted(combination))

def analyze_combination_repetitions(all_data):
    """
    Analyze if any exact 14/14 combinations have ever repeated
    across all series and events
    """
    print("="*80)
    print("STEP 1: ANALYZING COMBINATION REPETITIONS")
    print("="*80)
    print("\nChecking if exact 14/14 combinations ever repeat...")

    # Track all combinations seen
    combination_counter = Counter()
    combination_appearances = {}  # combo -> list of (series, event) where it appeared

    total_combinations = 0

    for series_id, events in sorted(all_data.items(), key=lambda x: int(x[0])):
        for event_idx, event in enumerate(events, 1):
            combo_tuple = combination_to_tuple(event)
            combination_counter[combo_tuple] += 1
            total_combinations += 1

            if combo_tuple not in combination_appearances:
                combination_appearances[combo_tuple] = []
            combination_appearances[combo_tuple].append((series_id, event_idx))

    print(f"\n📊 Analysis Results:")
    print(f"Total series: {len(all_data)}")
    print(f"Total events analyzed: {total_combinations}")
    print(f"Unique combinations: {len(combination_counter)}")
    print(f"Duplicate combinations: {sum(1 for count in combination_counter.values() if count > 1)}")

    # Find repeating combinations
    repeating_combos = {combo: count for combo, count in combination_counter.items() if count > 1}

    if repeating_combos:
        print(f"\n⚠️ FOUND {len(repeating_combos)} REPEATING COMBINATIONS!")
        print("\nRepeating combinations:")
        for combo, count in sorted(repeating_combos.items(), key=lambda x: x[1], reverse=True):
            combo_str = ' '.join(f'{n:02d}' for n in combo)
            appearances = combination_appearances[combo]
            print(f"\n  {combo_str} - appeared {count} times:")
            for series_id, event_idx in appearances:
                print(f"    Series {series_id}, Event {event_idx}")
    else:
        print("\n✅ NO EXACT COMBINATIONS HAVE EVER REPEATED!")
        print("This means we can eliminate all previous winning combinations from future searches.")

    return {
        'total_series': len(all_data),
        'total_events': total_combinations,
        'unique_combinations': len(combination_counter),
        'repeating_combinations': len(repeating_combos),
        'all_combinations': list(combination_counter.keys()),
        'combination_appearances': combination_appearances,
        'repeats': repeating_combos
    }

def calculate_search_space_reduction(analysis_result):
    """Calculate how much we can reduce the search space"""
    print("\n" + "="*80)
    print("STEP 2: SEARCH SPACE REDUCTION CALCULATION")
    print("="*80)

    from math import comb

    total_possible = comb(25, 14)  # C(25,14)
    used_combinations = analysis_result['unique_combinations']
    remaining_combinations = total_possible - used_combinations
    reduction_percent = (used_combinations / total_possible) * 100

    print(f"\n📈 Search Space Analysis:")
    print(f"Total possible combinations: {total_possible:,}")
    print(f"Already used (can eliminate): {used_combinations:,}")
    print(f"Remaining possibilities: {remaining_combinations:,}")
    print(f"Search space reduction: {reduction_percent:.4f}%")

    # Expected improvement
    original_expected_tries = total_possible / 7  # 7 winning combos per series
    new_expected_tries = remaining_combinations / 7
    improvement_factor = original_expected_tries / new_expected_tries

    print(f"\n⚡ Expected Performance Improvement:")
    print(f"Original expected tries: {original_expected_tries:,.0f}")
    print(f"New expected tries: {new_expected_tries:,.0f}")
    print(f"Improvement factor: {improvement_factor:.6f}x")
    print(f"Speedup: {((improvement_factor - 1) * 100):.4f}%")

    if reduction_percent < 1:
        print(f"\n⚠️ Warning: Only {reduction_percent:.4f}% reduction - minimal impact")
        print(f"With {analysis_result['total_events']} events out of {total_possible:,} possibilities,")
        print(f"the elimination strategy provides negligible benefit.")

    return {
        'total_possible': total_possible,
        'used': used_combinations,
        'remaining': remaining_combinations,
        'reduction_percent': reduction_percent,
        'improvement_factor': improvement_factor
    }

def check_series_pattern_overlap(all_data):
    """
    Check if numbers from previous series appear in later series
    to see if there are other elimination strategies
    """
    print("\n" + "="*80)
    print("STEP 3: PATTERN OVERLAP ANALYSIS")
    print("="*80)

    print("\nAnalyzing number frequency across all events...")

    number_frequency = Counter()
    for series_id, events in all_data.items():
        for event in events:
            for number in event:
                number_frequency[number] += 1

    total_events = sum(len(events) for events in all_data.values())
    total_slots = total_events * 14

    print(f"\n📊 Number Frequency Analysis:")
    print(f"Total events: {total_events}")
    print(f"Total number slots: {total_slots}")
    print(f"\nNumber frequency (sorted by occurrence):")

    for number in range(1, 26):
        count = number_frequency[number]
        percentage = (count / total_events) * 100
        expected = total_slots / 25  # Expected if uniform
        deviation = ((count - expected) / expected) * 100
        print(f"  {number:02d}: {count:4d} times ({percentage:5.1f}% of events, "
              f"{deviation:+.1f}% vs expected)")

    # Check for never-appearing or rarely-appearing numbers
    avg_frequency = sum(number_frequency.values()) / 25
    rare_numbers = [n for n in range(1, 26) if number_frequency[n] < avg_frequency * 0.7]
    hot_numbers = [n for n in range(1, 26) if number_frequency[n] > avg_frequency * 1.3]

    if rare_numbers:
        print(f"\n❄️ Rarely appearing numbers (< 70% of average): {rare_numbers}")
    if hot_numbers:
        print(f"\n🔥 Frequently appearing numbers (> 130% of average): {hot_numbers}")

    # Check consecutive series patterns
    print("\n" + "="*80)
    print("STEP 4: CONSECUTIVE SERIES PATTERN CHECK")
    print("="*80)

    series_ids = sorted([int(s) for s in all_data.keys()])

    if len(series_ids) >= 2:
        print("\nChecking if consecutive series share exact combinations...")
        consecutive_matches = 0

        for i in range(len(series_ids) - 1):
            curr_series = str(series_ids[i])
            next_series = str(series_ids[i + 1])

            curr_combos = {combination_to_tuple(e) for e in all_data[curr_series]}
            next_combos = {combination_to_tuple(e) for e in all_data[next_series]}

            overlap = curr_combos & next_combos
            if overlap:
                consecutive_matches += 1
                print(f"  Series {curr_series} -> {next_series}: {len(overlap)} shared combinations")

        if consecutive_matches == 0:
            print("\n✅ NO consecutive series share exact combinations!")
        else:
            print(f"\n⚠️ Found {consecutive_matches} cases of consecutive series sharing combinations")

def main():
    print("="*80)
    print("MANDEL-STYLE JACKPOT FINDER")
    print("Systematic Elimination Approach")
    print("="*80)
    print("\nObjective: Use historical patterns to eliminate impossible combinations")
    print("Strategy: If combinations never repeat, exclude all previous winners")
    print("="*80)

    # Load data (series 2982 onwards only)
    all_data = load_all_series_data(min_series=2982)
    print(f"\n✅ Loaded {len(all_data)} series (2982-3150)")

    # Step 1: Analyze repetitions
    analysis = analyze_combination_repetitions(all_data)

    # Step 2: Calculate reduction
    reduction = calculate_search_space_reduction(analysis)

    # Step 3: Pattern overlap
    check_series_pattern_overlap(all_data)

    # Save results
    output = {
        'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'analysis': {
            'total_series': analysis['total_series'],
            'total_events': analysis['total_events'],
            'unique_combinations': analysis['unique_combinations'],
            'repeating_combinations': analysis['repeating_combinations'],
            'repetition_details': {
                str(combo): {
                    'count': len(appearances),
                    'appearances': [(s, e) for s, e in appearances]
                }
                for combo, appearances in analysis['combination_appearances'].items()
                if len(appearances) > 1
            }
        },
        'reduction': reduction,
        'conclusion': {
            'can_eliminate_previous': analysis['repeating_combinations'] == 0,
            'elimination_count': analysis['unique_combinations'],
            'reduction_percent': reduction['reduction_percent'],
            'improvement_factor': reduction['improvement_factor']
        }
    }

    output_file = 'mandel_elimination_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "="*80)
    print("FINAL CONCLUSION")
    print("="*80)

    if analysis['repeating_combinations'] == 0:
        print("\n✅ ELIMINATION STRATEGY CONFIRMED:")
        print(f"   - All {analysis['unique_combinations']} previous combinations can be eliminated")
        print(f"   - Search space reduced by {reduction['reduction_percent']:.4f}%")
        print(f"   - Expected improvement: {reduction['improvement_factor']:.6f}x")

        if reduction['reduction_percent'] < 1:
            print(f"\n⚠️ HOWEVER: Reduction is only {reduction['reduction_percent']:.4f}%")
            print(f"   With {analysis['total_events']} events vs {reduction['total_possible']:,} total combinations,")
            print(f"   the practical benefit is negligible.")
            print(f"\n💡 RECOMMENDATION: Elimination strategy mathematically valid but practically ineffective")
            print(f"   The search space is so large that removing {analysis['unique_combinations']} combinations")
            print(f"   has minimal impact on jackpot finding speed.")
    else:
        print(f"\n⚠️ FOUND {analysis['repeating_combinations']} REPEATING COMBINATIONS")
        print("   Cannot use simple elimination strategy - some combinations do repeat!")

    print(f"\n📁 Detailed results saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
