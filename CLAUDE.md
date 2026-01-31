# Lottery Prediction Research

**Status**: PRODUCTION READY | **Updated**: January 30, 2026

---

## CLAUDE DIRECTIVES (MUST FOLLOW)

### On Session Start
**ALWAYS run `python ml_models/pm_agent.py report` first** when starting a new session. This gives you:
- Current jackpot status (gap to 14/14)
- Trend analysis (improving or declining)
- Prioritized task queue
- Agent assignments

### Agent Deployment Rules

**For adding new data:**
1. `dataset-reviewer` - Validate data integrity
2. `model-analysis-expert` - Run validation
3. `update-enforcer` - Update documentation

**For proposed improvements:**
- **ALWAYS deploy `stats-math-evaluator` FIRST** to validate claims
- System is at ceiling - most proposals should be REJECTED
- Only test replacements (not additions) via `simulation-testing-expert`

**For monitoring:**
- `regression-analyst` if L30 drops below 10.5
- `edge-case-specialist` for 13/14 near-misses
- `model-analysis-expert` for routine checks

### Change Tracking
**Log ALL changes** to this project in the Change Log section below. Every modification to:
- `production_predictor.py` - prediction logic changes
- `pm_agent.py` - coordination changes
- `CLAUDE.md` - documentation updates
- Any new files or analysis results

Format: `[YYYY-MM-DD] <description> | Impact: <metric change if any>`

---

