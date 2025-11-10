#!/usr/bin/env python3
"""
Comprehensive Validation: 8-series vs 16-series Lookback

The improvement test showed 8-series lookback achieved 71.4% on Series 3147
vs 64.3% with 16-series lookback. But this is just ONE series.

We need to validate on the full validation window (3140-3147) to ensure
this isn't just overfitting to Series 3147.
"""

import json
from true_learning_model import TrueLearningModel


def load_data():
    """Load full historical dataset"""
    with open('full_series_data_expanded.json', 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def test_lookback_on_series(lookback: int, boost: float, target_series: int, data: dict, seed: int = 999):
    """Test a specific lookback configuration on one series"""
    model = TrueLearningModel(seed=seed, cold_hot_boost=boost)

    # HACK: Change lookback window
    model.RECENT_SERIES_LOOKBACK = lookback

    # Train on all data before target series
    for sid in sorted(data.keys()):
        if sid < target_series:
            model.learn_from_series(sid, data[sid])

    # Generate prediction
    prediction = model.predict_best_combination(target_series)

    # Evaluate
    actual = data[target_series]
    matches = []
    for event in actual:
        match_count = len(set(prediction) & set(event))
        matches.append(match_count / 14)

    best_match = max(matches)
    avg_match = sum(matches) / len(matches)

    return {
        "best_match": best_match,
        "avg_match": avg_match,
        "prediction": prediction,
        "cold_numbers": sorted(model.hybrid_cold_numbers),
        "hot_numbers": sorted(model.hybrid_hot_numbers)
    }


def main():
    print("="*70)
    print("COMPREHENSIVE LOOKBACK VALIDATION")
    print("="*70)
    print()
    print("Testing 8-series vs 16-series lookback on 7 validation series")
    print("Series: 3140, 3141, 3142, 3143, 3144, 3145, 3147")
    print()

    data = load_data()

    # Validation window
    validation_series = [3140, 3141, 3142, 3143, 3144, 3145, 3147]

    # Configurations to test
    configurations = [
        {"lookback": 16, "boost": 25.0, "label": "Baseline (16-series, 25x)"},
        {"lookback": 8, "boost": 25.0, "label": "8-series, 25x boost"},
        {"lookback": 12, "boost": 25.0, "label": "12-series, 25x boost"},
        {"lookback": 20, "boost": 25.0, "label": "20-series, 25x boost"},

        # Also test some boost variations with 8-series
        {"lookback": 8, "boost": 20.0, "label": "8-series, 20x boost"},
        {"lookback": 8, "boost": 30.0, "label": "8-series, 30x boost"},
    ]

    all_results = {}

    for config in configurations:
        label = config["label"]
        lookback = config["lookback"]
        boost = config["boost"]

        print(f"Testing: {label}")

        results = []
        for series_id in validation_series:
            result = test_lookback_on_series(lookback, boost, series_id, data)
            result["series_id"] = series_id
            results.append(result)

        # Calculate summary
        avg_best = sum(r["best_match"] for r in results) / len(results)
        peak_best = max(r["best_match"] for r in results)

        all_results[label] = {
            "lookback": lookback,
            "boost": boost,
            "avg_best_match": avg_best,
            "peak_performance": peak_best,
            "series_results": results
        }

        print(f"  Avg Best: {avg_best:.3%}, Peak: {peak_best:.1%}")
        print()

    # Analysis
    print("="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print()

    # Sort by average performance
    sorted_results = sorted(all_results.items(), key=lambda x: x[1]["avg_best_match"], reverse=True)

    print(f"{'Rank':<6} {'Configuration':<30} {'Avg Best':<12} {'Peak':<10} {'vs Baseline'}")
    print("-"*75)

    baseline_perf = all_results["Baseline (16-series, 25x)"]["avg_best_match"]

    for i, (label, data) in enumerate(sorted_results, 1):
        diff = data["avg_best_match"] - baseline_perf
        marker = "✅" if diff > 0.01 else "⚠️" if diff > 0.005 else "➖" if abs(diff) < 0.005 else "❌"

        print(f"{i:<6} {label:<30} {data['avg_best_match']:<12.3%} {data['peak_performance']:<10.1%} "
              f"{diff:+.3%} {marker}")

    # Detailed series-by-series comparison
    print()
    print("="*70)
    print("SERIES-BY-SERIES COMPARISON: 8-series vs 16-series (Baseline)")
    print("="*70)
    print()

    config_8 = all_results["8-series, 25x boost"]
    config_16 = all_results["Baseline (16-series, 25x)"]

    print(f"{'Series':<10} {'8-series':<12} {'16-series':<12} {'Difference'}")
    print("-"*50)

    for i, series_id in enumerate(validation_series):
        perf_8 = config_8["series_results"][i]["best_match"]
        perf_16 = config_16["series_results"][i]["best_match"]
        diff = perf_8 - perf_16

        marker = "✅" if diff > 0.05 else "⚠️" if diff > 0.02 else "➖" if abs(diff) < 0.02 else "❌"

        print(f"{series_id:<10} {perf_8:<12.1%} {perf_16:<12.1%} {diff:+.1%} {marker}")

    # Recommendation
    print()
    print("="*70)
    print("RECOMMENDATION")
    print("="*70)
    print()

    best_label, best_data = sorted_results[0]
    improvement = best_data["avg_best_match"] - baseline_perf

    if best_label == "Baseline (16-series, 25x)":
        print("✅ KEEP CURRENT CONFIGURATION")
        print(f"   The baseline (16-series, 25x) is already optimal")
        print(f"   Performance: {baseline_perf:.3%}")
    elif improvement > 0.01:  # 1% improvement
        print(f"✅ SIGNIFICANT IMPROVEMENT - ADOPT NEW CONFIGURATION")
        print(f"   Best: {best_label}")
        print(f"   Improvement: {improvement:+.3%}")
        print(f"   New Performance: {best_data['avg_best_match']:.3%} (was {baseline_perf:.3%})")
    elif improvement > 0.005:  # 0.5% improvement
        print(f"⚠️  MARGINAL IMPROVEMENT")
        print(f"   Best: {best_label}")
        print(f"   Improvement: {improvement:+.3%}")
        print(f"   Consider adopting if consistent")
    else:
        print(f"❌ NO MEANINGFUL IMPROVEMENT")
        print(f"   Best alternative: {best_label} ({improvement:+.3%})")
        print(f"   Keep current configuration (16-series, 25x)")

    print()
    print("INTERPRETATION:")
    print("-"*70)

    if config_8["avg_best_match"] > baseline_perf:
        print("The 8-series lookback performs better on average. This suggests")
        print("that MORE RECENT patterns are more predictive than longer history.")
    else:
        print("The 16-series lookback performs better on average. The apparent")
        print("improvement on Series 3147 was just statistical variance (luck).")
        print("The longer lookback window provides better generalization.")

    # Save results
    output_file = "lookback_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_name": "Lookback Window Comprehensive Validation",
            "validation_series": validation_series,
            "all_results": {k: {**v, "series_results": [{**sr, "prediction": sr["prediction"]}
                                                        for sr in v["series_results"]]}
                           for k, v in all_results.items()},
            "baseline_performance": baseline_perf,
            "best_configuration": best_label,
            "improvement": improvement
        }, f, indent=2)

    print()
    print(f"✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
