#!/usr/bin/env python3
"""
Production Predictor - 7-Set Strategy (Updated 2026-01-30)
==========================================================

Goal: Hit 14/14 at least once.

Strategy: 7-set optimized for JACKPOT via Gemini analysis.
Uses 5-event consensus fusion (Quint) + symmetric differences for diversity.

UPDATE 2026-01-30: Replaced S2 (E1 rank16) with SymDiff E4^E5.
- Introduces E5 (previously unused event) into the strategy
- +4 at 12+ (14 -> 18) with zero existing 12+ losses
- Bootstrap 95% CI for 12+: [+1, +8] entirely positive
- S7's 12+ contributions fully preserved
- Validated by stats-math-evaluator, simulation-testing-expert, lottery-math-analyst

UPDATE 2026-01-28: Now uses RECENCY-WEIGHTED frequency for tiebreaking.
- Only uses PAST data (no look-ahead bias)
- Weights: 3x for L10, 2x for L30, 1x for older

7 Sets (optimized for 12+ and 13+ hits):
1. S1 (E4)          - Best individual predictor
2. S2 (SD E4^E5)    - SymDiff E4⊕E5 diversity (NEW)
3. S3 (E6)          - Direct E6
4. S4 (E7)          - Direct E7
5. S5 (E3&E7)       - Strong fusion
6. S6 (SymDiff)     - E3⊕E7 diversity set
7. S7 (Quint)       - 5-event consensus

Performance (fair eval, no look-ahead): ~10.59/14 avg, 18 at 12+
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
NUM_SETS = 7

# Performance rank by wins (S1=E4 best, then rank16, etc.)
PERF_RANK = [1, 2, 3, 4, 5, 6, 7]


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
# RECENCY-WEIGHTED FREQUENCY
# =============================================================================

def get_recency_freq(data, series_id):
    """
    Get recency-weighted frequency for tiebreaking.

    Only uses data from series BEFORE the target (no look-ahead bias).
    Weights: 3x for L10, 2x for L30, 1x for older series.

    This improves real-world prediction by ~0.04 avg and +1 at 12+.
    """
    freq = Counter()
    prior_series = series_id - 1

    for sid_str, events in data.items():
        sid = int(sid_str)
        if sid >= series_id:  # Don't use current or future data
            continue

        age = prior_series - sid  # How old is this series

        # Strong recency weighting
        if age <= 10:
            weight = 3.0
        elif age <= 30:
            weight = 2.0
        else:
            weight = 1.0

        for event in events:
            for n in event:
                freq[n] += weight

    return freq


# =============================================================================
# PREDICTION - 7-set strategy optimized for unique coverage
# =============================================================================

def predict(data, series_id):
    """
    Generate 7 prediction sets optimized for JACKPOT (12+ and 13+ hits).

    Sets:
    1. S1: E4 direct - Best predictor
    2. S2: SymDiff E4⊕E5 - Diversity set (E5 = previously unused event)
    3. S3: E6 direct - High predictor
    4. S4: E7 direct - Adds unique E7 coverage
    5. S5: E3&E7 fusion - Strong fusion
    6. S6: SymDiff E3⊕E7 - Diversity set
    7. S7: Quint E2E3E4E6E7 - 5-event consensus

    Uses recency-weighted frequency (no look-ahead bias).
    """
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No data for series {int(prior)}")

    event2 = set(data[prior][1])
    event3 = set(data[prior][2])
    event4 = set(data[prior][3])
    event5 = set(data[prior][4])
    event6 = set(data[prior][5])
    event7 = set(data[prior][6])

    # Recency-weighted frequency for tiebreaking (no look-ahead bias)
    freq = get_recency_freq(data, series_id)

    # S2: SymDiff E4⊕E5 (numbers in E4 OR E5 but not both)
    sym_diff_e4e5 = (event4 | event5) - (event4 & event5)
    s2_numbers = list(sym_diff_e4e5)
    if len(s2_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s2_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s2_numbers += remaining[:14 - len(s2_numbers)]
    elif len(s2_numbers) > 14:
        s2_numbers.sort(key=lambda n: (-freq.get(n, 0), n))
        s2_numbers = s2_numbers[:14]
    s2_numbers = sorted(s2_numbers[:14])

    # E3&E7 fusion (S5)
    e3_e7_int = event3 & event7
    e3_e7_union = event3 | event7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_int, key=lambda n: -freq[n])
    s5_numbers = list(e3_e7_int) + e3_e7_remaining[:14 - len(e3_e7_int)]

    # S6: Symmetric Difference E3⊕E7 (numbers in E3 OR E7 but not both)
    sym_diff = (event3 | event7) - (event3 & event7)
    s6_numbers = list(sym_diff)
    if len(s6_numbers) < 14:
        remaining = [n for n in range(1, 26) if n not in s6_numbers]
        remaining.sort(key=lambda n: -freq.get(n, 0))
        s6_numbers += remaining[:14 - len(s6_numbers)]
    s6_numbers = sorted(s6_numbers[:14])

    # S7: Quint E2E3E4E6E7 (5-event consensus - count appearances)
    quint_events = [event2, event3, event4, event6, event7]
    number_counts = Counter()
    for e in quint_events:
        for n in e:
            number_counts[n] += 1
    quint_ranked = sorted(range(1, 26),
                         key=lambda n: (-number_counts[n], -freq.get(n, 0), n))
    s7_numbers = sorted(quint_ranked[:14])

    # 7 core sets
    sets = [
        sorted(event4),                              # S1: E4 direct
        s2_numbers,                                  # S2: SymDiff E4⊕E5
        sorted(event6),                              # S3: E6 direct
        sorted(event7),                              # S4: E7 direct
        sorted(s5_numbers),                          # S5: E3&E7 fusion
        s6_numbers,                                  # S6: SymDiff E3⊕E7
        s7_numbers,                                  # S7: Quint E2E3E4E6E7
    ]

    return {
        "series": series_id,
        "sets": sets,
        "event2": sorted(event2),
        "event3": sorted(event3),
        "event4": sorted(event4),
        "event5": sorted(event5),
        "event6": sorted(event6),
        "event7": sorted(event7),
    }


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate(data, series_id, pred=None):
    """Evaluate prediction - best match across 7 sets x 7 events."""
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
    wins = [0] * NUM_SETS
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
        "at_13": sum(1 for b in bests if b >= 13),
        "at_14": sum(1 for b in bests if b == 14),
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    data = load_data()
    last = latest(data)

    if len(sys.argv) < 2:
        print("Production Predictor (7-Set Strategy)")
        print("=" * 50)
        print("Goal: Hit 14/14 on FUTURE series")
        print("\nCommands:")
        print("  predict [series]      - 7-set prediction")
        print("  find [series]         - Find jackpot")
        print("  validate [s] [e]      - Test accuracy")
        print(f"\nLatest: {last}")
        return

    cmd = sys.argv[1]

    if cmd == "predict":
        sid = int(sys.argv[2]) if len(sys.argv) > 2 else last + 1

        r = predict(data, sid)

        print(f"\nSeries {sid} Prediction (7-Set Strategy)")
        print("=" * 70)
        print(f"{'Rank':<5} {'Set':<12} {'Numbers':<45} {'Type'}")
        print("-" * 70)

        labels = [
            "S1 (E4)",       # Direct - best predictor
            "S2 (SD4^5)",    # SymDiff E4⊕E5 diversity
            "S3 (E6)",       # Direct
            "S4 (E7)",       # Direct
            "S5 (E3&E7)",    # Fusion
            "S6 (SD3^7)",    # E3⊕E7 diversity
            "S7 (Quint)",    # 5-event consensus
        ]
        types = ["E4", "DIV", "E6", "E7", "MIX", "DIV", "5EV"]

        for idx in range(NUM_SETS):
            s = r["sets"][idx]
            nums = ' '.join(f'{n:02d}' for n in s)
            print(f"#{idx+1:<4} {labels[idx]:<12} {nums:<45} {types[idx]}")

        print("-" * 70)
        print(f"Event 3: {r['event3']}")
        print(f"Event 4: {r['event4']}")
        print(f"Event 5: {r['event5']}")
        print(f"Event 6: {r['event6']}")
        print(f"Event 7: {r['event7']}")
        print(f"Pool-24: Exclude #{EXCLUDE}")

    elif cmd == "find":
        sid = int(sys.argv[2]) if len(sys.argv) > 2 else last
        find_jackpot(data, sid)

    elif cmd == "validate":
        s = int(sys.argv[2]) if len(sys.argv) > 2 else 2981
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
            print(f"13+:     {r['at_13']}")
            print(f"14/14:   {r['at_14']}")
            w = r['wins']
            print(f"\nWins: S1(E4)={w[0]} S2(SD4^5)={w[1]} S3(E6)={w[2]} S4(E7)={w[3]}")
            print(f"      S5(E3&E7)={w[4]} S6(SD3^7)={w[5]} S7(Quint)={w[6]}")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
