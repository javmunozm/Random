"""
Comprehensive Jackpot Finder - Series 3135-3152
Find ALL jackpots and analyze the pattern of tries needed
"""

import json
import random
from collections import defaultdict
import math

# Load data
with open('all_series_data.json', 'r') as f:
    data = json.load(f)

def find_all_jackpots_in_series(series_id, max_tries=1000000):
    """
    Find all jackpots (14/14 matches) in a series by random generation
    
    Returns:
        List of jackpots found with metadata
    """
    if str(series_id) not in data:
        return []
    
    actual_events = data[str(series_id)]
    jackpots_found = []
    
    # Track which event numbers have jackpots
    for event_idx, event in enumerate(actual_events, 1):
        event_set = set(event)
        
        # Try to find this jackpot with random predictions
        tries = 0
        found = False
        
        for try_num in range(1, max_tries + 1):
            # Generate random prediction
            prediction = sorted(random.sample(range(1, 26), 14))
            tries += 1
            
            # Check if it's a jackpot for this event
            if set(prediction) == event_set:
                jackpots_found.append({
                    'series': series_id,
                    'event': event_idx,
                    'tries': tries,
                    'combination': event,
                    'prediction': prediction
                })
                found = True
                break
        
        if not found:
            # Mark as not found within max_tries
            jackpots_found.append({
                'series': series_id,
                'event': event_idx,
                'tries': None,  # Not found
                'combination': event,
                'prediction': None
            })
    
    return jackpots_found

print("=" * 80)
print("COMPREHENSIVE JACKPOT FINDER - Series 3135-3152")
print("Finding ALL jackpots (7 per series) with random generation")
print("=" * 80)
print()

all_results = []
series_range = range(3135, 3153)  # 3135-3152 = 18 series

for series_id in series_range:
    if str(series_id) not in data:
        continue
    
    print(f"Series {series_id}:", end=" ", flush=True)
    
    jackpots = find_all_jackpots_in_series(series_id, max_tries=1000000)
    
    # Count found jackpots
    found_count = sum(1 for j in jackpots if j['tries'] is not None)
    total_tries = sum(j['tries'] for j in jackpots if j['tries'] is not None)
    avg_tries = total_tries / found_count if found_count > 0 else None
    
    print(f"{found_count}/7 jackpots found, Avg tries: {avg_tries:,.0f}" if avg_tries else f"{found_count}/7 found")
    
    all_results.extend(jackpots)

print()
print("=" * 80)
print("DETAILED RESULTS")
print("=" * 80)
print()

# Organize by series
found_jackpots = [r for r in all_results if r['tries'] is not None]
not_found = [r for r in all_results if r['tries'] is None]

print("Jackpots FOUND:")
print(f"{'Series':<8} {'Event':<6} {'Tries':>12} {'Combination'}")
print("-" * 80)

for jackpot in found_jackpots:
    combo_str = ' '.join([f'{n:02d}' for n in jackpot['combination']])
    print(f"{jackpot['series']:<8} {jackpot['event']:<6} {jackpot['tries']:>12,} {combo_str}")

print()
print(f"Jackpots NOT FOUND (exceeded 1M tries):")
print(f"{'Series':<8} {'Event':<6} {'Combination'}")
print("-" * 80)

for jackpot in not_found:
    combo_str = ' '.join([f'{n:02d}' for n in jackpot['combination']])
    print(f"{jackpot['series']:<8} {jackpot['event']:<6} {combo_str}")

print()
print("=" * 80)
print("STATISTICAL ANALYSIS")
print("=" * 80)
print()

