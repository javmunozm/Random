#!/usr/bin/env python3
"""
PM Agent - Project Manager for Jackpot Pursuit
===============================================

PRIMARY GOAL: Hit 14/14 on a FUTURE series prediction.

CRITICAL DISTINCTION:
- We are NOT optimizing for historical average performance
- We are trying to HIT JACKPOT on the NEXT unknown series
- Historical backtesting is for validation, not the goal itself
- A strategy that hits 14/14 once is worth more than +0.5 avg improvement

This agent coordinates all specialized agents to achieve the jackpot:
- lottery-math-analyst: Pattern analysis, probability calculations
- dataset-reviewer: Data validation, anomaly detection
- simulation-testing-expert: Monte Carlo, statistical validation
- model-analysis-expert: Performance analysis, error diagnosis
- stats-math-evaluator: Rigorous statistical evaluation

DYNAMIC AGENT CREATION:
- PM can create up to 4 new specialized agents when gaps are identified
- Agents are persisted to dynamic_agents.json
- Each agent has: name, focus, tools, trigger conditions

Strategy:
1. Diversification > Optimization (maximize jackpot probability)
2. Include "rescue numbers" that base strategy misses
3. Hedge against E1-ranking failures with contrarian picks
4. Every set should have a PLAUSIBLE path to 14/14
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict

# Import from production predictor
from production_predictor import load_data, latest, predict, evaluate, validate

# Dynamic agents file
DYNAMIC_AGENTS_FILE = Path(__file__).parent / "dynamic_agents.json"
MAX_DYNAMIC_AGENTS = 4


@dataclass
class JackpotStatus:
    """Current status toward jackpot goal."""
    series_tested: int
    current_best: int
    average: float
    at_12_plus: int
    at_13_plus: int
    at_14: int
    gap_to_jackpot: int
    best_performing_set: int
    hot_streak_set: Optional[int] = None


@dataclass
class AgentTask:
    """Task assignment for specialized agent."""
    agent: str
    priority: int  # 1=critical, 2=high, 3=medium, 4=low
    task: str
    expected_impact: str
    status: str = "pending"


@dataclass
class DynamicAgent:
    """Dynamically created specialized agent."""
    name: str
    focus: str
    description: str
    tools: List[str]
    trigger_conditions: List[str]
    created_at: str
    created_by: str = "pm-agent"
    status: str = "active"
    tasks_completed: int = 0
    last_used: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DynamicAgent":
        return cls(**data)


class PMAgent:
    """
    Project Manager Agent - Coordinates all agents toward 14/14 jackpot.

    Philosophy:
    - Every decision serves the jackpot goal
    - Prioritize high-impact, low-effort improvements
    - Trust statistical validation over intuition
    - Adapt strategy based on recent performance
    - Create new agents dynamically when gaps are identified (max 4)
    """

    # Core agents (built-in)
    CORE_AGENTS = {
        "lottery-math-analyst": "Pattern analysis, prediction algorithms, probability",
        "dataset-reviewer": "Data validation, integrity checks, anomaly detection",
        "simulation-testing-expert": "Monte Carlo simulations, statistical validation",
        "model-analysis-expert": "Model performance, prediction accuracy, error patterns",
        "stats-math-evaluator": "Statistical analysis, hypothesis testing, confidence intervals",
        "documentation-enforcer": "Code standards, KISS/YAGNI/SOLID compliance",
        "update-enforcer": "Keep all agents synchronized with current stats",
    }

    # Agent templates for dynamic creation
    AGENT_TEMPLATES = {
        "number-pattern-hunter": {
            "focus": "Identify recurring number patterns and sequences",
            "tools": ["Grep", "Read", "Bash"],
            "triggers": ["12+ rate drops", "specific numbers consistently missing"],
        },
        "event-correlation-analyst": {
            "focus": "Analyze correlations between different events (E1-E7)",
            "tools": ["Read", "Bash", "Glob"],
            "triggers": ["event fusion underperforming", "new event combinations needed"],
        },
        "hot-cold-tracker": {
            "focus": "Track hot/cold number streaks and momentum shifts",
            "tools": ["Read", "Bash"],
            "triggers": ["hot streak changes", "momentum shift detected"],
        },
        "edge-case-specialist": {
            "focus": "Analyze edge cases and near-misses for breakthrough opportunities",
            "tools": ["Read", "Bash", "Grep"],
            "triggers": ["13/14 near-miss", "consistent 1-number gap"],
        },
        "set-optimizer": {
            "focus": "Optimize existing sets and propose new set strategies",
            "tools": ["Read", "Edit", "Bash"],
            "triggers": ["set underperforming", "new strategy opportunity"],
        },
        "regression-analyst": {
            "focus": "Detect and analyze performance regressions",
            "tools": ["Read", "Bash", "Grep"],
            "triggers": ["average declining", "12+ rate dropping"],
        },
    }

    def __init__(self):
        self.data = load_data()
        self.latest_series = latest(self.data)
        self.status = self._compute_status()
        self.task_queue = []
        self.dynamic_agents = self._load_dynamic_agents()

    # =========================================================================
    # DYNAMIC AGENT MANAGEMENT
    # =========================================================================

    def _load_dynamic_agents(self) -> Dict[str, DynamicAgent]:
        """Load dynamic agents from persistent storage."""
        if not DYNAMIC_AGENTS_FILE.exists():
            return {}
        try:
            data = json.loads(DYNAMIC_AGENTS_FILE.read_text())
            return {name: DynamicAgent.from_dict(agent) for name, agent in data.items()}
        except (json.JSONDecodeError, KeyError):
            return {}

    def _save_dynamic_agents(self):
        """Save dynamic agents to persistent storage."""
        data = {name: agent.to_dict() for name, agent in self.dynamic_agents.items()}
        DYNAMIC_AGENTS_FILE.write_text(json.dumps(data, indent=2))

    @property
    def AGENTS(self) -> dict:
        """Combined core + dynamic agents."""
        agents = dict(self.CORE_AGENTS)
        for name, agent in self.dynamic_agents.items():
            if agent.status == "active":
                agents[name] = agent.description
        return agents

    def evaluate_agent_needs(self) -> List[dict]:
        """
        Evaluate current situation and identify if new agents are needed.
        Returns list of recommended new agents with justification.
        """
        recommendations = []
        s = self.status
        trends = self._analyze_trends()

        # Check if we can add more agents
        active_dynamic = sum(1 for a in self.dynamic_agents.values() if a.status == "active")
        slots_available = MAX_DYNAMIC_AGENTS - active_dynamic

        if slots_available <= 0:
            return [{"message": "Maximum dynamic agents reached (4). Deactivate one to add new."}]

        # Condition 1: Near-miss requires edge case specialist
        if s.current_best >= 13 and "edge-case-specialist" not in self.dynamic_agents:
            recommendations.append({
                "template": "edge-case-specialist",
                "reason": f"Current best is {s.current_best}/14 - need edge case analysis",
                "priority": 1,
            })

        # Condition 2: Declining performance needs regression analyst
        if trends.get("trend") == "DOWN" and trends.get("momentum", 0) < -0.1:
            if "regression-analyst" not in self.dynamic_agents:
                recommendations.append({
                    "template": "regression-analyst",
                    "reason": f"Performance declining (momentum: {trends.get('momentum', 0):+.3f})",
                    "priority": 1,
                })

        # Condition 3: 12+ rate below target needs pattern hunter
        twelve_plus_rate = s.at_12_plus / max(s.series_tested, 1)
        if twelve_plus_rate < 0.15 and "number-pattern-hunter" not in self.dynamic_agents:
            recommendations.append({
                "template": "number-pattern-hunter",
                "reason": f"12+ rate at {twelve_plus_rate*100:.1f}% - below 15% target",
                "priority": 2,
            })

        # Condition 4: Event fusion opportunity
        if s.current_best < 14 and "event-correlation-analyst" not in self.dynamic_agents:
            recommendations.append({
                "template": "event-correlation-analyst",
                "reason": "Event fusion strategies may unlock breakthrough",
                "priority": 2,
            })

        # Condition 5: Hot streak changes need tracking
        if s.hot_streak_set != s.best_performing_set:
            if "hot-cold-tracker" not in self.dynamic_agents:
                recommendations.append({
                    "template": "hot-cold-tracker",
                    "reason": f"Hot streak set (S{s.hot_streak_set}) differs from best (S{s.best_performing_set})",
                    "priority": 3,
                })

        # Condition 6: Set optimization opportunity
        if s.average > 10.5 and "set-optimizer" not in self.dynamic_agents:
            recommendations.append({
                "template": "set-optimizer",
                "reason": "Strong base performance - optimization could push to jackpot",
                "priority": 3,
            })

        # Sort by priority and limit to available slots
        recommendations.sort(key=lambda x: x.get("priority", 99))
        return recommendations[:slots_available]

    def create_agent(self, template_name: str, custom_name: str = None) -> dict:
        """
        Create a new dynamic agent from a template.

        Args:
            template_name: Name of the template to use
            custom_name: Optional custom name for the agent

        Returns:
            dict with success status and agent details
        """
        # Check slot availability
        active_dynamic = sum(1 for a in self.dynamic_agents.values() if a.status == "active")
        if active_dynamic >= MAX_DYNAMIC_AGENTS:
            return {
                "success": False,
                "error": f"Maximum {MAX_DYNAMIC_AGENTS} dynamic agents allowed. Deactivate one first.",
            }

        # Validate template
        if template_name not in self.AGENT_TEMPLATES:
            return {
                "success": False,
                "error": f"Unknown template: {template_name}",
                "available": list(self.AGENT_TEMPLATES.keys()),
            }

        template = self.AGENT_TEMPLATES[template_name]
        agent_name = custom_name or template_name

        # Check if agent already exists
        if agent_name in self.dynamic_agents:
            existing = self.dynamic_agents[agent_name]
            if existing.status == "active":
                return {"success": False, "error": f"Agent '{agent_name}' already exists and is active"}
            # Reactivate if inactive
            existing.status = "active"
            self._save_dynamic_agents()
            return {"success": True, "action": "reactivated", "agent": existing.to_dict()}

        # Create new agent
        new_agent = DynamicAgent(
            name=agent_name,
            focus=template["focus"],
            description=f"[DYNAMIC] {template['focus']}",
            tools=template["tools"],
            trigger_conditions=template["triggers"],
            created_at=datetime.now().isoformat(),
        )

        self.dynamic_agents[agent_name] = new_agent
        self._save_dynamic_agents()

        return {
            "success": True,
            "action": "created",
            "agent": new_agent.to_dict(),
            "slots_remaining": MAX_DYNAMIC_AGENTS - active_dynamic - 1,
        }

    def deactivate_agent(self, agent_name: str) -> dict:
        """Deactivate a dynamic agent (doesn't delete, just marks inactive)."""
        if agent_name not in self.dynamic_agents:
            return {"success": False, "error": f"Agent '{agent_name}' not found in dynamic agents"}

        if agent_name in self.CORE_AGENTS:
            return {"success": False, "error": f"Cannot deactivate core agent '{agent_name}'"}

        self.dynamic_agents[agent_name].status = "inactive"
        self._save_dynamic_agents()

        return {"success": True, "agent": agent_name, "status": "inactive"}

    def delete_agent(self, agent_name: str) -> dict:
        """Permanently delete a dynamic agent."""
        if agent_name not in self.dynamic_agents:
            return {"success": False, "error": f"Agent '{agent_name}' not found"}

        del self.dynamic_agents[agent_name]
        self._save_dynamic_agents()

        return {"success": True, "agent": agent_name, "action": "deleted"}

    def list_agents(self) -> dict:
        """List all agents (core + dynamic) with status."""
        return {
            "core_agents": self.CORE_AGENTS,
            "dynamic_agents": {
                name: {
                    "description": agent.description,
                    "focus": agent.focus,
                    "status": agent.status,
                    "tasks_completed": agent.tasks_completed,
                    "created_at": agent.created_at,
                }
                for name, agent in self.dynamic_agents.items()
            },
            "slots_used": sum(1 for a in self.dynamic_agents.values() if a.status == "active"),
            "slots_total": MAX_DYNAMIC_AGENTS,
        }

    def auto_create_agents(self) -> List[dict]:
        """
        Automatically evaluate and create needed agents.
        Returns list of actions taken.
        """
        recommendations = self.evaluate_agent_needs()
        actions = []

        for rec in recommendations:
            if "template" in rec:
                result = self.create_agent(rec["template"])
                actions.append({
                    "recommendation": rec,
                    "result": result,
                })

        return actions

    def _compute_status(self) -> JackpotStatus:
        """Compute current jackpot pursuit status."""
        # Full validation range
        start = min(int(s) for s in self.data.keys()) + 1  # Need prior for prediction
        end = self.latest_series

        results = validate(self.data, start, end)
        if not results:
            return JackpotStatus(0, 0, 0.0, 0, 0, 0, 14, 0)

        # Find best performing set
        wins = results["wins"]
        best_set = wins.index(max(wins)) + 1

        # Track recent hot streak (last 10 series)
        recent_start = max(start, end - 10)
        recent = validate(self.data, recent_start, end)
        recent_wins = recent["wins"] if recent else [0] * 25
        hot_streak_set = recent_wins.index(max(recent_wins)) + 1 if recent else None

        return JackpotStatus(
            series_tested=results["tested"],
            current_best=results["best"],
            average=results["avg"],
            at_12_plus=results["at_12"],
            at_13_plus=sum(1 for r in self._get_all_results(start, end) if r["best"] >= 13),
            at_14=results["at_14"],
            gap_to_jackpot=14 - results["best"],
            best_performing_set=best_set,
            hot_streak_set=hot_streak_set,
        )

    def _get_all_results(self, start, end):
        """Get individual results for all series."""
        return [evaluate(self.data, sid) for sid in range(start, end + 1)
                if evaluate(self.data, sid)]

    def assess_situation(self) -> dict:
        """
        Assess current situation and identify priorities.

        Returns strategic assessment with:
        - Current gap analysis
        - Improvement opportunities
        - Risk factors
        - Recommended focus areas
        """
        s = self.status

        # Gap analysis
        gap_analysis = {
            "current_ceiling": s.current_best,
            "target": 14,
            "gap": s.gap_to_jackpot,
            "difficulty": self._assess_difficulty(s.gap_to_jackpot),
        }

        # Performance trends
        trends = self._analyze_trends()

        # Improvement opportunities
        opportunities = self._identify_opportunities()

        # Risk assessment
        risks = self._assess_risks()

        return {
            "status": "ACTIVE" if s.gap_to_jackpot > 0 else "JACKPOT_ACHIEVED",
            "gap_analysis": gap_analysis,
            "trends": trends,
            "opportunities": opportunities,
            "risks": risks,
            "recommended_focus": self._recommend_focus(gap_analysis, trends, opportunities),
        }

    def _assess_difficulty(self, gap: int) -> str:
        """Assess difficulty of closing the gap."""
        if gap == 0:
            return "ACHIEVED"
        elif gap == 1:
            return "VERY_CLOSE - One number away, focus on edge cases"
        elif gap == 2:
            return "CLOSE - Statistical breakthrough possible"
        elif gap <= 4:
            return "MODERATE - Need systematic improvements"
        else:
            return "SIGNIFICANT - Fundamental strategy review needed"

    def _analyze_trends(self) -> dict:
        """Analyze recent performance trends."""
        end = self.latest_series

        # Last 20 vs previous 20
        recent = validate(self.data, end - 20, end)
        previous = validate(self.data, end - 40, end - 21)

        if not recent or not previous:
            return {"trend": "INSUFFICIENT_DATA"}

        trend_direction = "UP" if recent["avg"] > previous["avg"] else "DOWN"
        momentum = recent["avg"] - previous["avg"]

        return {
            "trend": trend_direction,
            "momentum": round(momentum, 3),
            "recent_avg": round(recent["avg"], 2),
            "previous_avg": round(previous["avg"], 2),
            "recent_12_plus": recent["at_12"],
            "assessment": self._interpret_trend(trend_direction, momentum),
        }

    def _interpret_trend(self, direction: str, momentum: float) -> str:
        """Interpret trend for strategic planning."""
        if direction == "UP" and momentum > 0.2:
            return "Strong positive momentum - continue current strategy"
        elif direction == "UP":
            return "Slight improvement - look for optimization opportunities"
        elif momentum < -0.2:
            return "Concerning decline - investigate recent failures"
        else:
            return "Stable performance - consider new approaches"

    def _identify_opportunities(self) -> list:
        """Identify improvement opportunities."""
        opportunities = []
        s = self.status

        # Opportunity 1: Event fusion analysis
        if s.current_best < 14:
            opportunities.append({
                "type": "EVENT_FUSION",
                "description": "Explore new event combinations (E2, E4, E5 underutilized)",
                "potential_impact": "HIGH",
                "agent": "lottery-math-analyst",
            })

        # Opportunity 2: Hot streak exploitation
        if s.hot_streak_set and s.hot_streak_set != s.best_performing_set:
            opportunities.append({
                "type": "HOT_STREAK",
                "description": f"Set S{s.hot_streak_set} showing recent strength",
                "potential_impact": "MEDIUM",
                "agent": "model-analysis-expert",
            })

        # Opportunity 3: Near-miss analysis
        if s.at_13_plus > 0:
            opportunities.append({
                "type": "NEAR_MISS",
                "description": f"{s.at_13_plus} series hit 13+, analyze missing numbers",
                "potential_impact": "HIGH",
                "agent": "stats-math-evaluator",
            })

        # Opportunity 4: Number frequency gaps
        opportunities.append({
            "type": "FREQUENCY_GAP",
            "description": "Analyze which numbers are under/over-predicted",
            "potential_impact": "MEDIUM",
            "agent": "dataset-reviewer",
        })

        return opportunities

    def _assess_risks(self) -> list:
        """Assess risks to achieving jackpot."""
        risks = []
        s = self.status

        # Risk 1: Overfitting
        if s.average > 11:
            risks.append({
                "type": "OVERFITTING",
                "description": "High average may indicate strategy tuned to past data",
                "mitigation": "Run out-of-sample validation",
                "agent": "simulation-testing-expert",
            })

        # Risk 2: Strategy stagnation
        if s.gap_to_jackpot > 1:
            risks.append({
                "type": "STAGNATION",
                "description": "Gap to jackpot not closing",
                "mitigation": "Explore fundamentally new approaches",
                "agent": "lottery-math-analyst",
            })

        # Risk 3: Data quality
        risks.append({
            "type": "DATA_QUALITY",
            "description": "Ensure dataset integrity before new experiments",
            "mitigation": "Run data validation checks",
            "agent": "dataset-reviewer",
        })

        return risks

    def _recommend_focus(self, gap_analysis: dict, trends: dict, opportunities: list) -> list:
        """Recommend focus areas based on assessment."""
        recommendations = []

        # Priority 1: If close to jackpot, focus on near-misses
        if gap_analysis["gap"] <= 2:
            recommendations.append({
                "priority": 1,
                "focus": "NEAR_MISS_ANALYSIS",
                "rationale": "Within striking distance - analyze what's preventing 14/14",
                "agents": ["stats-math-evaluator", "model-analysis-expert"],
            })

        # Priority 2: If trending down, investigate failures
        if trends.get("trend") == "DOWN":
            recommendations.append({
                "priority": 2,
                "focus": "FAILURE_INVESTIGATION",
                "rationale": "Declining performance needs root cause analysis",
                "agents": ["model-analysis-expert", "dataset-reviewer"],
            })

        # Priority 3: Always look for new opportunities
        high_impact = [o for o in opportunities if o["potential_impact"] == "HIGH"]
        if high_impact:
            recommendations.append({
                "priority": 3,
                "focus": "HIGH_IMPACT_OPPORTUNITIES",
                "rationale": f"{len(high_impact)} high-impact opportunities identified",
                "agents": list(set(o["agent"] for o in high_impact)),
            })

        return recommendations

    def generate_task_queue(self) -> list:
        """Generate prioritized task queue for all agents."""
        assessment = self.assess_situation()
        tasks = []

        # Task from recommendations
        for rec in assessment["recommended_focus"]:
            for agent in rec["agents"]:
                tasks.append(AgentTask(
                    agent=agent,
                    priority=rec["priority"],
                    task=f"{rec['focus']}: {rec['rationale']}",
                    expected_impact="High" if rec["priority"] <= 2 else "Medium",
                ))

        # Task from opportunities
        for opp in assessment["opportunities"]:
            tasks.append(AgentTask(
                agent=opp["agent"],
                priority=3,
                task=f"{opp['type']}: {opp['description']}",
                expected_impact=opp["potential_impact"],
            ))

        # Task from risks
        for risk in assessment["risks"]:
            tasks.append(AgentTask(
                agent=risk["agent"],
                priority=2,
                task=f"MITIGATE {risk['type']}: {risk['mitigation']}",
                expected_impact="Risk mitigation",
            ))

        # Sort by priority
        tasks.sort(key=lambda t: t.priority)
        self.task_queue = tasks
        return tasks

    def next_prediction(self, series_id: int = None) -> dict:
        """
        Generate PM-enhanced prediction using dynamic agents.

        The PM agent:
        1. Gets base prediction from production_predictor
        2. Consults active dynamic agents for modifications
        3. Generates PM-specific overlay sets
        4. Ranks sets based on agent recommendations
        """
        if series_id is None:
            series_id = self.latest_series + 1

        # Get base prediction
        base_pred = predict(self.data, series_id)

        # Consult dynamic agents for modifications
        agent_insights = self._consult_agents(series_id)

        # Generate PM overlay sets based on agent insights
        pm_sets = self._generate_pm_sets(series_id, agent_insights)

        # Combine and rank
        combined_sets = base_pred["sets"] + pm_sets["sets"]
        pm_ranking = self._rank_sets_by_agents(combined_sets, agent_insights)

        # Add PM commentary
        commentary = {
            "jackpot_status": f"Gap: {self.status.gap_to_jackpot} numbers",
            "strategy": f"28-set base + {len(pm_sets['sets'])} PM overlay sets",
            "confidence": self._compute_confidence(),
            "focus_sets": self._identify_focus_sets(),
            "pm_note": self._generate_pm_note(),
            "agents_consulted": list(agent_insights.keys()),
            "pm_modifications": pm_sets["rationale"],
        }

        return {
            "prediction": {
                "series": series_id,
                "base_sets": base_pred["sets"],
                "pm_sets": pm_sets["sets"],
                "pm_set_names": pm_sets["names"],
                "combined_count": len(combined_sets),
                "ranked": base_pred["ranked"],
                "hot_outside": base_pred["hot_outside"],
            },
            "pm_commentary": commentary,
            "agent_insights": agent_insights,
            "pm_ranking": pm_ranking,
        }

    def _consult_agents(self, series_id: int) -> dict:
        """Consult active dynamic agents for prediction insights."""
        insights = {}
        prior = str(series_id - 1)

        for name, agent in self.dynamic_agents.items():
            if agent.status != "active":
                continue

            # Each agent type provides different insights
            if "edge-case" in name:
                insights[name] = self._edge_case_insight(prior)
            elif "correlation" in name:
                insights[name] = self._correlation_insight(prior)
            elif "optimizer" in name:
                insights[name] = self._optimizer_insight(prior)
            elif "pattern" in name:
                insights[name] = self._pattern_insight(prior)
            elif "hot-cold" in name:
                insights[name] = self._hot_cold_insight(prior)
            elif "regression" in name:
                insights[name] = self._regression_insight(prior)

            # Mark agent as used
            agent.last_used = datetime.now().isoformat()
            agent.tasks_completed += 1

        self._save_dynamic_agents()
        return insights

    def _edge_case_insight(self, prior: str) -> dict:
        """Edge case specialist: Focus on boundary numbers."""
        # Analyze numbers at rank 13-16 boundary
        freq = Counter(n for events in self.data.values() for e in events for n in e)
        event1 = set(self.data[prior][0])
        ranked = sorted(range(1, 26), key=lambda n: (-(n in event1), -freq[n], n))

        boundary_nums = ranked[12:17]  # Rank 13-17
        return {
            "focus": "boundary numbers at rank 13-17",
            "boundary_numbers": boundary_nums,
            "recommendation": f"Include {boundary_nums[1]} and {boundary_nums[2]} in PM set",
            "exclude_suggestion": 13,  # Most over-selected
        }

    def _correlation_insight(self, prior: str) -> dict:
        """Event correlation analyst: Find cross-event patterns."""
        events = self.data[prior]
        # Find numbers appearing in 4+ events
        num_counts = Counter(n for e in events for n in e)
        high_correlation = [n for n, c in num_counts.most_common() if c >= 4]
        low_correlation = [n for n, c in num_counts.items() if c == 1]

        return {
            "focus": "cross-event correlations",
            "high_correlation": high_correlation[:5],
            "low_correlation": low_correlation[:5],
            "recommendation": f"Prioritize {high_correlation[:3]} (appear in 4+ events)",
        }

    def _optimizer_insight(self, prior: str) -> dict:
        """Set optimizer: Suggest set improvements."""
        # Analyze recent performance
        recent_results = [evaluate(self.data, sid) for sid in range(self.latest_series - 10, self.latest_series + 1)
                         if evaluate(self.data, sid)]

        # Find best performing set types recently
        set_scores = [0] * 28
        for r in recent_results:
            if r:
                for i, score in enumerate(r["set_bests"]):
                    if i < 28:
                        set_scores[i] += score

        best_sets = sorted(range(28), key=lambda i: -set_scores[i])[:5]

        return {
            "focus": "set optimization",
            "hot_sets": [f"S{i+1}" for i in best_sets],
            "recommendation": f"Weight toward S{best_sets[0]+1}, S{best_sets[1]+1} strategies",
        }

    def _pattern_insight(self, prior: str) -> dict:
        """Pattern hunter: Find recurring sequences."""
        # Look for numbers that appeared in last 3 series consistently
        recent = [str(self.latest_series - i) for i in range(3) if str(self.latest_series - i) in self.data]
        if len(recent) < 3:
            return {"focus": "patterns", "recommendation": "Insufficient data"}

        # Numbers in all 3 recent series (any event)
        sets = [set(n for e in self.data[s] for n in e) for s in recent]
        consistent = sets[0] & sets[1] & sets[2]

        return {
            "focus": "recurring patterns",
            "consistent_numbers": sorted(consistent),
            "recommendation": f"Include {sorted(consistent)[:3]} (appeared in all recent series)",
        }

    def _hot_cold_insight(self, prior: str) -> dict:
        """Hot/cold tracker: Identify momentum."""
        recent_freq = Counter()
        for i in range(3):
            sid = str(self.latest_series - i)
            if sid in self.data:
                for e in self.data[sid]:
                    recent_freq.update(e)

        hot = [n for n, _ in recent_freq.most_common(5)]
        cold = [n for n, _ in recent_freq.most_common()[-5:]]

        return {
            "focus": "hot/cold momentum",
            "hot_numbers": hot,
            "cold_numbers": cold,
            "recommendation": f"Hot: {hot[:3]}, consider cold regression: {cold[:2]}",
        }

    def _regression_insight(self, prior: str) -> dict:
        """Regression analyst: Detect decline patterns."""
        trends = self._analyze_trends()
        return {
            "focus": "performance regression",
            "trend": trends.get("trend", "UNKNOWN"),
            "momentum": trends.get("momentum", 0),
            "recommendation": "Diversify strategies" if trends.get("trend") == "DOWN" else "Continue current approach",
        }

    def _generate_pm_sets(self, series_id: int, insights: dict) -> dict:
        """
        Generate PM-specific sets based on agent insights.

        v3 algorithms (2026-01-16):
        - KEY INSIGHT: Base strategy commonly misses #20, #7, #14, #23 in weak series
        - These numbers also appear frequently in 12+ winning events
        - PM sets should COMPLEMENT base by including these "rescue" numbers
        - Balance E1 priority with rescue number inclusion
        """
        prior = str(series_id - 1)
        if prior not in self.data:
            return {"sets": [], "names": [], "rationale": []}

        freq = Counter(n for events in self.data.values() for e in events for n in e)
        event1 = set(self.data[prior][0])
        events = self.data[prior]
        event6 = set(events[5])

        # E1-ranked: numbers in E1 first, then by global frequency
        ranked = sorted(range(1, 26), key=lambda n: (-(n in event1), -freq[n], n))

        # Rescue numbers: commonly missed by base strategy
        rescue_nums = [20, 7, 14, 23]

        pm_sets = []
        names = []
        rationale = []

        # =====================================================================
        # PM-RESCUE: E1-ranked top-10 + all 4 rescue numbers (#20, #7, #14, #23)
        # Rationale: Covers the 4 most commonly missed numbers when base fails
        # =====================================================================
        if "edge-case-specialist" in insights:
            base10 = ranked[:10]
            rescue_to_add = [n for n in rescue_nums if n not in base10]
            fill = [n for n in ranked[10:] if n not in rescue_to_add]
            pm_rescue = sorted(base10 + rescue_to_add[:4] + fill[:4 - len(rescue_to_add)])[:14]
            if len(pm_rescue) == 14:
                pm_sets.append(pm_rescue)
                names.append("PM-RESCUE (E1+rescue nums)")
                rationale.append(f"E1 top-10 + rescue nums {rescue_to_add[:4]}")

        # =====================================================================
        # PM-LUCKY: E1-ranked top-11 + #23 + #20 + one from E6
        # Rationale: #23 and #20 appear in 16 and 14 of 30 12+ events respectively
        # =====================================================================
        if "event-correlation-analyst" in insights:
            base11 = ranked[:11]
            lucky_nums = [23, 20]
            lucky_to_add = [n for n in lucky_nums if n not in base11]
            e6_pick = [n for n in event6 if n not in base11 and n not in lucky_to_add]
            e6_pick = sorted(e6_pick, key=lambda n: -freq[n])[:1]
            pm_lucky = sorted(base11 + lucky_to_add + e6_pick)[:14]
            for n in ranked[11:]:
                if len(pm_lucky) >= 14:
                    break
                if n not in pm_lucky:
                    pm_lucky.append(n)
            pm_lucky = sorted(pm_lucky[:14])
            if len(pm_lucky) == 14:
                pm_sets.append(pm_lucky)
                names.append("PM-LUCKY (E1+#23+#20)")
                rationale.append(f"E1 top-11 + lucky {lucky_to_add} + E6 pick")

        # =====================================================================
        # PM-E1E6: Prioritize E1&E6 intersection, fill from E1 members
        # Rationale: E6 achieved 13/14, E1 is foundation - combine strengths
        # =====================================================================
        if "set-optimizer" in insights:
            e1_e6_intersection = event1 & event6
            e1_only = event1 - event6
            e6_only = sorted(event6 - event1, key=lambda n: -freq[n])
            pm_e1e6 = list(e1_e6_intersection)
            for n in sorted(e1_only, key=lambda n: -freq[n]):
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
                names.append("PM-E1E6 (intersection priority)")
                rationale.append(f"E1&E6 intersection ({len(e1_e6_intersection)}) + E1 fill")

        # =====================================================================
        # PM-ANTI: Contrarian hedge with #7, #15, #20 (commonly missed)
        # Rationale: Hedge against E1 ranking failures
        # =====================================================================
        # Always generate this set
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
            names.append("PM-ANTI (contrarian hedge)")
            rationale.append(f"E1 base + contrarian {anti_force}")

        return {"sets": pm_sets, "names": names, "rationale": rationale}

    def _rank_sets_by_agents(self, sets: list, insights: dict) -> list:
        """Rank all sets based on agent recommendations."""
        rankings = []
        for i, s in enumerate(sets):
            score = 0
            reasons = []

            # Edge case scoring
            if "edge-case-specialist" in insights:
                edge = insights["edge-case-specialist"]
                if 13 not in s:
                    score += 2
                    reasons.append("excludes #13")
                boundary = edge.get("boundary_numbers", [])
                boundary_count = sum(1 for n in boundary if n in s)
                score += boundary_count
                if boundary_count > 0:
                    reasons.append(f"{boundary_count} boundary nums")

            # Correlation scoring
            if "event-correlation-analyst" in insights:
                high_corr = insights["event-correlation-analyst"].get("high_correlation", [])
                corr_count = sum(1 for n in high_corr if n in s)
                score += corr_count * 0.5
                if corr_count >= 3:
                    reasons.append(f"{corr_count} high-corr nums")

            # Hot/cold scoring
            if "hot-cold-tracker" in insights:
                hot = insights["hot-cold-tracker"].get("hot_numbers", [])
                hot_count = sum(1 for n in hot if n in s)
                score += hot_count * 0.3
                if hot_count >= 3:
                    reasons.append(f"{hot_count} hot nums")

            set_name = f"S{i+1}" if i < 28 else f"PM-{i-27}"
            rankings.append({
                "set": set_name,
                "score": round(score, 2),
                "reasons": reasons,
            })

        rankings.sort(key=lambda x: -x["score"])
        return rankings[:10]  # Top 10

    def _compute_confidence(self) -> str:
        """Compute confidence level for next prediction."""
        s = self.status
        if s.at_12_plus / max(s.series_tested, 1) > 0.15:
            return "HIGH - Strong 12+ hit rate"
        elif s.average > 10.5:
            return "MEDIUM - Solid average performance"
        else:
            return "MODERATE - Room for improvement"

    def _identify_focus_sets(self) -> list:
        """Identify sets to watch closely."""
        # Based on PERF_RANK from production_predictor
        return [
            {"set": "S18", "reason": "Hot streak (3 recent 12+)"},
            {"set": "S9", "reason": "Only 13/14 achiever"},
            {"set": "S16", "reason": "Strong 12+ rate"},
        ]

    def _generate_pm_note(self) -> str:
        """Generate PM strategic note."""
        s = self.status
        if s.current_best == 13:
            return "ONE NUMBER AWAY from jackpot. Stay focused on edge cases."
        elif s.at_12_plus > 20:
            return "Solid 12+ performance. Push for breakthrough."
        else:
            return "Continue systematic improvement. Trust the process."

    def report(self) -> str:
        """Generate comprehensive PM report."""
        s = self.status
        assessment = self.assess_situation()
        tasks = self.generate_task_queue()

        lines = [
            "=" * 70,
            "PM AGENT REPORT - JACKPOT PURSUIT",
            "=" * 70,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Latest Series: {self.latest_series}",
            "",
            "JACKPOT STATUS",
            "-" * 40,
            f"  Goal:              14/14",
            f"  Current Best:      {s.current_best}/14",
            f"  Gap to Jackpot:    {s.gap_to_jackpot} numbers",
            f"  Average:           {s.average:.2f}/14",
            f"  Series Tested:     {s.series_tested}",
            f"  12+ Hits:          {s.at_12_plus} ({s.at_12_plus/max(s.series_tested,1)*100:.1f}%)",
            f"  13+ Hits:          {s.at_13_plus}",
            f"  14/14 Hits:        {s.at_14}",
            "",
            "GAP ANALYSIS",
            "-" * 40,
            f"  Difficulty: {assessment['gap_analysis']['difficulty']}",
            "",
            "TRENDS",
            "-" * 40,
        ]

        trends = assessment["trends"]
        if "trend" in trends and trends["trend"] != "INSUFFICIENT_DATA":
            lines.extend([
                f"  Direction:         {trends['trend']}",
                f"  Momentum:          {trends['momentum']:+.3f}",
                f"  Recent Avg:        {trends['recent_avg']:.2f}/14",
                f"  Previous Avg:      {trends['previous_avg']:.2f}/14",
                f"  Assessment:        {trends['assessment']}",
            ])
        else:
            lines.append("  Insufficient data for trend analysis")

        lines.extend([
            "",
            "IMPROVEMENT OPPORTUNITIES",
            "-" * 40,
        ])
        for i, opp in enumerate(assessment["opportunities"], 1):
            lines.append(f"  {i}. [{opp['potential_impact']}] {opp['type']}")
            lines.append(f"     {opp['description']}")
            lines.append(f"     Agent: {opp['agent']}")

        lines.extend([
            "",
            "RISKS",
            "-" * 40,
        ])
        for risk in assessment["risks"]:
            lines.append(f"  [{risk['type']}] {risk['description']}")
            lines.append(f"  Mitigation: {risk['mitigation']}")

        lines.extend([
            "",
            "RECOMMENDED FOCUS",
            "-" * 40,
        ])
        for rec in assessment["recommended_focus"]:
            lines.append(f"  P{rec['priority']}: {rec['focus']}")
            lines.append(f"      {rec['rationale']}")
            lines.append(f"      Agents: {', '.join(rec['agents'])}")

        lines.extend([
            "",
            "AGENT TASK QUEUE",
            "-" * 40,
        ])
        for i, task in enumerate(tasks[:10], 1):  # Top 10 tasks
            lines.append(f"  {i}. [P{task.priority}] {task.agent}")
            lines.append(f"     {task.task}")

        if len(tasks) > 10:
            lines.append(f"  ... and {len(tasks) - 10} more tasks")

        # Dynamic agents section
        lines.extend([
            "",
            "DYNAMIC AGENTS",
            "-" * 40,
        ])
        active_dynamic = sum(1 for a in self.dynamic_agents.values() if a.status == "active")
        lines.append(f"  Slots: {active_dynamic}/{MAX_DYNAMIC_AGENTS} used")

        if self.dynamic_agents:
            for name, agent in self.dynamic_agents.items():
                status_icon = "[+]" if agent.status == "active" else "[-]"
                lines.append(f"  {status_icon} {name}: {agent.focus}")
        else:
            lines.append("  No dynamic agents created yet")

        # Agent recommendations
        recommendations = self.evaluate_agent_needs()
        if recommendations and "template" in recommendations[0]:
            lines.extend([
                "",
                "RECOMMENDED NEW AGENTS",
                "-" * 40,
            ])
            for rec in recommendations[:3]:
                if "template" in rec:
                    lines.append(f"  [P{rec['priority']}] {rec['template']}")
                    lines.append(f"      Reason: {rec['reason']}")

        lines.extend([
            "",
            "=" * 70,
            "PM DIRECTIVE: Every action serves the jackpot goal.",
            "=" * 70,
        ])

        return "\n".join(lines)

    def dispatch_agent(self, agent_name: str, task_description: str) -> dict:
        """
        Prepare dispatch instructions for a specialized agent.

        Returns structured instructions for Claude Code to execute via Task tool.
        """
        if agent_name not in self.AGENTS:
            return {"error": f"Unknown agent: {agent_name}"}

        return {
            "agent": agent_name,
            "task": task_description,
            "context": {
                "goal": "Achieve 14/14 jackpot",
                "current_best": self.status.current_best,
                "gap": self.status.gap_to_jackpot,
                "latest_series": self.latest_series,
            },
            "priority": "HIGH",
            "instruction": f"Execute task with jackpot goal in mind. Current gap: {self.status.gap_to_jackpot} numbers.",
        }


def main():
    """CLI for PM Agent."""
    pm = PMAgent()

    if len(sys.argv) < 2:
        print("PM Agent - Jackpot Pursuit Coordinator")
        print("=" * 50)
        print("\nCommands:")
        print("  report              - Full PM status report")
        print("  status              - Quick jackpot status")
        print("  assess              - Situation assessment")
        print("  tasks               - Agent task queue")
        print("  predict [series]    - Prediction with PM commentary")
        print("  dispatch <agent>    - Dispatch specific agent")
        print("\nDynamic Agent Management:")
        print("  agents              - List all agents (core + dynamic)")
        print("  agents create <tpl> - Create agent from template")
        print("  agents auto         - Auto-create recommended agents")
        print("  agents deactivate   - Deactivate a dynamic agent")
        print("  agents delete       - Delete a dynamic agent")
        print("  agents templates    - List available templates")
        print(f"\nLatest: Series {pm.latest_series}")
        print(f"Jackpot Gap: {pm.status.gap_to_jackpot} numbers")
        active = sum(1 for a in pm.dynamic_agents.values() if a.status == "active")
        print(f"Dynamic Agents: {active}/{MAX_DYNAMIC_AGENTS}")
        return

    cmd = sys.argv[1]

    if cmd == "report":
        print(pm.report())

    elif cmd == "status":
        s = pm.status
        print(f"\nJACKPOT STATUS")
        print("=" * 40)
        print(f"Goal:           14/14")
        print(f"Current Best:   {s.current_best}/14")
        print(f"Gap:            {s.gap_to_jackpot} numbers")
        print(f"Average:        {s.average:.2f}/14")
        print(f"12+ Hits:       {s.at_12_plus}/{s.series_tested}")
        print(f"13+ Hits:       {s.at_13_plus}")
        print(f"14/14:          {s.at_14}")

    elif cmd == "assess":
        assessment = pm.assess_situation()
        print(json.dumps(assessment, indent=2))

    elif cmd == "tasks":
        tasks = pm.generate_task_queue()
        print("\nAGENT TASK QUEUE")
        print("=" * 60)
        for i, t in enumerate(tasks, 1):
            print(f"\n{i}. [P{t.priority}] {t.agent}")
            print(f"   Task: {t.task}")
            print(f"   Impact: {t.expected_impact}")

    elif cmd == "predict":
        series_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        result = pm.next_prediction(series_id)
        pred = result["prediction"]
        comm = result["pm_commentary"]
        insights = result.get("agent_insights", {})
        ranking = result.get("pm_ranking", [])

        print(f"\n{'='*70}")
        print(f"PM AGENT PREDICTION - Series {pred['series']}")
        print(f"{'='*70}")

        print(f"\nPM COMMENTARY:")
        print(f"  Status:     {comm['jackpot_status']}")
        print(f"  Strategy:   {comm['strategy']}")
        print(f"  Confidence: {comm['confidence']}")
        print(f"  PM Note:    {comm['pm_note']}")

        print(f"\nAGENTS CONSULTED ({len(insights)}):")
        for agent_name, insight in insights.items():
            print(f"  [{agent_name}]")
            print(f"    Focus: {insight.get('focus', 'N/A')}")
            print(f"    Recommendation: {insight.get('recommendation', 'N/A')}")

        print(f"\nPM MODIFICATIONS:")
        for mod in comm.get("pm_modifications", []):
            print(f"  - {mod}")

        print(f"\nTOP 10 SETS BY AGENT SCORING:")
        print(f"  {'Rank':<5} {'Set':<10} {'Score':<8} {'Reasons'}")
        print(f"  {'-'*50}")
        for i, r in enumerate(ranking, 1):
            reasons = ", ".join(r["reasons"]) if r["reasons"] else "-"
            print(f"  #{i:<4} {r['set']:<10} {r['score']:<8} {reasons}")

        print(f"\nPM OVERLAY SETS ({len(pred['pm_sets'])}):")
        for i, (s, name) in enumerate(zip(pred["pm_sets"], pred["pm_set_names"])):
            nums = " ".join(f"{n:02d}" for n in s)
            print(f"  {name}")
            print(f"    {nums}")

        print(f"\nBASE PREDICTION SETS (28):")
        for i, s in enumerate(pred["base_sets"], 1):
            nums = " ".join(f"{n:02d}" for n in s)
            print(f"  S{i:02d}: {nums}")

        print(f"\n{'='*70}")
        print(f"TOTAL: {pred['combined_count']} sets (28 base + {len(pred['pm_sets'])} PM overlay)")
        print(f"{'='*70}")

    elif cmd == "dispatch":
        if len(sys.argv) < 3:
            print("Usage: pm_agent.py dispatch <agent-name>")
            print("\nAvailable agents:")
            for name, desc in pm.AGENTS.items():
                print(f"  {name}: {desc}")
            return

        agent = sys.argv[2]
        task = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Analyze and recommend improvements"

        dispatch = pm.dispatch_agent(agent, task)
        print(json.dumps(dispatch, indent=2))

    elif cmd == "agents":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else "list"

        if subcmd == "list" or subcmd == "agents":
            # List all agents
            info = pm.list_agents()
            print("\nAGENT REGISTRY")
            print("=" * 60)
            print(f"\nCore Agents ({len(info['core_agents'])}):")
            for name, desc in info["core_agents"].items():
                print(f"  [CORE] {name}")
                print(f"         {desc}")

            print(f"\nDynamic Agents ({info['slots_used']}/{info['slots_total']} slots):")
            if info["dynamic_agents"]:
                for name, agent in info["dynamic_agents"].items():
                    status = "[+] ACTIVE" if agent["status"] == "active" else "[-] INACTIVE"
                    print(f"  {status} {name}")
                    print(f"           Focus: {agent['focus']}")
                    print(f"           Tasks: {agent['tasks_completed']} | Created: {agent['created_at'][:10]}")
            else:
                print("  No dynamic agents created")
                print("  Run 'pm_agent.py agents auto' to create recommended agents")

        elif subcmd == "create":
            if len(sys.argv) < 4:
                print("Usage: pm_agent.py agents create <template> [custom-name]")
                print("\nAvailable templates:")
                for name, info in pm.AGENT_TEMPLATES.items():
                    print(f"  {name}")
                    print(f"    Focus: {info['focus']}")
                    print(f"    Triggers: {', '.join(info['triggers'])}")
                return

            template = sys.argv[3]
            custom_name = sys.argv[4] if len(sys.argv) > 4 else None
            result = pm.create_agent(template, custom_name)
            print(json.dumps(result, indent=2))

        elif subcmd == "auto":
            print("\nAUTO-CREATING RECOMMENDED AGENTS")
            print("=" * 50)
            actions = pm.auto_create_agents()
            if not actions:
                print("No agents to create (all recommended agents exist or slots full)")
            else:
                for action in actions:
                    rec = action["recommendation"]
                    result = action["result"]
                    status = "CREATED" if result.get("success") else "FAILED"
                    print(f"\n[{status}] {rec['template']}")
                    print(f"  Reason: {rec['reason']}")
                    if result.get("error"):
                        print(f"  Error: {result['error']}")

        elif subcmd == "deactivate":
            if len(sys.argv) < 4:
                print("Usage: pm_agent.py agents deactivate <agent-name>")
                print("\nActive dynamic agents:")
                for name, agent in pm.dynamic_agents.items():
                    if agent.status == "active":
                        print(f"  {name}")
                return

            result = pm.deactivate_agent(sys.argv[3])
            print(json.dumps(result, indent=2))

        elif subcmd == "delete":
            if len(sys.argv) < 4:
                print("Usage: pm_agent.py agents delete <agent-name>")
                print("\nDynamic agents:")
                for name in pm.dynamic_agents:
                    print(f"  {name}")
                return

            result = pm.delete_agent(sys.argv[3])
            print(json.dumps(result, indent=2))

        elif subcmd == "templates":
            print("\nAVAILABLE AGENT TEMPLATES")
            print("=" * 60)
            for name, info in pm.AGENT_TEMPLATES.items():
                print(f"\n{name}")
                print(f"  Focus: {info['focus']}")
                print(f"  Tools: {', '.join(info['tools'])}")
                print(f"  Triggers: {', '.join(info['triggers'])}")

        elif subcmd == "recommend":
            print("\nRECOMMENDED NEW AGENTS")
            print("=" * 50)
            recommendations = pm.evaluate_agent_needs()
            if not recommendations:
                print("No new agents recommended at this time")
            elif "message" in recommendations[0]:
                print(recommendations[0]["message"])
            else:
                for i, rec in enumerate(recommendations, 1):
                    print(f"\n{i}. [P{rec['priority']}] {rec['template']}")
                    print(f"   Reason: {rec['reason']}")

        else:
            print(f"Unknown agents subcommand: {subcmd}")
            print("Valid: list, create, auto, deactivate, delete, templates, recommend")

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")


if __name__ == "__main__":
    main()
