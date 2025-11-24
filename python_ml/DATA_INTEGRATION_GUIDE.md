# Data Integration Guide - Adding New Series

**Purpose**: Step-by-step guide for integrating new lottery series data into the main dataset.

---

## 🔄 WHEN TO USE THIS GUIDE

Use this guide when:
- New lottery draw results arrive
- You have a `series_*_actual.json` file that needs integration
- Data count doesn't match expected total
- Starting a new Claude Code session and data seems outdated

---

## ✅ STEP 1: Verify New Series Data

Check if new series file exists:

```bash
cd python_ml
ls series_*_actual.json | tail -5
```

Example output:
```
series_3148_actual.json
series_3149_actual.json
series_3150_actual.json
series_3151_actual.json
series_3152_actual.json  ← New series to integrate
```

---

## ✅ STEP 2: Validate Data Format

Check the new series file structure:

```bash
cd python_ml
cat series_3152_actual.json
```

**Expected Format**:
```json
{
  "series_id": 3152,
  "date_received": "2025-11-22",
  "events": [
    [1, 4, 5, 6, 8, 9, 10, 12, 13, 18, 21, 23, 24, 25],
    [1, 4, 5, 8, 10, 13, 15, 17, 18, 20, 21, 23, 24, 25],
    [1, 3, 6, 7, 12, 13, 14, 15, 16, 19, 20, 21, 22, 25],
    [2, 4, 5, 6, 7, 9, 10, 14, 16, 17, 20, 22, 23, 24],
    [1, 2, 4, 8, 10, 11, 15, 16, 17, 19, 20, 21, 23, 25],
    [2, 3, 4, 5, 6, 9, 10, 12, 17, 18, 20, 21, 23, 24],
    [1, 2, 4, 5, 6, 7, 8, 12, 17, 18, 22, 23, 24, 25]
  ]
}
```

**Validate**:
- ✅ Has `series_id` field
- ✅ Has `events` array
- ✅ Contains exactly 7 events
- ✅ Each event has exactly 14 numbers
- ✅ All numbers are 1-25
- ✅ No duplicate numbers within each event

---

## ✅ STEP 3: Check Current Dataset Status

See what's already in the main dataset:

```bash
cd python_ml
python -c "import json; d=json.load(open('full_series_data.json')); print(f'Current total: {len(d)}'); print(f'Latest series: {max(d.keys())}'); print(f'Series to add: Check if newer exists')"
```

---

## ✅ STEP 4: Integrate New Series (Automated)

**Method 1: Python Script** (Recommended)

Create and run integration script:

```bash
cd python_ml
cat > integrate_new_series.py << 'EOF'
#!/usr/bin/env python3
import json
import sys

def integrate_series(series_id):
    # Load main dataset
    with open('full_series_data.json', 'r') as f:
        data = json.load(f)

    # Check if already integrated
    if str(series_id) in data:
        print(f"Series {series_id} already in dataset")
        return False

    # Load new series
    series_file = f'series_{series_id}_actual.json'
    try:
        with open(series_file, 'r') as f:
            new_series = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {series_file} not found")
        return False

    # Validate
    events = new_series.get('events', [])
    if len(events) != 7:
        print(f"ERROR: Expected 7 events, got {len(events)}")
        return False

    for i, event in enumerate(events):
        if len(event) != 14:
            print(f"ERROR: Event {i+1} has {len(event)} numbers (expected 14)")
            return False

    # Add to dataset
    data[str(series_id)] = events

    # Save
    with open('full_series_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Sync to all_series_data.json
    with open('all_series_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print(f"SUCCESS: Series {series_id} integrated")
    print(f"Total series now: {len(data)}")
    print(f"Range: {min(data.keys())} - {max(data.keys())}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python integrate_new_series.py <series_id>")
        print("Example: python integrate_new_series.py 3152")
        sys.exit(1)

    series_id = int(sys.argv[1])
    integrate_series(series_id)
EOF

python integrate_new_series.py 3152
```

**Method 2: Manual Python Commands**

