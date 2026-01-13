#!/usr/bin/env python3
"""
Production Predictor
====================

Goal: Hit 14/14 at least once.

Strategy: 12-set multi-event hedging (E1 + E3 + E6 + E7).
Performance: 10.35/14 avg, 13/14 ceiling.

Multi-event discoveries:
- E6: 13/14 in Series 3061 (breakthrough event)
- E3: 2x 12/14 (Series 2998, 3134) - independent from E1/E6
- E7: 2x 12/14 (Series 3004, 3072) - independent from E1/E6
- Adding E3+E7 increases 12+ ceiling from 3 to 7 hits
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

# Performance rank by 13+/12+ potential (goal: hit 14/14)
# S9 (E6) reached 13/14! E3/E7 add 4 more 12+ opportunities.
# Rank: S9(13+) > S11(E3,2x12+) > S12(E7,2x12+) > S4(4x12+) > S7(3x12+) > rest
PERF_RANK = [12, 11, 6, 4, 10, 9, 5, 7, 1, 8, 2, 3]  # Index = set-1, value = rank (12 sets)


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
# PREDICTION - The 12-set hedge logic lives HERE and ONLY here
# =============================================================================

def predict(data, series_id):
    """
    Generate 12 prediction sets (multi-event E1+E3+E6+E7 strategy).

    E1-based sets (S1-S8):
    - Set 1-3: Single swaps (top-13 + rank 15/16/18)
    - Set 4-7: Double swaps (top-12 + two ranks)
    - Set 8: Hot numbers

    Multi-event sets (S9-S12) - breakthrough ceiling:
    - Set 9:  Prior E6 directly (REACHED 13/14!)
    - Set 10: E1 & E6 intersection + fill from union
    - Set 11: Prior E3 directly (2x 12/14, independent)
    - Set 12: Prior E7 directly (2x 12/14, independent)

    Performance: 10.35/14 avg, 13/14 ceiling, 7x 12+ events.
    """
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No data for series {int(prior)}")

    event1 = set(data[prior][0])
    event3 = set(data[prior][2])
    event6 = set(data[prior][5])
    event7 = set(data[prior][6])

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

    # E1 & E6 combined set (S10)
    intersection = event1 & event6
    union = event1 | event6
    remaining = sorted(union - intersection, key=lambda n: -freq[n])
    s10_numbers = list(intersection) + remaining[:14 - len(intersection)]

    # 12 sets - multi-event strategy (2026-01-13)
    sets = [
        sorted(ranked[:13] + [ranked[15]]),              # S1: top-13 + rank16
        sorted(ranked[:13] + [ranked[14]]),              # S2: top-13 + rank15
        sorted(ranked[:13] + [ranked[17]]),              # S3: top-13 + rank18
        sorted(ranked[:12] + [ranked[14], ranked[15]]),  # S4: top-12 + r15 + r16
        sorted(ranked[:12] + [ranked[14], ranked[17]]),  # S5: top-12 + r15 + r18
        sorted(ranked[:12] + [ranked[15], ranked[17]]),  # S6: top-12 + r16 + r18
        sorted(ranked[:12] + [ranked[14], ranked[18]]),  # S7: top-12 + r15 + r19
        sorted(ranked[:12] + [hot_outside[1], hot_outside[2]]),  # S8: hot #2+#3
        sorted(event6),                                   # S9: E6 directly (13/14!)
        sorted(s10_numbers),                              # S10: E1 & E6 combined
        sorted(event3),                                   # S11: E3 directly (2x 12+)
        sorted(event7),                                   # S12: E7 directly (2x 12+)
    ]

    return {"series": series_id, "sets": sets, "ranked": ranked,
            "hot_outside": hot_outside, "event3": sorted(event3),
            "event6": sorted(event6), "event7": sorted(event7)}


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate(data, series_id, pred=None):
    """Evaluate prediction - best match across 12 sets x 7 events."""
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
    # S1-S3: single swaps, S4-S7: double swaps, S8: hot, S9-S12: multi-event
    single_best = max(set_bests[:3])
    double_helped = winner in [4, 5, 6, 7] and set_bests[winner-1] > single_best
    hot_helped = winner == 8 and set_bests[7] > max(single_best, max(set_bests[3:7]))
    e3_helped = winner == 11 and set_bests[10] > max(set_bests[:10])
    e7_helped = winner == 12 and set_bests[11] > max(set_bests[:11])

    return {"series": series_id, "set_bests": set_bests, "best": best, "winner": winner,
            "double_helped": double_helped, "hot_helped": hot_helped,
            "e3_helped": e3_helped, "e7_helped": e7_helped}


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
    wins = [0] * 12  # 12 sets now
    double_helped_count = 0
    hot_helped_count = 0
    e3_helped_count = 0
    e7_helped_count = 0
    for r in results:
        wins[r["winner"] - 1] += 1
        if r.get("double_helped"):
            double_helped_count += 1
        if r.get("hot_helped"):
            hot_helped_count += 1
        if r.get("e3_helped"):
            e3_helped_count += 1
        if r.get("e7_helped"):
            e7_helped_count += 1

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
        "e3_helped": e3_helped_count,
        "e7_helped": e7_helped_count,
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    data = load_data()
    last = latest(data)

    if len(sys.argv) < 2:
        print("Production Predictor (12-Set Multi-Event)")
        print("=" * 50)
        print("Goal: Hit 14/14")
        print("\nCommands:")
        print("  predict [series]  - 12-set prediction (E1+E3+E6+E7)")
        print("  find [series]     - Find jackpot")
        print("  validate [s] [e]  - Test accuracy")
        print(f"\nLatest: {last}")
        return

    cmd = sys.argv[1]

    if cmd == "predict":
        sid = int(sys.argv[2]) if len(sys.argv) > 2 else last + 1
        r = predict(data, sid)
        print(f"\nSeries {sid} Prediction (12-Set Multi-Event)")
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
            "S9 (E6)",         # Event 6 directly
            "S10 (E1&E6)",     # E1 & E6 combined
            "S11 (E3)",        # Event 3 directly
            "S12 (E7)",        # Event 7 directly
        ]
        types = ["SGL", "SGL", "SGL", "DBL", "DBL", "DBL", "DBL", "HOT", "E6", "MIX", "E3", "E7"]
        # Sort by performance rank for display
        order = sorted(range(12), key=lambda i: PERF_RANK[i])
        for idx in order:
            s = r["sets"][idx]
            nums = ' '.join(f'{n:02d}' for n in s)
            print(f"#{PERF_RANK[idx]:<4} {labels[idx]:<18} {nums:<45} {types[idx]}")
        print("-" * 75)
        print(f"Hot outside top-14: {r['hot_outside']}")
        print(f"Event 3: {r['event3']}")
        print(f"Event 6: {r['event6']}")
        print(f"Event 7: {r['event7']}")
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
            print(f"E6:      S9={w[8]} S10={w[9]}")
            print(f"E3:      S11={w[10]} (helped={r['e3_helped']})")
            print(f"E7:      S12={w[11]} (helped={r['e7_helped']})")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
