import json
import sys

def validate_dataset(file_path):
    """Validate lottery dataset integrity."""

    print("=" * 70)
    print("DATASET VALIDATION REPORT")
    print("=" * 70)
    print()

    issues = []
    warnings = []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FATAL: Invalid JSON syntax - {e}")
        return False
    except FileNotFoundError:
        print(f"FATAL: File not found - {file_path}")
        return False

    # Check 1: Total series count
    series_count = len(data)
    print(f"Total series in dataset: {series_count}")
    if series_count != 201:
        issues.append(f"Expected 201 series, found {series_count}")
    else:
        print("  [PASS] Series count is correct (201)")

    # Check 2: Series range
    series_ids = sorted([int(sid) for sid in data.keys()])
    min_series = min(series_ids)
    max_series = max(series_ids)
    print(f"\nSeries range: {min_series} to {max_series}")

    if min_series != 2980:
        issues.append(f"Expected minimum series 2980, found {min_series}")
    else:
        print("  [PASS] Minimum series is 2980")

    if max_series != 3180:
        issues.append(f"Expected maximum series 3180, found {max_series}")
    else:
        print("  [PASS] Maximum series is 3180")

    # Check 3: Sequential series IDs
    expected_range = set(range(2980, 3181))
    actual_range = set(series_ids)
    missing = expected_range - actual_range
    extra = actual_range - expected_range

    if missing:
        issues.append(f"Missing series IDs: {sorted(missing)}")
    if extra:
        issues.append(f"Unexpected series IDs: {sorted(extra)}")

    if not missing and not extra:
        print("  [PASS] Series IDs are sequential with no gaps")

    # Check 4-7: Validate each series structure
    print("\nValidating series structure...")
    structure_issues = 0

    for series_id in series_ids:
        series_str = str(series_id)
        events = data[series_str]

        # Check: 7 events per series
        if len(events) != 7:
            issues.append(f"Series {series_id}: Expected 7 events, found {len(events)}")
            structure_issues += 1
            continue

        # Check each event
        for event_idx, event in enumerate(events, 1):
            # Check: 14 numbers per event
            if len(event) != 14:
                issues.append(f"Series {series_id} Event {event_idx}: Expected 14 numbers, found {len(event)}")
                structure_issues += 1
                continue

            # Check: All numbers in range 1-25
            for num in event:
                if not isinstance(num, int) or num < 1 or num > 25:
                    issues.append(f"Series {series_id} Event {event_idx}: Invalid number {num} (must be 1-25)")
                    structure_issues += 1
                    break

            # Check: No duplicates within event
            if len(event) != len(set(event)):
                duplicates = [n for n in event if event.count(n) > 1]
                issues.append(f"Series {series_id} Event {event_idx}: Duplicate numbers found: {set(duplicates)}")
                structure_issues += 1

            # Check: Numbers are sorted (not critical, but good practice)
            if event != sorted(event):
                warnings.append(f"Series {series_id} Event {event_idx}: Numbers not sorted")

    if structure_issues == 0:
        print(f"  [PASS] All {series_count} series have correct structure")
        print(f"  [PASS] All events have 14 numbers")
        print(f"  [PASS] All numbers are in range 1-25")
        print(f"  [PASS] No duplicate numbers found within events")
    else:
        print(f"  [FAIL] Found {structure_issues} structural issues")

    # Statistical overview
    print("\n" + "=" * 70)
    print("STATISTICAL OVERVIEW")
    print("=" * 70)

    all_numbers = []
    for series_id in series_ids:
        for event in data[str(series_id)]:
            all_numbers.extend(event)

    total_draws = len(all_numbers)
    print(f"Total number draws: {total_draws}")
    print(f"Expected draws: {series_count * 7 * 14} = {series_count} series × 7 events × 14 numbers")

    from collections import Counter
    number_freq = Counter(all_numbers)
    print(f"\nNumber frequency distribution:")
    print(f"  Min appearances: {min(number_freq.values())} (number {min(number_freq, key=number_freq.get)})")
    print(f"  Max appearances: {max(number_freq.values())} (number {max(number_freq, key=number_freq.get)})")
    print(f"  Average: {sum(number_freq.values()) / len(number_freq):.2f} per number")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if issues:
        print(f"\n[FAIL] Found {len(issues)} critical issues:")
        for i, issue in enumerate(issues[:10], 1):  # Show first 10
            print(f"  {i}. {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
    else:
        print("\n[PASS] Dataset validation PASSED")
        print("  - JSON syntax valid")
        print("  - 201 series present (2980-3180)")
        print("  - All series have 7 events")
        print("  - All events have 14 numbers")
        print("  - All numbers in valid range (1-25)")
        print("  - No duplicate numbers within events")
        print("  - Sequential series IDs with no gaps")

    if warnings:
        print(f"\n[WARN] Found {len(warnings)} warnings (non-critical):")
        for i, warning in enumerate(warnings[:5], 1):
            print(f"  {i}. {warning}")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more warnings")

    print("\n" + "=" * 70)

    if issues:
        print("\nRECOMMENDATION: Fix critical issues before proceeding")
        return False
    else:
        print("\nRECOMMENDATION: Dataset is ready for analysis")
        return True

if __name__ == "__main__":
    file_path = r"E:\Python\random\Random\data\full_series_data.json"
    success = validate_dataset(file_path)
    sys.exit(0 if success else 1)