```bash
cd python_ml
python << 'EOF'
import json

# 1. Load main dataset
with open('full_series_data.json', 'r') as f:
    data = json.load(f)

# 2. Load new series
with open('series_3152_actual.json', 'r') as f:
    series_3152 = json.load(f)

# 3. Add to dataset
data['3152'] = series_3152['events']

# 4. Save main dataset
with open('full_series_data.json', 'w') as f:
    json.dump(data, f, indent=2)

# 5. Sync to alternative file
with open('all_series_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"SUCCESS: Series 3152 integrated")
print(f"Total: {len(data)}, Range: {min(data.keys())}-{max(data.keys())}")
EOF
```

---

## ✅ STEP 5: Verify Integration

Check that integration succeeded:

```bash
cd python_ml
python -c "
import json
data = json.load(open('full_series_data.json'))
series_id = '3152'

print('='*60)
print('INTEGRATION VERIFICATION')
print('='*60)
print(f'Total series: {len(data)}')
print(f'Latest series: {max(data.keys())}')
print(f'Series {series_id} present: {series_id in data}')
if series_id in data:
    print(f'Series {series_id} events: {len(data[series_id])}')
    print(f'Event 1: {data[series_id][0][:5]}... (first 5 numbers)')
print('='*60)
"
```

**Expected Output**:
```
============================================================
INTEGRATION VERIFICATION
============================================================
Total series: 173
Latest series: 3152
Series 3152 present: True
Series 3152 events: 7
Event 1: [1, 4, 5, 6, 8]... (first 5 numbers)
============================================================
```

---

## ✅ STEP 6: Update Documentation

Update the following files:

1. **LATEST_DATA_STATUS.md**:
   - Update "Total Series"
   - Update "Latest Series"
   - Update "Last Updated" date
   - Add new series to "Historical Series" table

2. **CLAUDE.md**:
   - Update "Current Dataset" section
   - Update series count in "Data Files" section

3. **README.md** (if exists):
   - Update any data statistics

---

## ✅ STEP 7: Test Data Loading

Verify scripts can load the new data:

```bash
cd python_ml

# Test 1: Load with winning strategy
python winning_strategy.py

# Test 2: Check comprehensive study
python -c "from comprehensive_study import load_series_data; d=load_series_data(); print(f'Loaded {len(d)} series')"

# Test 3: GA simulations can load
python -c "from ga_10k_simulations import load_series_data; d=load_series_data(); print(f'GA can load {len(d)} series')"
```

All should show the updated series count.

---

## 🔍 TROUBLESHOOTING

### Issue: "File not found"
```bash
# Check you're in the right directory
pwd
# Should be: E:\Python\random\Random\python_ml
```

### Issue: "JSON decode error"
```bash
# Validate JSON syntax
cd python_ml
python -m json.tool series_3152_actual.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

### Issue: "Series already exists"
```bash
# Check if series is already integrated
cd python_ml
python -c "import json; d=json.load(open('full_series_data.json')); print('3152' in d)"
```

### Issue: "Data counts don't match"
```bash
# Check both files are synced
cd python_ml
python -c "
import json
d1 = json.load(open('full_series_data.json'))
d2 = json.load(open('all_series_data.json'))
print(f'full_series_data.json: {len(d1)} series')
print(f'all_series_data.json: {len(d2)} series')
print(f'Match: {len(d1) == len(d2)}')
"
```

---

## 📋 QUICK REFERENCE

**Current Status** (2025-11-23):
- Total Series: 173
- Latest: 3152
- File: `python_ml/full_series_data.json`

**Add New Series** (Quick Command):
```bash
cd python_ml && python << EOF
import json
data = json.load(open('full_series_data.json'))
new = json.load(open('series_XXXX_actual.json'))  # Replace XXXX
data['XXXX'] = new['events']  # Replace XXXX
json.dump(data, open('full_series_data.json', 'w'), indent=2)
json.dump(data, open('all_series_data.json', 'w'), indent=2)
print(f"Done: {len(data)} series")
EOF
```

**Verify**:
```bash
cd python_ml && python -c "import json; d=json.load(open('full_series_data.json')); print(f'Latest: {max(d.keys())}, Total: {len(d)}')"
```

---

*Keep this guide handy when integrating new lottery series data.*
