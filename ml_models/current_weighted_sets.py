#!/usr/bin/env python3
"""
Current-Weighted Sets for Production Integration
=================================================

Finding: Adding current-weighted sets to ensemble gives +0.089/14

Now: Find the BEST current-weighted strategies to add.
"""

import json
from pathlib import Path
from collections import Counter
from itertools import combinations


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


def generate_current_weighted_strategies(data, series_id):
    """Generate various current-weighted prediction strategies."""
    prior = str(series_id - 1)
    if prior not in data:
        return {}

    events = data[prior]
    strategies = {}

    # Current frequency
    freq = Counter()
    for e in events:
        freq.update(e)

    # Strategy 1: Pure current frequency
    s1 = sorted(range(1, 26), key=lambda n: (-freq.get(n, 0), n))[:14]
    strategies['current_freq'] = sorted(s1)

    # Strategy 2: Consensus (5+ appearances)
    consensus = sorted([n for n, c in freq.items() if c >= 5], key=lambda n: -freq[n])
    if len(consensus) < 14:
        fill = sorted([n for n, c in freq.items() if c == 4], key=lambda n: -freq[n])
        consensus = consensus + fill[:14-len(consensus)]
    if len(consensus) >= 14:
        strategies['consensus_5plus'] = sorted(consensus[:14])

    # Strategy 3: Strong consensus (6+ appearances)
    strong = sorted([n for n, c in freq.items() if c >= 6], key=lambda n: -freq[n])
    if len(strong) < 14:
        fill = sorted([n for n, c in freq.items() if c == 5], key=lambda n: -freq[n])
        strong = strong + fill[:14-len(strong)]
    if len(strong) < 14:
        fill2 = sorted([n for n, c in freq.items() if c == 4], key=lambda n: -freq[n])
        strong = strong + fill2[:14-len(strong)]
    if len(strong) >= 14:
        strategies['consensus_6plus'] = sorted(strong[:14])

    # Strategy 4: Inverse - rare numbers (diversity)
    rare = sorted([n for n, c in freq.items() if c <= 3], key=lambda n: freq.get(n, 0))
    if len(rare) >= 14:
        strategies['rare_only'] = sorted(rare[:14])

    # Strategy 5: Balanced - some consensus + some rare
    core = sorted([n for n, c in freq.items() if c >= 5], key=lambda n: -freq[n])[:10]
    diverse = sorted([n for n, c in freq.items() if c <= 3], key=lambda n: freq.get(n, 0))[:4]
    if len(core) + len(diverse) >= 14:
        strategies['balanced_10_4'] = sorted((core + diverse)[:14])

    # Strategy 6: Event intersection - numbers in E1 AND E6 (most persistent)
    e1_set = set(events[0])
    for i in range(1, 7):
        ei_set = set(events[i])
        intersection = e1_set & ei_set
        remaining = sorted((e1_set | ei_set) - intersection, key=lambda n: -freq[n])
        fusion = sorted(list(intersection) + remaining[:14-len(intersection)])
        if len(fusion) >= 14:
            strategies[f'E1_E{i+1}_fusion'] = fusion[:14]

    # Strategy 7: Triple event intersection
    for i, j, k in [(0, 2, 5), (0, 3, 6), (1, 4, 6)]:  # E1&E3&E6, E1&E4&E7, E2&E5&E7
        triple_int = set(events[i]) & set(events[j]) & set(events[k])
        triple_union = set(events[i]) | set(events[j]) | set(events[k])
        remaining = sorted(triple_union - triple_int, key=lambda n: -freq[n])
        fusion = sorted(list(triple_int) + remaining[:14-len(triple_int)])
        if len(fusion) >= 14:
            strategies[f'triple_{i+1}_{j+1}_{k+1}'] = fusion[:14]

    # Strategy 8: Highest overlap event pair
    best_overlap = 0
    best_pair = (0, 1)
    for i in range(7):
        for j in range(i+1, 7):
            overlap = len(set(events[i]) & set(events[j]))
            if overlap > best_overlap:
                best_overlap = overlap
                best_pair = (i, j)

    i, j = best_pair
    pair_int = set(events[i]) & set(events[j])
    pair_union = set(events[i]) | set(events[j])
    remaining = sorted(pair_union - pair_int, key=lambda n: -freq[n])
    fusion = sorted(list(pair_int) + remaining[:14-len(pair_int)])
    if len(fusion) >= 14:
        strategies['best_overlap_pair'] = fusion[:14]

    # Strategy 9: Current freq weighted by position (numbers appearing early in events)
    position_weight = Counter()
    for e in events:
        for pos, n in enumerate(e):
            position_weight[n] += (14 - pos)  # Earlier = higher weight

    pos_weighted = sorted(range(1, 26), key=lambda n: -position_weight.get(n, 0))[:14]
    strategies['position_weighted'] = sorted(pos_weighted)

    # Strategy 10: Frequency * recency (recent series count more)
    recent_freq = Counter()
    for hist_sid in range(series_id - 4, series_id - 1):
        hist_str = str(hist_sid)
        if hist_str in data:
            for e in data[hist_str]:
                recent_freq.update(e)

    blended = {}
    max_f = max(freq.values()) if freq else 1
    max_r = max(recent_freq.values()) if recent_freq else 1
    for n in range(1, 26):
        blended[n] = 0.7 * freq.get(n, 0)/max_f + 0.3 * recent_freq.get(n, 0)/max_r

    blended_pred = sorted(range(1, 26), key=lambda n: -blended[n])[:14]
    strategies['current_70_recent_30'] = sorted(blended_pred)

    return strategies


