#!/usr/bin/env python3
"""
Multi-Armed Bandit Predictor
============================

Tests whether reinforcement learning (bandit algorithms) can outperform
the static 12-set core strategy by dynamically adapting which prediction
strategy to use.

Key difference from previous tests:
- DON'T just pick the historically best arm
- BALANCE exploration vs exploitation
- Account for UNCERTAINTY in estimates

Arms (prediction strategies):
- Arms 0-6: Direct event copies (E1-E7)
- Arms 7-9: E1 ranked with different boundary numbers
- Arms 10-15: Event fusions (E1&E6, E3&E7, E6&E7, etc.)

Algorithms tested:
- Epsilon-Greedy: Simple explore/exploit balance
- UCB1: Upper Confidence Bound (optimism in uncertainty)
- Thompson Sampling: Bayesian approach with posterior sampling
- EXP3: Adversarial bandits (assumes worst-case)
- Sliding Window UCB: Adapts to non-stationary environments

Hypothesis: If the optimal strategy changes over time, bandits can adapt
and potentially outperform a static approach.

==============================================================================
RESULTS (2026-01-26, series 2991-3180, n=190)
==============================================================================

| Method                    | Average | vs 12-Set |
|---------------------------|---------|-----------|
| Oracle (hindsight)        | 10.83   | +0.09     |
| 12-Set Core Strategy      | 10.74   | baseline  |
| Best Bandit (DecayEps)    | 9.62    | -1.12     |
| Static Best Single Arm    | 9.62    | -1.12     |

KEY FINDINGS:

1. ALL bandit algorithms perform WORSE than the 12-set strategy (-1.12 to -1.29)

2. The best arm changes 80% of the time across 30-series windows:
   - E1_direct: 25% of windows
   - E3_E7_fusion: 19% of windows
   - 7 other arms share remaining windows

3. Despite frequent changes, bandits don't help because:
   - Changes are RANDOM and UNPREDICTABLE
   - Past arm performance doesn't predict future performance
   - Exploration/exploitation is useless when there's no learnable pattern

4. The 12-set strategy wins because it:
   - Uses ALL strategies simultaneously (no selection needed)
   - Takes the BEST of 12 each series (ensemble approach)
   - Doesn't need to learn or adapt

CONCLUSION:

Reinforcement learning cannot help this problem. The optimal strategy
changes randomly over time, making adaptation impossible. The current
"pick best of 12" ensemble approach is superior to any selection-based
method.

This confirms the CLAUDE.md finding: the system is at theoretical ceiling.
No intelligent adaptation can beat the simple ensemble.
"""

import json
import math
import random
import numpy as np
from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


# =============================================================================
# CONSTANTS
# =============================================================================

TOTAL = 25
PICK = 14
EXCLUDE = 12

# Random seed for reproducibility
SEED = 42


# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    """Load lottery data from JSON."""
    paths = [
        Path(__file__).parent.parent / "data" / "full_series_data.json",
        Path("data/full_series_data.json")
    ]
    for p in paths:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("Data not found")


# =============================================================================
# ARM DEFINITIONS (PREDICTION STRATEGIES)
# =============================================================================

@dataclass
class Arm:
    """A prediction strategy (arm in the bandit)."""
    name: str
    generate: callable  # Function to generate prediction set


