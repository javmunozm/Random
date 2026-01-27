#!/usr/bin/env python3
"""
Deep analysis: When does CURRENT weighting beat HISTORICAL?

The previous test showed:
- Historical avg: 9.51, 11+ rate: 6.8%
- Current avg: 9.47, 11+ rate: 11.6%

Current weighting has HIGHER variance - lower average but more 11+ hits.
This might be exploitable.
"""

import json
from pathlib import Path
from collections import Counter


def load_data():
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def evaluate(data, series_id, prediction):
    sid = str(series_id)
    if sid not in data:
        return 0
    events = data[sid]
    pred_set = set(prediction)
    return max(len(pred_set & set(e)) for e in events)


def predict_historical(data, series_id, window=10):
    """Predict using historical frequency (last N series)."""
    hist_freq = Counter()
    for hist_sid in range(series_id - window - 1, series_id - 1):
        hist_str = str(hist_sid)
        if hist_str in data:
            for e in data[hist_str]:
                hist_freq.update(e)

    pred = sorted(range(1, 26), key=lambda n: -hist_freq.get(n, 0))[:14]
    return sorted(pred)


def predict_current(data, series_id):
    """Predict using ONLY the prior series' patterns."""
    prior = str(series_id - 1)
    if prior not in data:
        return None

    current_freq = Counter()
    for e in data[prior]:
        current_freq.update(e)

    pred = sorted(range(1, 26), key=lambda n: -current_freq.get(n, 0))[:14]
    return sorted(pred)


def predict_adaptive(data, series_id, window=10):
    """
    ADAPTIVE: Use current weighting when current draw shows strong consensus,
    use historical when current draw is dispersed.
    """
    prior = str(series_id - 1)
    if prior not in data:
        return None

    # Analyze current draw
    current_freq = Counter()
    for e in data[prior]:
        current_freq.update(e)

    # Measure consensus: how many numbers appear in 5+ events?
    high_consensus = sum(1 for n, c in current_freq.items() if c >= 5)

    # Historical frequency
    hist_freq = Counter()
    for hist_sid in range(series_id - window - 1, series_id - 1):
        hist_str = str(hist_sid)
        if hist_str in data:
            for e in data[hist_str]:
                hist_freq.update(e)

    # Adaptive weight: more consensus = trust current more
    # High consensus (10+) = 80% current, Low consensus (<5) = 20% current
    if high_consensus >= 10:
        current_weight = 0.8
    elif high_consensus >= 7:
        current_weight = 0.6
    elif high_consensus >= 5:
        current_weight = 0.4
    else:
        current_weight = 0.2

    # Normalize and blend
    max_c = max(current_freq.values()) if current_freq else 1
    max_h = max(hist_freq.values()) if hist_freq else 1

    blended = {}
    for n in range(1, 26):
        c = current_freq.get(n, 0) / max_c
        h = hist_freq.get(n, 0) / max_h
        blended[n] = current_weight * c + (1 - current_weight) * h

    pred = sorted(range(1, 26), key=lambda n: -blended[n])[:14]
    return sorted(pred), current_weight, high_consensus


