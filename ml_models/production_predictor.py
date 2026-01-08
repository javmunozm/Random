#!/usr/bin/env python3
"""
Production Predictor
====================

Goal: Hit 14/14 at least once.

Strategy: Prior Event 1 + 8-set hedging (4 standard + 2 ML + 2 extended).
Performance: 10.22/14 avg, 30.4% above random baseline.
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

# Performance rank by historical win rate (updated after each series)
# S1=44.8%, S2=22.9%, S4=10.9%, S6=6.8%, S5=5.2%, S7=3.6%, S8=3.1%, S3=2.6%
PERF_RANK = [1, 2, 8, 3, 5, 4, 6, 7]  # Index = set-1, value = rank


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
    Generate 8 prediction sets: 4 standard + 2 ML + 2 extended.

    Standard sets (ranks 13-16 swaps):
    - Set 1: Swap rank 14<>16 (best performer)
    - Set 2: Swap rank 13<>15
    - Set 3: Swap rank 14<>15
    - Set 4: Primary top 14

    ML sets (hot non-E1 numbers):
    - Set 5: Top 13 + hottest outside number
    - Set 6: Top 12 + two hottest outside numbers

    Extended sets (deeper rank swaps):
    - Set 7: Swap rank 14<>17
    - Set 8: Swap rank 14<>18

    Performance: 10.22/14 avg, 30.4% above random baseline.
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

    # Recent frequency for ML sets (last 5 series)
    prev_series = sorted(int(s) for s in data if int(s) < series_id)[-5:]
    recent_freq = Counter(n for s in prev_series for e in data[str(s)] for n in e)

    # Hot numbers outside top 14
    non_top14 = [n for n in range(1, TOTAL + 1) if n not in ranked[:14]]
    hot_outside = sorted(non_top14, key=lambda n: -recent_freq.get(n, 0))[:3]

    # 8 sets - 4 standard + 2 ML + 2 extended
    sets = [
        sorted(ranked[:13] + [ranked[15]]),              # Set 1: swap 14<>16
        sorted(ranked[:12] + [ranked[14], ranked[13]]),  # Set 2: swap 13<>15
        sorted(ranked[:13] + [ranked[14]]),              # Set 3: swap 14<>15
        sorted(ranked[:14]),                             # Set 4: primary
        sorted(ranked[:13] + [hot_outside[0]]),          # Set 5: ML hot #1
        sorted(ranked[:12] + hot_outside[:2]),           # Set 6: ML hot #1+#2
        sorted(ranked[:13] + [ranked[16]]),              # Set 7: swap 14<>17
        sorted(ranked[:13] + [ranked[17]]),              # Set 8: swap 14<>18
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
    std_best = max(set_bests[:4])
    ml_helped = winner in [5, 6] and set_bests[winner-1] > std_best
    ext_helped = winner in [7, 8] and set_bests[winner-1] > max(std_best, max(set_bests[4:6]))

    return {"series": series_id, "set_bests": set_bests, "best": best, "winner": winner,
            "ml_helped": ml_helped, "ext_helped": ext_helped}


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
    ml_helped_count = 0
    ext_helped_count = 0
    for r in results:
        wins[r["winner"] - 1] += 1
        if r.get("ml_helped"):
            ml_helped_count += 1
        if r.get("ext_helped"):
            ext_helped_count += 1

    return {
        "tested": n,
        "avg": sum(bests) / n,
        "best": max(bests),
        "worst": min(bests),
        "wins": wins,
        "at_11": sum(1 for b in bests if b >= 11),
        "at_12": sum(1 for b in bests if b >= 12),
        "at_14": sum(1 for b in bests if b == 14),
        "ml_helped": ml_helped_count,
        "ext_helped": ext_helped_count,
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
        print(f"\nSeries {sid} Prediction (8-Set)")
        print("=" * 75)
        print(f"{'Rank':<5} {'Set':<18} {'Numbers':<45} {'Type'}")
        print("-" * 75)
        labels = [
            "S1 (14<>16)",    # Standard
            "S2 (13<>15)",    # Standard
            "S3 (14<>15)",    # Standard
            "S4 (Primary)",   # Standard
            "S5 (ML hot#1)",  # ML
            "S6 (ML hot#2)",  # ML
            "S7 (14<>17)",    # Extended
            "S8 (14<>18)",    # Extended
        ]
        types = ["STD", "STD", "STD", "STD", "ML", "ML", "EXT", "EXT"]
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
            print(f"\nStandard: S1={w[0]} S2={w[1]} S3={w[2]} S4={w[3]}")
            print(f"ML sets:  S5={w[4]} S6={w[5]} (helped={r['ml_helped']})")
            print(f"Extended: S7={w[6]} S8={w[7]} (helped={r['ext_helped']})")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