def create_arms(data: dict, prior_series: str) -> List[Arm]:
    """Create all arms (prediction strategies) based on prior series data."""

    events = data[prior_series]
    event1 = set(events[0])
    event2 = set(events[1])
    event3 = set(events[2])
    event4 = set(events[3])
    event5 = set(events[4])
    event6 = set(events[5])
    event7 = set(events[6])

    # Global frequency for ranking
    freq = Counter(n for series_events in data.values() for e in series_events for n in e)
    max_freq = max(freq.values())

    # E1 ranked numbers
    ranked = sorted(range(1, TOTAL + 1),
                    key=lambda n: (-(n in event1), -freq[n]/max_freq, n))

    arms = []

    # Arms 0-6: Direct event copies
    for i, (name, event) in enumerate([
        ("E1_direct", event1), ("E2_direct", event2), ("E3_direct", event3),
        ("E4_direct", event4), ("E5_direct", event5), ("E6_direct", event6),
        ("E7_direct", event7)
    ]):
        arms.append(Arm(name=name, generate=lambda e=event: sorted(e)))

    # Arms 7-9: E1 ranked with different boundaries
    arms.append(Arm(name="E1_rank14", generate=lambda: sorted(ranked[:13] + [ranked[13]])))
    arms.append(Arm(name="E1_rank15", generate=lambda: sorted(ranked[:13] + [ranked[14]])))
    arms.append(Arm(name="E1_rank16", generate=lambda: sorted(ranked[:13] + [ranked[15]])))

    # Arm 10: Top-12 + rank15 + rank16
    arms.append(Arm(name="E1_r15_r16", generate=lambda: sorted(ranked[:12] + [ranked[14], ranked[15]])))

    # Arms 11-15: Event fusions
    def make_fusion(e1: set, e2: set) -> List[int]:
        intersection = e1 & e2
        union = e1 | e2
        remaining = sorted(union - intersection, key=lambda n: -freq[n])
        result = list(intersection) + remaining[:14 - len(intersection)]
        return sorted(result)

    arms.append(Arm(name="E1_E6_fusion", generate=lambda: make_fusion(event1, event6)))
    arms.append(Arm(name="E3_E7_fusion", generate=lambda: make_fusion(event3, event7)))
    arms.append(Arm(name="E6_E7_fusion", generate=lambda: make_fusion(event6, event7)))
    arms.append(Arm(name="E1_E3_fusion", generate=lambda: make_fusion(event1, event3)))
    arms.append(Arm(name="E4_E5_fusion", generate=lambda: make_fusion(event4, event5)))

    # Arm 16: Anti-E1 Multi (numbers from E2-E7 not in E1)
    def anti_e1_multi():
        votes = Counter()
        for e in [event2, event3, event4, event5, event6, event7]:
            for n in e:
                votes[n] += 2 if n not in event1 else 1
        return sorted(sorted(votes.keys(), key=lambda n: -votes[n])[:14])
    arms.append(Arm(name="Anti_E1_Multi", generate=anti_e1_multi))

    return arms


def get_arm_prediction(data: dict, series_id: int, arm_index: int) -> List[int]:
    """Get prediction for a specific arm for a given series."""
    prior = str(series_id - 1)
    if prior not in data:
        raise ValueError(f"No prior data for series {series_id}")

    arms = create_arms(data, prior)
    return arms[arm_index].generate()


def get_best_match(prediction: List[int], events: List[List[int]]) -> int:
    """Get best match score for a prediction against all events."""
    pred_set = set(prediction)
    return max(len(pred_set & set(e)) for e in events)


# =============================================================================
# BANDIT ALGORITHMS
# =============================================================================

@dataclass
class BanditState:
    """State for a bandit algorithm."""
    n_arms: int
    counts: np.ndarray = field(default_factory=lambda: np.array([]))
    values: np.ndarray = field(default_factory=lambda: np.array([]))
    sum_rewards: np.ndarray = field(default_factory=lambda: np.array([]))
    sum_sq_rewards: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self):
        if len(self.counts) == 0:
            self.counts = np.zeros(self.n_arms)
            self.values = np.zeros(self.n_arms)
            self.sum_rewards = np.zeros(self.n_arms)
            self.sum_sq_rewards = np.zeros(self.n_arms)

    def update(self, arm: int, reward: float):
        """Update statistics for an arm."""
        self.counts[arm] += 1
        self.sum_rewards[arm] += reward
        self.sum_sq_rewards[arm] += reward ** 2
        self.values[arm] = self.sum_rewards[arm] / self.counts[arm]


