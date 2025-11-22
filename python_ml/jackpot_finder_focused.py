"""
Focused Jackpot Finder - Series 3141-3150 (10 series)
Find jackpots faster with optimized approach
"""

import json
import random
from collections import defaultdict
import math

# Load data
with open('all_series_data.json', 'r') as f:
    data = json.load(f)

def find_jackpots_fast(series_id, max_tries_per_event=1000000):
    """
    Find jackpots for a series with progress tracking
    """
    if str(series_id) not in data:
        return []
    
    actual_events = data[str(series_id)]
    jackpots_found = []
    
    for event_idx, event in enumerate(actual_events, 1):
        event_set = set(event)
        
        # Try to find this jackpot
        for try_num in range(1, max_tries_per_event + 1):
            prediction = sorted(random.sample(range(1, 26), 14))
            
            if set(prediction) == event_set:
                jackpots_found.append({
                    'series': series_id,
                    'event': event_idx,
                    'tries': try_num,
                    'combination': event
                })
                print(f"  Event {event_idx}: FOUND in {try_num:,} tries!")
                break
        else:
            jackpots_found.append({
                'series': series_id,
                'event': event_idx,
                'tries': None,  # Not found
                'combination': event
            })
            print(f"  Event {event_idx}: NOT FOUND (exceeded {max_tries_per_event:,} tries)")
    
    return jackpots_found

print("=" * 80)
print("FOCUSED JACKPOT FINDER - Series 3141-3150")
print("Finding ALL 70 jackpots (7 per series × 10 series)")
print("Max 1M tries per jackpot")
print("=" * 80)
print()

all_results = []

for series_id in range(3141, 3151):
    if str(series_id) not in data:
        continue
    
    print(f"Series {series_id}:")
    jackpots = find_jackpots_fast(series_id, max_tries_per_event=1000000)
    all_results.extend(jackpots)
    
    found_count = sum(1 for j in jackpots if j['tries'] is not None)
    print(f"  Summary: {found_count}/7 jackpots found")
    print()

print("=" * 80)
print("COMPLETE RESULTS")
print("=" * 80)
print()

found = [r for r in all_results if r['tries'] is not None]
not_found = [r for r in all_results if r['tries'] is None]

print(f"JACKPOTS FOUND: {len(found)}/{len(all_results)}")
print(f"{'Series':<8} {'Event':<6} {'Tries':>12}")
print("-" * 35)

for j in found:
    print(f"{j['series']:<8} {j['event']:<6} {j['tries']:>12,}")

print()
print(f"NOT FOUND (exceeded 1M tries): {len(not_found)}")
if not_found:
    print(f"{'Series':<8} {'Event':<6}")
    print("-" * 20)
    for j in not_found:
        print(f"{j['series']:<8} {j['event']:<6}")

print()
print("=" * 80)
print("STATISTICAL ANALYSIS")
print("=" * 80)
print()

if found:
    tries_list = [j['tries'] for j in found]
    
    min_tries = min(tries_list)
    max_tries = max(tries_list)
    avg_tries = sum(tries_list) / len(tries_list)
    median_tries = sorted(tries_list)[len(tries_list) // 2]
    
    print(f"Total found: {len(found)}/{len(all_results)} ({len(found)/len(all_results)*100:.1f}%)")
    print(f"Total not found: {len(not_found)}/{len(all_results)} ({len(not_found)/len(all_results)*100:.1f}%)")
    print()
    print(f"Tries statistics (for found jackpots):")
    print(f"  Minimum: {min_tries:,}")
    print(f"  Maximum: {max_tries:,}")
    print(f"  Average: {avg_tries:,.0f}")
    print(f"  Median: {median_tries:,}")
    print()
    
    # Theoretical
    total_combinations = math.comb(25, 14)
    theoretical_avg = total_combinations
    
    print(f"Theoretical expectation:")
    print(f"  Total combinations: {total_combinations:,}")
    print(f"  Expected tries per jackpot: {theoretical_avg:,}")
    print(f"  Actual vs Theoretical: {avg_tries/theoretical_avg:.2%}")
    print()
    
    # Exponential distribution
    lambda_param = 1 / avg_tries
    
    print(f"Exponential Distribution Fit:")
    print(f"  λ (lambda) = {lambda_param:.12f}")
    print(f"  Mean (1/λ) = {1/lambda_param:,.0f} tries")
    print()
    
    print(f"Prediction - Probability of finding jackpot within X tries:")
    for tries in [100000, 200000, 500000, 1000000, 2000000, 5000000]:
        prob = 1 - math.exp(-lambda_param * tries)
        print(f"  {tries:>9,} tries: {prob*100:6.2f}%")
    
    print()
    
    # Mathematical curve for NEXT jackpot
    print("=" * 80)
    print("PREDICTIVE MODEL - Next Jackpot Occurrence")
    print("=" * 80)
    print()
    
    # Sort by series and event
    found_sorted = sorted(found, key=lambda x: (x['series'], x['event']))
    
    print(f"Historical pattern (jackpots in order):")
    print(f"{'Index':<6} {'Series':<8} {'Event':<6} {'Tries':>12}")
    print("-" * 40)
    
    for idx, j in enumerate(found_sorted, 1):
        print(f"{idx:<6} {j['series']:<8} {j['event']:<6} {j['tries']:>12,}")
    
    print()
    
    # Calculate cumulative tries
    cumulative = 0
    cumulative_list = []
    for j in found_sorted:
        cumulative += j['tries']
        cumulative_list.append(cumulative)
    
    print("Cumulative tries to find N jackpots:")
    print(f"{'N':<6} {'Total Tries':>15} {'Avg per Jackpot':>18}")
    print("-" * 45)
    
    for i, cum in enumerate(cumulative_list[::7], 1):  # Every 7th (one series)
        n = i * 7
        avg_per = cum / n
        print(f"{n:<6} {cum:>15,} {avg_per:>18,.0f}")
    
    print()
    
    # Predict next jackpot
    next_jackpot_num = len(found) + 1
    predicted_tries = int(1 / lambda_param)  # Mean of exponential distribution
    
    print(f"PREDICTION for next jackpot (#{next_jackpot_num}):")
    print(f"  Expected tries: {predicted_tries:,}")
    print(f"  50% probability within: {int(math.log(2) / lambda_param):,} tries")
    print(f"  90% probability within: {int(math.log(10) / lambda_param):,} tries")
    print(f"  99% probability within: {int(math.log(100) / lambda_param):,} tries")

# Save results
output = {
    'series_range': '3141-3150',
    'total_jackpots': len(all_results),
    'found': len(found),
    'not_found': len(not_found),
    'jackpots': all_results,
    'statistics': {
        'min_tries': min(tries_list) if found else None,
        'max_tries': max(tries_list) if found else None,
        'avg_tries': avg_tries if found else None,
        'median_tries': median_tries if found else None,
        'lambda': lambda_param if found else None,
        'theoretical_avg': math.comb(25, 14),
    } if found else None
}

with open('jackpot_finder_focused_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print()
print("📁 Results saved to: jackpot_finder_focused_results.json")