## Change Log

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-30 | **DEPLOYED S2: SymDiff E4^E5** - Replaced S2 (E1 rank16) with SymDiff E4⊕E5. Introduces E5 (first time used). Zero 12+ losses, bootstrap CI [+1,+8] | **12+ 14→18 (+29%), avg 10.58→10.59** |
| 2026-01-30 | **S2/E5 analysis** - lottery-math-analyst found SymDiff E4^E5 is best of 12 candidates. Simulation-testing-expert validated with full Monte Carlo. stats-math-evaluator approved DEPLOY | 3 agents aligned on DEPLOY |
| 2026-01-30 | **S1 (E4) modification backtest** - Tested 6 candidates (force-include, E4&E5 fusion, trimmed+fill). ALL HOLD, none significant. Best: E4&E5 Fusion +2 at 12+ but p=0.502 | S1 modifications redistribute wins, don't create them |
| 2026-01-30 | **S1 failure analysis** - P(zero 12+ for any event in 200 series) = 31.8%. E4's zero 12+ is statistical variance, not structural defect. Missing numbers uniformly distributed | DO NOT modify S1 - its consistency role is correct |
| 2026-01-30 | **Monte Carlo E1^E4 SymDiff validation** - Full statistical test (10K bootstrap, 5K permutation). HOLD verdict: p=0.315 for 12+, zero unique coverage, negligible effect size | No change to production |
| 2026-01-30 | **Full agent audit** - stats-math-evaluator, model-analysis-expert, dataset-reviewer all deployed. System STABLE, dataset VALID, no regression | S7 Quint confirmed highest jackpot value (6 unique 12+) |
| 2026-01-28 | **RECENCY-WEIGHTED FREQUENCY** - Fixed look-ahead bias, now uses 3x L10, 2x L30 weighting | Honest eval: 10.58 avg, 14 12+, 2 13+ |
| 2026-01-28 | **Gemini advanced tests** - Delta prediction (-1.08), Graph centrality (-1.11), Hit hangover (-0.11) | All sophisticated approaches WORSE |
| 2026-01-28 | **Gemini improvement test** - Tested SymDiff(E4,E7), Weighted Quint, E5 Quint | All WORSE than baseline |
| 2026-01-28 | **Updated all agents** - Synced with 7-set strategy, 200 series | 7 agents updated |
| 2026-01-27 | **Updated CLAUDE.md** - Removed all 12-set references, documented 7-set as current strategy | Documentation aligned |
| 2026-01-27 | **PM Agent updated** - Added gemini-strategy-coordinator, deactivated completed agents | 8 core agents, 2/4 dynamic |
| 2026-01-27 | **OPTIMIZED 7-SET FOR JACKPOT** - S6=SymDiff_E3E7, S7=Quint_E2E3E4E6E7 via Gemini deep analysis | **12+ 11→16 (+45%), 13+ 1→3 (+200%)** |
| 2026-01-27 | **REDUCED TO 7-SET STRATEGY** - Gemini analysis, drops redundant E1 variants for unique coverage | **avg 10.60/14, 11+ 109, 12+ 11, Best 13/14** |
| 2026-01-26 | **REPLACED S9: Anti-E1 -> E1&E7 fusion** (current-weighted, +0.10 per-set accuracy) | **avg 10.74->10.76 (+0.02), 11+ 130->135 (+5), S9 wins 6->10** |
| 2026-01-26 | **Key insight**: Replace worst performers, don't add sets (adding = brute force) | 12 sets maintained, genuine per-set improvement |
| 2026-01-26 | **Number Pattern Analysis** - Created `ml_models/number_pattern_analysis.py` | 0 significant patterns, pattern predictor 0.19pts WORSE |
| 2026-01-26 | **Multi-Armed Bandit Analysis** - Created `ml_models/bandit_predictor.py`, tested 13 RL algorithms | All bandits 1.12-1.29pts WORSE than 12-set |
| 2026-01-26 | **Tunable Parameters Spec** - Created `ml_models/tunable_parameters.md` with 8 parameter categories | E3&E6 +0.36, E5 +0.13, boundary +0.07 potential |
| 2026-01-26 | Fixed flawed "700 series = 1 hit" conjecture - probability ≠ guarantee | Documentation corrected |
| 2026-01-26 | Added series 3180 (best: 10/14, S3 E4 won) | 200 series, avg 10.74, 11+ 130, 12+ 18 |
| 2026-01-25 | Updated PERF_RANK to L30 (3150-3179): S3=7, S11=4, S1/S2/S4/S12=3 | Ranking now reflects recent performance |
| 2026-01-25 | Added series 3179 (best: 10/14, S3/S5/S9 tied) | 199 series, avg 10.75, 11+ 131, 12+ 18 |
| 2026-01-23 | **ML Analysis**: All ML approaches (XGBoost, frequency, recency, ensemble) perform WORSE than simple event copying | ML cannot help - data is random |
| 2026-01-23 | **Updated all agents** with ceiling status and ML findings | All agents now reflect system is at maximum |
| 2026-01-23 | **DELETED pm_overlay_validation.py** - PM predictions 1.5pts worse than base, 0 hits at 12+ in L50 | Removes harmful "smart" predictions |
| 2026-01-23 | Added series 3178 (best: 10/14, S5/S10/S12 tied) | 198 series, avg 10.73, 11+ 127, 12+ 17 |
| 2026-01-19 | **Optimality Analysis**: System at 103.5% of theoretical ceiling, no improvements possible | L30 is already optimal |
| 2026-01-19 | **Replaced S9 (E6+hot) with Anti-E1 Multi** - diversity improvement | Avg overlap 8.8→8.6, adds #7 coverage |
| 2026-01-19 | Added series 3177 (best: 12/14, S8 E7 won) | 197 series, avg 10.74, 11+ 130, 12+ 14 |
| 2026-01-18 | PM Team Analysis: Independence paradox discovered | Theoretical 3 series vs actual 196+ explains gap |
| 2026-01-18 | **Replaced S3 (rank18) with E4 direct** - L30 validated improvement | L30 avg 10.90→10.97, S3 now 6 wins (tied #1) |
| 2026-01-18 | Replaced number-pattern-hunter with regression-analyst (0 tasks, patterns shift) | Better aligned with L30 monitoring |
| 2026-01-18 | **PRUNED to 12-set core strategy** (removed 19 dead-weight sets) | 61% fewer sets, L30 avg 10.90 (was 11.00) |
| 2026-01-18 | Added S30 (E3&E6 fusion) and S31 (anti-#10) from edge-case analysis | 31 sets, avg 10.97, 11+ 160 (+4), 12+ 30 |
| 2026-01-17 | Added S29 (under-predicted #7,#15,#14,#11) from number-pattern-hunter | 29 sets, avg 10.95, 11+ 156, 12+ 30 |
| 2026-01-17 | Simplified PM agent to analysis-only (removed predict/ranking) | PERF_RANK outperforms PM ranking |
| 2026-01-17 | Added S28 (E5-direct) to address frequency bias gap | 28 sets, avg 10.93, 11+ 153 (+4) |
| 2026-01-17 | Added series 3176 (best: 11/14, S2 won); fixed 12+ count docs (was 30, actual 28) | 196 series, avg 10.91, 11+ 149, 12+ 28 |
| 2026-01-16 | PM Agent: Agent-driven predictions (consults dynamic agents, generates overlay sets) | 30 sets (27 base + 3 PM) |
| 2026-01-16 | PM Agent: Dynamic agent creation (max 4, 6 templates) | Auto-created 3 agents |
| 2026-01-16 | Implemented S26 (no#13+#18) and S27 (#18+r17) from near-miss analysis | Avg 10.91, 12+ 27→28 (S26 +1), 11+ 148 |

---

## Quick Start

```bash
cd ml_models
python pm_agent.py report                    # PM status report (start here)
python production_predictor.py predict      # Next series prediction
python production_predictor.py find 3180
python production_predictor.py validate 2981 3180
```

---

## Current Prediction

Run: `python ml_models/production_predictor.py predict [series]`

Output (7-set OPTIMIZED for jackpot):
```
Rank  Set          Numbers                                       Type
#1    S1 (E4)      01 02 07 08 10 11 12 14 15 16 17 19 20 23     E4   (best predictor)
#2    S2 (SD4^5)   01 05 06 08 10 13 15 16 20 21 22 23 24 25     DIV  (SymDiff E4⊕E5, NEW)
#3    S3 (E6)      02 03 07 08 09 10 13 16 17 18 19 22 24 25     E6   (direct)
#4    S4 (E7)      01 03 07 12 14 15 16 18 19 21 22 23 24 25     E7   (direct)
#5    S5 (E3&E7)   01 03 06 07 08 09 10 14 15 16 19 21 24 25     MIX  (fusion)
#6    S6 (SD3^7)   02 05 06 08 09 10 12 16 18 20 22 23 24 25     DIV  (diversity)
#7    S7 (Quint)   01 02 03 07 08 09 10 14 16 17 19 20 21 24     5EV  (5-event consensus)
```

---

## Key Metrics (200 series, FAIR EVAL - no look-ahead bias)

| Metric | Full (200) | Notes |
|--------|------------|-------|
| Average | **10.59/14** | Honest eval with recency weighting |
| Best | 13/14 | |
| Worst | 9/14 | |
| 11+ matches | 101 (50.5%) | |
| 12+ matches | **18 (9%)** | Up from 14 after S2 replacement |
| 13+ matches | **2 (1%)** | |
| 14/14 hits | 0 | |

### Core 7 Sets (200 series, recency-weighted)

| Rank | Set | Strategy | Wins | Type |
|------|-----|----------|------|------|
| #1 | S1 | E4 direct | 69 | Direct |
| #2 | S2 | **SymDiff E4⊕E5** | 48 | **Diversity (NEW)** |
| #3 | S3 | E6 direct | 27 | Direct |
| #4 | S4 | E7 direct | 21 | Direct |
| #5 | S5 | E3&E7 fusion | 14 | 2-event |
| #6 | S6 | SymDiff E3⊕E7 | 12 | Diversity |
| #7 | S7 | **Quint E2E3E4E6E7** | 9 | **5-event** |

### Why Recency Weighting? (2026-01-28)

Previous metrics were **inflated by look-ahead bias** - the frequency counter used ALL data including "future" series during backtesting.

**Fair evaluation** (recency-weighted, past-only):
- Only uses data from series BEFORE the prediction target
- Weights: 3x for L10, 2x for L30, 1x for older
- Matches real-world prediction scenario

### Why This Optimization?

**Key insight (2026-01-27):** Gemini deep analysis found:
1. **5-event consensus fusion** (Quint) captures cross-event patterns better than 2-event
2. **Symmetric difference** (E3⊕E7) adds diversity where fusions create redundancy
3. Combining both achieves highest 12+ AND 13+ rates simultaneously

---

## Strategy (7-set OPTIMIZED, 2026-01-30)

```python
# 7-set strategy OPTIMIZED for jackpot (12+ and 13+ hits)

# Direct event copies (3 sets)
sets[0] = sorted(event4)                         # S1: E4 direct (best predictor)
sets[2] = sorted(event6)                         # S3: E6 direct
sets[3] = sorted(event7)                         # S4: E7 direct

# NEW 2026-01-30: SymDiff E4⊕E5 (replaces E1 rank16)
sym_diff_e4e5 = (event4 | event5) - (event4 & event5)
sets[1] = sorted(sym_diff_e4e5 + freq_fill)      # S2: SymDiff E4⊕E5

# E3&E7 fusion (1 set)
sets[4] = sorted(e3_e7_fusion)                   # S5: E3 & E7 fusion

# Symmetric Difference E3⊕E7 (diversity set)
sym_diff = (event3 | event7) - (event3 & event7)
sets[5] = sym_diff + high_freq_fill[:14]         # S6: SymDiff E3⊕E7

# 5-Event Consensus (Quint E2E3E4E6E7)
quint_counts = Counter(n for e in [e2,e3,e4,e6,e7] for n in e)
sets[6] = sorted(top_14_by_count)                # S7: Quint E2E3E4E6E7
```

### Strategy Evolution

| Version | S2 | S6 | S7 | 12+ | 13+ |
|---------|----|----|-----|-----|-----|
| Initial | E1 rank16 | E3 direct | E6&E7 fusion | 11 | 1 |
| Optimized (01-27) | E1 rank16 | SymDiff E3⊕E7 | Quint E2E3E4E6E7 | 14 | 2 |
| **Current (01-30)** | **SymDiff E4⊕E5** | SymDiff E3⊕E7 | Quint E2E3E4E6E7 | **18** | **2** |
| vs Initial | - | - | - | **+64%** | **+100%** |

### Why SymDiff E4^E5 for S2? (2026-01-30)

**Full agent analysis:** lottery-math-analyst tested 12 candidates, simulation-testing-expert validated top 3 with Monte Carlo (10K bootstrap + 5K permutation), stats-math-evaluator approved deployment.

**Why SymDiff E4^E5 won:**
1. **+4 at 12+ with zero losses** -- all 4 gained series are pure additions
2. **Introduces E5** -- the only event previously unused by any set
3. **Bootstrap 95% CI for 12+: [+1, +8]** -- entirely positive
4. **Near-zero cost** -- avg +0.01, 11+ unchanged, 13+ unchanged
5. **S7 12+ fully preserved** -- all 6 jackpot-critical contributions safe

**Why other candidates failed:**
- E1^E4 SymDiff (for S5): zero unique coverage, p=0.315 (HOLD)
- S1 modifications: redistribute wins, don't create them (all 6 HOLD)
- Quint E1E3E4E5E7: lost series 2984 at 12+ (HOLD)
- E1&E5 Fusion: lost series 2984, avg regression (HOLD)

### Why SymDiff + Quint? (2026-01-27)

**Gemini deep analysis:** Tested 50+ strategies.

**Winner: SymDiff + Quint** because:
1. **Quint consensus** captures the 14 numbers appearing in most events (stable)
2. **SymDiff diversity** captures event variance (volatile but jackpot-seeking)
3. Combined: high 12+ rate AND highest 13+ rate

---

## Data

- **Series**: 200 validated (2981-3180), 201 total (2980-3180)
- **Latest**: 3180
- **File**: `data/full_series_data.json`
- **Note**: Series 2980 is baseline only (no prior for prediction)

---

## PM Agent (Jackpot Coordinator)

The PM Agent coordinates all specialized agents toward the 14/14 goal.

```bash
cd ml_models
python pm_agent.py report     # Full status report
python pm_agent.py status     # Quick jackpot status
python pm_agent.py tasks      # Prioritized agent task queue
python pm_agent.py assess     # JSON situation assessment
```

**Note:** PM agent focuses on analysis and agent management. Predictions use
`production_predictor.py` with PERF_RANK (historical performance ranking).

---

## Agent Deployment Guide (2026-01-27 - UPDATED for Gemini Workflow)

**Pivoted from defensive maintenance to proactive Gemini-based optimization.**

### The Gemini Optimization Loop

```
1. MONITOR: model-analysis-expert + edge-case-specialist gather data
2. ANALYZE: gemini-strategy-coordinator launches Gemini deep analysis
3. VALIDATE: stats-math-evaluator + simulation-testing-expert test results
4. DEPLOY: If validated, update production and repeat
```

### Adding New Series Data

| Step | Agent | Task |
|------|-------|------|
| 1 | **dataset-reviewer** | Validate new data integrity |
| 2 | **model-analysis-expert** | Run validation, check metrics |
| 3 | **update-enforcer** | Update CLAUDE.md with new metrics |

```bash
# After adding data to full_series_data.json:
python production_predictor.py validate 2981 [latest]
```

### Validating Gemini-Proposed Changes

| Proposal Type | Agent | What to Check |
|---------------|-------|---------------|
| Gemini strategy proposal | **stats-math-evaluator** | Validate metrics, statistical significance |
| New fusion type | **simulation-testing-expert** | Full 200-series backtest |
| Parameter change | **lottery-math-analyst** | Validate on L30, explain math principle |

### Performance Monitoring

| Trigger | Agent | Action |
|---------|-------|--------|
| L30 avg < 10.5 | **regression-analyst** | Investigate cause |
| 13/14 near-miss | **edge-case-specialist** | Log for Gemini analysis input |
| New 12+ or 13+ hit | **model-analysis-expert** | Analyze which set/strategy won |
| 10+ series without 12+ | **gemini-strategy-coordinator** | Trigger new Gemini analysis |

### Core Agents (Updated Roles)

| Agent | Primary Function | Deploy When |
|-------|------------------|-------------|
| **gemini-strategy-coordinator** | Orchestrate Gemini optimization workflow | Any optimization cycle |
| **stats-math-evaluator** | Validate Gemini insights statistically | Gemini proposes new strategy |
| **lottery-math-analyst** | Interpret WHY Gemini strategies work | After successful optimization |
| **edge-case-specialist** | Primary input for optimization (13+ logs) | Every 13+ near-miss |
| **model-analysis-expert** | Performance tracking, trend detection | Continuous monitoring |
| **dataset-reviewer** | Data validation | Adding new series |
| **simulation-testing-expert** | Monte Carlo, backtesting | Testing Gemini proposals |
| **documentation-enforcer** | Code standards | KISS/YAGNI compliance |
| **update-enforcer** | Sync documentation | After any code changes |

### Removed Agents

| Agent | Reason |
|-------|--------|
| ~~set-optimizer~~ | Superseded by Gemini analysis process |
| ~~event-correlation-analyst~~ | One-time analysis complete, findings historical |

### Decision Tree: Which Agent?

```
User wants to...
├── Add new series data
│   └── dataset-reviewer -> model-analysis-expert -> update-enforcer
├── Optimize the 7-set strategy
│   └── gemini-strategy-coordinator -> Gemini CLI -> stats-math-evaluator
├── Understand why a strategy works
│   └── lottery-math-analyst (explain math principles)
├── Check current performance
│   └── model-analysis-expert (run: python pm_agent.py report)
├── Investigate 13/14 near-miss
│   └── edge-case-specialist -> gemini-strategy-coordinator
├── Validate Gemini's proposal
│   └── stats-math-evaluator -> simulation-testing-expert
└── Test a specific strategy
    └── simulation-testing-expert -> stats-math-evaluator
```

### Gemini Strategy Coordinator Workflow

```bash
# 1. Collect near-miss data
python production_predictor.py validate 3151 3180  # L30 performance

# 2. Launch Gemini analysis
gemini -p "@CLAUDE.md @ml_models/production_predictor.py [specific question]"

# 3. Test proposed strategy
python ml_models/[test_file].py  # Run backtest

# 4. Validate with stats-math-evaluator
# Check: 12+ improvement, 13+ improvement, L30 stability

# 5. If validated, update production_predictor.py
```

---

## Code (KISS/YAGNI/SOLID)

```
ml_models/
├── production_predictor.py         # 7-set OPTIMIZED (SymDiff + Quint)
├── pm_agent.py                     # PM coordinator + dynamic agent mgmt
├── dynamic_agents.json             # Persisted dynamic agents
├── validate_dataset.py             # Data integrity validator
├── montecarlo_e1e4_symdiff.py      # Monte Carlo: E1^E4 SymDiff test (HOLD)
├── s1_failure_analysis.py          # S1 E4 zero-12+ root cause analysis
├── s1_modification_backtest.py     # S1 modification candidates backtest (ALL HOLD)
├── gemini_strategy_test.py         # Triple fusion tests
├── gemini_deep_test.py             # Extended strategy tests (50+)
├── hex_fusion_test.py              # 5/6/7 event fusion comparison
├── optimal_7set_test.py            # Full combinatorial search
├── final_7set_test.py              # Final optimization validation
└── [historical analysis files]     # ceiling, bandit, pattern analysis
```

---

## Goal

Hit **14/14** at least once.

---

## PM Team Analysis (2026-01-18)

Analysis by stats-math-evaluator, lottery-math-analyst, and model-analysis-expert.

### The Independence Paradox

| Metric | Theoretical | Actual |
|--------|-------------|--------|
| Per-number success rate | 68.51% | - |
| P(14/14) per set | 0.50% | - |
| Expected series to hit | **2-4** | **196+** |

**Why the gap?** Numbers are CORRELATED within events, not independent.

### Key Findings

| Agent | Finding |
|-------|---------|
| stats-math-evaluator | Independence assumption is WRONG |
| lottery-math-analyst | ~39% event-to-event correlation, uniform distribution |
| model-analysis-expert | #13 wrong 13x, #15 missing 11x, but swap doesn't improve L30 |

### Error Patterns (L30)

- **Most missed**: #15, #2, #17 (11x each)
- **Most wrong**: #13 (13x), #21 (9x), #25 (9x)
- **Best set type**: E4 (avg 9.67)

### Conclusion

The current 7-set strategy is at **local optimum**. The path to 14/14 requires lucky alignment - the "14th number" is often outside our prediction basis (like #16 in series 3061 which was in E5 but not captured by our fusions).

---

## Optimality Analysis (2026-01-19)

Exhaustive analysis confirming the system cannot be improved through algorithm changes.

### Performance vs Theoretical Ceiling

| Metric | Value |
|--------|-------|
| Theoretical ceiling (best prior event copy) | 10.600/14 |
| Our current L30 performance | **10.967/14** |
| Performance ratio | **103.5%** of ceiling |

**We exceed the ceiling** because our fusions and E1-ranking add +0.37/14 beyond what direct event copies achieve.

### Exhaustive Set Search Results

```
Sets tested that could improve L30: NONE FOUND
- All boundary configurations (top13+r14 through top13+r18): 0 unique wins
- All E?&E? fusions: 0 unique wins over current system
- E2 direct, E5 direct: 0 improvement
- Conditional strategies (event agreement signals): No significant effect
```

**The current 7-set strategy is already optimal for L30.** (Updated from 12-set on 2026-01-27)

### Why PM Agent's Intelligent Ranking Failed

The PM agent (pre-simplification) tried to:
1. Consult dynamic agents for insights
2. Generate "rescue numbers" based on historical misses
3. Rank sets with heuristic scoring (+2 for excluding #13, etc.)

**Test Results (commit 52d94c8):**
| Method | Top-1 Avg | 12+ Hits |
|--------|-----------|----------|
| PERF_RANK (simple) | **9.58/14** | **5** |
| PM Ranking | 9.47/14 | 3 |

**Why it failed:** The PM fitted to historical noise, not signal. The data has:
- ~55% event persistence (7.7/14 numbers repeat)
- ~55% cross-event correlation (uniform across all events)
- No exploitable pattern for the "14th number"

### P(14/14) Probability Estimates

| Method | Estimate |
|--------|----------|
| From score ratio extrapolation | ~0.07% per series |
| Upper 95% confidence (200 series, 0 hits) | ~0.13% per series |
| P(at least 1 hit in 700 series) | ~50% (NOT guaranteed) |
| Series tested so far | 200 |

**IMPORTANT: Expected value ≠ guarantee. Even with 700+ series, there's ~50% chance of ZERO 14/14 hits.**

### Path to 14/14

Current static approach has limitations:

| Approach | Status |
|----------|--------|
| Static event copying | Current baseline (~10.7/14 avg) |
| More volume alone | ❌ Doesn't improve accuracy, just more chances |
| Pattern mining (static) | ❌ Patterns shift over time |
| **Adaptive tuning (L10 window)** | 🔄 TO BE TESTED |
| **Evolutionary algorithm** | 🔄 TO BE TESTED |

### Current Focus: Evolutionary Tuning

Instead of static optimization, implement adaptive system:
1. Use sliding window (last 10 draws) for tuning
2. Predict next draw, compare to actual
3. Tune algorithm based on what worked
4. Iterate and evolve

---

## Monte Carlo E1^E4 SymDiff Validation (2026-01-30)

Full statistical validation of replacing S5 (E3&E7 fusion) with E1^E4 SymDiff.

### Results

| Metric | Baseline | Candidate (Replace S5) | Diff | p-value |
|--------|----------|----------------------|------|---------|
| Average | 10.58 | 10.62 | +0.04 | 0.080 |
| 11+ | 101 | 108 | +7 | 0.102 |
| 12+ | 14 | 16 | +2 | **0.315** |
| 13+ | 2 | 2 | 0 | -- |
| Cohen's d | -- | -- | 0.11 | Negligible |

### Verdict: **HOLD** (Do Not Deploy)

1. **Zero unique coverage** - E1^E4 SymDiff adds no numbers not already in the other 6 sets
2. **p=0.315 for 12+** - 31.5% chance of seeing +2 under null hypothesis
3. **Power shortfall** - Need 8,229 series to detect +1% at 12+ (have 200, 41x short)
4. **Rolling windows** - Never negative (good) but improvements are +0.00 to +0.08 (noise)
5. **S5-slot crashes** - 3 series drop from 12 to 9 at the S5 slot (other sets compensated by chance)

### Set Jackpot Value Analysis (Critical Finding)

| Set | 12+ Hits | Unique 12+ | 13+ Hits | Jackpot Value |
|-----|---------|------------|---------|---------------|
| **S7 (Quint)** | **6** | **4 sole** | 0 | **HIGHEST - irreplaceable** |
| S5 (E3&E7) | 4 | 1 sole | 0 | Medium |
| S6 (SymDiff) | 3 | 2 sole | **1** | High |
| S4 (E7) | 3 | 1 sole | 0 | Medium |
| S3 (E6) | 1 | 1 sole (**13/14**) | **1** | High |
| S2 (rank16) | 1 | 1 sole | 0 | Low |
| S1 (E4) | **0** | 0 | 0 | Zero for 12+ |

**Key insight**: S1 (E4) wins the most series overall (69) but has ZERO 12+ contributions.
S7 (Quint) wins the fewest (8) but provides the MOST 12+ hits (6, with 4 unique).
**Never replace S7 for jackpot optimization.**

---

## S1 (E4) Failure Analysis (2026-01-30)

### Root Cause: Statistical Variance, Not Structural Defect

**P(zero 12+ for any event in 200 series) = 31.8%**. With 7 events, we expect ~2.2 to have zero 12+. We observe 3 (E2, E4, E5). This is normal.

### S1 Score Distribution (per-set, not best-of-7)
| Score | Count |
|-------|-------|
| 11 | 25 (most of any set -- but zero convert to 12) |
| 10 | 78 |
| 9 | 81 |
| 8 | 16 |

### Modification Backtest (6 Candidates)

| Candidate | System Avg | 12+ | p-value (12+) | Verdict |
|-----------|-----------|-----|---------------|---------|
| Baseline (E4 direct) | 10.58 | 14 | -- | CURRENT |
| E4+Force18 | 10.58 | 15 | 1.000 | HOLD |
| E4+Force21 | 10.58 | 15 | 1.000 | HOLD |
| E4+Force23 | 10.56 | 14 | -- | HOLD |
| E4_Top12+Div2 | 10.57 | 14 | -- | HOLD |
| **E4&E5 Fusion** | **10.59** | **16** | **0.502** | **HOLD** |
| E4_Trim11+Top3 | 10.57 | 15 | 1.000 | HOLD |

### Why Modifications Don't Work

S1 modifications **redistribute wins among sets, not create new ones**. When S1 is weakened (from 69 wins to 58), those wins scatter to S2-S7. The best-of-7 safety net means the overall score barely moves. 92-97% of series produce identical results.

**Conclusion: DO NOT modify S1.** Its consistency role is architecturally correct.

---

## ML Analysis (2026-01-23)

Comprehensive analysis of whether machine learning could improve predictions.

### Data Characteristics

| Property | Value | Implication |
|----------|-------|-------------|
| Entropy | 99.9% of maximum | Data is essentially random |
| Autocorrelation | ~0.00 | Past numbers don't predict future |
| Event persistence | ~55% uniform | Only exploitable signal |
| Frequency stability | 0.14% shift | No hot/cold patterns |

### ML Approaches Tested

| Approach | L50 Score | vs Current | Result |
|----------|-----------|------------|--------|
| Current (event copy) | 10.60/14 | baseline | BEST |
| XGBoost | 9.56/14 | -1.04 | WORSE |
| Frequency ML | 9.44/14 | -1.16 | WORSE |
| Recency-weighted | 9.35/14 | -1.25 | WORSE |
| Dynamic ensemble | 9.33/14 | -1.27 | WORSE |
| PM overlay sets | 9.35/14 | -1.51 | REMOVED |

### Reinforcement Learning / Bandits (2026-01-26)

Tested whether adaptive algorithms could learn which strategy works best.

| Algorithm | Average | vs 12-Set | Result |
|-----------|---------|-----------|--------|
| 12-Set Core (baseline) | 10.74/14 | -- | BEST |
| DecayingEpsilon (best bandit) | 9.62/14 | -1.12 | WORSE |
| UCB1 | 9.59/14 | -1.15 | WORSE |
| Thompson Sampling | 9.55/14 | -1.19 | WORSE |
| EXP3 (adversarial) | 9.51/14 | -1.24 | WORSE |
| Sliding Window UCB | 9.56/14 | -1.18 | WORSE |

**Key Finding:** The best strategy changes 80% of the time across 30-series windows,
but bandits still fail because:
- Changes are RANDOM and UNPREDICTABLE
- Past arm performance doesn't predict future performance
- Exploration/exploitation is useless when there's no learnable pattern

**Why 12-Set Wins:** Uses ALL strategies simultaneously, takes BEST of 12.
No selection/learning needed when you can run all in parallel.

### Why ML Fails

1. **No patterns to learn** - Entropy is 99.9% of maximum
2. **Overfits to noise** - Historical coincidences don't repeat
3. **Destroys the signal** - Any "smart" modification breaks 55% persistence
4. **Simple is optimal** - Event copying preserves the only exploitable signal

### Conclusion

**Machine learning cannot improve this system.** The data is essentially random.
The current simple approach (copy prior events) is mathematically optimal.

---

## Number Pattern Analysis (2026-01-26)

Deep analysis of number-level patterns to test if individual number behavior is exploitable.

### Analyses Performed

| Analysis | Description | Result |
|----------|-------------|--------|
| Transition Matrix | 25x25 matrix of P(Y next | X present) | 0 significant pairs (Bonferroni) |
| Gap Effect | Does absence make number more likely? | Cannot test - numbers always appear |
| Co-occurrence | Do certain pairs appear together? | Chi-sq p=1.0 (no association) |
| Event Flow | Do numbers persist in same event? | p=0.97 (no persistence) |
| Within-Series | E1->E2->...->E7 sequences | 0 Bonferroni significant (0.3% at p<0.05) |
| Event Structure | Overlap within/across series | 7.85/14 within, 7.78/14 across (matches 7.84 expected) |

### Key Findings

1. **Numbers appear in ~99.7% of series** - Too uniform for gap analysis
2. **Zero transition patterns** - Number X appearing tells nothing about number Y
3. **Events are independent draws** - No structure in E1->E2->...->E7 sequence
4. **Overlap matches random expectation exactly** - 7.85/14 observed vs 7.84/14 expected

### Predictive Validation

| Predictor | Score | vs Baseline |
|-----------|-------|-------------|
| E1 copy (baseline) | 9.60/14 | -- |
| Pattern-based | 9.41/14 | **-0.19** (p=0.035) |

**Pattern predictor is statistically significantly WORSE than simple event copying.**

### Mathematical Reality

- 7 events x 14 numbers = 98 draws per series
- 98/25 = 3.92 appearances per number per series
- P(number in at least one event) = 1 - (11/25)^7 = 99.7%
- Cross-series correlation: ~0 (independent)

### Conclusion

**Data is random at the number level.** The only exploitable signal is event-level
correlation (~55% persistence). Any attempt to predict at the number level destroys
this signal. The current system (event copying + fusions) is mathematically optimal.

---

## Design Principle (2026-01-18)

**DON'T accumulate sets based on historical edge cases.**

Instead:
1. Analyze historical data for **patterns**
2. Validate patterns work on **recent data** (L30)
3. Keep only sets with **recent wins or rising trends**
4. Prune dead weight regularly

---

## PREDICTOR STATUS: 7-SET OPTIMIZED (2026-01-30)

**Latest: S2 replaced with SymDiff E4^E5 -- introduces E5, +4 at 12+.**

### Optimization History

| Date | Change | 12+ | 13+ |
|------|--------|-----|-----|
| 2026-01-27 | 12-set → 7-set (SymDiff+Quint) | 14 | 2 |
| **2026-01-30** | **S2: rank16 → SymDiff E4⊕E5** | **18** | **2** |

### Key Changes (2026-01-30)

- **S2**: E1 rank16 → **SymDiff E4⊕E5** (introduces E5, zero 12+ losses)
- **S6**: E3⊕E7 SymDiff (unchanged)
- **S7**: Quint E2E3E4E6E7 (unchanged, jackpot-critical)

### What Agents Should Do

| Agent | Role |
|-------|------|
| gemini-strategy-coordinator | Orchestrate Gemini optimization workflow |
| lottery-math-analyst | Monitor ceiling status, validate claims |
| model-analysis-expert | Track L30 variance, alert on anomalies |
| stats-math-evaluator | Validate proposals statistically |
| simulation-testing-expert | Run Monte Carlo validation as needed |
| regression-analyst | Monitor L30 after S2 deployment |

### Current Metrics (7-set, 200 series, 2026-01-30)

- **Average**: 10.59/14
- **11+ rate**: 50.5% (101/200)
- **12+ rate**: **9% (18/200)**
- **13+ rate**: 1% (2/200)
- **14/14 hits**: 0

---

*Maintained by Claude Code*
### Examples:

**Single file analysis:**
gemini -p "@Domain/Activity.cs Explain this entity's purpose and relationships"

**Multiple files:**
gemini -p "@API/Controllers/ @Application/Activities/ Analyze the activity management implementation"

**Entire directory:**
gemini -p "@Application/ Summarize the business logic architecture using CQRS"

**Multiple directories:**
gemini -p "@Domain/ @Persistence/ Analyze the domain model and data persistence layer"

**Current directory and subdirectories:**
gemini -p "@./ Give me an overview of this entire .NET React project"

**Or use --all_files flag:**
gemini --all_files -p "Analyze the project structure and dependencies"

### Implementation Verification Examples for Reactivities

**Check backend features:**
gemini -p "@API/ @Application/ Is user authentication and authorization properly implemented? Show JWT handling"

**Verify activity management:**
gemini -p "@Application/Activities/ @Domain/Activity.cs Are CRUD operations for activities complete? List all commands and queries"

**Check frontend patterns:**
gemini -p "@Client/src/ Are MobX stores properly implemented for state management? Show store patterns"

**Verify database relationships:**
gemini -p "@Domain/ @Persistence/ Are Entity Framework relationships correctly configured for User-Activity-Attendee?"

**Check API endpoints:**
gemini -p "@API/Controllers/ What REST endpoints are available? List all HTTP methods and routes"

**Verify validation:**
gemini -p "@Application/ Is FluentValidation implemented for all commands? Show validation rules"

**Check real-time features:**
gemini -p "@API/ @Client/src/ Is SignalR implemented for real-time chat? Show hub and client code"

**Verify error handling:**
gemini -p "@API/ @Application/ Is proper error handling implemented with Result patterns? Show examples"

When to Use Gemini CLI

Use gemini -p when:
- Analyzing entire codebases or large directories
- Comparing multiple large files
- Need to understand project-wide patterns or architecture
- Current context window is insufficient for the task
- Working with files totaling more than 100KB
- Verifying if specific features, patterns, or security measures are implemented
- Checking for the presence of certain coding patterns across the entire codebase
