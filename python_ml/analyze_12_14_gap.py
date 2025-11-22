import json

# Load data
with open('all_series_data.json', 'r') as f:
    data = json.load(f)

# Best result from simulation: Series 3133, Seed 70
series_id = "3133"
best_prediction = [1, 3, 5, 6, 8, 9, 10, 14, 16, 18, 19, 21, 23, 25]

print("=" * 80)
print("ANALYZING 12/14 GAP - Series 3133, Seed 70")
print("=" * 80)
print()

print(f"Prediction: {' '.join([f'{n:02d}' for n in best_prediction])}")
print()

# Check each event
actual_events = data[series_id]
for i, event in enumerate(actual_events, 1):
    event_set = set(event)
    pred_set = set(best_prediction)
    
    matches = event_set & pred_set
    missed = event_set - pred_set
    wrong = pred_set - event_set
    
    match_count = len(matches)
    
    print(f"Event {i}: {match_count}/14 matches")
    print(f"  Actual:  {' '.join([f'{n:02d}' for n in sorted(event)])}")
    
    if match_count == 12:
        print(f"  ✓ Matched ({match_count}): {' '.join([f'{n:02d}' for n in sorted(matches)])}")
        print(f"  ✗ Missed (2):  {' '.join([f'{n:02d}' for n in sorted(missed)])}")
        print(f"  ✗ Wrong (2):   {' '.join([f'{n:02d}' for n in sorted(wrong)])}")
        print()
        print(f"  → Perfect swap exists: Remove {sorted(wrong)}, Add {sorted(missed)}")
        
    print()

# Analyze frequency patterns
print("=" * 80)
print("FREQUENCY ANALYSIS")
print("=" * 80)
print()

# Get all numbers from all events
all_numbers = []
for event in actual_events:
    all_numbers.extend(event)

from collections import Counter
freq = Counter(all_numbers)

print("Number frequencies in Series 3133:")
for num in range(1, 26):
    count = freq.get(num, 0)
    in_pred = "✓" if num in best_prediction else " "
    print(f"  {num:02d}: {count}/7 events  {in_pred}")

print()
print("Missed numbers in 12/14 event:")
# Event 4 was the 12/14 match
event_4 = actual_events[3]
missed_in_event_4 = set(event_4) - set(best_prediction)
wrong_in_event_4 = set(best_prediction) - set(event_4)

for num in sorted(missed_in_event_4):
    count = freq.get(num, 0)
    print(f"  {num:02d}: appeared {count}/7 events in series")

print()
print("Wrong numbers in 12/14 event:")
for num in sorted(wrong_in_event_4):
    count = freq.get(num, 0)
    print(f"  {num:02d}: appeared {count}/7 events in series")