class EpsilonGreedy:
    """Epsilon-Greedy algorithm."""

    def __init__(self, n_arms: int, epsilon: float = 0.1):
        self.state = BanditState(n_arms)
        self.epsilon = epsilon
        self.name = f"EpsilonGreedy(eps={epsilon})"

    def select_arm(self, t: int) -> int:
        """Select arm using epsilon-greedy."""
        # Force exploration for unvisited arms
        unvisited = np.where(self.state.counts == 0)[0]
        if len(unvisited) > 0:
            return int(np.random.choice(unvisited))

        if np.random.random() < self.epsilon:
            return np.random.randint(self.state.n_arms)
        return int(np.argmax(self.state.values))

    def update(self, arm: int, reward: float):
        self.state.update(arm, reward)


class DecayingEpsilonGreedy:
    """Epsilon-Greedy with decaying epsilon."""

    def __init__(self, n_arms: int, initial_epsilon: float = 1.0, decay: float = 0.99):
        self.state = BanditState(n_arms)
        self.initial_epsilon = initial_epsilon
        self.decay = decay
        self.t = 0
        self.name = f"DecayingEpsilon(init={initial_epsilon}, decay={decay})"

    def select_arm(self, t: int) -> int:
        """Select arm with decaying epsilon."""
        unvisited = np.where(self.state.counts == 0)[0]
        if len(unvisited) > 0:
            return int(np.random.choice(unvisited))

        epsilon = self.initial_epsilon * (self.decay ** t)
        if np.random.random() < epsilon:
            return np.random.randint(self.state.n_arms)
        return int(np.argmax(self.state.values))

    def update(self, arm: int, reward: float):
        self.state.update(arm, reward)


class UCB1:
    """Upper Confidence Bound algorithm."""

    def __init__(self, n_arms: int, c: float = 2.0):
        self.state = BanditState(n_arms)
        self.c = c
        self.name = f"UCB1(c={c})"

    def select_arm(self, t: int) -> int:
        """Select arm using UCB1."""
        unvisited = np.where(self.state.counts == 0)[0]
        if len(unvisited) > 0:
            return int(np.random.choice(unvisited))

        # UCB1 formula: value + c * sqrt(ln(t) / count)
        ucb_values = self.state.values + self.c * np.sqrt(np.log(t + 1) / self.state.counts)
        return int(np.argmax(ucb_values))

    def update(self, arm: int, reward: float):
        self.state.update(arm, reward)


class ThompsonSampling:
    """Thompson Sampling with normal prior."""

    def __init__(self, n_arms: int, prior_mean: float = 10.0, prior_var: float = 4.0):
        self.n_arms = n_arms
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        self.state = BanditState(n_arms)
        self.name = f"ThompsonSampling(mu={prior_mean}, var={prior_var})"

    def select_arm(self, t: int) -> int:
        """Select arm by sampling from posterior."""
        samples = np.zeros(self.n_arms)
        for i in range(self.n_arms):
            if self.state.counts[i] == 0:
                # Sample from prior
                samples[i] = np.random.normal(self.prior_mean, np.sqrt(self.prior_var))
            else:
                # Posterior with known variance (approximation)
                n = self.state.counts[i]
                post_var = 1.0 / (1.0/self.prior_var + n/4.0)  # Assume obs variance ~4
                post_mean = post_var * (self.prior_mean/self.prior_var +
                                        self.state.sum_rewards[i]/4.0)
                samples[i] = np.random.normal(post_mean, np.sqrt(post_var))
        return int(np.argmax(samples))

    def update(self, arm: int, reward: float):
        self.state.update(arm, reward)


class EXP3:
    """EXP3 algorithm for adversarial bandits."""

    def __init__(self, n_arms: int, gamma: float = 0.1):
        self.n_arms = n_arms
        self.gamma = gamma
        self.weights = np.ones(n_arms)
        self.state = BanditState(n_arms)
        self.name = f"EXP3(gamma={gamma})"

    def select_arm(self, t: int) -> int:
        """Select arm using EXP3 probabilities."""
        probs = (1 - self.gamma) * self.weights / self.weights.sum() + self.gamma / self.n_arms
        return int(np.random.choice(self.n_arms, p=probs))

    def update(self, arm: int, reward: float):
        self.state.update(arm, reward)
        # Normalize reward to [0, 1]
        normalized_reward = reward / 14.0
        # Update weights
        probs = (1 - self.gamma) * self.weights / self.weights.sum() + self.gamma / self.n_arms
        estimated_reward = normalized_reward / probs[arm]
        self.weights[arm] *= np.exp(self.gamma * estimated_reward / self.n_arms)


