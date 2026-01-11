"""
E1-Correlated Monte Carlo Simulation

This simulation captures the structural correlation between E1 and future events:
1. E1 carryover count follows observed distribution (mean ~7.9, mode 8)
2. Within-E1 selection is nearly uniform (slight freq bias)
3. Non-E1 entry fills remaining slots (slight freq bias)
"""

import json
import random
from collections import Counter
from pathlib import Path

def load_data():
    data_path = Path(__file__).parent.parent / "data" / "full_series_data.json"
    with open(data_path) as f:
        return json.load(f)

def analyze_structure(data):
    """Extract E1 correlation structure from historical data."""
    series_keys = sorted([int(k) for k in data.keys()])

    # Global frequency for ranking
    global_freq = Counter(n for events in data.values() for e in events for n in e)
    max_freq = max(global_freq.values())

    # E1 carryover distribution
    carryover_counts = []

    # Conditional probabilities: P(position appears | carryover count)
    # This captures the KEY insight: rank-14 behavior depends on carryover level
    e1_cond_probs = {c: [0]*14 for c in range(4, 13)}  # carryover -> position counts
    non_e1_cond_probs = {c: [0]*11 for c in range(4, 13)}
    carryover_event_counts = Counter()

    for i, s in enumerate(series_keys[:-1]):
        next_s = str(series_keys[i+1])
        e1 = set(data[str(s)][0])

        # Use global frequency ranking (matches production_predictor)
        ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -global_freq[n]/max_freq, n))
        e1_ranked = [n for n in ranked if n in e1]
        non_e1_ranked = [n for n in ranked if n not in e1]

        for event in data[next_s]:
            event_set = set(event)

            # Count E1 carryover
            e1_count = len(e1 & event_set)
            carryover_counts.append(e1_count)
            carryover_event_counts[e1_count] += 1

            # Track CONDITIONAL position rates
            if e1_count in e1_cond_probs:
                for pos, num in enumerate(e1_ranked):
                    if num in event_set:
                        e1_cond_probs[e1_count][pos] += 1
                for pos, num in enumerate(non_e1_ranked):
                    if num in event_set:
                        non_e1_cond_probs[e1_count][pos] += 1

    # Convert to probabilities
    carryover_dist = Counter(carryover_counts)
    carryover_probs = {k: v/len(carryover_counts) for k, v in carryover_dist.items()}

    # Conditional probabilities normalized
    e1_cond_final = {}
    non_e1_cond_final = {}
    for c in e1_cond_probs:
        n = carryover_event_counts[c]
        if n > 0:
            e1_cond_final[c] = [x/n for x in e1_cond_probs[c]]
            non_e1_cond_final[c] = [x/n for x in non_e1_cond_probs[c]]

    return {
        'carryover_probs': carryover_probs,
        'e1_cond_probs': e1_cond_final,
        'non_e1_cond_probs': non_e1_cond_final,
        'mean_carryover': sum(carryover_counts) / len(carryover_counts)
    }

def simulate_event(e1_ranked, non_e1_ranked, structure):
    """Simulate a single event using E1 correlation structure with conditional probabilities."""
    # Sample number of E1 carryovers from distribution
    carryover_vals = list(structure['carryover_probs'].keys())
    carryover_weights = list(structure['carryover_probs'].values())
    n_e1 = random.choices(carryover_vals, weights=carryover_weights, k=1)[0]
    n_non_e1 = 14 - n_e1

    # Get CONDITIONAL probabilities for this carryover level
    # This is the KEY improvement: position probabilities depend on carryover count
    if n_e1 in structure['e1_cond_probs']:
        e1_weights = structure['e1_cond_probs'][n_e1]
        non_e1_weights = structure['non_e1_cond_probs'][n_e1]
    else:
        # Fallback to uniform for rare carryover counts
        e1_weights = [1/14] * 14
        non_e1_weights = [1/11] * 11

    # Select E1 numbers using conditional probabilities
    selected_e1 = set()
    available_e1 = list(range(14))

    while len(selected_e1) < n_e1 and available_e1:
        weights = [e1_weights[i] for i in available_e1]
        total = sum(weights)
        if total > 0:
            weights = [w/total for w in weights]
        else:
            weights = [1/len(available_e1)] * len(available_e1)
        idx = random.choices(available_e1, weights=weights, k=1)[0]
        selected_e1.add(e1_ranked[idx])
        available_e1.remove(idx)

    # Select non-E1 numbers using conditional probabilities
    selected_non_e1 = set()
    available_non_e1 = list(range(11))

    while len(selected_non_e1) < n_non_e1 and available_non_e1:
        weights = [non_e1_weights[i] for i in available_non_e1]
        total = sum(weights)
        if total > 0:
            weights = [w/total for w in weights]
        else:
            weights = [1/len(available_non_e1)] * len(available_non_e1)
        idx = random.choices(available_non_e1, weights=weights, k=1)[0]
        selected_non_e1.add(non_e1_ranked[idx])
        available_non_e1.remove(idx)

    return selected_e1 | selected_non_e1

