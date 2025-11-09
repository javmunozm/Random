# Database Export Instructions

## Goal
Export historical lottery data from LuckyDb for series 2800-2979 (~170 additional series)

---

## Option 1: Query to Check Available Data

```bash
dotnet run query "SELECT MIN(series_id) as earliest, MAX(series_id) as latest, COUNT(DISTINCT series_id) as total FROM event"
```

This will show you what data range is available in the database.

---

## Option 2: Export Missing Ranges

If data exists for earlier series, export them:

```bash
# Export series 2800-2897
dotnet run export 2800 2897

# Export series 2908-2979
dotnet run export 2908 2979
```

The C# program should create JSON export files in the `Results/` folder.

---

## Option 3: Provide Data in Any Format

If you can access the data through any means:

1. **JSON format** (preferred):
```json
{
  "2800": [
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15],
    ... (7 events total)
  ],
  "2801": [...],
  ...
}
```

2. **CSV format**:
```
series_id,event_num,numbers
2800,1,"01 02 03 04 05 06 07 08 09 10 11 12 13 14"
2800,2,"01 02 03 04 05 06 07 08 09 10 11 12 13 15"
...
```

3. **Plain text**:
```
Series 2800:
Event 1: 01 02 03 04 05 06 07 08 09 10 11 12 13 14
Event 2: 01 02 03 04 05 06 07 08 09 10 11 12 13 15
...
```

I can parse any of these formats and merge with our current dataset.

---

## Current Status

**We have**: 176 series (2898-2907, 2980-3146)
**We need**: Series 2800-2897 and 2908-2979 (~170 additional series)

**Why we can't scrape**:
- Network environment blocks all HTTP requests (403 Forbidden)
- Playwright browser downloads blocked
- Site has enterprise anti-bot protection

**Best solution**: Database export from LuckyDb

---

## What Happens Next

Once you provide the data:
1. I'll merge it with current 176-series dataset
2. Re-train model with expanded data (~346 total series!)
3. Generate improved predictions with more historical depth
4. Commit everything to git

This could potentially improve model accuracy by having 2x more training data!
