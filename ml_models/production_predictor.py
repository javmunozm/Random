#!/usr/bin/env python3
"""
Production Predictor
====================

Goal: Hit 14/14 at least once.

Strategy: 27-set multi-event hedging (E1 + E3 + E6 + E7 + fusions + mixed/ALL + near-miss fixes).
Performance: 10.89/14 avg, 13/14 ceiling.

Multi-event discoveries:
- E6: 13/14 in Series 3061 (breakthrough event)
- E3: 2x 12/14 (Series 2998, 3134) - independent from E1/E6
- E7: 2x 12/14 (Series 3004, 3072) - independent from E1/E6
- Adding E3+E7 increases 12+ ceiling from 3 to 7 hits

Near-miss analysis (2026-01-16):
- S26: #13 exclusion + #18 (fixes 71% vs 57% over-selection)
- S27: #18 inclusion (fixes 18.8% under-selection in 12+ events)
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

# Performance rank by RECENCY-FIRST strategy (goal: hit 14/14)
# S18 #1 (3 recent 12+, HOT!) | S9 #2 (only 13/14 ever, but cold 114 series)
# Prioritizes what's working NOW over historical one-time breakthrough
# Updated 2026-01-16: Added S26 (#13 excl) and S27 (#18 incl) from near-miss analysis
PERF_RANK = [24, 20, 9, 4, 8, 7, 12, 16, 2, 25, 14, 13, 18, 6, 21, 3, 5, 1, 17, 23, 22, 19, 10, 15, 11, 26, 27, 28]  # 28 sets


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
# PREDICTION - The 27-set hedge logic lives HERE and ONLY here
# =============================================================================

def predict(data, series_id):
    """
    Generate 28 prediction sets (multi-event E1+E3+E5+E6+E7 + fusions + mixed/ALL + near-miss fixes).

    E1-based sets (S1-S8):
    - Set 1-3: Single swaps (top-13 + rank 15/16/18)
    - Set 4-7: Double swaps (top-12 + two ranks)
    - Set 8: Hot numbers

    Multi-event sets (S9-S12) - breakthrough ceiling:
    - Set 9:  Prior E6 directly (REACHED 13/14!)
    - Set 10: E1 & E6 intersection + fill from union
    - Set 11: Prior E3 directly (2x 12/14, independent)
    - Set 12: Prior E7 directly (2x 12/14, independent)

    #12 inclusion sets (S13-S14):
    - Set 13: top-12 + #12 + rank16
    - Set 14: top-12 + #12 + rank15

    Multi-event swap variants (S15-S18):
    - Set 15: E6 top-13 + hot outside E6
    - Set 16: E3 top-13 + hot outside E3
    - Set 17: E7 top-13 + hot outside E7
    - Set 18: E3 & E7 intersection + fill from union

    Fusion sets (S19-S22):
    - Set 19: top-12 (no #22) + #22 + rank16
    - Set 20: E6 & E7 intersection + fill from union
    - Set 21: E1 & E3 intersection + fill from union
    - Set 22: E3 & E6 & E7 intersection + fill from union

    New sets (S23-S25) - +6 12+ events:
    - Set 23: top-12 + hot#1 + cold#1 (mixed hot/cold)
    - Set 24: ALL-event intersection + fill from union
    - Set 25: E1 & E2 intersection + fill from union

    Near-miss fix sets (S26-S27) - from 2026-01-16 analysis:
    - Set 26: top-13 (no #13) + #18 (#13 over-selected 71% vs 57%)
    - Set 27: top-12 (no #18) + #18 + rank17 (#18 under-selected in 18.8% of 12+)

    E5-direct set (S28) - from 2026-01-17 analysis:
    - Set 28: Prior E5 directly (addresses frequency bias gap)
    """
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No data for series {int(prior)}")

    event1 = set(data[prior][0])
    event3 = set(data[prior][2])
    event5 = set(data[prior][4])
    event6 = set(data[prior][5])
    event7 = set(data[prior][6])

    # Global frequency for tiebreaking
    freq = Counter(n for events in data.values() for e in events for n in e)
    max_freq = max(freq.values())

    # Rank: Event1 numbers first, then by frequency
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event1), -freq[n]/max_freq, n))

    # Recent frequency for hot sets (last 3 series - optimized via lookback tuning)
    prev_series = sorted(int(s) for s in data if int(s) < series_id)[-3:]
    recent_freq = Counter(n for s in prev_series for e in data[str(s)] for n in e)

    # Hot numbers outside top 14
    non_top14 = [n for n in range(1, TOTAL + 1) if n not in ranked[:14]]
    hot_outside = sorted(non_top14, key=lambda n: -recent_freq.get(n, 0))[:3]

    # E1 & E6 combined set (S10)
    intersection = event1 & event6
    union = event1 | event6
    remaining = sorted(union - intersection, key=lambda n: -freq[n])
    s10_numbers = list(intersection) + remaining[:14 - len(intersection)]

    # #12 inclusion sets (S13-S14)
    # Force #12 into prediction by taking top-12 (excluding #12) + #12 + rank
    top12_no12 = [n for n in ranked[:14] if n != EXCLUDE][:12]
    s13_numbers = top12_no12 + [EXCLUDE, ranked[15]]  # +#12 + rank16
    s14_numbers = top12_no12 + [EXCLUDE, ranked[14]]  # +#12 + rank15

    # Multi-event swap variants (S15-S17)
    # Rank each event by global frequency, take top-13, add hot outside
    e6_ranked = sorted(event6, key=lambda n: -freq[n])
    e3_ranked = sorted(event3, key=lambda n: -freq[n])
    e7_ranked = sorted(event7, key=lambda n: -freq[n])

    hot_outside_e6 = sorted([n for n in range(1, TOTAL+1) if n not in event6],
                            key=lambda n: -recent_freq.get(n, 0))[0]
    hot_outside_e3 = sorted([n for n in range(1, TOTAL+1) if n not in event3],
                            key=lambda n: -recent_freq.get(n, 0))[0]
    hot_outside_e7 = sorted([n for n in range(1, TOTAL+1) if n not in event7],
                            key=lambda n: -recent_freq.get(n, 0))[0]

    s15_numbers = e6_ranked[:13] + [hot_outside_e6]  # E6 top-13 + hot
    s16_numbers = e3_ranked[:13] + [hot_outside_e3]  # E3 top-13 + hot
    s17_numbers = e7_ranked[:13] + [hot_outside_e7]  # E7 top-13 + hot

    # E3 & E7 combined set (S18)
    e3_e7_intersection = event3 & event7
    e3_e7_union = event3 | event7
    e3_e7_remaining = sorted(e3_e7_union - e3_e7_intersection, key=lambda n: -freq[n])
    s18_numbers = list(e3_e7_intersection) + e3_e7_remaining[:14 - len(e3_e7_intersection)]

    # S19: #22 inclusion (top-12 excluding #22 + #22 + rank16)
    top12_no22 = [n for n in ranked[:14] if n != 22][:12]
    s19_numbers = top12_no22 + [22, ranked[15]]

    # S20: E6 & E7 fusion (intersection + fill from union by freq)
    e6_e7_intersection = event6 & event7
    e6_e7_union = event6 | event7
    e6_e7_remaining = sorted(e6_e7_union - e6_e7_intersection, key=lambda n: -freq[n])
    s20_numbers = list(e6_e7_intersection) + e6_e7_remaining[:14 - len(e6_e7_intersection)]

    # S21: E1 & E3 fusion (intersection + fill from union by freq)
    e1_e3_intersection = event1 & event3
    e1_e3_union = event1 | event3
    e1_e3_remaining = sorted(e1_e3_union - e1_e3_intersection, key=lambda n: -freq[n])
    s21_numbers = list(e1_e3_intersection) + e1_e3_remaining[:14 - len(e1_e3_intersection)]

    # S22: Triple E3 & E6 & E7 fusion (intersection + fill from union by freq)
    e3_e6_e7_intersection = event3 & event6 & event7
    e3_e6_e7_union = event3 | event6 | event7
    e3_e6_e7_remaining = sorted(e3_e6_e7_union - e3_e6_e7_intersection, key=lambda n: -freq[n])
    s22_numbers = list(e3_e6_e7_intersection) + e3_e6_e7_remaining[:14 - len(e3_e6_e7_intersection)]

    # S23: Mixed hot+cold (top-12 + hot#1 + cold#1)
    non_top12 = [n for n in range(1, TOTAL + 1) if n not in ranked[:12]]
    cold_outside = sorted(non_top12, key=lambda n: recent_freq.get(n, 0))  # Ascending = coldest
    s23_numbers = ranked[:12] + [hot_outside[0], cold_outside[0]]

    # S24: ALL-event fusion (intersection of all 7 events + fill from union)
    all_intersection = event1 & event3 & event6 & event7
    for i in [1, 3, 4]:  # E2, E4, E5
        all_intersection = all_intersection & set(data[prior][i])
    all_union = set()
    for ev in data[prior]:
        all_union |= set(ev)
    all_remaining = sorted(all_union - all_intersection, key=lambda n: -freq[n])
    s24_numbers = list(all_intersection) + all_remaining[:14 - len(all_intersection)]

    # S25: E1 & E2 fusion (intersection + fill from union by freq)
    event2 = set(data[prior][1])
    e1_e2_intersection = event1 & event2
    e1_e2_union = event1 | event2
    e1_e2_remaining = sorted(e1_e2_union - e1_e2_intersection, key=lambda n: -freq[n])
    s25_numbers = list(e1_e2_intersection) + e1_e2_remaining[:14 - len(e1_e2_intersection)]

    # S26: #13 exclusion + #18 (near-miss fix: #13 over-selected 71% vs 57%)
    # Force exclude #13, force include #18, fill with best available
    base_no13 = [n for n in ranked if n != 13][:13]  # Top 13 excluding #13
    if 18 in base_no13:
        s26_numbers = base_no13 + [ranked[14] if ranked[14] != 13 else ranked[15]]
    else:
        s26_numbers = base_no13 + [18]

    # S27: #18 inclusion + different fill (near-miss fix: #18 under-selected)
    # Force include #18, use rank17 as fill to differentiate from other sets
    top12_no18 = [n for n in ranked[:14] if n != 18][:12]
    s27_numbers = top12_no18 + [18, ranked[16]]  # rank17 instead of rank16 for diversity

    # 28 sets - expanded strategy (2026-01-17)
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
        sorted(s13_numbers),                              # S13: top-12 + #12 + r16
        sorted(s14_numbers),                              # S14: top-12 + #12 + r15
        sorted(s15_numbers),                              # S15: E6 top-13 + hot
        sorted(s16_numbers),                              # S16: E3 top-13 + hot
        sorted(s17_numbers),                              # S17: E7 top-13 + hot
        sorted(s18_numbers),                              # S18: E3 & E7 combined
        sorted(s19_numbers),                              # S19: top-12 + #22 + r16
        sorted(s20_numbers),                              # S20: E6 & E7 combined
        sorted(s21_numbers),                              # S21: E1 & E3 combined
        sorted(s22_numbers),                              # S22: E3 & E6 & E7 combined
        sorted(s23_numbers),                              # S23: hot#1 + cold#1
        sorted(s24_numbers),                              # S24: ALL-event fusion
        sorted(s25_numbers),                              # S25: E1 & E2 fusion
        sorted(s26_numbers),                              # S26: no#13 + #18 (near-miss fix)
        sorted(s27_numbers),                              # S27: #18 inclusion (near-miss fix)
        sorted(event5),                                   # S28: E5 directly (freq bias fix)
    ]

    return {"series": series_id, "sets": sets, "ranked": ranked,
            "hot_outside": hot_outside, "event3": sorted(event3),
            "event5": sorted(event5), "event6": sorted(event6),
            "event7": sorted(event7)}


# =============================================================================
# PM OVERLAY SETS (Optional --pm flag)
# =============================================================================
# Goal: Maximize chance of hitting 14/14 on FUTURE series (not historical avg)
# Strategy: Diversify with rescue numbers that base strategy often misses

def generate_pm_overlays(data, series_id):
    """
    Generate PM overlay sets for jackpot pursuit on FUTURE series.

    Philosophy:
    - These sets are NOT optimized for historical average
    - They are designed to HIT JACKPOT on unknown future draws
    - Diversification > optimization
    - Include numbers base strategy commonly misses

    Returns 4 PM sets that complement the base 27-set strategy.
    """
    prior = str(series_id - 1)
    if prior not in data:
        return {"sets": [], "names": []}

    freq = Counter(n for events in data.values() for e in events for n in e)
    events = data[prior]
    event1 = set(events[0])
    event6 = set(events[5])

    # E1-ranked foundation
    ranked = sorted(range(1, 26), key=lambda n: (-(n in event1), -freq[n], n))

    # Rescue numbers: commonly missed by base when it fails
    # These could be the difference between 13/14 and 14/14
    rescue_nums = [20, 7, 14, 23]

    pm_sets = []
    names = []

    # PM-RESCUE: E1 top-10 + all 4 rescue numbers
    # Rationale: Maximum coverage of historically missed numbers
    base10 = ranked[:10]
    rescue_to_add = [n for n in rescue_nums if n not in base10]
    fill = [n for n in ranked[10:] if n not in rescue_to_add]
    pm_rescue = sorted(base10 + rescue_to_add[:4] + fill[:4 - len(rescue_to_add)])[:14]
    if len(pm_rescue) == 14:
        pm_sets.append(pm_rescue)
        names.append("PM-RESCUE")

    # PM-LUCKY: E1 top-11 + #23 + #20 + E6 pick
    # Rationale: #23 and #20 appear frequently in 12+ winning events
    base11 = ranked[:11]
    lucky_nums = [23, 20]
    lucky_to_add = [n for n in lucky_nums if n not in base11]
    e6_pick = sorted([n for n in event6 if n not in base11 and n not in lucky_to_add],
                     key=lambda n: -freq[n])[:1]
    pm_lucky = sorted(base11 + lucky_to_add + e6_pick)[:14]
    for n in ranked[11:]:
        if len(pm_lucky) >= 14:
            break
        if n not in pm_lucky:
            pm_lucky.append(n)
    pm_lucky = sorted(pm_lucky[:14])
    if len(pm_lucky) == 14:
        pm_sets.append(pm_lucky)
        names.append("PM-LUCKY")

    # PM-E1E6: E1&E6 intersection priority
    # Rationale: E6 achieved 13/14, combining with E1 foundation
    e1_e6_int = event1 & event6
    e1_only = sorted(event1 - event6, key=lambda n: -freq[n])
    e6_only = sorted(event6 - event1, key=lambda n: -freq[n])
    pm_e1e6 = list(e1_e6_int)
    for n in e1_only:
        if len(pm_e1e6) < 14:
            pm_e1e6.append(n)
    for n in e6_only:
        if len(pm_e1e6) < 14:
            pm_e1e6.append(n)
    for n in ranked:
        if len(pm_e1e6) >= 14:
            break
        if n not in pm_e1e6:
            pm_e1e6.append(n)
    pm_e1e6 = sorted(pm_e1e6[:14])
    if len(pm_e1e6) == 14:
        pm_sets.append(pm_e1e6)
        names.append("PM-E1E6")

    # PM-ANTI: Contrarian hedge with commonly missed numbers
    # Rationale: Hedge against E1 ranking failures
    anti_force = [7, 15, 20]
    base_anti = [n for n in ranked[:14] if n not in anti_force][:11]
    pm_anti = sorted(base_anti + anti_force)[:14]
    for n in ranked:
        if len(pm_anti) >= 14:
            break
        if n not in pm_anti:
            pm_anti.append(n)
    pm_anti = sorted(pm_anti[:14])
    if len(pm_anti) == 14:
        pm_sets.append(pm_anti)
        names.append("PM-ANTI")

    return {"sets": pm_sets, "names": names}


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate(data, series_id, pred=None):
    """Evaluate prediction - best match across 27 sets x 7 events."""
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
    # Track which category helped
    base_best = max(set_bests[:12])  # Original 12 sets
    n12_helped = winner in [13, 14, 19] and set_bests[winner-1] > base_best  # #12, #22 inclusions
    swap_helped = winner in [15, 16, 17, 18] and set_bests[winner-1] > base_best
    fusion_helped = winner in [20, 21, 22] and set_bests[winner-1] > base_best  # Fusions
    new_helped = winner in [23, 24, 25] and set_bests[winner-1] > base_best  # Mixed/ALL/E1E2
    nearmiss_helped = winner in [26, 27] and set_bests[winner-1] > base_best  # Near-miss fixes

    return {"series": series_id, "set_bests": set_bests, "best": best, "winner": winner,
            "n12_helped": n12_helped, "swap_helped": swap_helped, "fusion_helped": fusion_helped,
            "new_helped": new_helped, "nearmiss_helped": nearmiss_helped}


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
    wins = [0] * 28  # 28 sets
    n12_helped_count = 0
    swap_helped_count = 0
    fusion_helped_count = 0
    new_helped_count = 0
    nearmiss_helped_count = 0
    for r in results:
        wins[r["winner"] - 1] += 1
        if r.get("n12_helped"):
            n12_helped_count += 1
        if r.get("swap_helped"):
            swap_helped_count += 1
        if r.get("fusion_helped"):
            fusion_helped_count += 1
        if r.get("new_helped"):
            new_helped_count += 1
        if r.get("nearmiss_helped"):
            nearmiss_helped_count += 1

    return {
        "tested": n,
        "avg": sum(bests) / n,
        "best": max(bests),
        "worst": min(bests),
        "wins": wins,
        "at_11": sum(1 for b in bests if b >= 11),
        "at_12": sum(1 for b in bests if b >= 12),
        "at_14": sum(1 for b in bests if b == 14),
        "n12_helped": n12_helped_count,
        "swap_helped": swap_helped_count,
        "fusion_helped": fusion_helped_count,
        "new_helped": new_helped_count,
        "nearmiss_helped": nearmiss_helped_count,
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    data = load_data()
    last = latest(data)

    if len(sys.argv) < 2:
        print("Production Predictor (27-Set Multi-Event)")
        print("=" * 50)
        print("Goal: Hit 14/14 on FUTURE series")
        print("\nCommands:")
        print("  predict [series]      - 27-set prediction")
        print("  predict [series] --pm - 31-set prediction (+ PM overlay for jackpot pursuit)")
        print("  find [series]         - Find jackpot")
        print("  validate [s] [e]      - Test accuracy")
        print(f"\nLatest: {last}")
        return

    cmd = sys.argv[1]

    if cmd == "predict":
        # Parse arguments
        use_pm = "--pm" in sys.argv
        args = [a for a in sys.argv[2:] if a != "--pm"]
        sid = int(args[0]) if args else last + 1

        r = predict(data, sid)
        pm_overlay = generate_pm_overlays(data, sid) if use_pm else None

        set_count = 32 if use_pm else 28
        print(f"\nSeries {sid} Prediction ({set_count}-Set {'+ PM Jackpot Pursuit' if use_pm else 'Multi-Event'})")
        print("=" * 80)
        print(f"{'Rank':<5} {'Set':<18} {'Numbers':<45} {'Type'}")
        print("-" * 80)
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
            "S13 (#12+r16)",   # #12 inclusion
            "S14 (#12+r15)",   # #12 inclusion
            "S15 (E6+hot)",    # E6 swap
            "S16 (E3+hot)",    # E3 swap
            "S17 (E7+hot)",    # E7 swap
            "S18 (E3&E7)",     # E3 & E7 combined
            "S19 (#22+r16)",   # #22 inclusion
            "S20 (E6&E7)",     # E6 & E7 fusion
            "S21 (E1&E3)",     # E1 & E3 fusion
            "S22 (E3&E6&E7)",  # Triple fusion
            "S23 (hot+cold)",  # Mixed hot/cold
            "S24 (ALL)",       # ALL-event fusion
            "S25 (E1&E2)",     # E1 & E2 fusion
            "S26 (no#13+#18)", # Near-miss fix: #13 exclusion
            "S27 (#18+r17)",   # Near-miss fix: #18 inclusion
            "S28 (E5)",        # Event 5 directly (freq bias fix)
        ]
        types = ["SGL", "SGL", "SGL", "DBL", "DBL", "DBL", "DBL", "HOT",
                 "E6", "MIX", "E3", "E7", "#12", "#12", "E6S", "E3S", "E7S", "MIX",
                 "#22", "MIX", "MIX", "MIX", "MIX", "ALL", "MIX", "NMF", "NMF", "E5"]
        # Sort by performance rank for display
        order = sorted(range(28), key=lambda i: PERF_RANK[i])
        for idx in order:
            s = r["sets"][idx]
            nums = ' '.join(f'{n:02d}' for n in s)
            print(f"#{PERF_RANK[idx]:<4} {labels[idx]:<18} {nums:<45} {types[idx]}")
        # Display PM overlay sets if --pm flag used
        if use_pm and pm_overlay and pm_overlay["sets"]:
            print("-" * 80)
            print("PM OVERLAY SETS (Jackpot Pursuit)")
            print("-" * 80)
            pm_labels = ["S29 (PM-RESCUE)", "S30 (PM-LUCKY)", "S31 (PM-E1E6)", "S32 (PM-ANTI)"]
            pm_rationale = [
                "rescue #20,#7,#14,#23",
                "#23+#20 (12+ freq)",
                "E1&E6 intersection",
                "contrarian hedge"
            ]
            for i, (pm_set, name) in enumerate(zip(pm_overlay["sets"], pm_overlay["names"])):
                nums = ' '.join(f'{n:02d}' for n in pm_set)
                label = pm_labels[i] if i < len(pm_labels) else f"S{29+i} ({name})"
                rat = pm_rationale[i] if i < len(pm_rationale) else "PM"
                print(f"{'--':<5} {label:<18} {nums:<45} {rat}")

        print("-" * 80)
        print(f"Hot outside top-14: {r['hot_outside']}")
        print(f"Event 3: {r['event3']}")
        print(f"Event 5: {r['event5']}")
        print(f"Event 6: {r['event6']}")
        print(f"Event 7: {r['event7']}")
        print(f"Pool-24: Exclude #{EXCLUDE}")
        if use_pm:
            print(f"\nPM GOAL: Hit 14/14 on this FUTURE series (not historical optimization)")

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
            print(f"Double:  S4={w[3]} S5={w[4]} S6={w[5]} S7={w[6]}")
            print(f"Hot:     S8={w[7]}")
            print(f"E6:      S9={w[8]} S10={w[9]}")
            print(f"E3:      S11={w[10]}")
            print(f"E7:      S12={w[11]}")
            print(f"#12:     S13={w[12]} S14={w[13]} (helped={r['n12_helped']})")
            print(f"Swaps:   S15={w[14]} S16={w[15]} S17={w[16]} S18={w[17]} (helped={r['swap_helped']})")
            print(f"#22:     S19={w[18]}")
            print(f"Fusions: S20={w[19]} S21={w[20]} S22={w[21]} (helped={r['fusion_helped']})")
            print(f"New:     S23={w[22]} S24={w[23]} S25={w[24]} (helped={r['new_helped']})")
            print(f"NMFix:   S26={w[25]} S27={w[26]} (helped={r['nearmiss_helped']})")
            print(f"E5:      S28={w[27]}")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
