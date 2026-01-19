#!/usr/bin/env python3
"""
Production Predictor
====================

Goal: Hit 14/14 at least once.

Strategy: 12-set core strategy (pruned from 31 sets based on recent performance).
Only sets with wins in last 30 series or rising trends are kept.

Core sets (validated on L30 data 2026-01-18):
- E1-based: S1 rank16, S2 rank15, S4 r15+r16
- Multi-event direct: S3 E4, S5 E6 (13/14!), S7 E3, S8 E7
- Multi-event fusions: S6 E1&E6, S9 Anti-E1, S10 E7+hot, S11 E3&E7, S12 E6&E7

Performance: 10.97/14 avg on L30 (improved from 10.90 with E4 replacement).
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

# Performance rank by recent wins (L30 data, 2026-01-18, E4 replacement)
# S1=6, S3(E4)=6, S4=3, S7=3, S11=3, S5=3, S6=3, S2=2, S10=2, S12=2, S8=1, S9=1
PERF_RANK = [1, 4, 2, 3, 5, 6, 7, 12, 11, 8, 9, 10]  # 12 sets


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
# PREDICTION - 12-set core strategy
# =============================================================================

def predict(data, series_id):
    """
    Generate 12 prediction sets (pruned core strategy).

    E1-based sets (S1, S2, S4):
    - S1: top-13 + rank16 (6 wins L30, top performer)
    - S2: top-13 + rank15 (2 wins L30)
    - S4: top-12 + r15 + r16 (3 wins L30)

    Multi-event direct (S3, S5, S7, S8):
    - S3: E4 directly (6 wins L30, replaced rank18)
    - S5: E6 directly (13/14 achiever, 3 wins L30)
    - S7: E3 directly (3 wins L30)
    - S8: E7 directly (1 win L30)

    Multi-event fusions (S6, S9-S12):
    - S6:  E1 & E6 intersection + fill (3 wins L30)
    - S9:  Anti-E1 Multi - numbers from E2-E7 not in E1 (diversity)
    - S10: E7 top-13 + hot outside (2 wins L30)
    - S11: E3 & E7 fusion (3 wins L30)
    - S12: E6 & E7 fusion (2 wins L30)
    """
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No data for series {int(prior)}")

    event1 = set(data[prior][0])
    event2 = set(data[prior][1])
    event3 = set(data[prior][2])
    event4 = set(data[prior][3])
    event5 = set(data[prior][4])
    event6 = set(data[prior][5])
    event7 = set(data[prior][6])

    # Global frequency for tiebreaking
    freq = Counter(n for events in data.values() for e in events for n in e)
    max_freq = max(freq.values())

    # Rank: Event1 numbers first, then by frequency
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event1), -freq[n]/max_freq, n))

    # Recent frequency for hot sets (last 3 series)
    prev_series = sorted(int(s) for s in data if int(s) < series_id)[-3:]
    recent_freq = Counter(n for s in prev_series for e in data[str(s)] for n in e)

    # E1 & E6 fusion (S6)
    e1_e6_int = event1 & event6
    e1_e6_union = event1 | event6
    e1_e6_remaining = sorted(e1_e6_union - e1_e6_int, key=lambda n: -freq[n])
    s6_numbers = list(e1_e6_int) + e1_e6_remaining[:14 - len(e1_e6_int)]

    # Anti-E1 Multi (S9) - prioritizes numbers from E2-E7 that are NOT in E1
    anti_e1_votes = Counter()
    for e in [event2, event3, event4, event5, event6, event7]:
        for n in e:
            if n not in event1:
                anti_e1_votes[n] += 2  # Bonus for not in E1
            else:
                anti_e1_votes[n] += 1
    s9_numbers = sorted(anti_e1_votes.keys(), key=lambda n: -anti_e1_votes[n])[:14]

    # E7 + hot (S10)
    e7_ranked = sorted(event7, key=lambda n: -freq[n])
    hot_outside_e7 = sorted([n for n in range(1, TOTAL+1) if n not in event7],
                            key=lambda n: -recent_freq.get(n, 0))[0]
    s10_numbers = e7_ranked[:13] + [hot_outside_e7]

    # E3 & E7 fusion (S11)
    e3_e7_int = event3 & event7
    e3_e7_union = event3 | event7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s11_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # E6 & E7 fusion (S12)
    e6_e7_int = event6 & event7
    e6_e7_union = event6 | event7
    e6_e7_remaining = sorted(e6_e7_union - e6_e7_int, key=lambda n: -freq[n])
    s12_numbers = list(e6_e7_int) + e6_e7_remaining[:14 - len(e6_e7_int)]

    # 12 core sets
    sets = [
        sorted(ranked[:13] + [ranked[15]]),              # S1: top-13 + rank16
        sorted(ranked[:13] + [ranked[14]]),              # S2: top-13 + rank15
        sorted(event4),                                   # S3: E4 directly (6 wins L30!)
        sorted(ranked[:12] + [ranked[14], ranked[15]]),  # S4: top-12 + r15 + r16
        sorted(event6),                                   # S5: E6 directly (13/14!)
        sorted(s6_numbers),                               # S6: E1 & E6 fusion
        sorted(event3),                                   # S7: E3 directly
        sorted(event7),                                   # S8: E7 directly
        sorted(s9_numbers),                               # S9: Anti-E1 Multi
        sorted(s10_numbers),                              # S10: E7 + hot
        sorted(s11_numbers),                              # S11: E3 & E7 fusion
        sorted(s12_numbers),                              # S12: E6 & E7 fusion
    ]

    return {"series": series_id, "sets": sets, "ranked": ranked,
            "event3": sorted(event3), "event4": sorted(event4),
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

    return {"series": series_id, "set_bests": set_bests, "best": best, "winner": winner}


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
    wins = [0] * 12  # 12 sets
    for r in results:
        wins[r["winner"] - 1] += 1

    return {
        "tested": n,
        "avg": sum(bests) / n,
        "best": max(bests),
        "worst": min(bests),
        "wins": wins,
        "at_11": sum(1 for b in bests if b >= 11),
        "at_12": sum(1 for b in bests if b >= 12),
        "at_14": sum(1 for b in bests if b == 14),
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    data = load_data()
    last = latest(data)

    if len(sys.argv) < 2:
        print("Production Predictor (12-Set Core Strategy)")
        print("=" * 50)
        print("Goal: Hit 14/14 on FUTURE series")
        print("\nCommands:")
        print("  predict [series]      - 12-set prediction")
        print("  find [series]         - Find jackpot")
        print("  validate [s] [e]      - Test accuracy")
        print(f"\nLatest: {last}")
        return

    cmd = sys.argv[1]

    if cmd == "predict":
        sid = int(sys.argv[2]) if len(sys.argv) > 2 else last + 1

        r = predict(data, sid)

        print(f"\nSeries {sid} Prediction (12-Set Core Strategy)")
        print("=" * 80)
        print(f"{'Rank':<5} {'Set':<15} {'Numbers':<45} {'Type'}")
        print("-" * 80)

        labels = [
            "S1 (rank16)",    # E1-based
            "S2 (rank15)",    # E1-based
            "S3 (E4)",        # Multi-event direct (6 wins L30!)
            "S4 (r15+r16)",   # E1-based
            "S5 (E6)",        # Multi-event direct (13/14!)
            "S6 (E1&E6)",     # Fusion
            "S7 (E3)",        # Multi-event direct
            "S8 (E7)",        # Multi-event direct
            "S9 (Anti-E1)",   # Diversity set
            "S10 (E7+hot)",   # Multi-event swap
            "S11 (E3&E7)",    # Fusion
            "S12 (E6&E7)",    # Fusion
        ]
        types = ["E1", "E1", "E4", "E1", "E6", "MIX", "E3", "E7", "DIV", "E7S", "MIX", "MIX"]

        # Sort by performance rank for display
        order = sorted(range(12), key=lambda i: PERF_RANK[i])
        for idx in order:
            s = r["sets"][idx]
            nums = ' '.join(f'{n:02d}' for n in s)
            print(f"#{PERF_RANK[idx]:<4} {labels[idx]:<15} {nums:<45} {types[idx]}")

        print("-" * 80)
        print(f"Event 3: {r['event3']}")
        print(f"Event 4: {r['event4']}")
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
            print(f"\nE1-based:  S1={w[0]} S2={w[1]} S3={w[2]} S4={w[3]}")
            print(f"Direct:    S5(E6)={w[4]} S7(E3)={w[6]} S8(E7)={w[7]}")
            print(f"Fusions:   S6={w[5]} S9={w[8]} S10={w[9]} S11={w[10]} S12={w[11]}")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
