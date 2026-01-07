#!/usr/bin/env python3
"""
Stress Test for Production Predictor
=====================================

Tests:
1. Performance under load: 1000 rapid predictions
2. Edge cases: First/latest series
3. Extreme patterns: Various series ranges
4. Error handling: Invalid series, missing data

Benchmarks:
- Target: Single prediction < 10ms
- Alert: > 50ms
"""

import sys
import time
import json
import traceback
from pathlib import Path
from statistics import mean, stdev, median

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from production_predictor import load_data, predict, evaluate, validate, latest

# Constants
TARGET_MS = 10
ALERT_MS = 50
LOAD_TEST_ITERATIONS = 1000


def format_time(ms):
    """Format time with status indicator."""
    if ms < TARGET_MS:
        return f"{ms:.3f}ms [PASS]"
    elif ms < ALERT_MS:
        return f"{ms:.3f}ms [WARN]"
    else:
        return f"{ms:.3f}ms [ALERT]"


def validate_prediction(pred, series_id):
    """Validate prediction structure and content."""
    errors = []

    # Check structure
    if not isinstance(pred, dict):
        return ["Prediction is not a dictionary"]

    required_keys = ["series", "sets", "ranked", "hot_outside"]
    for key in required_keys:
        if key not in pred:
            errors.append(f"Missing key: {key}")

    if errors:
        return errors

    # Check series
    if pred["series"] != series_id:
        errors.append(f"Series mismatch: expected {series_id}, got {pred['series']}")

    # Check sets
    if len(pred["sets"]) != 8:
        errors.append(f"Expected 8 sets, got {len(pred['sets'])}")

    for i, s in enumerate(pred["sets"]):
        if len(s) != 14:
            errors.append(f"Set {i+1}: Expected 14 numbers, got {len(s)}")
        if len(set(s)) != 14:
            errors.append(f"Set {i+1}: Contains duplicates")
        if not all(1 <= n <= 25 for n in s):
            errors.append(f"Set {i+1}: Numbers out of range [1-25]")
        if sorted(s) != s:
            errors.append(f"Set {i+1}: Not sorted")

    # Check ranked
    if len(pred["ranked"]) != 25:
        errors.append(f"Ranked: Expected 25 numbers, got {len(pred['ranked'])}")
    if set(pred["ranked"]) != set(range(1, 26)):
        errors.append("Ranked: Does not contain numbers 1-25")

    # Check hot_outside
    if len(pred["hot_outside"]) < 2:
        errors.append(f"Hot outside: Expected at least 2, got {len(pred['hot_outside'])}")

    return errors


