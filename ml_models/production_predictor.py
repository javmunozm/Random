#!/usr/bin/env python3
"""
Production Predictor
====================

Goal: Hit 14/14 at least once.

Strategy: Prior Event 1 + 8-set hedging (r15_heavy strategy).
Performance: 10.26/14 avg, 11 series with 12+ matches.

Ranking (2026-01-12): Prioritize 12+ potential over win rate.
- S4 (r15+r16) leads with 4x 12+ scores
- S1 (r16) wins often but has 0x 12+ (ceiling limited)
- r16 correlates with high-top13 events; r15 with low-top13 events
- r15 value comes from COMBINING with r16 (S4), not as single-swap (S2)
"""

import json
import sys
from pathlib import Path
from itertools import combinations
from datetime import datetime
from collections import Counter

# Constants
TOTAL = 25
PICK = 14
EXCLUDE = 12

# Performance rank by 12+ potential (goal: hit 14/14)
# Rank order: S4(4×12+) > S7(3×12+) > S3(2×12+) > S8(2×12+) > S6(1×12+) > S5(1×12+) > S2(1×12+) > S1(0×12+)
# Key insight: S1 wins often but never reaches 12+; S4 has highest ceiling
PERF_RANK = [8, 7, 3, 1, 6, 5, 2, 4]  # Index = set-1, value = rank


def load_data():
    """Load data from JSON."""
    for p in [Path(__file__).parent.parent / "data" / "full_series_data.json",
              Path("data/full_series_data.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


def latest(data):
    """Get latest series ID."""
    return max(int(s) for s in data.keys())


# =============================================================================
# PREDICTION - The 8-set hedge logic lives HERE and ONLY here
# =============================================================================

def predict(data, series_id):
    """
    Generate 8 prediction sets (r15_heavy strategy).

    Single-swap sets (top-13 + one rank):
    - Set 1: top-13 + rank16 (best performer, 40.4%)
    - Set 2: top-13 + rank15 (8.3%)
    - Set 3: top-13 + rank18 (15.5%)

    Double-swap sets (top-12 + two ranks):
    - Set 4: top-12 + r15 + r16 (15.5%)
    - Set 5: top-12 + r15 + r18 (6.7%)
    - Set 6: top-12 + r16 + r18 (5.2%)
    - Set 7: top-12 + r15 + r19 (4.1%)

    Hot set:
    - Set 8: top-12 + hot#2 + hot#3 (4.1%)

    Performance: 10.28/14 avg, 10 series with 12+ (vs 7 previous).
    Optimized 2026-01-11: r15_heavy focuses on rank15 to capture near-misses.
    """
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No data for series {int(prior)}")

    event1 = set(data[prior][0])

    # Global frequency for tiebreaking
    freq = Counter(n for events in data.values() for e in events for n in e)
    max_freq = max(freq.values())

    # Rank: Event1 numbers first, then by frequency
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event1), -freq[n]/max_freq, n))

    # Recent frequency for hot sets (last 5 series)
    prev_series = sorted(int(s) for s in data if int(s) < series_id)[-5:]
    recent_freq = Counter(n for s in prev_series for e in data[str(s)] for n in e)

    # Hot numbers outside top 14
    non_top14 = [n for n in range(1, TOTAL + 1) if n not in ranked[:14]]
    hot_outside = sorted(non_top14, key=lambda n: -recent_freq.get(n, 0))[:3]

    # 8 sets - r15_heavy strategy (2026-01-11)
    sets = [
        sorted(ranked[:13] + [ranked[15]]),              # Set 1: top-13 + rank16
        sorted(ranked[:13] + [ranked[14]]),              # Set 2: top-13 + rank15
        sorted(ranked[:13] + [ranked[17]]),              # Set 3: top-13 + rank18
        sorted(ranked[:12] + [ranked[14], ranked[15]]),  # Set 4: top-12 + r15 + r16
        sorted(ranked[:12] + [ranked[14], ranked[17]]),  # Set 5: top-12 + r15 + r18
        sorted(ranked[:12] + [ranked[15], ranked[17]]),  # Set 6: top-12 + r16 + r18
        sorted(ranked[:12] + [ranked[14], ranked[18]]),  # Set 7: top-12 + r15 + r19
        sorted(ranked[:12] + [hot_outside[1], hot_outside[2]]),  # Set 8: hot #2+#3
    ]

    return {"series": series_id, "sets": sets, "ranked": ranked, "hot_outside": hot_outside}


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate(data, series_id, pred=None):
    """Evaluate prediction - best match across 8 sets x 7 events."""
    sid = str(series_id)
    if sid not in data:
        return None

    if pred is None:
        pred = predict(data, series_id)

    events = data[sid]

    # Best match for each set
    set_bests = []
    for s in pred["sets"]:
        matches = [len(set(s) & set(e)) for e in events]
        set_bests.append(max(matches))

    best = max(set_bests)
    winner = set_bests.index(best) + 1
    # S1-S3: single swaps, S4-S7: double swaps, S8: hot
    single_best = max(set_bests[:3])
    double_helped = winner in [4, 5, 6, 7] and set_bests[winner-1] > single_best
    hot_helped = winner == 8 and set_bests[7] > max(single_best, max(set_bests[3:7]))

    return {"series": series_id, "set_bests": set_bests, "best": best, "winner": winner,
            "double_helped": double_helped, "hot_helped": hot_helped}