def analyze_when_current_wins():
    """Find patterns in WHEN current-weighted prediction beats historical."""
    data = load_data()
    series_ids = sorted(int(s) for s in data.keys())
    start = series_ids[11]
    end = series_ids[-1]

    current_wins = []
    historical_wins = []
    ties = []

    for sid in range(start, end + 1):
        h_pred = predict_historical(data, sid)
        c_pred = predict_current(data, sid)

        if c_pred is None:
            continue

        h_score = evaluate(data, sid, h_pred)
        c_score = evaluate(data, sid, c_pred)

        prior = str(sid - 1)
        current_freq = Counter()
        for e in data[prior]:
            current_freq.update(e)

        consensus_5plus = sum(1 for n, c in current_freq.items() if c >= 5)
        consensus_6plus = sum(1 for n, c in current_freq.items() if c >= 6)

        record = {
            'series': sid,
            'h_score': h_score,
            'c_score': c_score,
            'consensus_5plus': consensus_5plus,
            'consensus_6plus': consensus_6plus,
        }

        if c_score > h_score:
            current_wins.append(record)
        elif h_score > c_score:
            historical_wins.append(record)
        else:
            ties.append(record)

    print("=" * 70)
    print("WHEN DOES CURRENT WEIGHTING WIN?")
    print("=" * 70)
    print(f"\nTotal series: {len(current_wins) + len(historical_wins) + len(ties)}")
    print(f"Current wins: {len(current_wins)} ({100*len(current_wins)/(len(current_wins)+len(historical_wins)+len(ties)):.1f}%)")
    print(f"Historical wins: {len(historical_wins)} ({100*len(historical_wins)/(len(current_wins)+len(historical_wins)+len(ties)):.1f}%)")
    print(f"Ties: {len(ties)} ({100*len(ties)/(len(current_wins)+len(historical_wins)+len(ties)):.1f}%)")

    # Analyze conditions when current wins
    if current_wins:
        avg_consensus_when_current_wins = sum(r['consensus_5plus'] for r in current_wins) / len(current_wins)
        avg_score_when_current_wins = sum(r['c_score'] for r in current_wins) / len(current_wins)
    else:
        avg_consensus_when_current_wins = 0
        avg_score_when_current_wins = 0

    if historical_wins:
        avg_consensus_when_hist_wins = sum(r['consensus_5plus'] for r in historical_wins) / len(historical_wins)
        avg_score_when_hist_wins = sum(r['h_score'] for r in historical_wins) / len(historical_wins)
    else:
        avg_consensus_when_hist_wins = 0
        avg_score_when_hist_wins = 0

    print(f"\nWhen CURRENT wins:")
    print(f"  Avg consensus (5+): {avg_consensus_when_current_wins:.2f}")
    print(f"  Avg score: {avg_score_when_current_wins:.2f}")

    print(f"\nWhen HISTORICAL wins:")
    print(f"  Avg consensus (5+): {avg_consensus_when_hist_wins:.2f}")
    print(f"  Avg score: {avg_score_when_hist_wins:.2f}")

    # Test adaptive strategy
    print("\n" + "=" * 70)
    print("ADAPTIVE STRATEGY TEST")
    print("=" * 70)

    adaptive_scores = []
    current_scores = []
    historical_scores = []
    baseline_scores = []

    for sid in range(start, end + 1):
        h_pred = predict_historical(data, sid)
        c_pred = predict_current(data, sid)
        a_result = predict_adaptive(data, sid)

        if c_pred is None or a_result is None:
            continue

        a_pred, weight, consensus = a_result

        h_score = evaluate(data, sid, h_pred)
        c_score = evaluate(data, sid, c_pred)
        a_score = evaluate(data, sid, a_pred)

        # Baseline: E1 copy
        prior = str(sid - 1)
        b_score = evaluate(data, sid, data[prior][0])

        historical_scores.append(h_score)
        current_scores.append(c_score)
        adaptive_scores.append(a_score)
        baseline_scores.append(b_score)

    print(f"\n{'Strategy':<20} {'Average':<12} {'11+ Rate':<12} {'12+ Count':<12}")
    print("-" * 60)

    for name, scores in [
        ('E1 Copy (baseline)', baseline_scores),
        ('Historical (L10)', historical_scores),
        ('Current Only', current_scores),
        ('Adaptive', adaptive_scores),
    ]:
        avg = sum(scores) / len(scores)
        rate_11 = sum(1 for s in scores if s >= 11) / len(scores) * 100
        count_12 = sum(1 for s in scores if s >= 12)
        print(f"{name:<20} {avg:.2f}/14      {rate_11:.1f}%        {count_12}")

    # Head-to-head comparison
    print("\n" + "=" * 70)
    print("HEAD-TO-HEAD: ADAPTIVE vs BASELINE")
    print("=" * 70)

    adaptive_better = sum(1 for a, b in zip(adaptive_scores, baseline_scores) if a > b)
    baseline_better = sum(1 for a, b in zip(adaptive_scores, baseline_scores) if b > a)
    ties = sum(1 for a, b in zip(adaptive_scores, baseline_scores) if a == b)

    print(f"\nAdaptive wins: {adaptive_better}")
    print(f"Baseline wins: {baseline_better}")
    print(f"Ties: {ties}")

    # When adaptive wins, by how much?
    adaptive_margins = [a - b for a, b in zip(adaptive_scores, baseline_scores) if a > b]
    baseline_margins = [b - a for a, b in zip(adaptive_scores, baseline_scores) if b > a]

    if adaptive_margins:
        print(f"\nWhen adaptive wins, avg margin: +{sum(adaptive_margins)/len(adaptive_margins):.2f}")
    if baseline_margins:
        print(f"When baseline wins, avg margin: +{sum(baseline_margins)/len(baseline_margins):.2f}")