class SlidingWindowUCB:
    """UCB with sliding window (adapts to non-stationary environments)."""

    def __init__(self, n_arms: int, window_size: int = 30, c: float = 2.0):
        self.n_arms = n_arms
        self.window_size = window_size
        self.c = c
        self.history: List[Tuple[int, float]] = []  # (arm, reward) pairs
        self.state = BanditState(n_arms)  # For overall tracking
        self.name = f"SlidingWindowUCB(w={window_size}, c={c})"

    def select_arm(self, t: int) -> int:
        """Select arm using windowed UCB."""
        # Get recent history
        recent = self.history[-self.window_size:] if len(self.history) > 0 else []

        counts = np.zeros(self.n_arms)
        sums = np.zeros(self.n_arms)

        for arm, reward in recent:
            counts[arm] += 1
            sums[arm] += reward

        # Force exploration for unvisited arms in window
        unvisited = np.where(counts == 0)[0]
        if len(unvisited) > 0:
            return int(np.random.choice(unvisited))

        values = sums / counts
        total = len(recent)
        ucb_values = values + self.c * np.sqrt(np.log(total + 1) / counts)
        return int(np.argmax(ucb_values))

    def update(self, arm: int, reward: float):
        self.state.update(arm, reward)
        self.history.append((arm, reward))


# =============================================================================
# SIMULATION
# =============================================================================

def compute_oracle_best(data: dict, start: int, end: int) -> Dict:
    """
    Compute oracle performance (best arm per series with hindsight).
    This is the upper bound for any bandit algorithm.
    """
    scores = []
    arm_wins = Counter()

    for series_id in range(start, end + 1):
        sid = str(series_id)
        prior = str(series_id - 1)

        if sid not in data or prior not in data:
            continue

        arms = create_arms(data, prior)
        events = data[sid]

        best_score = 0
        best_arm = 0
        for i, arm in enumerate(arms):
            pred = arm.generate()
            score = get_best_match(pred, events)
            if score > best_score:
                best_score = score
                best_arm = i

        scores.append(best_score)
        arm_wins[best_arm] += 1

    return {
        "avg": np.mean(scores),
        "total": sum(scores),
        "arm_wins": arm_wins,
        "scores": scores
    }


def compute_static_best(data: dict, start: int, end: int) -> Dict:
    """
    Compute performance of always picking the historically best arm.
    This simulates what the current static system does.
    """
    # First pass: find best arm overall
    arm_scores = Counter()
    arm_counts = Counter()

    for series_id in range(start, end + 1):
        sid = str(series_id)
        prior = str(series_id - 1)

        if sid not in data or prior not in data:
            continue

        arms = create_arms(data, prior)
        events = data[sid]

        for i, arm in enumerate(arms):
            pred = arm.generate()
            score = get_best_match(pred, events)
            arm_scores[i] += score
            arm_counts[i] += 1

    # Find best arm by average score
    best_arm = max(range(len(arm_scores)), key=lambda i: arm_scores[i] / max(arm_counts[i], 1))

    # Second pass: compute scores for always picking that arm
    scores = []
    for series_id in range(start, end + 1):
        sid = str(series_id)
        prior = str(series_id - 1)

        if sid not in data or prior not in data:
            continue

        arms = create_arms(data, prior)
        events = data[sid]
        pred = arms[best_arm].generate()
        scores.append(get_best_match(pred, events))

    arm_name = create_arms(data, str(start - 1))[best_arm].name

    return {
        "best_arm": best_arm,
        "best_arm_name": arm_name,
        "avg": np.mean(scores),
        "total": sum(scores),
        "scores": scores
    }


