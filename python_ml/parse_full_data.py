"""
Parse data_toadd.txt to create full SERIES_DATA dictionary
This contains all 166 series (2980-3145) that the C# model uses
"""

import json

def parse_data_file(filename):
    """Parse the data_toadd.txt file into SERIES_DATA format"""
    series_data = {}

    with open(filename, 'r') as f:
        lines = [line.strip() for line in f.readlines()]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a series ID line
        if line and ':' in line:
            series_id = int(line.replace(':', '').strip())
            events = []

            # Read next 7 lines (the 7 events)
            for j in range(1, 8):
                if i + j < len(lines):
                    event_line = lines[i + j].strip()
                    if event_line:
                        # Parse numbers
                        numbers = [int(n) for n in event_line.split()]
                        events.append(numbers)

            if len(events) == 7:
                series_data[series_id] = events

            # Move past this series (1 ID line + 7 event lines + 1 blank)
            i += 9
        else:
            i += 1

    return series_data

if __name__ == "__main__":
    # Parse the file
    print("Parsing data_toadd.txt...")
    series_data = parse_data_file('data_toadd.txt')

    print(f"Total series parsed: {len(series_data)}")
    print(f"Series range: {min(series_data.keys())} to {max(series_data.keys())}")

    # Verify a few entries
    sample_ids = sorted(series_data.keys())[:3] + sorted(series_data.keys())[-3:]
    print(f"\nSample series IDs: {sample_ids}")

    for sid in sample_ids[:2]:
        print(f"\nSeries {sid}:")
        print(f"  Events: {len(series_data[sid])}")
        print(f"  Event 1: {series_data[sid][0]}")

    # Save to JSON for easy loading
    output_file = 'full_series_data.json'
    with open(output_file, 'w') as f:
        # Convert keys to strings for JSON
        json_data = {str(k): v for k, v in series_data.items()}
        json.dump(json_data, f, indent=2)

    print(f"\n✅ Saved to {output_file}")
    print(f"Total series: {len(series_data)}")