def test_all_strategies():
    """Test all current-weighted strategies."""
    data = load_data()
    series_ids = sorted(int(s) for s in data.keys())
    start = series_ids[11]
    end = series_ids[-1]

    print("=" * 80)
    print("CURRENT-WEIGHTED STRATEGY EVALUATION")
    print("=" * 80)
    print(f"\nTesting {end - start + 1} series ({start}-{end})")

    # Collect all strategy results
    strategy_scores = {}

    # Also track production baseline
    production_scores = []

    for sid in range(start, end + 1):
        prior = str(sid - 1)
        target = str(sid)

        if prior not in data or target not in data:
            continue

        # Production: best of 7 events
        prod_best = 0
        for event in data[prior]:
            score = evaluate(data, sid, event)
            prod_best = max(prod_best, score)
        production_scores.append(prod_best)

        # Current-weighted strategies
        strategies = generate_current_weighted_strategies(data, sid)
        for name, pred in strategies.items():
            if name not in strategy_scores:
                strategy_scores[name] = []
            score = evaluate(data, sid, pred)
            strategy_scores[name].append(score)

    # Report
    print(f"\n{'Strategy':<25} {'Average':<10} {'11+':<8} {'12+':<8} {'Unique Wins':<12}")
    print("-" * 75)

    # Calculate unique wins (when strategy beats production)
    for name, scores in sorted(strategy_scores.items(), key=lambda x: -sum(x[1])/len(x[1])):
        if len(scores) != len(production_scores):
            continue

        avg = sum(scores) / len(scores)
        rate_11 = sum(1 for s in scores if s >= 11)
        rate_12 = sum(1 for s in scores if s >= 12)

        # Unique wins: when this strategy beats production
        unique_wins = sum(1 for s, p in zip(scores, production_scores) if s > p)

        print(f"{name:<25} {avg:.2f}/14   {rate_11:<8} {rate_12:<8} {unique_wins}")

    print(f"\n{'PRODUCTION (best of 7)':<25} {sum(production_scores)/len(production_scores):.2f}/14   "
          f"{sum(1 for s in production_scores if s >= 11):<8} "
          f"{sum(1 for s in production_scores if s >= 12):<8} --")

    # Find best strategies to ADD to ensemble
    print("\n" + "=" * 80)
    print("BEST STRATEGIES TO ADD TO ENSEMBLE")
    print("=" * 80)

    # Test adding each strategy to production
    for name, scores in sorted(strategy_scores.items(), key=lambda x: -sum(x[1])/len(x[1])):
        if len(scores) != len(production_scores):
            continue

        # Enhanced = max(production, strategy)
        enhanced = [max(p, s) for p, s in zip(production_scores, scores)]
        delta = sum(enhanced)/len(enhanced) - sum(production_scores)/len(production_scores)

        if delta > 0.01:  # Only show if meaningful improvement
            enhanced_11 = sum(1 for s in enhanced if s >= 11)
            enhanced_12 = sum(1 for s in enhanced if s >= 12)
            print(f"{name:<25} delta: +{delta:.3f}/14, 11+: {enhanced_11}, 12+: {enhanced_12}")

    # Test adding MULTIPLE strategies
    print("\n" + "=" * 80)
    print("BEST COMBINATION OF STRATEGIES")
    print("=" * 80)

    # Find top 5 by delta
    deltas = []
    for name, scores in strategy_scores.items():
        if len(scores) != len(production_scores):
            continue
        enhanced = [max(p, s) for p, s in zip(production_scores, scores)]
        delta = sum(enhanced)/len(enhanced) - sum(production_scores)/len(production_scores)
        deltas.append((name, scores, delta))

    deltas.sort(key=lambda x: -x[2])
    top_strategies = deltas[:5]

    print(f"\nTop 5 strategies by individual delta:")
    for name, _, delta in top_strategies:
        print(f"  {name}: +{delta:.3f}")

    # Combine top strategies
    combined = production_scores.copy()
    added = []
    for name, scores, _ in top_strategies:
        prev_avg = sum(combined) / len(combined)
        combined = [max(c, s) for c, s in zip(combined, scores)]
        new_avg = sum(combined) / len(combined)
        marginal = new_avg - prev_avg
        added.append((name, marginal))
        print(f"\nAfter adding {name}: {new_avg:.3f}/14 (marginal: +{marginal:.3f})")

    final_avg = sum(combined) / len(combined)
    final_11 = sum(1 for s in combined if s >= 11)
    final_12 = sum(1 for s in combined if s >= 12)
    total_delta = final_avg - sum(production_scores)/len(production_scores)

    print(f"\n" + "=" * 80)
    print(f"FINAL RESULT: Production + Top 5 Current-Weighted Strategies")
    print(f"=" * 80)
    print(f"Average: {final_avg:.3f}/14 (was {sum(production_scores)/len(production_scores):.3f})")
    print(f"11+ hits: {final_11} (was {sum(1 for s in production_scores if s >= 11)})")
    print(f"12+ hits: {final_12} (was {sum(1 for s in production_scores if s >= 12)})")
    print(f"TOTAL IMPROVEMENT: +{total_delta:.3f}/14")


if __name__ == "__main__":
    test_all_strategies()