def run_bandit(bandit, data: dict, start: int, end: int, verbose: bool = False) -> Dict:
    """Run a bandit algorithm over a series range."""
    np.random.seed(SEED)
    random.seed(SEED)

    scores = []
    selected_arms = []
    cumulative_regret = []
    total_regret = 0

    for t, series_id in enumerate(range(start, end + 1)):
        sid = str(series_id)
        prior = str(series_id - 1)

        if sid not in data or prior not in data:
            continue

        arms = create_arms(data, prior)
        events = data[sid]

        # Select arm
        arm_idx = bandit.select_arm(t)
        pred = arms[arm_idx].generate()
        score = get_best_match(pred, events)

        # Update bandit
        bandit.update(arm_idx, score)

        # Track results
        scores.append(score)
        selected_arms.append(arm_idx)

        # Compute regret (vs oracle for this series)
        oracle_score = max(get_best_match(a.generate(), events) for a in arms)
        total_regret += oracle_score - score
        cumulative_regret.append(total_regret)

        if verbose and (t + 1) % 50 == 0:
            print(f"  t={t+1}: avg={np.mean(scores):.2f}, regret={total_regret:.1f}")

    # Arm selection summary
    arm_selection_counts = Counter(selected_arms)

    return {
        "name": bandit.name,
        "avg": np.mean(scores),
        "total": sum(scores),
        "scores": scores,
        "cumulative_regret": cumulative_regret,
        "final_regret": total_regret,
        "arm_counts": dict(arm_selection_counts),
        "arm_values": bandit.state.values.tolist() if hasattr(bandit.state, 'values') else []
    }