# =============================================================================
# JACKPOT FINDER
# =============================================================================

def find_jackpot(data, series_id, verbose=True):
    """Find exact 14/14 match using Pool-24."""
    sid = str(series_id)
    if sid not in data:
        raise ValueError(f"Series {series_id} not found")

    targets = {tuple(sorted(e)) for e in data[sid]}
    pool = [n for n in range(1, TOTAL + 1) if n != EXCLUDE]

    # Skip historical (never repeat)
    historical = {tuple(sorted(e)) for events in data.values() for e in events} - targets

    if verbose:
        print(f"Finding jackpot for {series_id} (Pool-24, exclude #{EXCLUDE})")

    start = datetime.now()
    tries = 0

    for combo in combinations(pool, PICK):
        if combo in historical:
            continue
        tries += 1
        if combo in targets:
            t = (datetime.now() - start).total_seconds()
            if verbose:
                print(f"FOUND in {tries:,} tries ({t:.2f}s): {list(combo)}")
            return {"found": True, "jackpot": list(combo), "tries": tries, "time": t}

    t = (datetime.now() - start).total_seconds()
    if verbose:
        print(f"Not found ({tries:,} tries, {t:.2f}s)")
    return {"found": False, "tries": tries, "time": t}


# =============================================================================
# VALIDATION
# =============================================================================

def validate(data, start, end):
    """Batch validation."""
    results = []
    for sid in range(start, end + 1):
        r = evaluate(data, sid)
        if r:
            results.append(r)

    if not results:
        return None

    n = len(results)
    bests = [r["best"] for r in results]
    wins = [0, 0, 0, 0, 0, 0, 0, 0]
    double_helped_count = 0
    hot_helped_count = 0
    for r in results:
        wins[r["winner"] - 1] += 1
        if r.get("double_helped"):
            double_helped_count += 1
        if r.get("hot_helped"):
            hot_helped_count += 1

    return {
        "tested": n,
        "avg": sum(bests) / n,
        "best": max(bests),
        "worst": min(bests),
        "wins": wins,
        "at_11": sum(1 for b in bests if b >= 11),
        "at_12": sum(1 for b in bests if b >= 12),
        "at_14": sum(1 for b in bests if b == 14),
        "double_helped": double_helped_count,
        "hot_helped": hot_helped_count,
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    data = load_data()
    last = latest(data)

    if len(sys.argv) < 2:
        print("Production Predictor (8-Set)")
        print("=" * 50)
        print("Goal: Hit 14/14")
        print("\nCommands:")
        print("  predict [series]  - 8-set prediction")
        print("  find [series]     - Find jackpot")
        print("  validate [s] [e]  - Test accuracy")
        print(f"\nLatest: {last}")
        return

    cmd = sys.argv[1]

    if cmd == "predict":
        sid = int(sys.argv[2]) if len(sys.argv) > 2 else last + 1
        r = predict(data, sid)
        print(f"\nSeries {sid} Prediction (8-Set Optimized)")
        print("=" * 75)
        print(f"{'Rank':<5} {'Set':<18} {'Numbers':<45} {'Type'}")
        print("-" * 75)
        labels = [
            "S1 (rank16)",     # Single swap
            "S2 (rank15)",     # Single swap
            "S3 (rank18)",     # Single swap
            "S4 (r15+r16)",    # Double swap
            "S5 (r15+r18)",    # Double swap
            "S6 (r16+r18)",    # Double swap
            "S7 (r15+r19)",    # Double swap
            "S8 (hot#2+#3)",   # Hot
        ]
        types = ["SGL", "SGL", "SGL", "DBL", "DBL", "DBL", "DBL", "HOT"]
        # Sort by performance rank for display
        order = sorted(range(8), key=lambda i: PERF_RANK[i])
        for idx in order:
            s = r["sets"][idx]
            nums = ' '.join(f'{n:02d}' for n in s)
            print(f"#{PERF_RANK[idx]:<4} {labels[idx]:<18} {nums:<45} {types[idx]}")
        print("-" * 75)
        print(f"Hot outside top-14: {r['hot_outside']}")
        print(f"Pool-24: Exclude #{EXCLUDE}")

    elif cmd == "find":
        sid = int(sys.argv[2]) if len(sys.argv) > 2 else last
        find_jackpot(data, sid)

    elif cmd == "validate":
        s = int(sys.argv[2]) if len(sys.argv) > 2 else 3100
        e = int(sys.argv[3]) if len(sys.argv) > 3 else last
        r = validate(data, s, e)
        if r:
            print(f"\nValidation: {s}-{e}")
            print("=" * 50)
            print(f"Tested:  {r['tested']}")
            print(f"Average: {r['avg']:.2f}/14")
            print(f"Best:    {r['best']}/14")
            print(f"Worst:   {r['worst']}/14")
            print(f"11+:     {r['at_11']}")
            print(f"12+:     {r['at_12']}")
            print(f"14/14:   {r['at_14']}")
            w = r['wins']
            print(f"\nSingle:  S1={w[0]} S2={w[1]} S3={w[2]}")
            print(f"Double:  S4={w[3]} S5={w[4]} S6={w[5]} S7={w[6]} (helped={r['double_helped']})")
            print(f"Hot:     S8={w[7]} (helped={r['hot_helped']})")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
