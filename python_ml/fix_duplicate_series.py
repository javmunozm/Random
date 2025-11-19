#!/usr/bin/env python3
"""
Fix duplicate series data in full_series_data.json
Correct series: 3009, 3072, 3103, 3106
"""

import json

# Load current data
with open('full_series_data.json', 'r') as f:
    data = json.load(f)

print("Fixing duplicate series data...")
print(f"Total series before: {len(data)}")

# Correct data provided by user
corrections = {
    "3009": [
        [1, 3, 4, 6, 8, 9, 10, 12, 13, 14, 18, 21, 22, 24],
        [1, 2, 4, 6, 7, 8, 9, 10, 13, 14, 20, 21, 22, 24],
        [1, 4, 5, 6, 7, 8, 10, 12, 13, 14, 18, 20, 24, 25],
        [4, 5, 10, 11, 12, 13, 14, 15, 17, 18, 19, 21, 23, 24],
        [1, 4, 5, 6, 8, 10, 13, 15, 20, 21, 22, 23, 24, 25],
        [3, 4, 5, 10, 14, 16, 17, 18, 19, 20, 21, 22, 24, 25],
        [1, 3, 4, 7, 12, 13, 14, 16, 19, 20, 21, 23, 24, 25]
    ],
    "3072": [
        [1, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 21, 22, 25],
        [1, 2, 4, 5, 7, 8, 9, 10, 13, 17, 18, 20, 23, 25],
        [1, 3, 6, 7, 9, 11, 14, 16, 17, 19, 20, 21, 23, 24],
        [3, 4, 5, 7, 10, 11, 12, 17, 18, 20, 22, 23, 24, 25],
        [1, 2, 5, 6, 8, 9, 10, 11, 12, 14, 16, 21, 22, 23],
        [1, 6, 8, 9, 10, 11, 12, 13, 14, 18, 21, 22, 23, 24],
        [1, 4, 6, 8, 9, 12, 14, 15, 18, 19, 21, 22, 23, 24]
    ],
    "3103": [
        [2, 3, 7, 8, 9, 10, 11, 13, 16, 17, 19, 20, 23, 24],
        [2, 3, 4, 5, 7, 8, 9, 10, 11, 14, 16, 18, 23, 25],
        [2, 5, 6, 7, 10, 11, 13, 14, 16, 17, 20, 23, 24, 25],
        [1, 5, 7, 8, 9, 10, 11, 13, 15, 17, 19, 21, 23, 25],
        [1, 2, 4, 5, 7, 9, 10, 11, 14, 15, 16, 17, 18, 21],
        [3, 4, 5, 6, 7, 8, 10, 15, 17, 18, 19, 23, 24, 25],
        [3, 4, 5, 6, 10, 11, 12, 14, 15, 17, 18, 22, 24, 25]
    ],
    "3106": [
        [4, 5, 6, 7, 9, 11, 12, 13, 15, 18, 19, 21, 23, 24],
        [2, 3, 5, 6, 7, 9, 11, 17, 18, 19, 21, 23, 24, 25],
        [2, 4, 5, 6, 7, 8, 9, 10, 13, 18, 20, 23, 24, 25],
        [1, 2, 3, 7, 8, 10, 11, 13, 15, 16, 18, 19, 24, 25],
        [1, 2, 3, 9, 10, 12, 13, 14, 16, 17, 19, 21, 23, 24],
        [5, 6, 7, 9, 10, 11, 14, 17, 18, 21, 22, 23, 24, 25],
        [1, 4, 5, 6, 7, 8, 10, 12, 15, 18, 19, 20, 22, 23]
    ]
}

# Update data
for series_id, events in corrections.items():
    if series_id in data:
        old_data = data[series_id]
        data[series_id] = events
        print(f"\n✓ Updated series {series_id}")
        print(f"  Old event 1: {old_data[0]}")
        print(f"  New event 1: {events[0]}")
    else:
        print(f"⚠ Series {series_id} not found in data")

# Save corrected data
with open('full_series_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n✅ Corrected data saved to full_series_data.json")
print(f"Total series after: {len(data)}")
print("\nCorrected series: 3009, 3072, 3103, 3106")
