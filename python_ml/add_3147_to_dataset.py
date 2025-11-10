#!/usr/bin/env python3
"""
Add Series 3147 to the dataset
"""

import json

# Series 3147 actual results
SERIES_3147 = [
    [1, 3, 5, 7, 10, 12, 14, 15, 17, 18, 20, 21, 22, 25],
    [2, 5, 7, 8, 9, 10, 11, 15, 16, 17, 18, 21, 22, 25],
    [1, 3, 4, 5, 7, 10, 12, 14, 16, 19, 21, 22, 23, 25],
    [1, 2, 3, 4, 7, 10, 11, 13, 14, 16, 18, 19, 23, 25],
    [1, 6, 7, 8, 11, 12, 14, 15, 16, 18, 21, 22, 23, 24],
    [1, 3, 4, 5, 8, 11, 12, 15, 18, 19, 20, 22, 23, 24],
    [6, 7, 10, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25]
]

def main():
    # Load existing data
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)

    print(f"Loaded dataset: {len(data)} series")
    print(f"Range: {min(data.keys())} to {max(data.keys())}")
    print()

    # Add Series 3147
    if "3147" in data:
        print("⚠️  Series 3147 already exists, overwriting...")

    data["3147"] = SERIES_3147

    # Save updated data
    with open('full_series_data_expanded.json', 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Added Series 3147 to dataset")
    print(f"Updated dataset: {len(data)} series")

    # Verify
    series_ids = sorted([int(k) for k in data.keys()])
    print(f"New range: {min(series_ids)} to {max(series_ids)}")
    print()
    print("Series 3147 data:")
    for i, event in enumerate(data["3147"], 1):
        print(f"  Event {i}: {' '.join(f'{n:02d}' for n in event)}")

if __name__ == "__main__":
    main()
