#!/usr/bin/env python3
"""
Insert Series 3152 data and find jackpot using winning strategy
"""

import json
import sys
from winning_strategy import WinningStrategy

def insert_series_3152(events_data):
    """
    Insert Series 3152 into all_series_data.json

    Args:
        events_data: List of 7 events, each containing 14 numbers
    """
    # Validate input
    if len(events_data) != 7:
        raise ValueError(f"Expected 7 events, got {len(events_data)}")

    for i, event in enumerate(events_data, 1):
        if len(event) != 14:
            raise ValueError(f"Event {i}: Expected 14 numbers, got {len(event)}")
        if not all(1 <= n <= 25 for n in event):
            raise ValueError(f"Event {i}: Numbers must be between 1 and 25")

    # Load existing data
    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    # Check if already exists
    if '3152' in data:
        print("⚠️  Series 3152 already exists in database")
        overwrite = input("Overwrite? (yes/no): ")
        if overwrite.lower() != 'yes':
            print("❌ Cancelled")
            return False

    # Add new series
    data['3152'] = events_data

    # Save
    with open('all_series_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("✅ Series 3152 inserted successfully")
    print(f"\nData added:")
    for i, event in enumerate(events_data, 1):
        print(f"  Event {i}: {' '.join(f'{n:02d}' for n in sorted(event))}")

    return True

def find_jackpot_3152():
    """Find jackpot for Series 3152 using winning strategy"""

    # Load data
    with open('all_series_data.json', 'r') as f:
        data = json.load(f)

    if '3152' not in data:
        print("❌ Series 3152 not found in database")
        print("Please insert data first")
        return None

    # Run winning strategy
    strategy = WinningStrategy(data)
    result = strategy.find_jackpot(3152, use_fallback=True)

    return result

def main():
    """Main entry point"""

    if len(sys.argv) > 1 and sys.argv[1] == 'find':
        # Just find jackpot (data must already be inserted)
        print("="*80)
        print("FINDING JACKPOT FOR SERIES 3152")
        print("="*80)
        result = find_jackpot_3152()
        if result and result['found']:
            print(f"\n🎉 JACKPOT FOUND!")
            print(f"Combination: {' '.join(f'{n:02d}' for n in result['jackpots_found'][0])}")
            print(f"Tries: {result.get('total_tries', result.get('tries')):,}")
            print(f"Time: {result['time_seconds']:.3f} seconds")
    else:
        # Interactive mode: insert data then find
        print("="*80)
        print("INSERT SERIES 3152 DATA")
        print("="*80)
        print("\nEnter the 7 events for Series 3152")
        print("Format: 14 space-separated numbers (1-25) per event\n")

        events_data = []
        for i in range(1, 8):
            while True:
                try:
                    line = input(f"Event {i}: ").strip()
                    numbers = [int(x) for x in line.split()]

                    if len(numbers) != 14:
                        print(f"  ❌ Expected 14 numbers, got {len(numbers)}")
                        continue

                    if not all(1 <= n <= 25 for n in numbers):
                        print(f"  ❌ Numbers must be between 1 and 25")
                        continue

                    if len(set(numbers)) != 14:
                        print(f"  ❌ Numbers must be unique")
                        continue

                    events_data.append(sorted(numbers))
                    break

                except ValueError:
                    print("  ❌ Invalid input. Please enter 14 numbers separated by spaces")

        # Insert data
        print("\n" + "="*80)
        if insert_series_3152(events_data):
            print("\n" + "="*80)
            print("FINDING JACKPOT")
            print("="*80)
            result = find_jackpot_3152()

            if result and result['found']:
                print(f"\n🎉 JACKPOT FOUND!")
                print(f"Combination: {' '.join(f'{n:02d}' for n in result['jackpots_found'][0])}")
                print(f"Tries: {result.get('total_tries', result.get('tries')):,}")
                print(f"Time: {result['time_seconds']:.3f} seconds")
                print(f"Phase: {result['phase']}")

if __name__ == '__main__':
    main()