def build_sets(ranked, non_e1_ranked):
    """Build 8 prediction sets in order (S1-S8). Ties go to lowest index."""
    # Order matters for tie-breaking: first set to achieve max wins
    return [
        ('S1', set(ranked[:13] + [ranked[15]])),           # swap 14<>16
        ('S2', set(ranked[:12] + [ranked[14], ranked[13]])),  # swap 13<>15
        ('S3', set(ranked[:13] + [ranked[14]])),           # swap 14<>15
        ('S4', set(ranked[:14])),                          # primary
        ('S5', set(ranked[:13] + [non_e1_ranked[0]])),     # ML hot #1
        ('S6', set(ranked[:12] + [non_e1_ranked[0], non_e1_ranked[1]])),  # ML hot #1+#2
        ('S7', set(ranked[:13] + [ranked[16]])),           # swap 14<>17
        ('S8', set(ranked[:13] + [ranked[17]])),           # swap 14<>18
    ]

def build_sets_with_ml(ranked, hot_outside):
    """Build 8 prediction sets with specific hot_outside numbers."""
    return [
        ('S1', set(ranked[:13] + [ranked[15]])),           # swap 14<>16
        ('S2', set(ranked[:12] + [ranked[14], ranked[13]])),  # swap 13<>15
        ('S3', set(ranked[:13] + [ranked[14]])),           # swap 14<>15
        ('S4', set(ranked[:14])),                          # primary
        ('S5', set(ranked[:13] + [hot_outside[0]])),       # ML hot #1
        ('S6', set(ranked[:12] + hot_outside[:2])),        # ML hot #1+#2
        ('S7', set(ranked[:13] + [ranked[16]])),           # swap 14<>17
        ('S8', set(ranked[:13] + [ranked[17]])),           # swap 14<>18
    ]