def test_production_integration():
    """
    Test: What if we add current-weighted sets to the 12-set ensemble?
    The MAX() approach means we only need current weighting to WIN sometimes.
    """
    data = load_data()
    series_ids = sorted(int(s) for s in data.keys())
    start = series_ids[11]
    end = series_ids[-1]

    print("\n" + "=" * 70)
    print("INTEGRATION TEST: ADD CURRENT-WEIGHTED SETS TO ENSEMBLE")
    print("=" * 70)

    # Simulate current production (12 sets, take max)
    # vs production + 2 current-weighted sets

    production_scores = []
    enhanced_scores = []

    for sid in range(start, end + 1):
        prior = str(sid - 1)
        target = str(sid)

        if prior not in data or target not in data:
            continue

        # Production: best of E1-E7 events (simplified)
        prod_best = 0
        for event in data[prior]:
            score = evaluate(data, sid, event)
            prod_best = max(prod_best, score)

        # Current-weighted prediction
        current_freq = Counter()
        for e in data[prior]:
            current_freq.update(e)
        c_pred = sorted(range(1, 26), key=lambda n: -current_freq.get(n, 0))[:14]
        c_score = evaluate(data, sid, sorted(c_pred))

        # Consensus-based prediction
        consensus = [n for n, c in current_freq.items() if c >= 5]
        if len(consensus) < 14:
            fill = [n for n, c in current_freq.items() if c == 4]
            consensus = consensus + fill[:14-len(consensus)]
        consensus_score = evaluate(data, sid, sorted(consensus[:14])) if len(consensus) >= 14 else 0

        # Enhanced: max of production + current sets
        enhanced_best = max(prod_best, c_score, consensus_score)

        production_scores.append(prod_best)
        enhanced_scores.append(enhanced_best)

    print(f"\n{'Strategy':<30} {'Average':<12} {'11+ Rate':<12} {'12+ Count':<12}")
    print("-" * 70)

    for name, scores in [
        ('Production (best of 7 events)', production_scores),
        ('Enhanced (+2 current sets)', enhanced_scores),
    ]:
        avg = sum(scores) / len(scores)
        rate_11 = sum(1 for s in scores if s >= 11) / len(scores) * 100
        count_12 = sum(1 for s in scores if s >= 12)
        print(f"{name:<30} {avg:.2f}/14      {rate_11:.1f}%        {count_12}")

    delta = sum(enhanced_scores)/len(enhanced_scores) - sum(production_scores)/len(production_scores)
    print(f"\nDelta: {delta:+.3f}/14")

    # How often do current sets contribute?
    current_helps = 0
    for i in range(len(production_scores)):
        if enhanced_scores[i] > production_scores[i]:
            current_helps += 1

    print(f"Current sets improved score: {current_helps} times ({100*current_helps/len(production_scores):.1f}%)")


if __name__ == "__main__":
    analyze_when_current_wins()
    test_production_integration()
