"""
Expand dataset by combining data_toadd.txt with database export

Current: 166 series (2980-3145)
Database export: 174 series (2898-3143)
Result: 249 series (2898-3146)!
"""

import json

def parse_database_export():
    """Parse the JSON database export"""
    with open('../Results/database_export_2898_3143_20251105_135513.json') as f:
        export_data = json.load(f)

    series_data = {}
    for series in export_data['data']:
        series_id = series['series_id']
        events = []
        for event in series['events']:
            events.append(event['numbers'])

        if len(events) == 7:
            series_data[series_id] = events

    return series_data

def load_current_data():
    """Load current full_series_data.json"""
    with open('full_series_data.json') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def main():
    print("="*70)
    print("EXPANDING DATASET")
    print("="*70)
    print()

    # Load both sources
    print("Loading database export (2898-3143)...")
    try:
        db_export = parse_database_export()
        print(f"✅ Loaded {len(db_export)} series from database export")
    except FileNotFoundError:
        print("❌ Database export not found, fetching from git...")
        import subprocess
        subprocess.run([
            'git', 'show',
            'origin/main:Results/database_export_2898_3143_20251105_135513.json'
        ], stdout=open('database_export_temp.json', 'w'))

        with open('database_export_temp.json') as f:
            export_data = json.load(f)

        db_export = {}
        for series in export_data['data']:
            series_id = series['series_id']
            events = [event['numbers'] for event in series['events']]
            if len(events) == 7:
                db_export[series_id] = events

        print(f"✅ Loaded {len(db_export)} series from git")

    print()
    print("Loading current data (2980-3146)...")
    current_data = load_current_data()
    print(f"✅ Loaded {len(current_data)} series from current data")
    print()

    # Merge
    print("Merging datasets...")
    combined = {}

    # Add database export (older series)
    for series_id, events in db_export.items():
        combined[series_id] = events

    # Add current data (newer series, will override any duplicates)
    for series_id, events in current_data.items():
        combined[series_id] = events

    print(f"✅ Combined: {len(combined)} total series")
    print()

    # Show ranges
    all_ids = sorted(combined.keys())
    print("Dataset range:")
    print(f"  First series: {all_ids[0]}")
    print(f"  Last series: {all_ids[-1]}")
    print(f"  Total series: {len(all_ids)}")
    print(f"  Total events: {len(all_ids) * 7}")
    print()

    # Identify new series
    new_series = set(combined.keys()) - set(current_data.keys())
    if new_series:
        new_sorted = sorted(new_series)
        print(f"✅ Added {len(new_series)} NEW series:")
        print(f"   Range: {new_sorted[0]} to {new_sorted[-1]}")
        print()

    # Save
    output_file = 'full_series_data_expanded.json'
    with open(output_file, 'w') as f:
        # Convert to string keys for JSON
        json_data = {str(k): v for k, v in combined.items()}
        json.dump(json_data, f, indent=2)

    print(f"💾 Saved to: {output_file}")
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Previous: {len(current_data)} series")
    print(f"Now: {len(combined)} series")
    print(f"Growth: +{len(combined) - len(current_data)} series (+{(len(combined) - len(current_data))/len(current_data)*100:.1f}%)")
    print()
    print("More data = better ML learning!")
    print("="*70)

if __name__ == "__main__":
    main()