def run_simulation(n_sims=10000, seed=42, backtest=False):
    """Run E1-correlated simulation."""
    random.seed(seed)

    data = load_data()
    structure = analyze_structure(data)
    series_keys = sorted([int(k) for k in data.keys()])

    print("=" * 70)
    print("E1-CORRELATED MONTE CARLO SIMULATION")
    print("=" * 70)
    print(f"Simulations: {n_sims:,}")
    print(f"Mean E1 carryover: {structure['mean_carryover']:.2f}")
    print(f"Mode: {'Backtest (all series)' if backtest else 'Forward (series 3174)'}")
    print()

    set_names = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']
    results = {name: [] for name in set_names}
    best_match_dist = []
    winner_counts = Counter()

    # Global frequency (matches production_predictor - uses ALL data)
    global_freq = Counter(n for events in data.values() for e in events for n in e)
    max_freq = max(global_freq.values())

    if backtest:
        # Backtest: simulate across all historical series configurations
        sims_per_series = max(1, n_sims // len(series_keys[:-1]))
        actual_sims = 0

        for i, s in enumerate(series_keys[:-1]):
            next_s = str(series_keys[i+1])
            e1 = set(data[str(s)][0])

            # Use GLOBAL frequency ranking (matches production_predictor)
            ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -global_freq[n]/max_freq, n))
            e1_ranked = [n for n in ranked if n in e1]
            non_e1_ranked = [n for n in ranked if n not in e1]

            # Recent frequency for ML sets
            prev_5 = sorted(int(ss) for ss in data if int(ss) < int(next_s))[-5:]
            recent_freq = Counter(n for ss in prev_5 for e in data[str(ss)] for n in e)
            non_top14 = [n for n in range(1, 26) if n not in ranked[:14]]
            hot_outside = sorted(non_top14, key=lambda n: -recent_freq.get(n, 0))[:3]

            sets = build_sets_with_ml(ranked, hot_outside)

            for _ in range(sims_per_series):
                sim_events = [simulate_event(e1_ranked, non_e1_ranked, structure) for _ in range(7)]

                set_bests = []
                for name, pred in sets:
                    best = max(len(pred & event) for event in sim_events)
                    set_bests.append(best)
                    results[name].append(best)

                best_overall = max(set_bests)
                winner_idx = set_bests.index(best_overall)
                winner = set_names[winner_idx]

                best_match_dist.append(best_overall)
                winner_counts[winner] += 1
                actual_sims += 1

        n_sims = actual_sims
    else:
        # Forward: use latest series as basis
        latest = str(series_keys[-1])
        e1 = set(data[latest][0])

        # Use GLOBAL frequency ranking (matches production_predictor)
        ranked = sorted(range(1, 26), key=lambda n: (-(n in e1), -global_freq[n]/max_freq, n))
        e1_ranked = [n for n in ranked if n in e1]
        non_e1_ranked = [n for n in ranked if n not in e1]

        prev_5 = series_keys[-5:]
        recent_freq = Counter(n for s in prev_5 for e in data[str(s)] for n in e)
        non_top14 = [n for n in range(1, 26) if n not in ranked[:14]]
        hot_outside = sorted(non_top14, key=lambda n: -recent_freq.get(n, 0))[:3]

        sets = build_sets_with_ml(ranked, hot_outside)

        print(f"Predicting for series {int(latest)+1}")
        print(f"E1 basis: {sorted(e1)}")
        print(f"Hot outside: {hot_outside}")
        print()

        for sim in range(n_sims):
            sim_events = [simulate_event(e1_ranked, non_e1_ranked, structure) for _ in range(7)]

            set_bests = []
            for name, pred in sets:
                best = max(len(pred & event) for event in sim_events)
                set_bests.append(best)
                results[name].append(best)

            best_overall = max(set_bests)
            winner_idx = set_bests.index(best_overall)
            winner = set_names[winner_idx]

            best_match_dist.append(best_overall)
            winner_counts[winner] += 1

    # Report results
    print("EXPECTED MATCH DISTRIBUTION (best of 8 sets):")
    match_counts = Counter(best_match_dist)
    for m in sorted(match_counts.keys(), reverse=True):
        pct = match_counts[m] / n_sims * 100
        bar = '#' * int(pct / 2)
        print(f"  {m:2d}/14: {match_counts[m]:5d} ({pct:5.1f}%) {bar}")

    mean_best = sum(best_match_dist) / n_sims
    print(f"\nMean best match: {mean_best:.2f}/14")
    print(f"P(11+): {sum(1 for m in best_match_dist if m >= 11)/n_sims*100:.1f}%")
    print(f"P(12+): {sum(1 for m in best_match_dist if m >= 12)/n_sims*100:.1f}%")
    print(f"P(13+): {sum(1 for m in best_match_dist if m >= 13)/n_sims*100:.1f}%")
    print(f"P(14/14): {sum(1 for m in best_match_dist if m == 14)/n_sims*100:.3f}%")

    print("\nSET WIN RATES (with tie-breaking):")
    for name in set_names:
        wins = winner_counts[name]
        pct = wins / n_sims * 100
        avg = sum(results[name]) / n_sims
        print(f"  {name}: {wins:5d} wins ({pct:5.1f}%), avg {avg:.2f}/14")

    # Compare to historical
    print("\n" + "=" * 70)
    print("COMPARISON TO HISTORICAL")
    print("=" * 70)
    historical = {'S1': 46.6, 'S2': 21.8, 'S3': 2.6, 'S4': 10.4,
                  'S5': 4.7, 'S6': 6.7, 'S7': 4.7, 'S8': 2.6}

    print(f"{'Set':<6} {'Historical':>12} {'Simulated':>12} {'Diff':>10}")
    print("-" * 42)
    for name in set_names:
        hist = historical[name]
        sim_pct = winner_counts[name] / n_sims * 100
        diff = sim_pct - hist
        print(f"{name:<6} {hist:>11.1f}% {sim_pct:>11.1f}% {diff:>+9.1f}%")

    return results, winner_counts, best_match_dist

if __name__ == "__main__":
    import sys
    n_sims = 10000
    backtest = False

    for arg in sys.argv[1:]:
        if arg == "--backtest":
            backtest = True
        elif arg.isdigit():
            n_sims = int(arg)

    run_simulation(n_sims, backtest=backtest)
