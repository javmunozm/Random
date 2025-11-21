#!/usr/bin/env python3
"""
Validate combination exclusion strategy on historical data
Test if excluding pattern-violating combinations successfully captures actual jackpots
"""

import json
from itertools import combinations
from collections import Counter

def load_all_data():
    with open('all_series_data.json', 'r') as f:
        return json.load(f)

def analyze_ml_patterns(recent_series_ids, all_data):
    """Analyze ML patterns from recent series"""
    counter = Counter()
    total_events = 0

    for sid in recent_series_ids:
        for event in all_data[str(sid)]:
            total_events += 1
            for num in event:
                counter[num] += 1

    critical_threshold = total_events * 0.5
    critical_numbers = {num for num, count in counter.items() if count > critical_threshold}

    rare_threshold = total_events * 0.3
    rare_numbers = {num for num in range(1, 26) if counter.get(num, 0) < rare_threshold}

    col_distributions = []
    for sid in recent_series_ids:
        for event in all_data[str(sid)]:
            col0 = len([n for n in event if 1 <= n <= 9])
            col1 = len([n for n in event if 10 <= n <= 19])
            col2 = len([n for n in event if 20 <= n <= 25])
            col_distributions.append((col0, col1, col2))

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
    }

def should_exclude_combination(combo, patterns, historical_combos):
    """Determine if combination should be excluded"""

    if combo in historical_combos:
        return (True, "Historical")

    critical_overlap = len(set(combo) & patterns['critical_numbers'])
    if critical_overlap < len(patterns['critical_numbers']) * 0.5:
        return (True, "Insufficient critical")

    rare_count = len(set(combo) & patterns['rare_numbers'])
    if rare_count > 8:
        return (True, "Too many rare")

    col0 = len([n for n in combo if 1 <= n <= 9])
    col1 = len([n for n in combo if 10 <= n <= 19])
    col2 = len([n for n in combo if 20 <= n <= 25])

    col0_min, col0_max = patterns['col0_range']
    col1_min, col1_max = patterns['col1_range']
    col2_min, col2_max = patterns['col2_range']

    if not (col0_min - 1 <= col0 <= col0_max + 1):
        return (True, "Column 0 range")
    if not (col1_min - 1 <= col1 <= col1_max + 1):
        return (True, "Column 1 range")
    if not (col2_min - 1 <= col2 <= col2_max + 1):
        return (True, "Column 2 range")

    return (False, "Valid")

def validate_on_series(target_series, lookback_series, all_data):
    """Validate combination exclusion on a single series"""

    # Build historical combinations (before target)
    historical_combos = set()
    for sid_str, events in all_data.items():
        if int(sid_str) < target_series:
            for event in events:
                historical_combos.add(tuple(sorted(event)))

    # Get patterns from lookback
    patterns = analyze_ml_patterns(lookback_series, all_data)

    # Get actual events for target
    actual_events = all_data[str(target_series)]

    # Check if actual events would be excluded
    results = []
    for i, actual_event in enumerate(actual_events, 1):
        actual_combo = tuple(sorted(actual_event))
        should_exclude, reason = should_exclude_combination(actual_combo, patterns, historical_combos)

        results.append({
            'event': i,
            'combination': list(actual_combo),
            'excluded': should_exclude,
            'reason': reason
        })

    return {
        'target_series': target_series,
        'patterns': {
            'critical_count': len(patterns['critical_numbers']),
            'rare_count': len(patterns['rare_numbers']),
            'col0_range': patterns['col0_range'],
            'col1_range': patterns['col1_range'],
            'col2_range': patterns['col2_range']
        },
        'results': results,
        'valid_count': sum(1 for r in results if not r['excluded']),
        'excluded_count': sum(1 for r in results if r['excluded'])
    }

def run_validation(test_range_start, test_range_end, lookback_count=5):
    """Run validation across multiple series"""

    all_data = load_all_data()

    print("="*80)
    print("COMBINATION EXCLUSION VALIDATION")
    print("="*80)
    print(f"\nTesting on Series {test_range_start}-{test_range_end}")
    print(f"Using {lookback_count} series lookback\n")

    all_results = []

    for target_id in range(test_range_start, test_range_end + 1):
        lookback_series = list(range(target_id - lookback_count, target_id))

        print(f"\n{'='*80}")
        print(f"SERIES {target_id}")
        print(f"{'='*80}")

        result = validate_on_series(target_id, lookback_series, all_data)

        print(f"Patterns: Critical={result['patterns']['critical_count']}, "
              f"Rare={result['patterns']['rare_count']}")
        print(f"Column ranges: {result['patterns']['col0_range']}, "
              f"{result['patterns']['col1_range']}, {result['patterns']['col2_range']}")

        print(f"\n{'Event':<8} {'Status':<12} {'Reason':<30} {'Combination'}")
        print("-" * 80)

        for r in result['results']:
            status = "❌ EXCLUDED" if r['excluded'] else "✅ VALID"
            combo_str = ' '.join(f"{n:02d}" for n in r['combination'][:7]) + ' ...'
            print(f"Event {r['event']:<3} {status:<12} {r['reason']:<30} {combo_str}")

        print(f"\nSummary: Valid={result['valid_count']}/7, Excluded={result['excluded_count']}/7")

        all_results.append(result)

    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}\n")

    total_valid = sum(r['valid_count'] for r in all_results)
    total_excluded = sum(r['excluded_count'] for r in all_results)
    total_events = len(all_results) * 7

    print(f"Series tested: {len(all_results)}")
    print(f"Total events: {total_events}")
    print(f"Valid (not excluded): {total_valid}/{total_events} ({total_valid/total_events*100:.1f}%)")
    print(f"Excluded (false positives): {total_excluded}/{total_events} ({total_excluded/total_events*100:.1f}%)")

    print(f"\n{'Series':<10} {'Valid':<15} {'Excluded':<15} {'Success Rate'}")
    print("-" * 80)
    for r in all_results:
        success_rate = r['valid_count'] / 7 * 100
        print(f"{r['target_series']:<10} {r['valid_count']}/7{'':<11} {r['excluded_count']}/7{'':<11} {success_rate:.1f}%")

    # Key metric: We want 100% valid (0% excluded actual jackpots)
    if total_excluded == 0:
        print(f"\n✅ PERFECT: 0% false exclusions - all actual jackpots would be in valid set!")
    else:
        print(f"\n⚠️  WARNING: {total_excluded/total_events*100:.1f}% false exclusions - some jackpots would be excluded!")

    # Save results
    with open('combination_exclusion_validation.json', 'w') as f:
        json.dump({
            'test_range': f"{test_range_start}-{test_range_end}",
            'summary': {
                'total_valid': total_valid,
                'total_excluded': total_excluded,
                'total_events': total_events,
                'valid_rate': total_valid / total_events,
                'false_exclusion_rate': total_excluded / total_events
            },
            'detailed_results': all_results
        }, f, indent=2)

    print(f"\n📁 Results saved to: combination_exclusion_validation.json")

    return all_results

if __name__ == '__main__':
    run_validation(3147, 3151, lookback_count=5)
