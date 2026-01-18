# Lottery Prediction Research

**Status**: PRODUCTION READY | **Updated**: January 18, 2026 (12-set core strategy)

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
python production_predictor.py predict 3177
python production_predictor.py find 3176
python production_predictor.py validate 2981 3176
```

---

## Current Prediction

Run: `python ml_models/production_predictor.py predict [series]`

Output is **ordered by recent performance** (L30 wins):
```
Rank  Set             Numbers                                       Type
#1    S1 (rank16)     ...                                           E1   (5 wins L30)
#2    S7 (E3)         ...                                           E3   (3 wins L30)
#3    S4 (r15+r16)    ...                                           E1   (3 wins L30)
#4    S5 (E6)         ...                                           E6   (2 wins, 13/14 achiever)
...
```

---

## Key Metrics (196 series validated, 12-set core)

| Metric | Value |
|--------|-------|
| Average | **10.72/14** (full), **10.90/14** (L30) |
| Best | **13/14** (S5 E6) |
| Worst | 10/14 |
| 11+ matches | 121 (62%) full, 24 (80%) L30 |
| 12+ matches | 19 (10%) full, 3 (10%) L30 |
| 14/14 hits | 0 |

### Why 12 Sets Instead of 31?

**Problem with accumulating sets:**
- Historical analysis → add set → repeat = brute force, not intelligence
- Sets S28-S31 had **0 wins in last 50 series** (dead weight)
- 40/50 recent series had **ties** for best score (redundancy)

**Pruning criteria:**
- Keep sets with **wins in L30** or **rising trends**
- Remove sets with 0 wins recently or falling trends
- Result: 61% fewer sets, 97% of recent performance retained

### Performance by Time Window

| Window | Sets | Average | 11+ Rate |
|--------|------|---------|----------|
| L30 | 12 | 10.90 | 80% |
| L30 | 31 | 11.00 | 90% |
| **Loss** | | **-0.10** | **-10%** |

### Core 12 Sets (ranked by L30 wins)

| Rank | Set | Strategy | L30 Wins | Trend |
|------|-----|----------|----------|-------|
| #1 | S1 | rank16 | 5 | STABLE |
| #2 | S7 | E3 direct | 3 | RISING |
| #3 | S4 | r15+r16 | 3 | RISING |
| #4 | S5 | E6 direct | 2 | STABLE (13/14!) |
| #5 | S2 | rank15 | 2 | RISING |
| #6 | S10 | E7+hot | 2 | RISING |
| #7 | S11 | E3&E7 | 3 | RISING |
| #8 | S12 | E6&E7 | 2 | RISING |
| #9 | S8 | E7 direct | 1 | STABLE |
| #10 | S3 | rank18 | 1 | FALLING |
| #11 | S6 | E1&E6 | 1 | STABLE |
| #12 | S9 | E6+hot | 1 | STABLE |

---

## Strategy (12-set core, 2026-01-18)

```python
# 12-set core strategy - validated on recent data

# E1-based sets (S1-S4)
sets[0:4] = [
    ranked[:13] + [ranked[15]],              # S1: rank16 (5 wins L30)
    ranked[:13] + [ranked[14]],              # S2: rank15 (2 wins L30)
    ranked[:13] + [ranked[17]],              # S3: rank18 (1 win L30)
    ranked[:12] + [ranked[14], ranked[15]],  # S4: r15+r16 (3 wins L30)
]

# Multi-event direct (S5, S7, S8)
sets[4] = sorted(event6)                     # S5: E6 (13/14 achiever!)
sets[6] = sorted(event3)                     # S7: E3 (3 wins L30)
sets[7] = sorted(event7)                     # S8: E7 (1 win L30)

# Multi-event fusions (S6, S9-S12)
sets[5] = sorted(e1_e6_fusion)               # S6: E1 & E6 fusion
sets[8] = e6_ranked[:13] + [hot_outside_e6]  # S9: E6 + hot
sets[9] = e7_ranked[:13] + [hot_outside_e7]  # S10: E7 + hot
sets[10] = sorted(e3_e7_fusion)              # S11: E3 & E7 fusion
sets[11] = sorted(e6_e7_fusion)              # S12: E6 & E7 fusion
```

### Sets REMOVED (19 dead-weight sets)

| Set | Reason |
|-----|--------|
| S5-S8 (old) | Redundant with core E1 sets |
| S13-S14 | #12 inclusion - 0 wins L50 |
| S16 | E3+hot - falling trend |
| S19-S25 | Fusions/mixed - 0-1 wins L30 |
| S26-S31 | Near-miss fixes - 0 wins L50 |

---

## Data

- **Series**: 197 (2980-3176)
- **Latest**: 3176
- **File**: `data/full_series_data.json`

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

## Code (KISS/YAGNI/SOLID)

```
ml_models/
├── production_predictor.py         # ~330 lines, 12-set core strategy
├── pm_agent.py                     # PM coordinator + dynamic agent mgmt
├── dynamic_agents.json             # Persisted dynamic agents
├── ceiling_analysis.py             # Theoretical limits analysis
└── monte_carlo_validation.py       # Statistical validation
```

---

## Goal

Hit **14/14** at least once.

---

## Design Principle (2026-01-18)

**DON'T accumulate sets based on historical edge cases.**

Instead:
1. Analyze historical data for **patterns**
2. Validate patterns work on **recent data** (L30)
3. Keep only sets with **recent wins or rising trends**
4. Prune dead weight regularly

---

## PREDICTOR IMPROVEMENT DIRECTIVE

**ALL agents MUST follow these rules when suggesting predictor changes:**

### Rule 1: Validate on Recent Data FIRST
- Any proposed set/strategy MUST be tested on L30 (last 30 series) before adding
- If L30 performance is worse than existing sets, REJECT the proposal
- Historical edge cases are NOT sufficient justification

### Rule 2: Replace, Don't Accumulate
- New sets should REPLACE underperforming sets, not add to total count
- Target: Keep set count at **10-15 sets maximum**
- If adding a set, identify which set to remove

### Rule 3: Measure What Matters
- Primary metric: **L30 wins** (what's working NOW)
- Secondary metric: **L30 average**
- Tertiary metric: Full historical average (least important)

### Rule 4: Prune Regularly
- Sets with **0 wins in L50** should be removed
- Sets with **falling trends** should be reviewed for removal
- Run pruning analysis monthly

### Rule 5: Document Rationale
- Every set must have: L30 wins, trend direction, why it's kept
- Log all changes in Change Log with impact metrics

### Agent Application
| Agent | How This Applies |
|-------|------------------|
| lottery-math-analyst | Propose replacements, not additions |
| model-analysis-expert | Evaluate L30 performance first |
| set-optimizer | Optimize existing sets, prune dead weight |
| number-pattern-hunter | Validate patterns on L30 before proposing |
| edge-case-specialist | Edge cases need L30 validation too |

---

*Maintained by Claude Code*
