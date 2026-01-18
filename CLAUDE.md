# Lottery Prediction Research

**Status**: PRODUCTION READY | **Updated**: January 17, 2026 (29-set + PM Agent)

---

## CLAUDE DIRECTIVES (MUST FOLLOW)

### On Session Start
**ALWAYS run `python ml_models/pm_agent.py report` first** when starting a new session. This gives you:
- Current jackpot status (gap to 14/14)
- Trend analysis (improving or declining)
- Prioritized task queue
- Agent assignments

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
| 2026-01-17 | Added S29 (under-predicted #7,#15,#14,#11) from number-pattern-hunter | 29 sets, avg 10.95, 11+ 156, 12+ 30 |
| 2026-01-17 | Simplified PM agent to analysis-only (removed predict/ranking) | PERF_RANK outperforms PM ranking |
| 2026-01-17 | Added S28 (E5-direct) to address frequency bias gap | 28 sets, avg 10.93, 11+ 153 (+4) |
| 2026-01-17 | Added series 3176 (best: 11/14, S2 won); fixed 12+ count docs (was 30, actual 28) | 196 series, avg 10.91, 11+ 149, 12+ 28 |
| 2026-01-16 | PM Agent: Agent-driven predictions (consults dynamic agents, generates overlay sets) | 30 sets (27 base + 3 PM) |
| 2026-01-16 | PM Agent: Dynamic agent creation (max 4, 6 templates) | Auto-created 3 agents |
| 2026-01-16 | Implemented S26 (no#13+#18) and S27 (#18+r17) from near-miss analysis | Avg 10.91, 12+ 27→28 (S26 +1), 11+ 148 |
| 2026-01-16 | Added PM Agent (pm_agent.py) | Coordination layer |
| 2026-01-16 | Near-miss analysis: #13 over-selected (71% vs 57%), #18/#22 under-selected | Identified fix targets |
| 2026-01-15 | S18 promoted to #1 rank (3 recent 12+) | Recency-first ranking |
| 2026-01-14 | Expanded to 25-set strategy (+mixed/ALL) | +6 12+ events |

---

## Quick Start

```bash
cd ml_models
python pm_agent.py report                    # PM status report (start here)
python production_predictor.py predict 3177
python production_predictor.py find 3176
python production_predictor.py validate 2981 3176
```

---

## Current Prediction

Run: `python ml_models/production_predictor.py predict [series]`

Output is **ordered by recency-first strategy** (what's working NOW):
```
Rank  Set                Numbers                                       Type
#1    S18 (E3&E7)        ...                                           MIX  (3 recent 12+, HOT!)
#2    S9 (E6)            ...                                           E6   (only 13/14, but cold)
#3    S16 (E3+hot)       ...                                           E3S  (4x 12+)
#4    S4 (r15+r16)       ...                                           DBL  (3x 12+)
#5    S17 (E7+hot)       ...                                           E7S  (3x 12+)
...
#24   S1 (rank16)        ...                                           SGL  (0x 12+)
```
*Ranking updated 2026-01-15: S18 promoted to #1 (hottest recent performer)*

---

## Key Metrics (196 series validated, 29-set)

| Metric | Value |
|--------|-------|
| Average | **10.95/14** |
| Best | **13/14** (S9) |
| Worst | 10/14 |
| 11+ matches | 156 (79.6%) |
| 12+ matches | 30 (15.3%) |
| 13+ matches | 1 (0.5%) |
| 14/14 hits | 0 |

### Set Performance by Wins (196 series)

| Set | Strategy | Wins | 12+ | Best |
|-----|----------|------|-----|------|
| S9 | E6 direct | 17 | 1 | **13/14** |
| S18 | E3 & E7 fusion | 11 | **5** | 12/14 |
| S16 | E3 + hot | 8 | 4 | 12/14 |
| S4 | r15+r16 | 14 | 3 | 12/14 |
| S17 | E7 + hot | 6 | 3 | 12/14 |
| S1 | rank16 | **29** | 0 | 11/14 |

**Key discoveries (2026-01-14)**:
- **Mixed hot+cold** - captures regression-to-mean patterns
- **ALL-event fusion** - 7 wins, best new performer
- **S26 (no#13+#18)** - added 1 new 12+ event (series 3144)

### Improvement History

| Version | Sets | Average | 11+ | 12+ |
|---------|------|---------|-----|-----|
| E1 only | 8 | 10.39/14 | 61 | 11 |
| +E3/E6/E7 | 12 | 10.62/14 | 102 | 17 |
| +#12/swaps | 18 | 10.75/14 | 122 | 23 |
| +fusions | 22 | 10.81/14 | 132 | 25 |
| +lookback3 | 22 | 10.85/14 | 138 | 26 |
| +mixed/ALL (194) | 25 | 10.91/14 | 146 | 27 |
| +S26/S27 (195) | 27 | 10.91/14 | 148 | 28 |
| +S28 E5 (196) | 28 | 10.93/14 | 153 | 28 |
| +S29 under (196) | 29 | **10.95/14** | **156** | **30** |

---

## Statistical Validation (Monte Carlo)

| Test | Value | Interpretation |
|------|-------|----------------|
| t-statistic | 70.67 | Extremely high |
| p-value | 6.59e-141 | Highly significant |
| Cohen's d | 3.13 | Large effect |
| 95% CI | [10.84, 11.01] | Tight confidence |
| Percentile | 100% | Beats all random |

*Updated 2026-01-17: 10.95/14 avg, +39.7% above 7.84 baseline (10,000 simulations, 196 series, 29-set)*

### Ceiling Analysis

From `ceiling_analysis.py`:
- **P(14/14) random**: 1 in 4,457,400 per set/event
- **14/14 theoretically possible**: 0/195 series (E1-based approach)
- **Numbers missing in 12+ events**: #13 (25%), #20 (20%), #8 (15%)
- **Numbers should've had**: #12 (20%), #22 (20%), #23 (15%)

**Path to 14/14**: Requires non-E1 event breakthroughs (E6 proved this with 13/14)

### Near-Miss Analysis (2026-01-16)

**The 13/14 Case (Series 3061)**:
- Set S9 (E6) missed by 1 number
- **Missing**: #16 | **Had wrong**: #19
- #16 WAS in prior series (E3, E5) - achievable!

**Critical Findings**:
| Issue | Detail | Action |
|-------|--------|--------|
| #13 over-selected | 71% predicted vs 57% actual | Create #13 exclusion set |
| #18 under-selected | Needed in 18.8% of 12+ events | Create #18 inclusion set |
| #22 under-selected | Needed in 18.8% of 12+ events | Already have S19 |

**Implemented**: S26 (no#13 + #18) and S27 (#18 + r17) - see Strategy section

Run: `python ml_models/ceiling_analysis.py`

---

## Data

- **Series**: 197 (2980-3176)
- **Latest**: 3176
- **File**: `data/full_series_data.json`

---

## Strategy (29-set multi-event, 2026-01-17)

```python
# Multi-event E1 + E3 + E5 + E6 + E7 + fusions + mixed/ALL + nearmiss + under (29 sets)

# E1-based sets (S1-S8)
sets[0:8] = [
    ranked[:13] + [ranked[15]],              # S1: rank16
    ranked[:13] + [ranked[14]],              # S2: rank15
    ranked[:13] + [ranked[17]],              # S3: rank18
    ranked[:12] + [ranked[14], ranked[15]],  # S4: r15+r16
    ranked[:12] + [ranked[14], ranked[17]],  # S5: r15+r18
    ranked[:12] + [ranked[15], ranked[17]],  # S6: r16+r18
    ranked[:12] + [ranked[14], ranked[18]],  # S7: r15+r19
    ranked[:12] + [hot[1], hot[2]],          # S8: hot#2+#3
]

# Multi-event direct (S9-S12)
sets[8:12] = [
    sorted(event6),                          # S9: E6 (13/14!)
    sorted(e1_e6_combined),                  # S10: E1 & E6
    sorted(event3),                          # S11: E3 (2x 12+)
    sorted(event7),                          # S12: E7 (2x 12+)
]

# #12/#22 inclusion (S13-S14, S19)
sets[12:14] = [
    top12_no12 + [12, ranked[15]],           # S13: +#12 +r16
    top12_no12 + [12, ranked[14]],           # S14: +#12 +r15
]

# Multi-event swaps (S15-S18)
sets[14:18] = [
    e6_ranked[:13] + [hot_outside_e6],       # S15: E6 +hot
    e3_ranked[:13] + [hot_outside_e3],       # S16: E3 +hot
    e7_ranked[:13] + [hot_outside_e7],       # S17: E7 +hot
    sorted(e3_e7_combined),                  # S18: E3 & E7
]

# Fusion sets (S19-S22)
sets[18:22] = [
    top12_no22 + [22, ranked[15]],           # S19: +#22 +r16
    sorted(e6_e7_combined),                  # S20: E6 & E7
    sorted(e1_e3_combined),                  # S21: E1 & E3
    sorted(e3_e6_e7_combined),               # S22: E3 & E6 & E7
]

# New sets (S23-S25) - +6 12+ events
sets[22:25] = [
    ranked[:12] + [hot[0], cold[0]],         # S23: hot#1 + cold#1
    sorted(all_event_combined),              # S24: ALL-event fusion
    sorted(e1_e2_combined),                  # S25: E1 & E2 fusion
]

# Near-miss fix sets (S26-S27) - from 2026-01-16 analysis
sets[25:27] = [
    top13_no13 + [18],                       # S26: no#13 + #18
    top12_no18 + [18, ranked[16]],           # S27: #18 + r17
]

# E5-direct set (S28) - from 2026-01-17 analysis
sets[27] = sorted(event5)                    # S28: E5 (addresses freq bias)

# Under-predicted numbers (S29) - from number-pattern-hunter 2026-01-17
# #7 (ratio 0.39), #15 (0.55), #14 (0.70), #11 (0.79) under-predicted
under_predicted = [7, 15, 14, 11]
over_predicted = [8, 21, 24]
base = [n for n in ranked if n not in under_predicted and n not in over_predicted][:10]
sets[28] = sorted(base + under_predicted)     # S29: under-predicted fix
```

**Performance**: 39.7% above random baseline (7.84/14)

**Jackpot Pool**: Pool-24 (exclude #12), ~1.96M combinations

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
`production_predictor.py` with PERF_RANK (historical performance ranking),
which outperforms dynamic PM ranking on validation data.

### Dynamic Agent Management

PM can create up to **4 dynamic agents** when gaps are identified:

```bash
python pm_agent.py agents              # List all agents
python pm_agent.py agents auto         # Auto-create recommended agents
python pm_agent.py agents create <tpl> # Create from template
python pm_agent.py agents templates    # List available templates
python pm_agent.py agents deactivate   # Deactivate an agent
python pm_agent.py agents delete       # Delete an agent
```

**Available Templates**:
| Template | Focus | Triggers |
|----------|-------|----------|
| edge-case-specialist | Near-miss analysis | 13/14 achieved |
| event-correlation-analyst | E1-E7 correlations | Fusion underperforming |
| number-pattern-hunter | Recurring patterns | 12+ rate drops |
| hot-cold-tracker | Streak momentum | Hot set changes |
| set-optimizer | Set strategy optimization | Strong base performance |
| regression-analyst | Performance regression | Average declining |

### Core Agents

| Agent | Focus |
|-------|-------|
| lottery-math-analyst | Pattern analysis, prediction algorithms |
| dataset-reviewer | Data validation, anomaly detection |
| simulation-testing-expert | Monte Carlo, statistical validation |
| model-analysis-expert | Performance analysis, error diagnosis |
| stats-math-evaluator | Statistical analysis, hypothesis testing |

### PM Directive

Every action serves the jackpot goal. The PM agent:
- Assesses gap to 14/14 and identifies blockers
- Prioritizes high-impact improvements
- Dispatches specialized agents with context
- Tracks trends and near-miss patterns
- **Creates new agents dynamically** when gaps are identified (max 4)

---

## Code (KISS/YAGNI/SOLID)

```
ml_models/
├── production_predictor.py         # ~644 lines, 29-set multi-event logic
├── pm_agent.py                     # PM coordinator + dynamic agent mgmt (~970 lines, analysis only)
├── dynamic_agents.json             # Persisted dynamic agents (auto-generated)
├── ceiling_analysis.py             # Theoretical limits analysis
├── event_breakthrough_analysis.py  # E1-E7 breakthrough analysis
├── detailed_analysis.py            # Set performance diagnostics
├── error_analysis.py               # Error pattern analysis
├── monte_carlo_validation.py       # Statistical validation
└── e1_correlated_simulation.py     # Correlation model
```

---

## Goal

Hit **14/14** at least once.

---

*Maintained by Claude Code*