def test_performance_under_load(data):
    """Test 1: 1000 rapid predictions - measure timing."""
    print("\n" + "="*70)
    print("TEST 1: Performance Under Load (1000 rapid predictions)")
    print("="*70)

    last = latest(data)
    # Use a range of series for variety
    series_range = list(range(2981, min(2981 + LOAD_TEST_ITERATIONS, last + 1)))
    if len(series_range) < LOAD_TEST_ITERATIONS:
        # Repeat series if we don't have enough
        series_range = series_range * (LOAD_TEST_ITERATIONS // len(series_range) + 1)
    series_range = series_range[:LOAD_TEST_ITERATIONS]

    times = []
    errors = []

    start_total = time.perf_counter()

    for i, sid in enumerate(series_range):
        start = time.perf_counter()
        try:
            pred = predict(data, sid)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

            # Validate first 10 and every 100th
            if i < 10 or i % 100 == 0:
                validation_errors = validate_prediction(pred, sid)
                if validation_errors:
                    errors.append(f"Series {sid}: {validation_errors}")
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
            errors.append(f"Series {sid}: {str(e)}")

    total_time = (time.perf_counter() - start_total) * 1000

    # Statistics
    avg_time = mean(times)
    min_time = min(times)
    max_time = max(times)
    std_time = stdev(times) if len(times) > 1 else 0
    med_time = median(times)

    # Percentiles
    sorted_times = sorted(times)
    p95 = sorted_times[int(len(sorted_times) * 0.95)]
    p99 = sorted_times[int(len(sorted_times) * 0.99)]

    above_target = sum(1 for t in times if t > TARGET_MS)
    above_alert = sum(1 for t in times if t > ALERT_MS)

    print(f"\nIterations: {LOAD_TEST_ITERATIONS}")
    print(f"Total time: {total_time:.2f}ms ({total_time/1000:.3f}s)")
    print(f"\nTiming Statistics:")
    print(f"  Average:  {format_time(avg_time)}")
    print(f"  Median:   {format_time(med_time)}")
    print(f"  Min:      {min_time:.3f}ms")
    print(f"  Max:      {max_time:.3f}ms")
    print(f"  Std Dev:  {std_time:.3f}ms")
    print(f"  P95:      {format_time(p95)}")
    print(f"  P99:      {format_time(p99)}")
    print(f"\nThreshold Analysis:")
    print(f"  Above {TARGET_MS}ms (target):  {above_target} ({above_target/LOAD_TEST_ITERATIONS*100:.1f}%)")
    print(f"  Above {ALERT_MS}ms (alert):   {above_alert} ({above_alert/LOAD_TEST_ITERATIONS*100:.1f}%)")

    if errors:
        print(f"\nErrors: {len(errors)}")
        for err in errors[:5]:
            print(f"  - {err}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")

    passed = avg_time < TARGET_MS and len(errors) == 0
    print(f"\nRESULT: {'PASS' if passed else 'FAIL'}")

    return {
        "name": "Performance Under Load",
        "passed": passed,
        "iterations": LOAD_TEST_ITERATIONS,
        "avg_ms": avg_time,
        "max_ms": max_time,
        "p95_ms": p95,
        "p99_ms": p99,
        "errors": len(errors)
    }


def test_edge_cases(data):
    """Test 2: Edge cases - first available series and latest series."""
    print("\n" + "="*70)
    print("TEST 2: Edge Cases")
    print("="*70)

    results = []

    # Find first available series (need prior series for prediction)
    all_series = sorted(int(s) for s in data.keys())
    first_series = all_series[1]  # Second series because we need prior data
    last_series = all_series[-1]

    test_cases = [
        ("First available series (minimal history)", first_series),
        ("Latest series (normal case)", last_series),
        ("Mid-range series", (first_series + last_series) // 2),
    ]

    all_passed = True

    for desc, sid in test_cases:
        print(f"\n{desc}: Series {sid}")
        print("-" * 50)

        start = time.perf_counter()
        try:
            pred = predict(data, sid)
            elapsed_ms = (time.perf_counter() - start) * 1000

            validation_errors = validate_prediction(pred, sid)

            if validation_errors:
                print(f"  Time: {format_time(elapsed_ms)}")
                print(f"  Validation: FAIL")
                for err in validation_errors:
                    print(f"    - {err}")
                all_passed = False
                results.append({"case": desc, "passed": False, "time_ms": elapsed_ms, "errors": validation_errors})
            else:
                print(f"  Time: {format_time(elapsed_ms)}")
                print(f"  Sets: 8 (14 numbers each)")
                print(f"  Validation: PASS")

                # Show first set as sample
                print(f"  Sample (Set 1): {pred['sets'][0]}")

                passed = elapsed_ms < ALERT_MS
                results.append({"case": desc, "passed": passed, "time_ms": elapsed_ms, "errors": []})
                if not passed:
                    all_passed = False

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  Time: {elapsed_ms:.3f}ms")
            print(f"  Error: {str(e)}")
            all_passed = False
            results.append({"case": desc, "passed": False, "time_ms": elapsed_ms, "errors": [str(e)]})

    print(f"\nRESULT: {'PASS' if all_passed else 'FAIL'}")

    return {
        "name": "Edge Cases",
        "passed": all_passed,
        "cases": results
    }


def test_extreme_patterns(data):
    """Test 3: Various series to check robustness."""
    print("\n" + "="*70)
    print("TEST 3: Extreme Patterns / Robustness")
    print("="*70)

    all_series = sorted(int(s) for s in data.keys())

    # Select diverse series for testing
    test_series = [
        all_series[1],      # Near start
        all_series[len(all_series)//4],   # 25%
        all_series[len(all_series)//2],   # 50%
        all_series[3*len(all_series)//4], # 75%
        all_series[-2],     # Near end
        all_series[-1],     # Last
    ]

    results = []
    all_passed = True

    print(f"\nTesting {len(test_series)} series across the data range...")

    for sid in test_series:
        start = time.perf_counter()
        try:
            pred = predict(data, sid)
            elapsed_ms = (time.perf_counter() - start) * 1000

            validation_errors = validate_prediction(pred, sid)

            # Check for set diversity (sets should be different)
            unique_sets = len(set(tuple(s) for s in pred["sets"]))
            if unique_sets < 6:  # Allow some overlap but not too much
                validation_errors.append(f"Low set diversity: only {unique_sets}/8 unique sets")

            passed = len(validation_errors) == 0 and elapsed_ms < ALERT_MS
            status = "PASS" if passed else "FAIL"

            print(f"  Series {sid}: {format_time(elapsed_ms)} [{status}]")

            if validation_errors:
                for err in validation_errors:
                    print(f"    - {err}")
                all_passed = False

            results.append({
                "series": sid,
                "passed": passed,
                "time_ms": elapsed_ms,
                "unique_sets": unique_sets,
                "errors": validation_errors
            })

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  Series {sid}: {elapsed_ms:.3f}ms [FAIL] - {str(e)}")
            all_passed = False
            results.append({
                "series": sid,
                "passed": False,
                "time_ms": elapsed_ms,
                "errors": [str(e)]
            })

    print(f"\nRESULT: {'PASS' if all_passed else 'FAIL'}")

    return {
        "name": "Extreme Patterns",
        "passed": all_passed,
        "tested": len(test_series),
        "results": results
    }


def test_error_handling(data):
    """Test 4: Invalid series, missing data."""
    print("\n" + "="*70)
    print("TEST 4: Error Handling")
    print("="*70)

    all_series = sorted(int(s) for s in data.keys())
    first_series = all_series[0]
    last_series = all_series[-1]

    test_cases = [
        ("Series before first (no prior data)", first_series, ValueError, "No data for series"),
        ("Non-existent future series", last_series + 100, ValueError, "No data for series"),
        ("Very old non-existent series", 1, ValueError, "No data for series"),
    ]

    results = []
    all_passed = True

    for desc, sid, expected_error, expected_msg in test_cases:
        print(f"\n{desc}: Series {sid}")
        print("-" * 50)

        try:
            pred = predict(data, sid)
            # If we get here, the expected error wasn't raised
            print(f"  Expected error not raised!")
            print(f"  Got prediction instead: {len(pred['sets'])} sets")
            all_passed = False
            results.append({
                "case": desc,
                "passed": False,
                "error": "Expected error not raised"
            })
        except expected_error as e:
            if expected_msg.lower() in str(e).lower():
                print(f"  Error raised: {type(e).__name__}")
                print(f"  Message: {str(e)}")
                print(f"  Validation: PASS")
                results.append({
                    "case": desc,
                    "passed": True,
                    "error_type": type(e).__name__,
                    "message": str(e)
                })
            else:
                print(f"  Error raised: {type(e).__name__}")
                print(f"  Message: {str(e)}")
                print(f"  Expected message containing: '{expected_msg}'")
                print(f"  Validation: FAIL")
                all_passed = False
                results.append({
                    "case": desc,
                    "passed": False,
                    "error": f"Wrong message: {str(e)}"
                })
        except Exception as e:
            print(f"  Unexpected error type: {type(e).__name__}")
            print(f"  Message: {str(e)}")
            print(f"  Expected: {expected_error.__name__}")
            all_passed = False
            results.append({
                "case": desc,
                "passed": False,
                "error": f"Wrong error type: {type(e).__name__}"
            })

    print(f"\nRESULT: {'PASS' if all_passed else 'FAIL'}")

    return {
        "name": "Error Handling",
        "passed": all_passed,
        "cases": results
    }


def test_evaluate_function(data):
    """Test 5: Evaluate function correctness."""
    print("\n" + "="*70)
    print("TEST 5: Evaluate Function")
    print("="*70)

    all_series = sorted(int(s) for s in data.keys())
    test_series = all_series[-10:]  # Test last 10 series

    results = []
    all_passed = True

    print(f"\nTesting evaluate() on {len(test_series)} series...")

    for sid in test_series:
        start = time.perf_counter()
        try:
            result = evaluate(data, sid)
            elapsed_ms = (time.perf_counter() - start) * 1000

            errors = []

            # Validate result structure
            if result is None:
                errors.append("Result is None")
            else:
                required_keys = ["series", "set_bests", "best", "winner", "ml_helped", "ext_helped"]
                for key in required_keys:
                    if key not in result:
                        errors.append(f"Missing key: {key}")

                if not errors:
                    # Validate set_bests
                    if len(result["set_bests"]) != 8:
                        errors.append(f"Expected 8 set_bests, got {len(result['set_bests'])}")

                    # All matches should be between 0 and 14
                    for i, b in enumerate(result["set_bests"]):
                        if not (0 <= b <= 14):
                            errors.append(f"Set {i+1} best ({b}) out of range [0-14]")

                    # Best should match max of set_bests
                    if result["best"] != max(result["set_bests"]):
                        errors.append(f"Best ({result['best']}) != max(set_bests) ({max(result['set_bests'])})")

                    # Winner should be valid
                    if not (1 <= result["winner"] <= 8):
                        errors.append(f"Winner ({result['winner']}) out of range [1-8]")

            passed = len(errors) == 0 and elapsed_ms < ALERT_MS
            status = "PASS" if passed else "FAIL"

            if errors:
                print(f"  Series {sid}: {elapsed_ms:.3f}ms [{status}]")
                for err in errors:
                    print(f"    - {err}")
                all_passed = False
            else:
                print(f"  Series {sid}: {elapsed_ms:.3f}ms - Best: {result['best']}/14, Winner: S{result['winner']} [{status}]")

            results.append({
                "series": sid,
                "passed": passed,
                "time_ms": elapsed_ms,
                "best": result["best"] if result else None,
                "errors": errors
            })

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  Series {sid}: {elapsed_ms:.3f}ms [FAIL] - {str(e)}")
            all_passed = False
            results.append({
                "series": sid,
                "passed": False,
                "time_ms": elapsed_ms,
                "errors": [str(e)]
            })

    print(f"\nRESULT: {'PASS' if all_passed else 'FAIL'}")

    return {
        "name": "Evaluate Function",
        "passed": all_passed,
        "tested": len(test_series),
        "results": results
    }


def test_validate_function(data):
    """Test 6: Validate (batch) function."""
    print("\n" + "="*70)
    print("TEST 6: Validate (Batch) Function")
    print("="*70)

    all_series = sorted(int(s) for s in data.keys())

    # Test with a small range
    start_sid = all_series[-20]
    end_sid = all_series[-1]

    print(f"\nTesting validate() on range {start_sid}-{end_sid}...")

    start = time.perf_counter()
    try:
        result = validate(data, start_sid, end_sid)
        elapsed_ms = (time.perf_counter() - start) * 1000

        errors = []

        if result is None:
            errors.append("Result is None")
        else:
            required_keys = ["tested", "avg", "best", "worst", "wins", "at_11", "at_12", "at_14", "ml_helped", "ext_helped"]
            for key in required_keys:
                if key not in result:
                    errors.append(f"Missing key: {key}")

            if not errors:
                # Validate ranges
                if not (7 <= result["avg"] <= 14):
                    errors.append(f"Average ({result['avg']:.2f}) out of expected range [7-14]")

                if not (0 <= result["worst"] <= result["best"] <= 14):
                    errors.append(f"Best/worst inconsistent: worst={result['worst']}, best={result['best']}")

                if len(result["wins"]) != 8:
                    errors.append(f"Expected 8 win counts, got {len(result['wins'])}")

                if sum(result["wins"]) != result["tested"]:
                    errors.append(f"Win counts ({sum(result['wins'])}) != tested ({result['tested']})")

        passed = len(errors) == 0

        if errors:
            print(f"  Time: {elapsed_ms:.3f}ms [FAIL]")
            for err in errors:
                print(f"    - {err}")
        else:
            print(f"  Time: {elapsed_ms:.3f}ms [PASS]")
            print(f"  Tested: {result['tested']} series")
            print(f"  Average: {result['avg']:.2f}/14")
            print(f"  Best: {result['best']}/14")
            print(f"  Worst: {result['worst']}/14")
            print(f"  11+: {result['at_11']}, 12+: {result['at_12']}, 14/14: {result['at_14']}")

        return {
            "name": "Validate Function",
            "passed": passed,
            "time_ms": elapsed_ms,
            "tested": result["tested"] if result else 0,
            "errors": errors
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  Time: {elapsed_ms:.3f}ms [FAIL]")
        print(f"  Error: {str(e)}")
        return {
            "name": "Validate Function",
            "passed": False,
            "time_ms": elapsed_ms,
            "errors": [str(e)]
        }


def main():
    """Run all stress tests."""
    print("="*70)
    print("PRODUCTION PREDICTOR STRESS TEST")
    print("="*70)
    print(f"Target: < {TARGET_MS}ms per prediction")
    print(f"Alert:  > {ALERT_MS}ms per prediction")

    # Load data
    print("\nLoading data...")
    start = time.perf_counter()
    data = load_data()
    load_time = (time.perf_counter() - start) * 1000
    print(f"Data loaded in {load_time:.2f}ms")
    print(f"Series available: {len(data)} ({min(int(s) for s in data)} - {max(int(s) for s in data)})")

    # Run all tests
    results = []

    results.append(test_performance_under_load(data))
    results.append(test_edge_cases(data))
    results.append(test_extreme_patterns(data))
    results.append(test_error_handling(data))
    results.append(test_evaluate_function(data))
    results.append(test_validate_function(data))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    total_passed = sum(1 for r in results if r["passed"])
    total_tests = len(results)

    print(f"\n{'Test':<35} {'Result':<10} {'Details'}")
    print("-"*70)

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        details = ""
        if "avg_ms" in r:
            details = f"Avg: {r['avg_ms']:.3f}ms, P99: {r['p99_ms']:.3f}ms"
        elif "cases" in r:
            details = f"{len([c for c in r['cases'] if c.get('passed', False)])}/{len(r['cases'])} cases"
        elif "tested" in r:
            details = f"{r['tested']} items tested"

        print(f"{r['name']:<35} {status:<10} {details}")

    print("-"*70)
    print(f"{'TOTAL':<35} {total_passed}/{total_tests}")

    overall = "PASS" if total_passed == total_tests else "FAIL"
    print(f"\n{'='*70}")
    print(f"OVERALL RESULT: {overall}")
    print(f"{'='*70}")

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