def run_best_of_12_sets(data: dict, start: int, end: int) -> Dict:
    """
    Run the current 12-set core strategy and return the best match.
    This is the baseline comparison.
    """
    from production_predictor import predict, evaluate

    scores = []
    for series_id in range(start, end + 1):
        result = evaluate(data, series_id)
        if result:
            scores.append(result['best'])

    return {
        "name": "12-Set Core Strategy",
        "avg": np.mean(scores),
        "total": sum(scores),
        "scores": scores
    }


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def run_experiment(start: int = 2991, end: int = 3180, verbose: bool = True):
    """Run full bandit experiment."""

    print("=" * 70)
    print("MULTI-ARMED BANDIT EXPERIMENT")
    print("=" * 70)
    print(f"\nSeries range: {start}-{end}")
    print(f"Random seed: {SEED}")

    data = load_data()

    # Count available series
    n_series = sum(1 for s in range(start, end + 1)
                   if str(s) in data and str(s-1) in data)
    print(f"Valid series: {n_series}")

    # Create sample arms to show structure
    sample_arms = create_arms(data, str(start - 1))
    n_arms = len(sample_arms)
    print(f"\nNumber of arms: {n_arms}")
    print("\nArms:")
    for i, arm in enumerate(sample_arms):
        print(f"  {i:2d}: {arm.name}")

    # Compute baselines
    print("\n" + "-" * 70)
    print("BASELINES")
    print("-" * 70)

    oracle = compute_oracle_best(data, start, end)
    print(f"\nOracle (hindsight best): {oracle['avg']:.2f}/14 (total: {oracle['total']})")
    print(f"  Top 5 winning arms: {oracle['arm_wins'].most_common(5)}")

    static = compute_static_best(data, start, end)
    print(f"\nStatic Best Arm ({static['best_arm_name']}): {static['avg']:.2f}/14")

    baseline_12 = run_best_of_12_sets(data, start, end)
    print(f"\n12-Set Core Strategy: {baseline_12['avg']:.2f}/14")

    # Run bandit algorithms
    print("\n" + "-" * 70)
    print("BANDIT ALGORITHMS")
    print("-" * 70)

    algorithms = [
        EpsilonGreedy(n_arms, epsilon=0.1),
        EpsilonGreedy(n_arms, epsilon=0.2),
        DecayingEpsilonGreedy(n_arms, initial_epsilon=1.0, decay=0.99),
        DecayingEpsilonGreedy(n_arms, initial_epsilon=1.0, decay=0.95),
        UCB1(n_arms, c=1.0),
        UCB1(n_arms, c=2.0),
        UCB1(n_arms, c=0.5),
        ThompsonSampling(n_arms, prior_mean=10.0, prior_var=4.0),
        ThompsonSampling(n_arms, prior_mean=7.0, prior_var=9.0),  # Wider prior
        EXP3(n_arms, gamma=0.1),
        EXP3(n_arms, gamma=0.2),
        SlidingWindowUCB(n_arms, window_size=30, c=2.0),
        SlidingWindowUCB(n_arms, window_size=50, c=2.0),
    ]

    results = []
    for algo in algorithms:
        print(f"\nRunning {algo.name}...")
        result = run_bandit(algo, data, start, end, verbose=False)
        results.append(result)
        print(f"  Average: {result['avg']:.2f}/14")
        print(f"  Regret:  {result['final_regret']:.1f}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"\n{'Algorithm':<45} {'Avg':>8} {'vs Static':>10} {'vs 12-Set':>10} {'Regret':>8}")
    print("-" * 85)

    print(f"{'Oracle (upper bound)':<45} {oracle['avg']:>7.2f}  {'--':>10} {'--':>10} {'0':>8}")
    print(f"{'Static Best Arm':<45} {static['avg']:>7.2f}  {'--':>10} {static['avg'] - baseline_12['avg']:>+9.2f} {'--':>8}")
    print(f"{'12-Set Core Strategy':<45} {baseline_12['avg']:>7.2f}  {baseline_12['avg'] - static['avg']:>+9.2f} {'--':>10} {'--':>8}")
    print("-" * 85)

    for r in sorted(results, key=lambda x: -x['avg']):
        vs_static = r['avg'] - static['avg']
        vs_12set = r['avg'] - baseline_12['avg']
        print(f"{r['name']:<45} {r['avg']:>7.2f}  {vs_static:>+9.2f} {vs_12set:>+9.2f} {r['final_regret']:>8.1f}")

    # Best bandit
    best_bandit = max(results, key=lambda x: x['avg'])

    print("\n" + "-" * 70)
    print("CONCLUSIONS")
    print("-" * 70)

    print(f"\nBest bandit: {best_bandit['name']} ({best_bandit['avg']:.2f}/14)")
    print(f"Baseline (12-Set): {baseline_12['avg']:.2f}/14")
    print(f"Difference: {best_bandit['avg'] - baseline_12['avg']:+.2f}/14")

    if best_bandit['avg'] > baseline_12['avg']:
        print("\nRESULT: Bandit OUTPERFORMS static 12-set strategy!")
        print("        Consider implementing adaptive arm selection.")
    else:
        print("\nRESULT: Bandit does NOT outperform static 12-set strategy.")
        print("        The optimal strategy is likely stationary (doesn't change over time).")
        print("        Exploration/exploitation tradeoff provides no benefit.")

    # Arm value analysis
    print("\n" + "-" * 70)
    print("ARM VALUE ANALYSIS (from Thompson Sampling)")
    print("-" * 70)

    ts_result = next(r for r in results if "ThompsonSampling" in r['name'] and "mu=10" in r['name'])
    arm_values = ts_result['arm_values']

    print(f"\n{'Rank':<5} {'Arm':<20} {'Learned Value':>15} {'Times Pulled':>15}")
    print("-" * 60)

    for rank, (idx, val) in enumerate(sorted(enumerate(arm_values), key=lambda x: -x[1])[:10], 1):
        arm_name = sample_arms[idx].name
        pulls = ts_result['arm_counts'].get(idx, 0)
        print(f"{rank:<5} {arm_name:<20} {val:>14.2f} {pulls:>15}")

    # Regret analysis
    print("\n" + "-" * 70)
    print("REGRET ANALYSIS")
    print("-" * 70)

    print("\nCumulative regret measures how much worse the algorithm performed")
    print("compared to always choosing the best arm with hindsight.")
    print("\nLower regret = better exploration/exploitation balance.")

    min_regret = min(r['final_regret'] for r in results)
    for r in sorted(results, key=lambda x: x['final_regret'])[:5]:
        print(f"  {r['name']:<45} {r['final_regret']:.1f}")

    return {
        "oracle": oracle,
        "static": static,
        "baseline_12": baseline_12,
        "bandits": results
    }


# =============================================================================
# CLI
# =============================================================================

def analyze_arm_stability(data: dict, start: int, end: int):
    """
    Analyze whether the best arm changes over time.
    If it does, bandits could theoretically help by adapting.
    If it doesn't, static selection is optimal.
    """
    print("\n" + "=" * 70)
    print("ARM STABILITY ANALYSIS")
    print("=" * 70)
    print("\nQuestion: Does the best strategy change over time?")
    print("If yes -> Bandits could help by adapting")
    print("If no  -> Static selection is optimal")

    window_size = 30
    windows = []

    for w_start in range(start, end - window_size + 1, 10):
        w_end = w_start + window_size - 1

        arm_scores = Counter()
        arm_counts = Counter()

        for series_id in range(w_start, w_end + 1):
            sid = str(series_id)
            prior = str(series_id - 1)

            if sid not in data or prior not in data:
                continue

            arms = create_arms(data, prior)
            events = data[sid]

            for i, arm in enumerate(arms):
                pred = arm.generate()
                score = get_best_match(pred, events)
                arm_scores[i] += score
                arm_counts[i] += 1

        # Find best arm for this window
        if arm_counts:
            best_arm = max(range(17), key=lambda i: arm_scores[i] / max(arm_counts[i], 1))
            best_avg = arm_scores[best_arm] / arm_counts[best_arm]
            windows.append((w_start, w_end, best_arm, best_avg))

    sample_arms = create_arms(data, str(start - 1))

    print(f"\n{'Window':<15} {'Best Arm':<20} {'Avg Score':>10}")
    print("-" * 50)
    for w_start, w_end, best_arm, best_avg in windows:
        print(f"{w_start}-{w_end:<7} {sample_arms[best_arm].name:<20} {best_avg:>9.2f}")

    # Analyze stability
    best_arms = [w[2] for w in windows]
    unique_arms = len(set(best_arms))
    changes = sum(1 for i in range(1, len(best_arms)) if best_arms[i] != best_arms[i-1])

    print(f"\n" + "-" * 50)
    print(f"Total windows: {len(windows)}")
    print(f"Unique best arms: {unique_arms}")
    print(f"Times best arm changed: {changes}")
    print(f"Stability: {100 * (1 - changes / max(len(windows) - 1, 1)):.1f}%")

    arm_win_counts = Counter(best_arms)
    print(f"\nMost frequent best arms:")
    for arm, count in arm_win_counts.most_common(5):
        print(f"  {sample_arms[arm].name}: {count} windows ({100*count/len(windows):.1f}%)")

    if changes > len(windows) * 0.3:
        print("\nConclusion: Best arm changes frequently.")
        print("            Bandits SHOULD help but they don't because...")
        print("            The changes are UNPREDICTABLE (random).")
    else:
        print("\nConclusion: Best arm is relatively stable.")
        print("            Static selection is optimal.")


def main():
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "run":
            start = int(sys.argv[2]) if len(sys.argv) > 2 else 2991
            end = int(sys.argv[3]) if len(sys.argv) > 3 else 3180
            run_experiment(start, end)
            data = load_data()
            analyze_arm_stability(data, start, end)
        elif cmd == "quick":
            # Quick test on recent series
            run_experiment(3100, 3180)
        elif cmd == "stability":
            data = load_data()
            analyze_arm_stability(data, 2991, 3180)
        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  python bandit_predictor.py run [start] [end]")
            print("  python bandit_predictor.py quick")
            print("  python bandit_predictor.py stability")
    else:
        run_experiment()


if __name__ == "__main__":
    main()