if found_jackpots:
    tries_list = [j['tries'] for j in found_jackpots]
    
    # Basic statistics
    min_tries = min(tries_list)
    max_tries = max(tries_list)
    avg_tries = sum(tries_list) / len(tries_list)
    median_tries = sorted(tries_list)[len(tries_list) // 2]
    
    print(f"Total jackpots found: {len(found_jackpots)}/{len(all_results)} ({len(found_jackpots)/len(all_results)*100:.1f}%)")
    print(f"Total not found: {len(not_found)}/{len(all_results)} ({len(not_found)/len(all_results)*100:.1f}%)")
    print()
    print(f"Tries statistics:")
    print(f"  Minimum: {min_tries:,}")
    print(f"  Maximum: {max_tries:,}")
    print(f"  Average: {avg_tries:,.0f}")
    print(f"  Median: {median_tries:,}")
    print()
    
    # Theoretical probability
    total_combinations = math.comb(25, 14)
    theoretical_prob = 1 / total_combinations
    theoretical_avg_tries = total_combinations
    
    print(f"Theoretical:")
    print(f"  Total combinations: {total_combinations:,}")
    print(f"  Probability per try: {theoretical_prob:.10f} ({theoretical_prob*100:.6f}%)")
    print(f"  Expected tries: {theoretical_avg_tries:,.0f}")
    print()
    
    print(f"Actual vs Theoretical:")
    print(f"  Actual avg: {avg_tries:,.0f}")
    print(f"  Theoretical: {theoretical_avg_tries:,.0f}")
    print(f"  Ratio: {avg_tries/theoretical_avg_tries:.2%}")

print()
print("=" * 80)
print("PATTERN ANALYSIS - CURVE FITTING")
print("=" * 80)
print()

if found_jackpots:
    # Sort by tries
    sorted_jackpots = sorted(found_jackpots, key=lambda x: x['tries'])
    
    # Try to fit a curve
    # X = jackpot index (1, 2, 3, ...)
    # Y = tries needed
    
    print("Jackpots ordered by tries:")
    print(f"{'Index':<8} {'Tries':>12} {'Series':<8} {'Event'}")
    print("-" * 50)
    
    for idx, jackpot in enumerate(sorted_jackpots, 1):
        print(f"{idx:<8} {jackpot['tries']:>12,} {jackpot['series']:<8} {jackpot['event']}")
    
    print()
    
    # Calculate distribution statistics
    # Group by ranges
    ranges = [
        (0, 100000, "0-100K"),
        (100000, 200000, "100K-200K"),
        (200000, 400000, "200K-400K"),
        (400000, 600000, "400K-600K"),
        (600000, 800000, "600K-800K"),
        (800000, 1000000, "800K-1M"),
    ]
    
    print("Distribution by try ranges:")
    for min_val, max_val, label in ranges:
        count = sum(1 for t in tries_list if min_val <= t < max_val)
        pct = count / len(tries_list) * 100 if tries_list else 0
        print(f"  {label:12}: {count:3} jackpots ({pct:5.1f}%)")
    
    print()
    
    # Exponential distribution fit
    # P(X > x) = e^(-λx) where λ = 1/mean
    lambda_param = 1 / avg_tries
    
    print("Exponential Distribution Model:")
    print(f"  λ (lambda) = {lambda_param:.10f}")
    print(f"  Mean (1/λ) = {1/lambda_param:,.0f}")
    print()
    
    # Predict probability of finding jackpot in X tries
    print("Probability of finding jackpot within X tries:")
    for tries in [10000, 50000, 100000, 200000, 500000, 1000000]:
        prob = 1 - math.exp(-lambda_param * tries)
        print(f"  {tries:>8,} tries: {prob:7.2%}")

# Save results
output = {
    'series_range': f'{min(series_range)}-{max(series_range)}',
    'total_jackpots': len(all_results),
    'found': len(found_jackpots),
    'not_found': len(not_found),
    'jackpots': all_results,
    'statistics': {
        'min_tries': min(tries_list) if found_jackpots else None,
        'max_tries': max(tries_list) if found_jackpots else None,
        'avg_tries': avg_tries if found_jackpots else None,
        'median_tries': median_tries if found_jackpots else None,
        'theoretical_avg': math.comb(25, 14),
    } if found_jackpots else None
}

with open('jackpot_finder_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print()
print("📁 Results saved to: jackpot_finder_results.json")
